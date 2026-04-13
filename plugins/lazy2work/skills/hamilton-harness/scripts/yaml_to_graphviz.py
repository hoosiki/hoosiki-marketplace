"""Render a hamilton-harness YAML spec to high-quality Graphviz output (PNG/SVG/PDF).

Requires the `graphviz` Python package and the `dot` binary on PATH.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

import yaml

try:
    from graphviz import Digraph
except ImportError:
    print("error: missing dependency `graphviz`. Install with `pip install graphviz` "
          "and ensure `dot` is on PATH (e.g., `brew install graphviz`).", file=sys.stderr)
    sys.exit(2)


_STYLE_INPUT = dict(shape="cylinder", style="filled",
                    fillcolor="#e8e8e8", color="#666", fontcolor="#222")
_STYLE_DEFAULT = dict(shape="box", style="rounded,filled",
                      fillcolor="#e6f0ff", color="#4477aa", fontcolor="#112244")
_STYLE_GUARDED = dict(shape="box", style="rounded,filled",
                      fillcolor="#d4f4dd", color="#2a7744", fontcolor="#113322")
_STYLE_CRITICAL = dict(shape="box", style="rounded,filled,bold",
                       fillcolor="#ffd9b3", color="#cc5500", fontcolor="#552200",
                       penwidth="2.5")


def _html_label(node: dict) -> str:
    name = node["name"]
    ntype = node.get("type", "Any")
    lines = [f"<b>{name}</b>",
             f'<font point-size="9" color="#555">: {ntype}</font>']
    for inv in node.get("invariants") or []:
        if "range" in inv:
            lo, hi = inv["range"]
            lines.append(f'<font point-size="8" color="#2a7">🛡 range [{lo}, {hi}]</font>')
        elif inv.get("no_nulls"):
            lines.append('<font point-size="8" color="#2a7">🛡 no nulls</font>')
        elif "values" in inv:
            lines.append(f'<font point-size="8" color="#2a7">🛡 values {inv["values"]}</font>')
    tags = node.get("tags") or {}
    if tags:
        kv = " · ".join(f"{k}={v}" for k, v in tags.items())
        lines.append(f'<font point-size="8" color="#888"><i>{kv}</i></font>')
    return "<" + "<br/>".join(lines) + ">"


def _pick_style(node: dict) -> dict:
    if node.get("source") == "input":
        return _STYLE_INPUT
    if (node.get("tags") or {}).get("importance") == "critical":
        return _STYLE_CRITICAL
    if node.get("invariants"):
        return _STYLE_GUARDED
    return _STYLE_DEFAULT


def render(spec: dict, output_base: str,
           format: str = "png", orient: str = "TB") -> list[str]:
    """Render to `<output_base>.<format>`. Returns list of files written."""
    dot = Digraph(
        name=spec.get("name", "pipeline"),
        format=format,
        graph_attr={
            "rankdir": orient,
            "bgcolor": "white",
            "fontname": "Helvetica",
            "label": f"<<b>{spec.get('name', 'pipeline')}</b>>",
            "labelloc": "t",
            "pad": "0.5",
            "ranksep": "0.7",
            "nodesep": "0.5",
        },
        node_attr={"fontname": "Helvetica"},
        edge_attr={"fontname": "Helvetica", "color": "#666", "arrowsize": "0.8"},
    )

    for node in spec.get("nodes", []):
        dot.node(node["name"], label=_html_label(node), **_pick_style(node))

    for node in spec.get("nodes", []):
        for parent in node.get("inputs", []) or []:
            dot.edge(parent, node["name"])

    Path(output_base).parent.mkdir(parents=True, exist_ok=True)
    out = dot.render(output_base, cleanup=True)
    return [out]


def _cli(argv: Iterable[str]) -> int:
    args = list(argv)
    if len(args) < 2:
        print("usage: yaml_to_graphviz.py <spec.yaml> <output_base> "
              "[--format png|svg|pdf] [--orient TB|LR]", file=sys.stderr)
        return 2
    spec_path, output_base = args[0], args[1]
    fmt = args[args.index("--format") + 1] if "--format" in args else "png"
    orient = args[args.index("--orient") + 1] if "--orient" in args else "TB"
    spec = yaml.safe_load(Path(spec_path).read_text())
    outputs = render(spec, output_base, format=fmt, orient=orient)
    for o in outputs:
        print(f"✓ wrote {o}")
    return 0


if __name__ == "__main__":
    sys.exit(_cli(sys.argv[1:]))
