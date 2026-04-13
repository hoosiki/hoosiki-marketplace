"""Generate Hamilton stub modules + Pydantic schemas from a YAML spec.

The stub functions all `raise NotImplementedError`; Hamilton still parses their
signatures to construct the DAG, so `display_all_functions()` works without any
implementation.
"""
from __future__ import annotations

import sys
import textwrap
from pathlib import Path
from typing import Iterable

import yaml

# ----- Pydantic emission ------------------------------------------------------

_TYPE_MAP = {
    "int": "int", "float": "float", "str": "str", "bool": "bool",
    "bytes": "bytes", "list": "list", "dict": "dict", "tuple": "tuple",
    "set": "set", "object": "object", "None": "None",
    "datetime": "datetime", "date": "date",
    "time": "time", "timedelta": "timedelta",
    "pd.DataFrame": "pd.DataFrame", "pd.Series": "pd.Series",
    "np.ndarray": "np.ndarray",
    "Path": "Path", "PurePath": "PurePath",
}


def _field_annotation(field: dict) -> str:
    if "values" in field:
        literal = ", ".join(repr(v) for v in field["values"])
        ann = f"Literal[{literal}]"
    else:
        ann = _TYPE_MAP.get(field.get("type", "object"), field.get("type", "object"))
    if field.get("nullable"):
        ann = f"Optional[{ann}]"
    return ann


def _field_options(field: dict) -> str:
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


def emit_pydantic_schemas(schemas: list[dict]) -> str:
    if not schemas:
        return ""
    lines = ["from typing import Literal, Optional",
             "from datetime import datetime, date, time, timedelta",
             "from pathlib import Path, PurePath",
             "import numpy as np",
             "import pandas as pd",
             "from pydantic import BaseModel, Field",
             ""]
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


# ----- Hamilton stub emission --------------------------------------------------

def _node_type(node: dict, schemas: set[str]) -> str:
    t = node.get("type", "object")
    if t in schemas:
        return t
    return _TYPE_MAP.get(t, t)


def _build_decorators(node: dict, ret_type: str) -> str:
    lines: list[str] = []
    # Hamilton's built-in @check_output(range=, allow_nans=) doesn't support
    # DataFrame returns — emit those invariants as TODO comments so the Driver
    # can still build (@check_output_custom with a RowModelValidator is the
    # supported path for DataFrames).
    df_return = ret_type == "pd.DataFrame"
    for inv in node.get("invariants") or []:
        if "range" in inv:
            lo, hi = inv["range"]
            if df_return:
                lines.append(f'# TODO: @check_output_custom(range=({lo}, {hi}))  # DataFrame')
            else:
                lines.append(f'@check_output(range=({lo}, {hi}), importance="fail")')
        elif inv.get("no_nulls"):
            if df_return:
                lines.append('# TODO: @check_output_custom(allow_nans=False)  # DataFrame')
            else:
                lines.append('@check_output(allow_nans=False, importance="fail")')
        elif "values" in inv or "regex" in inv:
            kind = "values" if "values" in inv else "regex"
            lines.append(f'# TODO: @check_output_custom({kind}={inv[kind]!r})')
    tags = node.get("tags") or {}
    if tags:
        kv = ", ".join(f'{k}="{v}"' for k, v in tags.items())
        lines.append(f"@tag({kv})")
    return "\n".join(lines) + ("\n" if lines else "")


def _params(node: dict, node_types: dict[str, str]) -> str:
    parts = []
    for parent in node.get("inputs", []) or []:
        ann = node_types.get(parent, "object")
        parts.append(f"{parent}: {ann}")
    return ", ".join(parts)


def emit_hamilton_stub(spec: dict) -> str:
    schemas = {s["name"] for s in spec.get("schemas", []) or []}
    node_types = {n["name"]: _node_type(n, schemas) for n in spec.get("nodes", [])}

    pipeline_name = spec.get("name", "pipeline")
    schema_import = (
        "from schemas import " + ", ".join(sorted(schemas))
        if schemas else ""
    )

    header = textwrap.dedent(f'''\
        """Auto-generated Hamilton stub for `{pipeline_name}`.

        Regenerate with:
            python ${{CLAUDE_SKILL_DIR}}/scripts/viz.py <spec>.yaml

        Fill in the function bodies; the DAG structure is already correct.
        """
        import datetime
        from pathlib import Path, PurePath
        import numpy as np
        import pandas as pd
        from hamilton.function_modifiers import check_output, tag
        {schema_import}
        ''')

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


# ----- orchestration ---------------------------------------------------------

def generate(spec: dict, output_stub: str,
             schema_output: str | None = None) -> list[str]:
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
