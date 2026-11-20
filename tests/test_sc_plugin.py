"""Structural checks for the `sc` Hermes plugin (Agent Plugins v1 layout).

The plugin is generated, so these tests guard what a regeneration must keep:
the license notice, the portable frontmatter Hermes accepts, the `/sc:` namespace,
attribution-only use of the upstream name, and the simulated-panel notices.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "plugins" / "sc"
SKILLS = PLUGIN / "skills"
SKILL_DIRS = sorted(p.parent for p in SKILLS.glob("*/SKILL.md"))
NAMES = {p.name for p in SKILL_DIRS}

# Hermes' portable validator (hermes_cli/agent_plugins.py) accepts these names only.
PLUGIN_FIELDS = {"$schema", "name", "version", "description", "author", "homepage",
                 "repository", "license", "keywords", "extensions"}
SKILL_NAME = re.compile(r"^(?!.*--)[a-z0-9]+(?:-[a-z0-9]+)*$")
UPSTREAM_COPYRIGHT = "Copyright (c) 2024 SuperClaude Framework Contributors"
PORT_COPYRIGHT = "Copyright (c) 2026 Junsang Park (Hermes port and modifications)"


def frontmatter(skill_md: Path) -> tuple[dict[str, str], dict[str, str], str]:
    """Split a SKILL.md into top-level fields, metadata fields and body.

    Args:
        skill_md: Path to the SKILL.md file.

    Returns:
        The raw top-level values, the decoded metadata strings, and the body text.

    Raises:
        AssertionError: If a nested field sits outside metadata or a metadata value is not a quoted string.

    Examples:
        >>> top, meta, body = frontmatter(SKILLS / "load" / "SKILL.md")
        >>> top["name"]
        'load'
        >>> meta["version"]
        '1.0.0'
    """
    _, head, body = skill_md.read_text(encoding="utf-8").split("---\n", 2)
    top: dict[str, str] = {}
    meta: dict[str, str] = {}
    section = None
    for line in head.splitlines():
        if line.startswith("  "):
            if section != "metadata":
                raise AssertionError(f"{skill_md}: nested field outside metadata: {line!r}")
            key, _, value = line.strip().partition(": ")
            if not value.startswith('"'):
                raise AssertionError(f"{skill_md}: metadata.{key} is not a quoted string")
            meta[key] = json.loads(value)
            continue
        key, _, value = line.partition(":")
        section = key
        top[key] = value.strip()
    return top, meta, body


def markdown_files(skill_dir: Path) -> list[Path]:
    """List every Markdown file of one skill, references included.

    Args:
        skill_dir: The skill directory.

    Returns:
        Sorted Markdown paths under the directory.

    Examples:
        >>> [p.name for p in markdown_files(SKILLS / "pm")]
        ['SKILL.md', 'examples.md', 'pdca.md']
    """
    return sorted(skill_dir.rglob("*.md"))


def test_manifest_with_portable_schema_uses_only_accepted_fields():
    """plugin.json declares the v1 schema and only fields Hermes accepts."""
    manifest = json.loads((PLUGIN / "plugin.json").read_text())
    assert set(manifest) <= PLUGIN_FIELDS
    assert manifest["$schema"] == "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
    assert (manifest["name"], manifest["license"]) == ("sc", "MIT")
    assert re.fullmatch(r"\d+\.\d+\.\d+", manifest["version"])


def test_license_with_port_notice_keeps_upstream_copyright_first():
    """LICENSE keeps the upstream copyright line and adds the port's line under it."""
    text = (PLUGIN / "LICENSE").read_text()
    assert text.startswith(f"MIT License\n\n{UPSTREAM_COPYRIGHT}\n{PORT_COPYRIGHT}\n")
    assert "The above copyright notice and this permission notice shall be included" in text


def test_skill_set_after_port_has_all_36_skills():
    """Every ported command and skill is present, 36 in all."""
    assert len(NAMES) == 36
    assert {"sc", "load", "save", "pm", "pm-mode", "spec-panel", "business-panel"} <= NAMES


@pytest.mark.parametrize("skill_dir", SKILL_DIRS, ids=lambda p: p.name)
def test_frontmatter_with_portable_rules_matches_directory_and_credits_port(skill_dir: Path):
    """Each SKILL.md has a portable name, a short description, and port attribution."""
    top, meta, body = frontmatter(skill_dir / "SKILL.md")
    assert top["name"] == skill_dir.name and SKILL_NAME.fullmatch(skill_dir.name)
    assert 0 < len(json.loads(top["description"])) <= 60
    assert top["license"] == "MIT"
    assert meta["author"].startswith("Junsang Park") and meta["upstream"].startswith("SuperClaude Framework ")
    assert "## When to Use" in body


@pytest.mark.parametrize("skill_dir", SKILL_DIRS, ids=lambda p: p.name)
def test_skill_references_inside_plugin_use_existing_sc_names(skill_dir: Path):
    """No hand-placed /sc- names remain, and every /sc:<name> points at a real skill."""
    for path in markdown_files(skill_dir):
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"(?<![\w/.-])/sc-[a-z*<]", text), f"{path}: hand-placed /sc- name"
        missing = set(re.findall(r"(?<![\w/.-])/sc:([a-z][a-z-]*)", text)) - NAMES
        assert not missing, f"{path}: no skill for {sorted(missing)}"


@pytest.mark.parametrize("skill_dir", SKILL_DIRS, ids=lambda p: p.name)
def test_superclaude_name_in_skills_appears_only_as_attribution(skill_dir: Path):
    """The upstream name appears only where it credits SuperClaude Framework."""
    offending = [
        f"{path.name}: {line.strip()}"
        for path in markdown_files(skill_dir)
        for line in path.read_text(encoding="utf-8").splitlines()
        if "SuperClaude" in line and not re.search(r"SuperClaude Framework|SuperClaude-Org", line)
    ]
    assert not offending


@pytest.mark.parametrize("name", ["spec-panel", "business-panel"])
def test_panel_skill_with_real_names_states_the_panel_is_simulated(name: str):
    """The panel skills say their expert quotes are invented."""
    _, _, body = frontmatter(SKILLS / name / "SKILL.md")
    assert "> **Simulated panel.**" in body and "not statements by these people" in body


def test_marketplace_for_claude_code_does_not_list_sc():
    """The plugin stays out of the Claude Code marketplace and has no Claude Code manifest."""
    marketplace = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
    assert "sc" not in {p["name"] for p in marketplace["plugins"]}
    assert not (PLUGIN / ".claude-plugin").exists()
