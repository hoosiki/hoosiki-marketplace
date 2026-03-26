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
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

# --- Constants ---

CLAUDE_DIR = Path.home() / ".claude"
SKILLS_DIR = CLAUDE_DIR / "skills"
PLUGINS_DIR = CLAUDE_DIR / "plugins"
COMMANDS_DIR = CLAUDE_DIR / "commands"
MARKETPLACES_DIR = PLUGINS_DIR / "marketplaces"
CACHE_DIR = PLUGINS_DIR / "cache"
INSTALLED_PLUGINS_FILE = PLUGINS_DIR / "installed_plugins.json"
KNOWN_MARKETPLACES_FILE = PLUGINS_DIR / "known_marketplaces.json"
SETTINGS_FILE = CLAUDE_DIR / "settings.json"

_BREW_TIMEOUT: int = 300
_GIT_TIMEOUT: int = 60
_DEFAULT_TIMEOUT: int = 120


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


def _write_installed_plugins(data: dict) -> None:
    """Atomically write installed_plugins.json via tempfile + rename.

    Args:
        data: Plugin data dict to serialize as JSON.

    Raises:
        OSError: If the write or rename fails.

    Examples:
        >>> _write_installed_plugins({"version": 2, "plugins": {}})
    """
    INSTALLED_PLUGINS_FILE.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        dir=str(INSTALLED_PLUGINS_FILE.parent), suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, str(INSTALLED_PLUGINS_FILE))
    except OSError:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


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


def update_marketplace(name: str, mkt_path: str) -> str:
    """Update a marketplace via ``git pull --ff-only``.

    Args:
        name: Marketplace display name (for logging).
        mkt_path: Absolute path to the marketplace git repo.

    Returns:
        Status message — either "Updated: ..." or "Update failed: ...".

    Examples:
        >>> update_marketplace("test", "/nonexistent/path")
        'Path not found: /nonexistent/path'
    """
    path = Path(mkt_path)
    if not path.exists():
        return f"Path not found: {mkt_path}"

    result = run(["git", "pull", "--ff-only"], cwd=str(path), timeout=_GIT_TIMEOUT)
    if result.returncode == 0:
        return f"Updated: {result.stdout.strip()}"
    return f"Update failed: {result.stderr.strip()}"


def _find_plugin_source(mkt_path: Path, plugin_name: str) -> Path | None:
    """Locate plugin source directory in a marketplace.

    Searches in order:
      1. ``plugins/{plugin_name}/``  (standard marketplace layout)
      2. ``{plugin_name}/``          (flat layout)
      3. ``marketplace.json`` source field  (root-source layout)

    Args:
        mkt_path: Root path of the marketplace git repo.
        plugin_name: Plugin name to look up (e.g. ``"lazy2work"``).

    Returns:
        Path to the plugin source directory, or None if not found.

    Examples:
        >>> _find_plugin_source(Path("/nonexistent"), "test") is None
        True
    """
    # Standard layout: plugins/<name>/
    candidate = mkt_path / "plugins" / plugin_name
    if candidate.exists():
        return candidate

    # Flat layout: <name>/
    candidate = mkt_path / plugin_name
    if candidate.exists():
        return candidate

    # Root-source layout: marketplace.json defines source="./"
    mkt_json = mkt_path / ".claude-plugin" / "marketplace.json"
    if mkt_json.exists():
        try:
            mdata = json.loads(mkt_json.read_text(encoding="utf-8"))
            for plugin_def in mdata.get("plugins", []):
                if plugin_def.get("name") == plugin_name:
                    source = plugin_def.get("source", "")
                    if source in ("./", "."):
                        return mkt_path
                    source_path = (mkt_path / source).resolve()
                    if source_path.exists():
                        return source_path
        except (OSError, json.JSONDecodeError):
            pass

    return None


