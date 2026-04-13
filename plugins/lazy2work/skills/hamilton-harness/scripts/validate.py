"""F2 — Standalone validator for hamilton-harness YAML specs.

Runs seven layers of validation:
    L1 jsonschema    (templates/spec-schema.json)
    L2 name uniqueness
    L3 cycle detection
    L4 orphan nodes
    L5 dangling references
    L6 type resolution
    L7 invariant syntax

Usage:
    python validate.py dag_specs/<name>.yaml [--strict] [--json] [--schema PATH]

Exit codes:
    0  valid
    1  jsonschema violation (L1)
    2  semantic validation failed (L2–L7)
    3  file not found / parse error
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import jsonschema
    import yaml
except ImportError as e:
    print(f"error: missing dependency {e.name}. Install with `pip install pyyaml jsonschema`.",
          file=sys.stderr)
    sys.exit(3)

# networkx is optional — fall back to a hand-rolled cycle check if absent
try:
    import networkx as nx
    HAVE_NETWORKX = True
except ImportError:
    HAVE_NETWORKX = False

# ----- built-in type set for L6 ----------------------------------------------
# Organized by ecosystem so new libraries can be added in isolation.
# When you add a new type here, also extend `_TYPE_MAP` and `_IMPORTS_FOR`
# in yaml_to_hamilton_stub.py so the stub generator emits the right imports.

# stdlib
BUILTIN_TYPES: set[str] = {
    "int", "float", "complex", "str", "bool", "bytes", "bytearray", "memoryview",
    "list", "dict", "tuple", "set", "frozenset", "range",
    "object", "None", "Any",
}
PATHLIB_TYPES: set[str] = {
    "Path", "PurePath", "PosixPath", "WindowsPath",
    "PurePosixPath", "PureWindowsPath",
}
DATETIME_TYPES: set[str] = {
    "datetime", "date", "time", "timedelta", "timezone", "tzinfo",
}
IO_TYPES: set[str] = {
    "BytesIO", "StringIO",
    "TextIOWrapper", "BufferedReader", "BufferedWriter", "FileIO",
}

# Data analysis — tabular
PANDAS_TYPES: set[str] = {
    "pd.DataFrame", "pd.Series",
    "pd.Index", "pd.MultiIndex", "pd.RangeIndex",
    "pd.DatetimeIndex", "pd.TimedeltaIndex", "pd.PeriodIndex", "pd.IntervalIndex",
    "pd.Categorical", "pd.CategoricalIndex",
    "pd.Timestamp", "pd.Timedelta", "pd.Period", "pd.Interval",
    "pd.Grouper", "pd.NaT",
}
POLARS_TYPES: set[str] = {
    "pl.DataFrame", "pl.LazyFrame", "pl.Series", "pl.Expr", "pl.DataType",
}
PYARROW_TYPES: set[str] = {
    "pa.Table", "pa.RecordBatch", "pa.Array", "pa.ChunkedArray",
    "pa.Schema", "pa.Field", "pa.DataType",
}

# Numerical computing
NUMPY_TYPES: set[str] = {"np.ndarray", "np.matrix", "np.recarray",
                         "np.ma.MaskedArray", "np.dtype", "np.generic",
                         "np.number", "np.integer", "np.floating", "np.complexfloating"}
NUMPY_DTYPES: set[str] = {f"np.{t}" for t in (
    "int8", "int16", "int32", "int64", "intp",
    "uint8", "uint16", "uint32", "uint64", "uintp",
    "float16", "float32", "float64", "float128",
    "complex64", "complex128", "complex256",
    "bool_", "byte", "ubyte", "short", "ushort",
    "intc", "uintc", "longlong", "ulonglong",
    "half", "single", "double", "longdouble",
    "csingle", "cdouble", "clongdouble",
    "str_", "bytes_", "void", "object_",
)}
SCIPY_SPARSE_TYPES: set[str] = {
    "sp.csr_matrix", "sp.csc_matrix", "sp.coo_matrix",
    "sp.lil_matrix", "sp.dok_matrix", "sp.bsr_matrix",
    "sp.dia_matrix", "sp.spmatrix",
}

# Classical ML
SKLEARN_TYPES: set[str] = {
    "sklearn.base.BaseEstimator", "sklearn.pipeline.Pipeline",
    "sklearn.pipeline.FeatureUnion", "sklearn.compose.ColumnTransformer",
    "BaseEstimator", "ClassifierMixin", "RegressorMixin",
    "TransformerMixin", "ClusterMixin", "Pipeline",
    "FeatureUnion", "ColumnTransformer",
    "StandardScaler", "MinMaxScaler", "RobustScaler",
    "OneHotEncoder", "LabelEncoder", "OrdinalEncoder",
    "TfidfVectorizer", "CountVectorizer",
}
XGBOOST_TYPES: set[str] = {
    "xgb.Booster", "xgb.DMatrix", "xgb.QuantileDMatrix",
    "xgb.XGBClassifier", "xgb.XGBRegressor", "xgb.XGBRanker", "xgb.XGBRFRegressor",
}
LIGHTGBM_TYPES: set[str] = {
    "lgb.Booster", "lgb.Dataset",
    "lgb.LGBMClassifier", "lgb.LGBMRegressor", "lgb.LGBMRanker",
}
CATBOOST_TYPES: set[str] = {
    "cb.CatBoost", "cb.Pool",
    "cb.CatBoostClassifier", "cb.CatBoostRegressor", "cb.CatBoostRanker",
}

# Deep learning
TENSORFLOW_TYPES: set[str] = {
    "tf.Tensor", "tf.Variable", "tf.SparseTensor", "tf.RaggedTensor",
    "tf.TensorArray", "tf.TensorSpec", "tf.dtypes.DType",
    "tf.data.Dataset", "tf.data.Iterator",
    "tf.keras.Model", "tf.keras.Sequential",
    "tf.keras.layers.Layer", "tf.keras.losses.Loss",
    "tf.keras.optimizers.Optimizer", "tf.keras.callbacks.Callback",
    "tf.keras.metrics.Metric", "tf.keras.utils.Sequence",
    "tf.train.Checkpoint", "tf.saved_model.SavedModel",
}
KERAS_TYPES: set[str] = {
    "keras.Model", "keras.Sequential",
    "keras.layers.Layer", "keras.losses.Loss",
    "keras.optimizers.Optimizer", "keras.callbacks.Callback",
    "keras.metrics.Metric", "keras.Input",
}
PYTORCH_TYPES: set[str] = {
    "torch.Tensor", "torch.nn.Module", "torch.nn.Parameter",
    "torch.utils.data.Dataset", "torch.utils.data.DataLoader",
    "torch.utils.data.IterableDataset", "torch.utils.data.Sampler",
    "torch.optim.Optimizer", "torch.optim.lr_scheduler.LRScheduler",
    "torch.optim.lr_scheduler._LRScheduler",
    "torch.cuda.Stream", "torch.cuda.Event",
    "torch.device", "torch.dtype", "torch.Size", "torch.Generator",
    "torch.distributions.Distribution",
    "torchvision.transforms.Compose", "torchvision.datasets.VisionDataset",
}
JAX_TYPES: set[str] = {
    "jax.Array", "jnp.ndarray", "jax.numpy.ndarray",
    "jax.random.PRNGKey", "jax.tree_util.PyTreeDef",
}
ONNX_TYPES: set[str] = {
    "onnx.ModelProto", "onnx.GraphProto", "onnx.TensorProto", "onnx.NodeProto",
}

# NLP — HuggingFace
HF_TRANSFORMERS_TYPES: set[str] = {
    "PreTrainedModel", "PreTrainedTokenizer", "PreTrainedTokenizerFast",
    "PreTrainedTokenizerBase", "PretrainedConfig", "PreTrainedFeatureExtractor",
    "AutoModel", "AutoModelForCausalLM", "AutoModelForMaskedLM",
    "AutoModelForSeq2SeqLM", "AutoModelForSequenceClassification",
    "AutoModelForTokenClassification", "AutoModelForQuestionAnswering",
    "AutoModelForImageClassification",
    "AutoTokenizer", "AutoConfig", "AutoFeatureExtractor", "AutoProcessor",
    "Pipeline", "BatchEncoding", "BatchFeature",
    "TrainingArguments", "Trainer", "Seq2SeqTrainingArguments",
}
HF_DATASETS_TYPES: set[str] = {
    "datasets.Dataset", "datasets.DatasetDict",
    "datasets.IterableDataset", "datasets.IterableDatasetDict",
    "datasets.Features", "datasets.ClassLabel", "datasets.Value",
}
SENTENCE_TRANSFORMERS_TYPES: set[str] = {"SentenceTransformer", "CrossEncoder"}

# NLP — others
SPACY_TYPES: set[str] = {
    "spacy.Language", "spacy.tokens.Doc", "spacy.tokens.Span",
    "spacy.tokens.Token", "spacy.vocab.Vocab", "spacy.lexeme.Lexeme",
}
NLTK_TYPES: set[str] = {
    "nltk.Text", "nltk.FreqDist", "nltk.ConditionalFreqDist",
}
GENSIM_TYPES: set[str] = {
    "gensim.models.KeyedVectors", "gensim.models.Word2Vec",
    "gensim.models.Doc2Vec", "gensim.models.FastText",
    "gensim.models.LdaModel", "gensim.models.TfidfModel",
    "gensim.corpora.Dictionary",
}

# LangChain / RAG / vector stores
LANGCHAIN_TYPES: set[str] = {
    "langchain_core.documents.Document",
    "langchain_core.messages.BaseMessage", "langchain_core.messages.AIMessage",
    "langchain_core.messages.HumanMessage", "langchain_core.messages.SystemMessage",
    "langchain_core.language_models.BaseLanguageModel",
    "langchain_core.language_models.BaseChatModel",
    "langchain_core.embeddings.Embeddings",
    "langchain_core.retrievers.BaseRetriever",
    "langchain_core.vectorstores.VectorStore",
    "langchain_core.tools.BaseTool",
    "langchain_core.runnables.Runnable", "langchain_core.runnables.RunnableSequence",
    "langchain_core.output_parsers.BaseOutputParser",
}
VECTOR_STORE_TYPES: set[str] = {
    "Chroma", "FAISS", "Pinecone", "Qdrant",
    "Weaviate", "Milvus", "Redis", "ElasticVectorSearch",
    "QdrantVectorStore", "ChromaVectorStore", "PineconeVectorStore",
    "InMemoryVectorStore",
}

# Image processing
IMAGE_TYPES: set[str] = {
    "PIL.Image.Image", "Image.Image",
    "cv2.Mat", "cv2.UMat",
}

# Validation / serialization
PYDANTIC_TYPES: set[str] = {"pydantic.BaseModel", "BaseModel"}


# ----- data classes -----------------------------------------------------------

@dataclass
class Issue:
    layer: str           # "L1".."L7"
    severity: str        # "error" | "warning"
    message: str
    location: str = ""   # optional breadcrumb

    def as_dict(self) -> dict[str, str]:
        return {"layer": self.layer, "severity": self.severity,
                "message": self.message, "location": self.location}


@dataclass
class Report:
    spec_path: str
    layers_passed: list[str] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)
    node_count: int = 0

    @property
    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == "warning"]

    def passed(self, strict: bool) -> bool:
        if self.errors:
            return False
        if strict and self.warnings:
            return False
        return True


# ----- validation layers ------------------------------------------------------

def layer_1_schema(spec: dict, schema: dict, report: Report) -> bool:
    """L1: jsonschema validation. Returns True if passed."""
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(spec), key=lambda e: e.path)
    if not errors:
        report.layers_passed.append("L1")
        return True
    for err in errors:
        location = "/".join(str(p) for p in err.absolute_path) or "<root>"
        report.issues.append(Issue("L1", "error", err.message, location))
    return False


def layer_2_uniqueness(spec: dict, report: Report) -> bool:
    seen: dict[str, int] = {}
    for i, node in enumerate(spec.get("nodes", [])):
        name = node.get("name")
        if name in seen:
            report.issues.append(Issue(
                "L2", "error",
                f"duplicate node name '{name}' at indices {seen[name]} and {i}",
                f"nodes[{i}]",
            ))
        else:
            seen[name] = i
    if any(i.layer == "L2" for i in report.issues):
        return False
    report.layers_passed.append("L2")
    return True


def _build_edges(spec: dict) -> list[tuple[str, str]]:
    edges = []
    for node in spec.get("nodes", []):
        for parent in node.get("inputs", []) or []:
            edges.append((parent, node["name"]))
    return edges


def layer_3_cycles(spec: dict, report: Report) -> bool:
    edges = _build_edges(spec)
    if HAVE_NETWORKX:
        g = nx.DiGraph()
        g.add_edges_from(edges)
        try:
            cycles = list(nx.simple_cycles(g))
        except nx.NetworkXNoCycle:
            cycles = []
    else:
        cycles = _manual_cycle_check(edges)

    if cycles:
        for cycle in cycles[:5]:  # cap at 5
            path = " -> ".join(cycle + [cycle[0]])
            report.issues.append(Issue("L3", "error", f"cycle detected: {path}"))
        return False
    report.layers_passed.append("L3")
    return True


def _manual_cycle_check(edges: list[tuple[str, str]]) -> list[list[str]]:
    """Simple DFS-based cycle detection when networkx is unavailable."""
    adj: dict[str, list[str]] = {}
    for a, b in edges:
        adj.setdefault(a, []).append(b)
    cycles = []
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {n: WHITE for n in adj}

    def dfs(n: str, stack: list[str]) -> None:
        color[n] = GRAY
        stack.append(n)
        for m in adj.get(n, []):
            if color.get(m, WHITE) == WHITE:
                dfs(m, stack)
            elif color.get(m) == GRAY and m in stack:
                idx = stack.index(m)
                cycles.append(stack[idx:])
        stack.pop()
        color[n] = BLACK

    for n in list(adj):
        if color.get(n, WHITE) == WHITE:
            dfs(n, [])
    return cycles


def layer_4_orphans(spec: dict, report: Report, strict: bool) -> bool:
    """Nodes without `source: input` and without `inputs`. Warn (error in strict)."""
    orphans = []
    for node in spec.get("nodes", []):
        has_source = node.get("source") == "input"
        has_inputs = bool(node.get("inputs"))
        if not has_source and not has_inputs:
            orphans.append(node["name"])
    severity = "error" if strict else "warning"
    for name in orphans:
        report.issues.append(Issue("L4", severity,
                                   f"node '{name}' has neither `source: input` nor `inputs`"))
    if not orphans:
        report.layers_passed.append("L4")
        return True
    return severity != "error"


def layer_5_dangling(spec: dict, report: Report) -> bool:
    names = {n["name"] for n in spec.get("nodes", [])}
    bad = False
    for node in spec.get("nodes", []):
        for parent in node.get("inputs", []) or []:
            if parent not in names:
                report.issues.append(Issue(
                    "L5", "error",
                    f"node '{node['name']}' references unknown input '{parent}'",
                ))
                bad = True
    if not bad:
        report.layers_passed.append("L5")
    return not bad


def layer_6_types(spec: dict, report: Report, strict: bool) -> bool:
    """Check every `type` resolves to a builtin, a recognized library type,
    or a declared schema.

    Recognized ecosystems (see the type set definitions above):
        stdlib: builtins, pathlib, datetime, io
        data analysis: pandas, polars, pyarrow, numpy (incl. dtypes), scipy.sparse
        classical ML: sklearn, xgboost, lightgbm, catboost
        deep learning: tensorflow, keras, pytorch, jax, onnx
        NLP: huggingface transformers/datasets, sentence-transformers,
             spacy, nltk, gensim
        RAG / vector stores: langchain_core, common vector store classes
        image: PIL, cv2
        validation: pydantic
    """
    declared_schemas = {s["name"] for s in spec.get("schemas", []) or []}
    known = (
        BUILTIN_TYPES | PATHLIB_TYPES | DATETIME_TYPES | IO_TYPES
        | PANDAS_TYPES | POLARS_TYPES | PYARROW_TYPES
        | NUMPY_TYPES | NUMPY_DTYPES | SCIPY_SPARSE_TYPES
        | SKLEARN_TYPES | XGBOOST_TYPES | LIGHTGBM_TYPES | CATBOOST_TYPES
        | TENSORFLOW_TYPES | KERAS_TYPES | PYTORCH_TYPES | JAX_TYPES | ONNX_TYPES
        | HF_TRANSFORMERS_TYPES | HF_DATASETS_TYPES | SENTENCE_TRANSFORMERS_TYPES
        | SPACY_TYPES | NLTK_TYPES | GENSIM_TYPES
        | LANGCHAIN_TYPES | VECTOR_STORE_TYPES
        | IMAGE_TYPES | PYDANTIC_TYPES
        | declared_schemas
    )

    unresolved = []
    for node in spec.get("nodes", []):
        t = node.get("type", "")
        # strip subscripts like list[int]
        base = t.split("[", 1)[0].strip()
        if base and base not in known:
            unresolved.append((node["name"], t))

    severity = "error" if strict else "warning"
    for name, t in unresolved:
        report.issues.append(Issue(
            "L6", severity,
            f"node '{name}' uses unresolved type '{t}'",
        ))
    if not unresolved:
        report.layers_passed.append("L6")
        return True
    return severity != "error"


def layer_7_invariants(spec: dict, report: Report) -> bool:
    """Each invariant must be a single-key dict with a recognized shape."""
    bad = False
    for node in spec.get("nodes", []):
        for j, inv in enumerate(node.get("invariants", []) or []):
            if not isinstance(inv, dict) or len(inv) != 1:
                report.issues.append(Issue(
                    "L7", "error",
                    f"invariant {j} on node '{node['name']}' must be a single-key dict",
                ))
                bad = True
                continue
            (key, value), = inv.items()
            if key == "range":
                if not (isinstance(value, list) and len(value) == 2
                        and all(isinstance(v, (int, float)) for v in value)):
                    report.issues.append(Issue(
                        "L7", "error",
                        f"invariant `range` on '{node['name']}' must be [lo, hi] numeric",
                    ))
                    bad = True
            elif key == "no_nulls":
                if not isinstance(value, bool):
                    report.issues.append(Issue(
                        "L7", "error",
                        f"invariant `no_nulls` on '{node['name']}' must be boolean",
                    ))
                    bad = True
            elif key == "values":
                if not (isinstance(value, list) and value):
                    report.issues.append(Issue(
                        "L7", "error",
                        f"invariant `values` on '{node['name']}' must be a non-empty list",
                    ))
                    bad = True
            elif key == "regex":
                if not isinstance(value, str):
                    report.issues.append(Issue(
                        "L7", "error",
                        f"invariant `regex` on '{node['name']}' must be a string",
                    ))
                    bad = True
            else:
                report.issues.append(Issue(
                    "L7", "error",
                    f"unknown invariant kind '{key}' on '{node['name']}'",
                ))
                bad = True
    if not bad:
        report.layers_passed.append("L7")
    return not bad


# ----- main orchestration -----------------------------------------------------

def validate(spec_path: Path, schema_path: Path, strict: bool) -> Report:
    try:
        spec = yaml.safe_load(spec_path.read_text())
    except FileNotFoundError:
        sys.exit(f"error: spec file not found: {spec_path}")
    except yaml.YAMLError as e:
        sys.exit(f"error: malformed YAML: {e}")

    try:
        schema = json.loads(schema_path.read_text())
    except FileNotFoundError:
        sys.exit(f"error: schema file not found: {schema_path}")

    report = Report(spec_path=str(spec_path))
    report.node_count = len(spec.get("nodes", []))

    # L1 is fatal — no point running L2-7 if the document structure is broken
    if not layer_1_schema(spec, schema, report):
        return report

    # Remaining layers are independent; run them all to collect as much feedback as possible
    layer_2_uniqueness(spec, report)
    layer_3_cycles(spec, report)
    layer_4_orphans(spec, report, strict)
    layer_5_dangling(spec, report)
    layer_6_types(spec, report, strict)
    layer_7_invariants(spec, report)
    return report


# ----- output formatting ------------------------------------------------------

def _print_human(report: Report, strict: bool) -> None:
    name = Path(report.spec_path).name
    print(f"hamilton-harness validate: {name}\n")
    for layer in ("L1", "L2", "L3", "L4", "L5", "L6", "L7"):
        if layer in report.layers_passed:
            detail = f" ({report.node_count} nodes)" if layer == "L1" else ""
            print(f"  ✓ {layer}{detail}")
        else:
            layer_issues = [i for i in report.issues if i.layer == layer]
            if layer_issues:
                print(f"  ✗ {layer}")
                for issue in layer_issues:
                    loc = f" [{issue.location}]" if issue.location else ""
                    print(f"      {issue.severity}: {issue.message}{loc}")
    print()
    status = "PASSED" if report.passed(strict) else "FAILED"
    print(f"{status} with {len(report.errors)} errors, {len(report.warnings)} warnings.")


def _print_json(report: Report, strict: bool) -> None:
    payload = {
        "spec_path": report.spec_path,
        "layers_passed": report.layers_passed,
        "errors": [i.as_dict() for i in report.errors],
        "warnings": [i.as_dict() for i in report.warnings],
        "node_count": report.node_count,
        "passed": report.passed(strict),
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def main() -> None:
    here = Path(__file__).parent
    default_schema = (here.parent / "templates" / "spec-schema.json").resolve()

    parser = argparse.ArgumentParser(description="Validate a hamilton-harness YAML spec.")
    parser.add_argument("spec_path", type=Path, help="Path to the YAML spec file")
    parser.add_argument("--schema", type=Path, default=default_schema,
                        help="Custom JSON schema file (default: bundled spec-schema.json)")
    parser.add_argument("--strict", action="store_true",
                        help="Treat warnings (L4, L6) as errors")
    parser.add_argument("--json", action="store_true",
                        help="Emit a JSON report on stdout")
    args = parser.parse_args()

    report = validate(args.spec_path, args.schema, args.strict)

    if args.json:
        _print_json(report, args.strict)
    else:
        _print_human(report, args.strict)

    if report.errors:
        # distinguish L1 (jsonschema) from the rest (L2-L7)
        if any(i.layer == "L1" for i in report.errors):
            sys.exit(1)
        sys.exit(2)
    if args.strict and report.warnings:
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
