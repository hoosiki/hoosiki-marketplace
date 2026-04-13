"""Generate Hamilton stub modules + Pydantic schemas from a YAML spec.

The stub functions all `raise NotImplementedError`; Hamilton still parses their
signatures to construct the DAG, so `display_all_functions()` works without any
implementation.

Imports are emitted **conditionally** based on which types appear in the spec —
the generated stub only imports what it actually uses. Supported ecosystems
include data analysis (pandas, polars, pyarrow, numpy, scipy.sparse), classical
ML (sklearn, xgboost, lightgbm, catboost), deep learning (tensorflow, keras,
pytorch, jax, onnx), NLP (transformers, datasets, sentence-transformers, spacy,
nltk, gensim), LangChain / vector stores, image processing (PIL, cv2), and the
Python stdlib (pathlib, datetime, io).
"""
from __future__ import annotations

import re
import sys
import textwrap
from pathlib import Path
from typing import Iterable

import yaml

# ---------------------------------------------------------------------------
# Type → Python annotation map
#
# Most entries are pass-through (the spec already uses the canonical Python
# name). The map exists mainly to:
#   1. Normalize stdlib aliases (e.g. `datetime.datetime` is unnecessary when
#      the stub does `from datetime import datetime`).
#   2. Provide a single source of truth for what counts as a "known" type.
# Anything not in the map is forwarded as-is to the generated annotation —
# this lets users use arbitrary user-defined classes without changing the map.
# ---------------------------------------------------------------------------

_BUILTIN_TYPES: dict[str, str] = {
    "int": "int", "float": "float", "complex": "complex",
    "str": "str", "bool": "bool",
    "bytes": "bytes", "bytearray": "bytearray", "memoryview": "memoryview",
    "list": "list", "dict": "dict", "tuple": "tuple",
    "set": "set", "frozenset": "frozenset", "range": "range",
    "object": "object", "None": "None", "Any": "Any",
}

_PATHLIB_TYPES: dict[str, str] = {
    "Path": "Path", "PurePath": "PurePath",
    "PosixPath": "PosixPath", "WindowsPath": "WindowsPath",
    "PurePosixPath": "PurePosixPath", "PureWindowsPath": "PureWindowsPath",
}

_DATETIME_TYPES: dict[str, str] = {
    "datetime": "datetime", "date": "date",
    "time": "time", "timedelta": "timedelta",
    "timezone": "timezone", "tzinfo": "tzinfo",
}

_IO_TYPES: dict[str, str] = {
    "BytesIO": "BytesIO", "StringIO": "StringIO",
    "TextIOWrapper": "TextIOWrapper",
    "BufferedReader": "BufferedReader", "BufferedWriter": "BufferedWriter",
    "FileIO": "FileIO",
}

_PYDANTIC_TYPES: dict[str, str] = {
    "BaseModel": "BaseModel", "pydantic.BaseModel": "BaseModel",
}

_HF_TRANSFORMERS_TYPES: dict[str, str] = {
    name: name for name in (
        "PreTrainedModel", "PreTrainedTokenizer", "PreTrainedTokenizerFast",
        "PreTrainedTokenizerBase", "PretrainedConfig",
        "AutoModel", "AutoModelForCausalLM", "AutoModelForMaskedLM",
        "AutoModelForSeq2SeqLM", "AutoModelForSequenceClassification",
        "AutoModelForTokenClassification", "AutoModelForQuestionAnswering",
        "AutoModelForImageClassification",
        "AutoTokenizer", "AutoConfig", "AutoFeatureExtractor", "AutoProcessor",
        "Pipeline", "BatchEncoding", "BatchFeature",
        "TrainingArguments", "Trainer", "Seq2SeqTrainingArguments",
    )
}

_SENTENCE_TRANSFORMERS_TYPES: dict[str, str] = {
    "SentenceTransformer": "SentenceTransformer",
    "CrossEncoder": "CrossEncoder",
}

_VECTOR_STORE_TYPES: dict[str, str] = {
    name: name for name in (
        "Chroma", "FAISS", "Pinecone", "Qdrant",
        "Weaviate", "Milvus", "Redis", "ElasticVectorSearch",
        "QdrantVectorStore", "ChromaVectorStore", "PineconeVectorStore",
        "InMemoryVectorStore",
    )
}