def update_plugin_cache(plugin_id: str, marketplace_name: str) -> str:
    """Refresh plugin cache to marketplace latest version.

    Copies plugin contents from marketplace source to the cache directory
    and updates installed_plugins.json with the new version and SHA.
    Skips if the cache already matches the current git SHA.

    Args:
        plugin_id: Full plugin identifier (e.g. ``"lazy2work@hoosiki-marketplace"``).
        marketplace_name: Name of the marketplace directory.

    Returns:
        Status message — "Already up to date", "Cache refreshed", or error.

    Examples:
        >>> update_plugin_cache("test@missing", "nonexistent")
        'Marketplace not found: nonexistent'
    """
    mkt_path = MARKETPLACES_DIR / marketplace_name
    if not mkt_path.exists():
        return f"Marketplace not found: {marketplace_name}"

    sha_result = run(["git", "rev-parse", "--short", "HEAD"], cwd=str(mkt_path), timeout=_GIT_TIMEOUT)
    if sha_result.returncode != 0:
        return "SHA check failed"
    new_sha = sha_result.stdout.strip()

    full_sha_result = run(["git", "rev-parse", "HEAD"], cwd=str(mkt_path), timeout=_GIT_TIMEOUT)
    new_full_sha = full_sha_result.stdout.strip()

    plugin_name = plugin_id.split("@")[0]

    # Detect plugin version from plugin.json or marketplace.json
    new_version = new_sha
    plugin_json = mkt_path / "plugins" / plugin_name / ".claude-plugin" / "plugin.json"
    if plugin_json.exists():
        try:
            pdata = json.loads(plugin_json.read_text(encoding="utf-8"))
            new_version = pdata.get("version", new_sha)
        except (OSError, json.JSONDecodeError):
            pass

    plugin_src = _find_plugin_source(mkt_path, plugin_name)
    if plugin_src is None:
        return f"Plugin source not found in marketplace: {plugin_name}"

    cache_dest = CACHE_DIR / marketplace_name / plugin_name / new_version

    # Check if cache exists AND git SHA matches (same version but different content)
    data = _read_installed_plugins()
    installed_sha = ""
    for inst in data.get("plugins", {}).get(plugin_id, []):
        installed_sha = inst.get("gitCommitSha", "")
        break

    if cache_dest.exists() and installed_sha == new_full_sha:
        return f"Already up to date: {new_version} ({new_sha})"

    # Remove stale cache if version matches but SHA differs
    if cache_dest.exists() and installed_sha != new_full_sha:
        shutil.rmtree(cache_dest)

    cache_dest.mkdir(parents=True, exist_ok=True)

    # Copy all plugin contents (skills, hooks, commands, rules, scripts, etc.)
    for item in plugin_src.iterdir():
        if item.name.startswith("."):
            continue
        dest_item = cache_dest / item.name
        if item.is_dir():
            shutil.copytree(str(item), str(dest_item), dirs_exist_ok=True)
        else:
            shutil.copy2(str(item), str(dest_item))

    if plugin_id in data.get("plugins", {}):
        for inst in data["plugins"][plugin_id]:
            inst["version"] = new_version
            inst["gitCommitSha"] = new_full_sha
            inst["installPath"] = str(cache_dest)
            inst["lastUpdated"] = datetime.now(timezone.utc).isoformat()
        try:
            _write_installed_plugins(data)
        except OSError as e:
            return f"installed_plugins.json update failed: {e}"

    return f"Cache refreshed: {plugin_name} {new_version} (was {new_sha[:7] if new_version != new_sha else 'new'})"


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


def run_skill() -> None:
    """Run full skill/plugin/SuperClaude check and update.

    Executes the complete skills maintenance workflow:
    user skills → plugin skills → plugin update detection →
    marketplace pull → cache refresh → SuperClaude update.

    Examples:
        >>> run_skill()  # prints skill/plugin status to stdout
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
        for u in plugin_info["updates_available"]:
            mkt_name = u["marketplace"]
            mkt_info = next(
                (m for m in plugin_info["marketplaces"] if m["name"] == mkt_name),
                None,
            )
            if mkt_info:
                print(f"\n  Updating {mkt_name} marketplace...")
                result = update_marketplace(mkt_name, mkt_info["install_location"])
                print(f"    {result}")

                for p in plugin_info["installed"]:
                    if mkt_name in p["id"]:
                        print(f"\n  Refreshing {p['id']} cache...")
                        cache_result = update_plugin_cache(p["id"], mkt_name)
                        print(f"    {cache_result}")
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
    args = parser.parse_args()

    # If neither flag is set, run both
    run_all = not args.brew and not args.skill

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print_section(f"up2date  ({now})")

    if run_all or args.brew:
        run_brew()

    if run_all or args.skill:
        run_skill()

    print_section("Update Complete")
    print()


if __name__ == "__main__":
    main()
