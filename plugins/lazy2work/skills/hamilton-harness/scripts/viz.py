"""F3 — Unified entry point. Runs F2 (validate), generates Hamilton stubs,
and optionally renders the DAG in Mermaid / Graphviz / Hamilton formats.

Usage:
    python viz.py dag_specs/<name>.yaml
    python viz.py dag_specs/<name>.yaml --format mermaid
    python viz.py dag_specs/<name>.yaml --format all
    python viz.py dag_specs/<name>.yaml --stub-only
    python viz.py dag_specs/<name>.yaml --no-stub
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).parent


def _run_validate(spec_path: Path) -> int:
    """Run validate.py and return its exit code."""
    cmd = [sys.executable, str(SCRIPT_DIR / "validate.py"), str(spec_path)]
    return subprocess.call(cmd)


def _generate_stub(spec: dict, spec_path: Path, output_dir: Path) -> list[str]:
    from yaml_to_hamilton_stub import generate

    name = spec.get("name") or spec_path.stem
    stub_out = output_dir / "stubs" / f"{name}_stub.py"
    schema_out = output_dir / "stubs" / "schemas.py" if spec.get("schemas") else None
    return generate(spec, str(stub_out),
                    schema_output=str(schema_out) if schema_out else None)


def _render_mermaid(spec: dict, output_dir: Path, spec_path: Path,
                    orient: str) -> list[str]:
    from yaml_to_mermaid import render

    name = spec.get("name") or spec_path.stem
    out = output_dir / "dags" / "spec" / f"{name}.mmd"
    render(spec, str(out), orient=orient)
    return [str(out)]


def _render_graphviz(spec: dict, output_dir: Path, spec_path: Path,
                     orient: str) -> list[str]:
    from yaml_to_graphviz import render

    name = spec.get("name") or spec_path.stem
    base = output_dir / "dags" / "spec" / name
    return render(spec, str(base), format="png", orient=orient)


def _render_hamilton(spec: dict, stub_paths: list[str],
                     output_dir: Path, spec_path: Path, orient: str) -> list[str]:
    """Import the generated stub and call Driver.display_all_functions()."""
    try:
        from hamilton import driver
    except ImportError:
        print("error: sf-hamilton not installed. Install with "
              "`pip install 'sf-hamilton[visualization]'`.", file=sys.stderr)
        return []

    import importlib.util

    stub_py = next((p for p in stub_paths if p.endswith("_stub.py")), None)
    if not stub_py:
        return []

    name = spec.get("name") or spec_path.stem
    spec_loader = importlib.util.spec_from_file_location(f"{name}_stub", stub_py)
    if spec_loader is None or spec_loader.loader is None:
        return []
    mod = importlib.util.module_from_spec(spec_loader)
    sys.modules[f"{name}_stub"] = mod
    try:
        spec_loader.loader.exec_module(mod)
    except Exception as e:
        print(f"warning: could not import stub for Hamilton render ({e}); skipping",
              file=sys.stderr)
        return []

    dr = driver.Builder().with_modules(mod).build()
    out_base = output_dir / "dags" / "spec" / f"{name}_hamilton"
    out_base.parent.mkdir(parents=True, exist_ok=True)
    dr.display_all_functions(
        output_file_path=str(out_base),
        render_kwargs={"format": "png"},
        orient=orient,
        deduplicate_inputs=True,
    )
    return [f"{out_base}.png"]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate + stub + (optional) render a hamilton-harness YAML spec.",
    )
    parser.add_argument("spec_path", type=Path)
    parser.add_argument("--format", default=None,
                        choices=["mermaid", "graphviz", "hamilton", "all"],
                        help="Render format. If omitted, only the stub is generated.")
    parser.add_argument("--output-dir", type=Path, default=Path("build"),
                        help="Base output directory (default: ./build)")
    parser.add_argument("--stub-only", action="store_true",
                        help="Generate stub only, do not render")
    parser.add_argument("--no-stub", action="store_true",
                        help="Skip stub generation, render only")
    parser.add_argument("--orient", default="TB", choices=["TB", "LR"])
    parser.add_argument("--skip-validate", action="store_true",
                        help="Skip the internal F2 check (not recommended)")
    args = parser.parse_args()

    if not args.spec_path.exists():
        print(f"error: spec file not found: {args.spec_path}", file=sys.stderr)
        sys.exit(3)

    # Step 1: F2 validation
    if not args.skip_validate:
        code = _run_validate(args.spec_path)
        if code != 0:
            print(f"\nvalidate.py failed with exit code {code}; aborting.",
                  file=sys.stderr)
            sys.exit(1)

    spec = yaml.safe_load(args.spec_path.read_text())
    out_dir = args.output_dir

    # Make scripts importable as siblings
    sys.path.insert(0, str(SCRIPT_DIR))

    produced: list[str] = []

    # Step 2: stub generation
    if not args.no_stub:
        produced += _generate_stub(spec, args.spec_path, out_dir)

    # Step 3: rendering
    if args.format and not args.stub_only:
        formats = ["mermaid", "graphviz", "hamilton"] if args.format == "all" else [args.format]
        for fmt in formats:
            try:
                if fmt == "mermaid":
                    produced += _render_mermaid(spec, out_dir, args.spec_path, args.orient)
                elif fmt == "graphviz":
                    if shutil.which("dot") is None:
                        print("warning: `dot` not on PATH; skipping graphviz render. "
                              "Install with `brew install graphviz`.", file=sys.stderr)
                        continue
                    produced += _render_graphviz(spec, out_dir, args.spec_path, args.orient)
                elif fmt == "hamilton":
                    stubs = [p for p in produced if p.endswith("_stub.py")]
                    produced += _render_hamilton(spec, stubs, out_dir, args.spec_path, args.orient)
            except Exception as e:
                print(f"warning: rendering {fmt} failed ({e})", file=sys.stderr)

    for p in produced:
        print(f"✓ {p}")


if __name__ == "__main__":
    main()