_TYPE_MAP: dict[str, str] = {
    **_BUILTIN_TYPES,
    **_PATHLIB_TYPES,
    **_DATETIME_TYPES,
    **_IO_TYPES,
    **_PYDANTIC_TYPES,
    **_HF_TRANSFORMERS_TYPES,
    **_SENTENCE_TRANSFORMERS_TYPES,
    **_VECTOR_STORE_TYPES,
    # Image (legacy aliases — prefer module-prefixed forms in new specs)
    "Image.Image": "Image.Image", "PIL.Image.Image": "PIL.Image.Image",
}


# ---------------------------------------------------------------------------
# Module aliases — a type prefix like "tf." or "pd." maps to an import line.
# Used to emit conditional imports based on which types appear in the spec.
# ---------------------------------------------------------------------------

_MODULE_ALIAS_IMPORTS: dict[str, str] = {
    # Data analysis
    "pd.": "import pandas as pd",
    "pl.": "import polars as pl",
    "pa.": "import pyarrow as pa",
    "np.": "import numpy as np",
    "sp.": "import scipy.sparse as sp",
    # Classical ML
    "sklearn.": "import sklearn",
    "xgb.": "import xgboost as xgb",
    "lgb.": "import lightgbm as lgb",
    "cb.": "import catboost as cb",
    # Deep learning
    "tf.": "import tensorflow as tf",
    "keras.": "import keras",
    "torch.": "import torch",
    "torchvision.": "import torchvision",
    "jax.": "import jax",
    "jnp.": "import jax.numpy as jnp",
    "onnx.": "import onnx",
    # NLP
    "spacy.": "import spacy",
    "nltk.": "import nltk",
    "gensim.": "import gensim",
    "datasets.": "import datasets",
    "langchain_core.": "import langchain_core",
    # Image
    "cv2.": "import cv2",
    "PIL.": "from PIL import Image",
}

# Bare (unprefixed) names → import lines.
# Order matters for grouping; emit stdlib first, then third-party.
_BARE_NAME_IMPORTS: dict[str, str] = {
    # stdlib — pathlib
    "Path": "from pathlib import Path",
    "PurePath": "from pathlib import PurePath",
    "PosixPath": "from pathlib import PosixPath",
    "WindowsPath": "from pathlib import WindowsPath",
    "PurePosixPath": "from pathlib import PurePosixPath",
    "PureWindowsPath": "from pathlib import PureWindowsPath",
    # stdlib — datetime
    "datetime": "from datetime import datetime",
    "date": "from datetime import date",
    "time": "from datetime import time",
    "timedelta": "from datetime import timedelta",
    "timezone": "from datetime import timezone",
    "tzinfo": "from datetime import tzinfo",
    # stdlib — io
    "BytesIO": "from io import BytesIO",
    "StringIO": "from io import StringIO",
    "TextIOWrapper": "from io import TextIOWrapper",
    "BufferedReader": "from io import BufferedReader",
    "BufferedWriter": "from io import BufferedWriter",
    "FileIO": "from io import FileIO",
    # stdlib — typing
    "Any": "from typing import Any",
    # pydantic
    "BaseModel": "from pydantic import BaseModel",
    # HuggingFace transformers
    **{name: f"from transformers import {name}" for name in _HF_TRANSFORMERS_TYPES},
    # sentence-transformers
    "SentenceTransformer": "from sentence_transformers import SentenceTransformer",
    "CrossEncoder": "from sentence_transformers import CrossEncoder",
    # LangChain vector stores — modern provider-specific packages.
    # Adjust the import path if your project pins different versions
    # (e.g. langchain_community.vectorstores).
    "Chroma": "from langchain_chroma import Chroma",
    "ChromaVectorStore": "from langchain_chroma import Chroma as ChromaVectorStore",
    "FAISS": "from langchain_community.vectorstores import FAISS",
    "Pinecone": "from langchain_pinecone import PineconeVectorStore as Pinecone",
    "PineconeVectorStore": "from langchain_pinecone import PineconeVectorStore",
    "Qdrant": "from langchain_qdrant import QdrantVectorStore as Qdrant",
    "QdrantVectorStore": "from langchain_qdrant import QdrantVectorStore",
    "Weaviate": "from langchain_community.vectorstores import Weaviate",
    "Milvus": "from langchain_community.vectorstores import Milvus",
    "Redis": "from langchain_community.vectorstores import Redis",
    "ElasticVectorSearch": "from langchain_community.vectorstores import ElasticVectorSearch",
    "InMemoryVectorStore": "from langchain_core.vectorstores import InMemoryVectorStore",
}


