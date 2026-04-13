"""Render a hamilton-harness YAML spec to Mermaid flowchart syntax.

Designed for inline display in chat / PR comments / Obsidian. Mermaid is fast,
text-based, and renders natively on GitHub and many other platforms.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

import yaml


def _safe_label(text: str) -> str:
    return text.replace('"', "'").replace("\n", " ")


def _node_decl(node: dict) -> str:
    name = node["name"]
    ntype = node.get("type", "Any")
    label_lines = [f"<b>{name}</b>", f"<i>{ntype}</i>"]
    invs = node.get("invariants") or []
    for inv in invs:
        if "range" in inv:
            lo, hi = inv["range"]
            label_lines.append(f"🛡 range [{lo}, {hi}]")
        elif inv.get("no_nulls"):
            label_lines.append("🛡 no nulls")
        elif "values" in inv:
            label_lines.append(f"🛡 ∈ {inv['values']}")
    tags = node.get("tags") or {}
    if tags:
        label_lines.append("<small>" + ", ".join(f"{k}={v}" for k, v in tags.items()) + "</small>")
    label = "<br/>".join(_safe_label(l) for l in label_lines)

    if node.get("source") == "input":
        return f'    {name}([{label}])'
    return f'    {name}["{label}"]'


def render(spec: dict, output_path: str, orient: str = "TB") -> None:
    lines: list[str] = []
    lines.append("```mermaid")
    lines.append(f"flowchart {orient}")

    for node in spec.get("nodes", []):
        lines.append(_node_decl(node))

    lines.append("")

    for node in spec.get("nodes", []):
        for parent in node.get("inputs", []) or []:
            lines.append(f"    {parent} --> {node['name']}")

    # simple style classes
    lines.append("")
    lines.append("    classDef input fill:#e0e0e0,stroke:#666,color:#222")
    lines.append("    classDef guarded fill:#d4f4dd,stroke:#2a7,color:#113")
    lines.append("    classDef critical fill:#ffd9b3,stroke:#c50,color:#522,stroke-width:2px")
    for node in spec.get("nodes", []):
        if node.get("source") == "input":
            lines.append(f"    class {node['name']} input")
        elif (node.get("tags") or {}).get("importance") == "critical":
            lines.append(f"    class {node['name']} critical")
        elif node.get("invariants"):
            lines.append(f"    class {node['name']} guarded")

    lines.append("```")

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n")


def _cli(argv: Iterable[str]) -> int:
    args = list(argv)
    if len(args) < 2:
        print("usage: yaml_to_mermaid.py <spec.yaml> <output.mmd> [--orient TB|LR]",
              file=sys.stderr)
        return 2
    spec_path, output = args[0], args[1]
    orient = "TB"
    if "--orient" in args:
        orient = args[args.index("--orient") + 1]
    spec = yaml.safe_load(Path(spec_path).read_text())
    render(spec, output, orient=orient)
    print(f"✓ wrote {output}")
    return 0


if __name__ == "__main__":
    sys.exit(_cli(sys.argv[1:]))
