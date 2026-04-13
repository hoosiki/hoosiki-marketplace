"""Dump Hamilton Driver metadata (node names, types, dependencies, tags) to JSON.

Used by CI / test_dag_matches_spec.py to verify the impl module's DAG matches
what the spec declares.
"""
from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import sys
from pathlib import Path


def _load_module(module_path: str):
    """Accept either a dotted path (`src.pipelines.churn`) or a file path."""
    path_obj = Path(module_path)
    if path_obj.exists() and path_obj.suffix == ".py":
        spec = importlib.util.spec_from_file_location(path_obj.stem, path_obj)
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load {module_path}")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    return importlib.import_module(module_path)


def dump(module_ref: str, output_path: str) -> dict:
    try:
        from hamilton import driver
    except ImportError:
        sys.exit("error: sf-hamilton is required. `pip install sf-hamilton[visualization]`.")

    module = _load_module(module_ref)
    dr = driver.Builder().with_modules(module).build()

    meta = []
    for node in dr.list_available_variables():
        meta.append({
            "name": node.name,
            "type": str(node.type),
            "deps": sorted(node.required_dependencies or []),
            "tags": dict(sorted((node.tags or {}).items())),
        })
    meta.sort(key=lambda n: n["name"])

    payload = {"module": module_ref, "nodes": meta, "count": len(meta)}
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Dump Hamilton Driver metadata.")
    parser.add_argument("module", help="Module path (dotted or file)")
    parser.add_argument("output", help="Output JSON file")
    args = parser.parse_args()
    payload = dump(args.module, args.output)
    print(f"✓ wrote {args.output} ({payload['count']} nodes)")


if __name__ == "__main__":
    main()