def _imports_for_types(types_used: set[str]) -> list[str]:
    """Resolve a set of used types to the minimum set of import statements.

    Args:
        types_used: Set of base type names extracted from the spec
            (subscripts already stripped, schemas excluded).

    Returns:
        Sorted, de-duplicated list of import statements grouped roughly as
        stdlib → third-party. Entries are joined with newlines by callers.

    Examples:
        >>> sorted(_imports_for_types({"pd.DataFrame", "Path"}))
        ['from pathlib import Path', 'import pandas as pd']
        >>> _imports_for_types(set())
        []
    """
    stdlib_imports: set[str] = set()
    third_party_imports: set[str] = set()

    # Module-prefixed types → use the alias import once per module
    for type_name in types_used:
        for prefix, import_line in _MODULE_ALIAS_IMPORTS.items():
            if type_name.startswith(prefix):
                third_party_imports.add(import_line)
                break

    # Bare names → use the explicit `from X import Y` line
    for type_name in types_used:
        # Only consider top-level names (no dot in the base part)
        if "." in type_name:
            continue
        if type_name in _BARE_NAME_IMPORTS:
            line = _BARE_NAME_IMPORTS[type_name]
            if line.startswith(("from pathlib", "from datetime",
                                "from io", "from typing")):
                stdlib_imports.add(line)
            else:
                third_party_imports.add(line)

    return sorted(stdlib_imports) + sorted(third_party_imports)


# ---------------------------------------------------------------------------
# Pydantic schema emission
# ---------------------------------------------------------------------------

def _field_annotation(field: dict) -> str:
    """Render the type annotation for a single Pydantic field.

    Args:
        field: A field spec dict (may contain `type`, `values`, `nullable`).

    Returns:
        The Python annotation string.

    Examples:
        >>> _field_annotation({"type": "str"})
        'str'
        >>> _field_annotation({"values": ["a", "b"]})
        "Literal['a', 'b']"
        >>> _field_annotation({"type": "int", "nullable": True})
        'Optional[int]'
    """
    if "values" in field:
        literal = ", ".join(repr(v) for v in field["values"])
        ann = f"Literal[{literal}]"
    else:
        ann = _TYPE_MAP.get(field.get("type", "object"), field.get("type", "object"))
    if field.get("nullable"):
        ann = f"Optional[{ann}]"
    return ann


def _field_options(field: dict) -> str:
    """Render the `Field(...)` constraint expression for a field.

    Args:
        field: A field spec dict (may contain ge/le/gt/lt/min_length/
            max_length/pattern/description/nullable).

    Returns:
        Either an empty string (no constraints) or a `Field(...)` expression.

    Examples:
        >>> _field_options({})
        ''
        >>> _field_options({"ge": 0, "le": 100})
        'Field(ge=0, le=100)'
    """
    opts: list[str] = []
    for k in ("ge", "le", "gt", "lt", "min_length", "max_length"):
        if k in field:
            opts.append(f"{k}={field[k]!r}")
    if "pattern" in field:
        opts.append(f"pattern={field['pattern']!r}")
    if "description" in field:
        opts.append(f"description={field['description']!r}")
    if field.get("nullable"):
        opts.append("default=None")
    if not opts:
        return ""
    return f"Field({', '.join(opts)})"


def _collect_schema_types(schemas: list[dict]) -> set[str]:
    """Collect the set of base type names referenced by all schema fields.

    Args:
        schemas: List of schema specs.

    Returns:
        Set of base type strings (subscripts stripped).

    Examples:
        >>> _collect_schema_types([{"name": "S", "fields": {"a": {"type": "int"}}}])
        {'int'}
    """
    types_used: set[str] = set()
    for schema in schemas:
        for fspec in (schema.get("fields") or {}).values():
            t = fspec.get("type")
            if not t:
                continue
            base = t.split("[", 1)[0].strip()
            if base:
                types_used.add(base)
    return types_used


def emit_pydantic_schemas(schemas: list[dict]) -> str:
    """Emit a Python module defining Pydantic models for each schema.

    Imports are scoped to the types actually used by the schemas — the
    module won't import pandas/numpy/etc. unless one of the field types
    needs them.

    Args:
        schemas: List of schema specs from the YAML.

    Returns:
        Python source code, or an empty string if no schemas were given.

    Examples:
        >>> emit_pydantic_schemas([])
        ''
        >>> "from pydantic import BaseModel, Field" in emit_pydantic_schemas(
        ...     [{"name": "S", "fields": {"x": {"type": "int"}}}]
        ... )
        True
    """
    if not schemas:
        return ""

    types_used = _collect_schema_types(schemas)
    type_imports = _imports_for_types(types_used)

    lines = [
        "from typing import Literal, Optional",
        "from pydantic import BaseModel, Field",
    ]
    if type_imports:
        lines.append("")
        lines.extend(type_imports)
    lines.append("")

    for schema in schemas:
        lines.append(f"class {schema['name']}(BaseModel):")
        if not schema.get("fields"):
            lines.append("    pass")
            lines.append("")
            continue
        for fname, fspec in schema["fields"].items():
            ann = _field_annotation(fspec)
            opts = _field_options(fspec)
            if opts:
                lines.append(f"    {fname}: {ann} = {opts}")
            else:
                lines.append(f"    {fname}: {ann}")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Hamilton stub emission
