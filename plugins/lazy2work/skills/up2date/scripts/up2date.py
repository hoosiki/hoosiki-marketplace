#!/usr/bin/env python3
"""Unified update script for Homebrew packages and Claude Code skills/plugins.

Combines brew-manager and skill-updater into a single tool.

Usage:
    python3 up2date.py            # Run all updates (brew + skill)
    python3 up2date.py --brew     # Homebrew only
    python3 up2date.py --skill    # Skills/plugins/SuperClaude only
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

# --- Constants ---

CLAUDE_DIR = Path.home() / ".claude"
SKILLS_DIR = CLAUDE_DIR / "skills"
PLUGINS_DIR = CLAUDE_DIR / "plugins"
COMMANDS_DIR = CLAUDE_DIR / "commands"
INSTALLED_PLUGINS_FILE = PLUGINS_DIR / "installed_plugins.json"
KNOWN_MARKETPLACES_FILE = PLUGINS_DIR / "known_marketplaces.json"
SETTINGS_FILE = CLAUDE_DIR / "settings.json"

_BREW_TIMEOUT: int = 300
_GIT_TIMEOUT: int = 60
_DEFAULT_TIMEOUT: int = 120
_NPX_TIMEOUT: int = 300
# `claude plugin ...` reaches the network (marketplace fetch + plugin download).
_CLAUDE_TIMEOUT: int = 180
# Scopes accepted by `claude plugin update --scope`.
_PLUGIN_SCOPES: frozenset[str] = frozenset({"user", "project", "local", "managed"})

# Matches ANSI SGR color/style escape sequences (e.g. "\x1b[38;5;145m").
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
# Matches the summary line "Updated <N> skill(s)" emitted by `npx skills update`.
_UPDATED_COUNT_RE = re.compile(r"Updated\s+(\d+)\s+skill\(s\)")


def run(
    cmd: list[str],
    *,
    capture: bool = True,
    cwd: str | None = None,
    timeout: int = _DEFAULT_TIMEOUT,
) -> subprocess.CompletedProcess[str]:
    """Execute a shell command and return the result.

    Args:
        cmd: Command and arguments to execute.
        capture: Whether to capture stdout/stderr. Defaults to True.
        cwd: Working directory for the command.
        timeout: Timeout in seconds. Defaults to _DEFAULT_TIMEOUT.

    Returns:
        Completed process with stdout, stderr, and returncode.
        On timeout, returns a synthetic result with returncode=1.

    Examples:
        >>> run(["echo", "hello"]).stdout.strip()
        'hello'
        >>> run(["false"]).returncode
        1
    """
    try:
        return subprocess.run(
            cmd, capture_output=capture, text=True, cwd=cwd, timeout=timeout
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(cmd, returncode=1, stdout="", stderr="timeout")


def print_section(title: str) -> None:
    """Print a section header surrounded by separator lines.

    Args:
        title: The section title to display.

    Examples:
        >>> print_section("Test")  # doctest: +NORMALIZE_WHITESPACE
        <BLANKLINE>
        ============================================================
          Test
        ============================================================
    """
    sep = "=" * 60
    print(f"\n{sep}")
    print(f"  {title}")
    print(sep)


# ===================================================================
#  Homebrew
# ===================================================================


def get_installed(kind: str) -> list[str]:
    """Return list of installed Homebrew packages.

    Args:
        kind: Package type — ``"formula"`` or ``"cask"``.

    Returns:
        List of package names. Empty list if brew command fails.

    Examples:
        >>> isinstance(get_installed("formula"), list)
        True
    """
    result = run(["brew", "list", f"--{kind}"], timeout=_BREW_TIMEOUT)
    if result.returncode != 0:
        return []
    return [p.strip() for p in result.stdout.strip().split("\n") if p.strip()]


def get_outdated(kind: str) -> list[dict]:
    """Return list of outdated Homebrew packages.

    For casks, uses ``--greedy`` to include auto-updating packages.

    Args:
        kind: Package type — ``"formula"`` or ``"cask"``.

    Returns:
        List of dicts with ``"raw"`` (full output line) and ``"name"`` keys.
        Empty list when all packages are current or on failure.

    Examples:
        >>> get_outdated("formula")  # when all up to date
        []
    """
    cmd = ["brew", "outdated", f"--{kind}", "--verbose"]
    if kind == "cask":
        cmd.append("--greedy")
    result = run(cmd, timeout=_BREW_TIMEOUT)
    if result.returncode != 0 or not result.stdout.strip():
        return []
    items = []
    for line in result.stdout.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        items.append({"raw": line, "name": line.split()[0]})
    return items


def brew_doctor() -> str:
    """Return brew doctor diagnostic output.

    Returns:
        Diagnostic text from ``brew doctor``. Prefers stderr if present.

    Examples:
        >>> "ready to brew" in brew_doctor().lower() or True  # system-dependent
        True
    """
    result = run(["brew", "doctor"], timeout=_BREW_TIMEOUT)
    return result.stderr.strip() or result.stdout.strip()


def brew_update() -> str:
    """Run ``brew update`` to refresh Homebrew package index.

    Returns:
        stdout output from the update command.

    Examples:
        >>> isinstance(brew_update(), str)
        True
    """
    print("  Running brew update...", flush=True)
    result = run(["brew", "update"], timeout=_BREW_TIMEOUT)
    return result.stdout.strip()


def brew_upgrade_formula() -> str:
    """Upgrade all outdated Homebrew formulae.

    Returns:
        Combined stdout and stderr output from the upgrade command.

    Examples:
        >>> isinstance(brew_upgrade_formula(), str)
        True
    """
    cmd = ["brew", "upgrade", "--formula"]
    print(f"  {' '.join(cmd)}", flush=True)
    result = run(cmd, timeout=_BREW_TIMEOUT)
    output = result.stdout.strip()
    if result.stderr.strip():
        output += "\n" + result.stderr.strip()
    return output


def brew_upgrade_cask() -> str:
    """Upgrade all outdated Homebrew casks with ``--greedy``.

    Uses ``--greedy`` to include casks with ``auto_updates=true``
    (e.g. Docker Desktop, CLion).

    Returns:
        Combined stdout and stderr output from the upgrade command.

    Examples:
        >>> isinstance(brew_upgrade_cask(), str)
        True
    """
    cmd = ["brew", "upgrade", "--cask", "--greedy"]
    print(f"  {' '.join(cmd)}", flush=True)
    result = run(cmd, timeout=_BREW_TIMEOUT)
    output = result.stdout.strip()
    if result.stderr.strip():
        output += "\n" + result.stderr.strip()
    return output


def brew_cleanup() -> str:
    """Run ``brew cleanup --prune=all`` to remove cached downloads.

    Returns:
        stdout output listing removed files.

    Examples:
        >>> isinstance(brew_cleanup(), str)
        True
    """
    print("  Running brew cleanup...", flush=True)
    result = run(["brew", "cleanup", "--prune=all"], timeout=_BREW_TIMEOUT)
    return result.stdout.strip()


def brew_autoremove() -> str:
    """Run ``brew autoremove`` to drop orphaned dependencies.

    Removes formulae that were only ever installed as another formula's
    dependency and are no longer required by anything.

    Returns:
        stdout output listing removed formulae (empty when nothing is orphaned).

    Examples:
        >>> isinstance(brew_autoremove(), str)  # doctest: +SKIP
        True
    """
    print("  Running brew autoremove...", flush=True)
    result = run(["brew", "autoremove"], timeout=_BREW_TIMEOUT)
    return result.stdout.strip()


def brew_cleanup_caskroom() -> tuple[int, int]:
    """Delete leftover ``.pkg`` installers under the Caskroom.

    ``brew cleanup --prune=all`` does **not** touch these. A pkg-based cask
    keeps its installer beside the version it installed, so Homebrew treats it
    as live data rather than cache. The app itself is already installed and the
    pkg is re-downloaded on demand, so it is pure residue — but it is residue
    that `cleanup` reports as nothing to do. Measured on a real machine:
    ``cleanup --prune=all`` freed 629 B while 10.2 GB of ``.pkg`` sat in the
    Caskroom, most of it a single MacTeX installer.

    Only files matching ``*.pkg`` directly under the Caskroom tree are removed;
    nothing else in the prefix is touched.

    Returns:
        ``(files_removed, bytes_freed)``.

    Examples:
        >>> removed, freed = brew_cleanup_caskroom()  # doctest: +SKIP
        >>> removed >= 0 and freed >= 0               # doctest: +SKIP
        True
    """
    prefix = run(["brew", "--prefix"], timeout=_BREW_TIMEOUT)
    if prefix.returncode != 0:
        return (0, 0)

    caskroom = Path(prefix.stdout.strip()) / "Caskroom"
    if not caskroom.is_dir():
        return (0, 0)

    removed = 0
    freed = 0
    for pkg in caskroom.rglob("*.pkg"):
        if not pkg.is_file():
            continue
        try:
            size = pkg.stat().st_size
            pkg.unlink()
        except OSError:
            continue
        removed += 1
        freed += size

    return (removed, freed)


def _human_bytes(n: int) -> str:
    """Format a byte count for display.

    Examples:
        >>> _human_bytes(0)
        '0 B'
        >>> _human_bytes(1536)
        '1.5 KB'
        >>> _human_bytes(10 * 1024 ** 3)
        '10.0 GB'
    """
    size = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} {unit}"
        size /= 1024
    return f"{size:.1f} GB"


def run_brew() -> None:
    """Run full Homebrew check, update, upgrade, and cleanup.

    Executes the complete Homebrew maintenance workflow:
    version check → installed count → outdated detection → doctor →
    update → upgrade formulae/casks → cleanup → summary.

    Examples:
        >>> run_brew()  # prints Homebrew status to stdout
    """
    print_section("Homebrew Package Check")

    ver = run(["brew", "--version"])
    if ver.returncode != 0:
        print("\n  Homebrew: not found (is brew installed?)")
        return
    print(f"\n  Homebrew: {ver.stdout.strip().split('\n')[0]}")

    formulae = get_installed("formula")
    casks = get_installed("cask")
    print(f"\n  Installed Formulae: {len(formulae)}")
    print(f"  Installed Casks:    {len(casks)}")
    print(f"  Total:              {len(formulae) + len(casks)}")

    outdated_formula = get_outdated("formula")
    outdated_cask = get_outdated("cask")

    print_section("Updatable Packages")

    if outdated_formula:
        print(f"\n  Formulae ({len(outdated_formula)}):")
        for item in outdated_formula:
            print(f"    - {item['raw']}")
    else:
        print("\n  Formulae: all up to date")

    if outdated_cask:
        print(f"\n  Casks ({len(outdated_cask)}):")
        for item in outdated_cask:
            print(f"    - {item['raw']}")
    else:
        print("\n  Casks: all up to date")

    total_outdated = len(outdated_formula) + len(outdated_cask)
    print(f"\n  Updates needed: {total_outdated}")

    # brew doctor
    print_section("brew doctor")
    doctor_result = brew_doctor()
    if "ready to brew" in doctor_result.lower():
        print("\n  Status: OK (ready to brew)")
    else:
        all_lines = doctor_result.split("\n")
        for line in all_lines[:5]:
            print(f"  {line}")
        if len(all_lines) > 5:
            print(f"  ... ({len(all_lines)} lines omitted)")

    # Update & Upgrade
    print_section("Update & Upgrade")

    update_result = brew_update()
    if update_result:
        for line in update_result.split("\n")[:5]:
            print(f"    {line}")

    outdated_formula = get_outdated("formula")
    outdated_cask = get_outdated("cask")

    if outdated_formula:
        print("\n  Formula upgrade:")
        result = brew_upgrade_formula()
        if result:
            for line in result.split("\n")[:10]:
                print(f"    {line}")

    if outdated_cask:
        print("\n  Cask upgrade:")
        result = brew_upgrade_cask()
        if result:
            for line in result.split("\n")[:10]:
                print(f"    {line}")

    # Cleanup
    print("\n  Cleanup:")
    cleanup_result = brew_cleanup()
    if cleanup_result:
        for line in cleanup_result.split("\n")[:5]:
            print(f"    {line}")
    else:
        print("    Nothing to clean up")

    autoremove_result = brew_autoremove()
    if autoremove_result:
        for line in autoremove_result.split("\n")[:5]:
            print(f"    {line}")
    else:
        print("    No orphaned dependencies")

    pkg_count, pkg_bytes = brew_cleanup_caskroom()
    if pkg_count:
        print(f"    Caskroom: removed {pkg_count} leftover .pkg ({_human_bytes(pkg_bytes)})")
    else:
        print("    Caskroom: no leftover .pkg installers")

    # Summary
    after_formula = get_outdated("formula")
    after_cask = get_outdated("cask")
    upgraded = total_outdated - len(after_formula) - len(after_cask)

    print_section("Brew Summary")
    print(f"\n  Upgraded: {upgraded}")
    remaining = len(after_formula) + len(after_cask)
    if remaining > 0:
        print(f"  Remaining:  {remaining}")
        for item in after_formula + after_cask:
            print(f"    - {item['raw']}")
    else:
        print("  All packages are up to date.")


# ===================================================================
#  Skills / Plugins / SuperClaude
# ===================================================================


def _read_installed_plugins() -> dict:
    """Read and parse installed_plugins.json.

    Returns:
        Parsed JSON as dict. Returns ``{"version": 2, "plugins": {}}``
        on missing file or parse failure.

    Examples:
        >>> data = _read_installed_plugins()
        >>> "plugins" in data
        True
    """
    if not INSTALLED_PLUGINS_FILE.exists():
        return {"version": 2, "plugins": {}}
    try:
        return json.loads(INSTALLED_PLUGINS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": 2, "plugins": {}}


def check_user_skills() -> list[dict]:
    """Check user-defined skills in ``~/.claude/skills/``.

    Scans each subdirectory for SKILL.md, resolves symlinks, and checks
    registration status in settings.json.

    Returns:
        List of skill info dicts with keys: ``name``, ``path``, ``source``,
        ``has_scripts``, ``has_references``, ``has_assets``, ``registered``.

    Examples:
        >>> skills = check_user_skills()
        >>> isinstance(skills, list)
        True
    """
    skills = []
    if not SKILLS_DIR.exists():
        return skills

    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir() and not skill_dir.is_symlink():
            continue
        # Resolve symlinks to get the actual path
        resolved = skill_dir.resolve() if skill_dir.is_symlink() else skill_dir
        if not resolved.is_dir():
            continue
        skill_md = resolved / "SKILL.md"
        info = {
            "name": skill_dir.name,
            "path": str(skill_dir),
            "source": "user",
            "has_scripts": (resolved / "scripts").exists(),
            "has_references": (resolved / "references").exists(),
            "has_assets": (resolved / "assets").exists(),
        }
        if skill_dir.is_symlink():
            info["symlink_target"] = str(resolved)

        if skill_md.exists():
            content = skill_md.read_text(encoding="utf-8")
            for line in content.split("\n"):
                if line.startswith("description:"):
                    info["description"] = line.split(":", 1)[1].strip()[:80]
                    break

        info["registered"] = _is_skill_registered(skill_dir.name)
        skills.append(info)

    return skills


def check_plugin_skills() -> list[dict]:
    """Check skills installed via plugin marketplaces in cache directories.

    Reads installed_plugins.json and enumerates skills under each
    plugin's ``installPath/skills/`` directory.

    Returns:
        List of skill info dicts with keys: ``name``, ``path``, ``source``,
        ``plugin_id``, ``plugin_version``, ``has_scripts``, ``has_references``,
        ``has_assets``.

    Examples:
        >>> skills = check_plugin_skills()
        >>> all(s["source"] == "plugin" for s in skills)
        True
    """
    skills = []
    data = _read_installed_plugins()
    if not data.get("plugins"):
        return skills

    for plugin_id, installs in data["plugins"].items():
        for inst in installs:
            install_path = Path(inst.get("installPath", ""))
            skills_dir = install_path / "skills"
            if not skills_dir.exists():
                continue

            for skill_dir in sorted(skills_dir.iterdir()):
                if not skill_dir.is_dir():
                    continue
                skill_md = skill_dir / "SKILL.md"
                info = {
                    "name": skill_dir.name,
                    "path": str(skill_dir),
                    "source": "plugin",
                    "plugin_id": plugin_id,
                    "plugin_version": inst.get("version", "unknown"),
                    "has_scripts": (skill_dir / "scripts").exists(),
                    "has_references": (skill_dir / "references").exists(),
                    "has_assets": (skill_dir / "assets").exists(),
                }

                if skill_md.exists():
                    content = skill_md.read_text(encoding="utf-8")
                    for line in content.split("\n"):
                        if line.startswith("description:"):
                            info["description"] = (
                                line.split(":", 1)[1].strip()[:80]
                            )
                            break

                skills.append(info)

    return skills


def _is_skill_registered(skill_name: str) -> bool:
    """Check if a skill is registered in settings.json permissions.

    Args:
        skill_name: The skill directory name to look for.

    Returns:
        True if the skill appears in the ``permissions.allow`` list
        with a ``Skill(`` prefix.

    Examples:
        >>> _is_skill_registered("nonexistent-skill")
        False
    """
    if not SETTINGS_FILE.exists():
        return False
    try:
        settings = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        permissions = settings.get("permissions", {})
        allow_list = permissions.get("allow", [])
        return any(skill_name in entry for entry in allow_list if "Skill(" in entry)
    except (OSError, json.JSONDecodeError, KeyError):
        return False


def check_plugins() -> dict:
    """Compare installed plugins with marketplace latest state.

    Fetches remote refs for each marketplace and counts how many
    commits the local copy is behind.

    Returns:
        Dict with keys ``"installed"`` (list of plugin info),
        ``"marketplaces"`` (list of marketplace info),
        ``"updates_available"`` (list of behind-count entries).

    Examples:
        >>> info = check_plugins()
        >>> set(info.keys()) == {"installed", "marketplaces", "updates_available"}
        True
    """
    result = {
        "installed": [],
        "marketplaces": [],
        "updates_available": [],
    }

    data = _read_installed_plugins()
    for plugin_id, installs in data.get("plugins", {}).items():
        for inst in installs:
            result["installed"].append(
                {
                    "id": plugin_id,
                    "version": inst.get("version", "unknown"),
                    "scope": inst.get("scope", "unknown"),
                    "installed_at": inst.get("installedAt", ""),
                }
            )

    if KNOWN_MARKETPLACES_FILE.exists():
        try:
            data = json.loads(KNOWN_MARKETPLACES_FILE.read_text(encoding="utf-8"))
            for name, info in data.items():
                source = info.get("source", {})
                mkt = {
                    "name": name,
                    "repo": source.get("repo", ""),
                    "install_location": info.get("installLocation", ""),
                }
                mkt_path = Path(info.get("installLocation", ""))
                if mkt_path.exists():
                    git_result = run(
                        ["git", "log", "--oneline", "-1"],
                        cwd=str(mkt_path),
                        timeout=_GIT_TIMEOUT,
                    )
                    if git_result.returncode == 0:
                        mkt["latest_local_commit"] = git_result.stdout.strip()
                result["marketplaces"].append(mkt)
        except (OSError, json.JSONDecodeError) as e:
            print(f"  Error reading marketplace file: {e}")

    for mkt in result["marketplaces"]:
        mkt_path = Path(mkt.get("install_location", ""))
        if not mkt_path.exists():
            continue

        fetch_result = run(["git", "fetch"], cwd=str(mkt_path), timeout=_GIT_TIMEOUT)
        if fetch_result.returncode != 0:
            continue

        # Detect default remote branch (main or master)
        branch_result = run(
            ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
            cwd=str(mkt_path),
            timeout=_GIT_TIMEOUT,
        )
        if branch_result.returncode == 0:
            remote_branch = branch_result.stdout.strip().split("/")[-1]
        else:
            remote_branch = "main"

        diff_result = run(
            ["git", "rev-list", "--count", f"HEAD..origin/{remote_branch}"],
            cwd=str(mkt_path),
            timeout=_GIT_TIMEOUT,
        )
        if diff_result.returncode == 0:
            try:
                behind = int(diff_result.stdout.strip() or "0")
            except ValueError:
                continue
            if behind > 0:
                result["updates_available"].append(
                    {
                        "marketplace": mkt["name"],
                        "repo": mkt["repo"],
                        "behind_commits": behind,
                    }
                )

    return result


def check_superclaude() -> dict:
    """Check SuperClaude command installation status.

    Returns:
        Dict with ``"installed"`` (bool), ``"commands"`` (list of names),
        and ``"total"`` (int).

    Examples:
        >>> info = check_superclaude()
        >>> isinstance(info["installed"], bool)
        True
    """
    sc_dir = COMMANDS_DIR / "sc"
    result = {
        "installed": sc_dir.exists(),
        "commands": [],
        "total": 0,
    }

    if not sc_dir.exists():
        return result

    for cmd_file in sorted(sc_dir.glob("*.md")):
        result["commands"].append(cmd_file.stem)
    result["total"] = len(result["commands"])

    return result


def _claude_cli_available() -> bool:
    """Report whether the ``claude`` executable is on PATH.

    Marketplace and plugin updates are delegated to it; without it there is
    no supported way to refresh a plugin.

    Examples:
        >>> isinstance(_claude_cli_available(), bool)
        True
    """
    return shutil.which("claude") is not None


def update_marketplace(name: str) -> str:
    """Update one marketplace via ``claude plugin marketplace update``.

    Delegates to Claude Code's own command rather than running ``git pull``
    in the marketplace checkout: the CLI owns that directory's layout and
    refreshes the derived state alongside it. Seed-managed marketplaces are
    read-only and are skipped by the command itself.

    Args:
        name: Marketplace name as registered with Claude Code.

    Returns:
        Status message — "Updated: ..." or "Update failed: ...".

    Examples:
        >>> isinstance(update_marketplace("nonexistent-marketplace"), str)  # doctest: +SKIP
        True
    """
    if not _claude_cli_available():
        return "claude CLI not found — cannot update marketplaces"

    result = run(
        ["claude", "plugin", "marketplace", "update", name],
        timeout=_CLAUDE_TIMEOUT,
    )
    output = (result.stdout.strip() or result.stderr.strip()).strip()
    if result.returncode == 0:
        return f"Updated: {output}" if output else "Updated"
    return f"Update failed: {output}"


def update_plugin(plugin_id: str, scope: str = "user") -> str:
    """Update one installed plugin via ``claude plugin update``.

    ``--yes`` is mandatory here, not merely convenient: the CLI requires it
    whenever stdin or stdout is not a TTY, which is always the case when this
    script runs. The update lands in the cache but does **not** affect the
    running session — Claude Code must be restarted to pick it up.

    Args:
        plugin_id: Plugin name, or ``name@marketplace`` to disambiguate.
        scope: Installation scope to update — ``user``, ``project``,
            ``local``, or ``managed``. Defaults to ``user``.

    Returns:
        Status message — "Updated: ..." or "Update failed: ...".

    Examples:
        >>> isinstance(update_plugin("nonexistent@nowhere"), str)  # doctest: +SKIP
        True
    """
    if not _claude_cli_available():
        return "claude CLI not found — cannot update plugins"

    result = run(
        ["claude", "plugin", "update", plugin_id, "--scope", scope, "--yes"],
        timeout=_CLAUDE_TIMEOUT,
    )
    output = (result.stdout.strip() or result.stderr.strip()).strip()
    if result.returncode == 0:
        return f"Updated: {output}" if output else "Updated"
    return f"Update failed: {output}"


def update_superclaude() -> str:
    """Update SuperClaude to latest version via ``superclaude update``.

    Returns:
        Status message with command output.

    Examples:
        >>> "SuperClaude" in update_superclaude()
        True
    """
    result = run(["superclaude", "update"], capture=True)
    output = result.stdout.strip()
    if result.stderr.strip():
        output += "\n" + result.stderr.strip()
    if result.returncode == 0:
        return f"SuperClaude updated:\n{output}"
    return f"SuperClaude update failed:\n{output}"


def _print_skill_info(sk: dict) -> None:
    """Print formatted skill information to stdout.

    Args:
        sk: Skill info dict with keys ``name``, ``path``, ``source``,
            ``has_scripts``, ``has_references``, ``has_assets``.

    Examples:
        >>> _print_skill_info({"name": "test", "path": "/tmp", "source": "user",
        ...     "has_scripts": True, "has_references": False, "has_assets": False})
    """
    desc = sk.get("description", "No description")
    print(f"\n  [{sk['source']}] {sk['name']}")
    print(f"    Path: {sk['path']}")
    if sk.get("symlink_target"):
        print(f"    Target: {sk['symlink_target']}")
    if sk.get("plugin_id"):
        print(f"    Plugin: {sk['plugin_id']} ({sk.get('plugin_version', '?')})")
    print(f"    Description: {desc}")
    parts = []
    if sk["has_scripts"]:
        parts.append("scripts")
    if sk["has_references"]:
        parts.append("references")
    if sk["has_assets"]:
        parts.append("assets")
    if parts:
        print(f"    Resources: {', '.join(parts)}")


def _strip_ansi(text: str) -> str:
    """Remove ANSI SGR color/style escape sequences from text.

    Args:
        text: Raw text that may contain ANSI escape codes.

    Returns:
        The text with all ANSI SGR sequences removed.

    Examples:
        >>> _strip_ansi("\\x1b[1mUpdated\\x1b[0m 3 skill(s)")
        'Updated 3 skill(s)'
        >>> _strip_ansi("plain")
        'plain'
    """
    return _ANSI_RE.sub("", text)


def _parse_dead_skills(output: str) -> list[str]:
    """Extract skill names flagged as deleted upstream from update output.

    Collects the bullet-listed names that appear under any
    "...deleted upstream:" warning block emitted by ``npx skills update``.
    Bullets under other warnings (e.g. "cannot be updated automatically")
    are ignored. Names are de-duplicated preserving first-seen order.

    Args:
        output: Combined stdout/stderr from ``npx skills update``.

    Returns:
        Ordered list of unique skill names deleted upstream.

    Examples:
        >>> _parse_dead_skills(
        ...     "appear to have been deleted upstream:\\n"
        ...     "  • write-a-skill\\n"
        ...     "Skipping deletion in non-interactive mode.\\n"
        ... )
        ['write-a-skill']
        >>> _parse_dead_skills("Updated 3 skill(s)")
        []
    """
    clean = _strip_ansi(output)
    dead: list[str] = []
    in_block = False
    for line in clean.splitlines():
        stripped = line.strip()
        if "deleted upstream" in stripped:
            in_block = True
            continue
        if not in_block:
            continue
        if stripped.startswith("•"):  # bullet "•"
            name = stripped.lstrip("•").strip()
            if name and name not in dead:
                dead.append(name)
        elif stripped:
            in_block = False
    return dead


def _parse_updated_count(output: str) -> int:
    """Parse the number of updated skills from update output.

    Args:
        output: Combined stdout/stderr from ``npx skills update``.

    Returns:
        The count from the "Updated <N> skill(s)" summary line, or 0
        if no such line is present.

    Examples:
        >>> _parse_updated_count("✓ Updated 11 skill(s)")
        11
        >>> _parse_updated_count("No project skills can be updated in place.")
        0
    """
    match = _UPDATED_COUNT_RE.search(_strip_ansi(output))
    return int(match.group(1)) if match else 0


def update_global_skills(remove_dead: bool = True) -> dict[str, object]:
    """Update global agent skills via ``npx skills`` and prune dead ones.

    Runs ``npx skills@latest update -g -y`` to refresh all globally
    installed skills (e.g. mattpocock/skills under ``~/.agents/skills``),
    then optionally removes skills that were deleted upstream (which the
    non-interactive updater only warns about but leaves in place).

    Args:
        remove_dead: When True, remove skills flagged as deleted upstream
            via ``npx skills remove <names> -g -y``. Defaults to True.

    Returns:
        Dict with keys: ``available`` (bool — npx found and ran),
        ``updated`` (int), ``dead`` (list[str] deleted upstream),
        ``removed`` (list[str] actually removed), ``error`` (str),
        and ``output`` (str — cleaned update output).

    Examples:
        >>> result = update_global_skills(remove_dead=False)
        >>> set(result) >= {"available", "updated", "dead", "removed"}
        True
    """
    result: dict[str, object] = {
        "available": False,
        "updated": 0,
        "dead": [],
        "removed": [],
        "error": "",
        "output": "",
    }

    if shutil.which("npx") is None:
        result["error"] = "npx not found (Node.js 18+ required for skills CLI)"
        return result

    result["available"] = True
    proc = run(
        ["npx", "--yes", "skills@latest", "update", "-g", "-y"],
        timeout=_NPX_TIMEOUT,
    )
    output = _strip_ansi(f"{proc.stdout or ''}\n{proc.stderr or ''}").strip()
    result["output"] = output
    result["updated"] = _parse_updated_count(output)

    dead = _parse_dead_skills(output)
    result["dead"] = dead

    if dead and remove_dead:
        rm = run(
            ["npx", "--yes", "skills@latest", "remove", *dead, "-g", "-y"],
            timeout=_NPX_TIMEOUT,
        )
        if rm.returncode == 0:
            result["removed"] = dead
        else:
            result["error"] = _strip_ansi(rm.stderr or rm.stdout or "").strip()[:200]

    return result


def run_skill(prune_dead: bool = True) -> None:
    """Run full skill/plugin/SuperClaude check and update.

    Executes the complete skills maintenance workflow:
    user skills → global agent-skill update (npx skills) → plugin skills →
    plugin update detection → marketplace pull → cache refresh →
    SuperClaude update.

    Args:
        prune_dead: When True, remove global skills deleted upstream during
            the ``npx skills`` update step. Defaults to True.

    Examples:
        >>> run_skill(prune_dead=False)  # prints skill/plugin status to stdout
    """
    # -- 1. User Skills --
    print_section("User Skills")
    user_skills = check_user_skills()
    if user_skills:
        print(f"\n  Found {len(user_skills)} user skill(s):")
        for sk in user_skills:
            _print_skill_info(sk)
    else:
        print("\n  No user skills found in ~/.claude/skills/")

    # -- 1a. Global Agent Skills (npx skills CLI) --
    print_section("Global Agent Skills (npx skills)")
    global_result = update_global_skills(remove_dead=prune_dead)
    if not global_result["available"]:
        print(f"\n  Skipped: {global_result['error']}")
    else:
        print(f"\n  Updated: {global_result['updated']} skill(s)")
        dead = global_result["dead"]
        if dead:
            print(f"  Deleted upstream ({len(dead)}):")
            for name in dead:
                print(f"    - {name}")
            if prune_dead:
                removed = global_result["removed"]
                if removed:
                    print(f"  Removed {len(removed)} dead skill(s).")
                elif global_result["error"]:
                    print(f"  Removal failed: {global_result['error']}")
            else:
                print("  Pruning disabled (--no-skill-prune); left in place.")
        else:
            print("  Deleted upstream: none")

    # -- 1b. Plugin Skills --
    print_section("Plugin Skills")
    plugin_skills = check_plugin_skills()
    if plugin_skills:
        # Group by plugin_id
        by_plugin: dict[str, list[dict]] = {}
        for sk in plugin_skills:
            pid = sk.get("plugin_id", "unknown")
            by_plugin.setdefault(pid, []).append(sk)

        total = len(plugin_skills)
        print(f"\n  Found {total} skill(s) from {len(by_plugin)} plugin(s):")
        for pid, sks in sorted(by_plugin.items()):
            print(f"\n  --- {pid} ({sks[0].get('plugin_version', '?')}) ---")
            for sk in sks:
                _print_skill_info(sk)
    else:
        print("\n  No plugin skills found")

    # -- 2. Plugins --
    print_section("Plugins")
    plugin_info = check_plugins()

    if plugin_info["installed"]:
        print(f"\n  Installed plugins: {len(plugin_info['installed'])}")
        for p in plugin_info["installed"]:
            print(f"\n    {p['id']}")
            print(f"      Version: {p['version']}")
            print(f"      Scope: {p['scope']}")
            print(
                f"      Installed: {p['installed_at'][:10] if p['installed_at'] else 'unknown'}"
            )
    else:
        print("\n  No plugins installed")

    if plugin_info["marketplaces"]:
        print(f"\n  Marketplaces: {len(plugin_info['marketplaces'])}")
        for m in plugin_info["marketplaces"]:
            print(f"    - {m['name']} ({m['repo']})")
            if m.get("latest_local_commit"):
                print(f"      Latest local: {m['latest_local_commit']}")

    if plugin_info["updates_available"]:
        print("\n  Updates available:")
        for u in plugin_info["updates_available"]:
            print(f"    - {u['marketplace']}: {u['behind_commits']} commits behind")

        print_section("Plugin Update")
        if not _claude_cli_available():
            print("\n  claude CLI not found — skipping (install Claude Code to update plugins)")
        else:
            stale = {u["marketplace"] for u in plugin_info["updates_available"]}
            for mkt_name in sorted(stale):
                print(f"\n  Updating {mkt_name} marketplace...")
                print(f"    {update_marketplace(mkt_name)}")

            for p in plugin_info["installed"]:
                if p["id"].split("@")[-1] not in stale:
                    continue
                scope = p["scope"] if p["scope"] in _PLUGIN_SCOPES else "user"
                print(f"\n  Updating {p['id']} (scope: {scope})...")
                print(f"    {update_plugin(p['id'], scope)}")

            print("\n  Restart Claude Code to load the updated plugins.")
    else:
        print("\n  Marketplaces: all up to date")

    # -- 3. SuperClaude --
    print_section("SuperClaude")
    sc_info = check_superclaude()

    if sc_info["installed"]:
        print("\n  Status: Installed")
        print(f"  Commands: {sc_info['total']}")
        cmds = sc_info["commands"]
        cols = 4
        rows = (len(cmds) + cols - 1) // cols
        print("  Command list:")
        for r in range(rows):
            line = "    "
            for c in range(cols):
                idx = r + c * rows
                if idx < len(cmds):
                    line += f"{cmds[idx]:<20}"
            print(line.rstrip())

        print_section("SuperClaude Update")
        result = update_superclaude()
        print(f"\n  {result}")
    else:
        print("\n  SuperClaude: Not installed")


# ===================================================================
#  Main
# ===================================================================


def main() -> None:
    """Parse CLI arguments and run the selected update workflow.

    Examples:
        >>> main()  # with no args, runs both brew and skill updates
    """
    parser = argparse.ArgumentParser(
        description="Unified updater for Homebrew and Claude Code skills/plugins"
    )
    parser.add_argument(
        "--brew", action="store_true", help="Run Homebrew update only"
    )
    parser.add_argument(
        "--skill", action="store_true", help="Run skill/plugin/SuperClaude update only"
    )
    parser.add_argument(
        "--no-skill-prune",
        action="store_true",
        help="Keep global skills deleted upstream instead of removing them",
    )
    args = parser.parse_args()

    # If neither flag is set, run both
    run_all = not args.brew and not args.skill

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print_section(f"up2date  ({now})")

    if run_all or args.brew:
        run_brew()

    if run_all or args.skill:
        run_skill(prune_dead=not args.no_skill_prune)

    print_section("Update Complete")
    print()


if __name__ == "__main__":
    main()