# ---------------------------------------------------------------------------

def _node_type(node: dict, schemas: set[str]) -> str:
    """Resolve a node's declared type to its Python annotation string.

    Args:
        node: A node spec dict.
        schemas: Set of declared schema names (left as-is when matched).

    Returns:
        The Python annotation string.

    Examples:
        >>> _node_type({"type": "pd.DataFrame"}, set())
        'pd.DataFrame'
        >>> _node_type({"type": "MyModel"}, {"MyModel"})
        'MyModel'
    """
    t = node.get("type", "object")
    if t in schemas:
        return t
    return _TYPE_MAP.get(t, t)


def _build_decorators(node: dict, ret_type: str) -> str:
    """Render the Hamilton decorator stack for a node.

    DataFrame returns receive `# TODO: @check_output_custom(...)` comments
    instead of `@check_output(...)` because Hamilton's built-in decorator
    doesn't support DataFrame outputs (use `@check_output_custom` with a
    `RowModelValidator` for those).

    Args:
        node: The node spec.
        ret_type: The resolved return-type annotation string.

    Returns:
        Newline-terminated decorator block, or empty string if no decorators.

    Examples:
        >>> _build_decorators({"invariants": [{"range": [0, 1]}]}, "float")
        '@check_output(range=(0, 1), importance="fail")\\n'
    """
    lines: list[str] = []
    df_return = ret_type == "pd.DataFrame"
    for inv in node.get("invariants") or []:
        if "range" in inv:
            lo, hi = inv["range"]
            if df_return:
                lines.append(f"# TODO: @check_output_custom(range=({lo}, {hi}))  # DataFrame")
            else:
                lines.append(f'@check_output(range=({lo}, {hi}), importance="fail")')
        elif inv.get("no_nulls"):
            if df_return:
                lines.append("# TODO: @check_output_custom(allow_nans=False)  # DataFrame")
            else:
                lines.append('@check_output(allow_nans=False, importance="fail")')
        elif "values" in inv or "regex" in inv:
            kind = "values" if "values" in inv else "regex"
            lines.append(f"# TODO: @check_output_custom({kind}={inv[kind]!r})")
    tags = node.get("tags") or {}
    if tags:
        kv = ", ".join(f'{k}="{v}"' for k, v in tags.items())
        lines.append(f"@tag({kv})")
    return "\n".join(lines) + ("\n" if lines else "")


def _params(node: dict, node_types: dict[str, str]) -> str:
    """Render the parameter list for a Hamilton node function.

    Args:
        node: The node spec.
        node_types: Map from node name to its resolved annotation string.

    Returns:
        Comma-separated parameter list, e.g. `a: int, b: pd.DataFrame`.

    Examples:
        >>> _params({"inputs": ["x"]}, {"x": "int"})
        'x: int'
        >>> _params({}, {})
        ''
    """
    parts = []
    for parent in node.get("inputs", []) or []:
        ann = node_types.get(parent, "object")
        parts.append(f"{parent}: {ann}")
    return ", ".join(parts)


_BASE_TYPE_RE = re.compile(r"[\w.]+")


def _collect_used_types(spec: dict, schemas: set[str]) -> set[str]:
    """Collect every base type name referenced by node `type` fields.

    Subscripts (`list[int]`) are stripped to their base. Declared schema
    names are excluded (they don't need a separate import).

    Args:
        spec: The full YAML spec.
        schemas: Set of declared schema names to exclude.

    Returns:
        Set of base type strings.

    Examples:
        >>> _collect_used_types({"nodes": [{"type": "pd.DataFrame"}]}, set())
        {'pd.DataFrame'}
        >>> _collect_used_types({"nodes": [{"type": "list[int]"}]}, set())
        {'int', 'list'}
    """
    types_used: set[str] = set()
    for node in spec.get("nodes", []):
        t = node.get("type", "")
        if not t:
            continue
        # Capture every word-like fragment so we catch types inside subscripts:
        # "list[pd.DataFrame]" → {"list", "pd.DataFrame"}.
        for m in _BASE_TYPE_RE.findall(t):
            if m and m not in schemas and m not in {"None", "Any"}:
                types_used.add(m)
    return types_used


def emit_hamilton_stub(spec: dict) -> str:
    """Emit a Hamilton stub module for every node in the spec.

    The header imports only the libraries actually needed by the node
    annotations (and unconditionally imports Hamilton's `check_output`/`tag`
    decorators since stubs always need them).

    Args:
        spec: The parsed YAML spec dict.

    Returns:
        Python source code for the stub module.

    Examples:
        >>> "raise NotImplementedError" in emit_hamilton_stub(
        ...     {"name": "p", "nodes": [{"name": "n", "type": "int"}]}
        ... )
        True
    """
    schemas = {s["name"] for s in spec.get("schemas", []) or []}
    node_types = {n["name"]: _node_type(n, schemas) for n in spec.get("nodes", [])}
    types_used = _collect_used_types(spec, schemas)
    type_imports = _imports_for_types(types_used)

    pipeline_name = spec.get("name", "pipeline")
    schema_import = (
        "from schemas import " + ", ".join(sorted(schemas))
        if schemas else ""
    )

    base_imports = ["from hamilton.function_modifiers import check_output, tag"]
    all_imports = type_imports + base_imports
    if schema_import:
        all_imports.append(schema_import)

    header = textwrap.dedent('''\
        """Auto-generated Hamilton stub for `{name}`.

        Regenerate with:
            python ${{CLAUDE_SKILL_DIR}}/scripts/viz.py <spec>.yaml

        Fill in the function bodies; the DAG structure is already correct.
        """
        ''').format(name=pipeline_name) + "\n".join(all_imports) + "\n"

    body_parts: list[str] = [header]

    for node in spec.get("nodes", []):
        if node.get("source") == "input":
            continue  # external inputs come via Driver.execute(inputs=...)

        params = _params(node, node_types)
        ret = _node_type(node, schemas)
        decorators = _build_decorators(node, ret)
        desc = (node.get("description") or "").replace('"', "'").replace("\n", " ")

        body_parts.append("\n")
        body_parts.append(decorators)
        body_parts.append(f"def {node['name']}({params}) -> {ret}:\n")
        body_parts.append(f'    """{desc}"""\n')
        body_parts.append(f'    raise NotImplementedError("TODO: implement {node["name"]}")\n')

    return "".join(body_parts)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def generate(spec: dict, output_stub: str,
             schema_output: str | None = None) -> list[str]:
    """Write the stub (and optionally a schemas module) to disk.

    Args:
        spec: The parsed YAML spec dict.
        output_stub: Destination path for the stub `.py` file.
        schema_output: Optional destination path for the schemas `.py` file.

    Returns:
        List of file paths that were written.

    Examples:
        >>> # Side-effecting; tested via integration tests in tests/.
    """
    written: list[str] = []

    # schemas first (stub imports from it)
    schema_code = emit_pydantic_schemas(spec.get("schemas", []) or [])
    if schema_code and schema_output:
        p = Path(schema_output)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(schema_code)
        written.append(str(p))

    stub_code = emit_hamilton_stub(spec)
    out = Path(output_stub)
    out.parent.mkdir(parents=True, exist_ok=True)
    (out.parent / "__init__.py").touch()
    out.write_text(stub_code)
    written.append(str(out))
    return written


def _cli(argv: Iterable[str]) -> int:
    """Entry point for direct script invocation.

    Args:
        argv: Argument list (without the program name).

    Returns:
        Process exit code (0 on success, 2 on usage error).

    Examples:
        >>> _cli([])
        2
    """
    args = list(argv)
    if len(args) < 2:
        print("usage: yaml_to_hamilton_stub.py <spec.yaml> <output_stub.py> "
              "[--schema-output schemas.py]", file=sys.stderr)
        return 2
    spec_path, stub_out = args[0], args[1]
    schema_out = None
    if "--schema-output" in args:
        schema_out = args[args.index("--schema-output") + 1]
    spec = yaml.safe_load(Path(spec_path).read_text())
    outputs = generate(spec, stub_out, schema_output=schema_out)
    for o in outputs:
        print(f"✓ wrote {o}")
    return 0


if __name__ == "__main__":
    sys.exit(_cli(sys.argv[1:]))
