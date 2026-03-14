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
import shutil
import subprocess
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


def run(
    cmd: list[str], *, capture: bool = True, cwd: str | None = None
) -> subprocess.CompletedProcess[str]:
    """Execute a shell command and return the result."""
    return subprocess.run(cmd, capture_output=capture, text=True, cwd=cwd)


def print_section(title: str) -> None:
    """Print a section header surrounded by separator lines."""
    sep = "=" * 60
    print(f"\n{sep}")
    print(f"  {title}")
    print(sep)


# ===================================================================
#  Homebrew
# ===================================================================


def get_installed(kind: str) -> list[str]:
    """Return list of installed packages. kind: 'formula' or 'cask'."""
    result = run(["brew", "list", f"--{kind}"])
    if result.returncode != 0:
        return []
    return [p.strip() for p in result.stdout.strip().split("\n") if p.strip()]


def get_outdated(kind: str) -> list[dict]:
    """Return list of updatable packages."""
    result = run(["brew", "outdated", f"--{kind}", "--verbose"])
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
    """Return brew doctor output."""
    result = run(["brew", "doctor"])
    return result.stderr.strip() or result.stdout.strip()


def brew_update() -> str:
    """Run brew update."""
    print("  Running brew update...", flush=True)
    result = run(["brew", "update"])
    return result.stdout.strip()


def brew_upgrade_formula() -> str:
    """Upgrade all formulae."""
    cmd = ["brew", "upgrade", "--formula"]
    print(f"  {' '.join(cmd)}", flush=True)
    result = run(cmd)
    output = result.stdout.strip()
    if result.stderr.strip():
        output += "\n" + result.stderr.strip()
    return output


def brew_upgrade_cask() -> str:
    """Upgrade all casks."""
    cmd = ["brew", "upgrade", "--cask"]
    print(f"  {' '.join(cmd)}", flush=True)
    result = run(cmd)
    output = result.stdout.strip()
    if result.stderr.strip():
        output += "\n" + result.stderr.strip()
    return output


def brew_cleanup() -> str:
    """Run brew cleanup."""
    print("  Running brew cleanup...", flush=True)
    result = run(["brew", "cleanup", "--prune=all"])
    return result.stdout.strip()


def run_brew() -> None:
    """Run full Homebrew check, update, upgrade, and cleanup."""
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
        lines = doctor_result.split("\n")[:5]
        for line in lines:
            print(f"  {line}")
        if len(doctor_result.split("\n")) > 5:
            print(f"  ... ({len(doctor_result.split('\n'))} lines omitted)")

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


def check_user_skills() -> list[dict]:
    """Check user-defined skills in ~/.claude/skills/."""
    skills = []
    if not SKILLS_DIR.exists():
        return skills

    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        info = {
            "name": skill_dir.name,
            "path": str(skill_dir),
            "has_scripts": (skill_dir / "scripts").exists(),
            "has_references": (skill_dir / "references").exists(),
            "has_assets": (skill_dir / "assets").exists(),
        }

        if skill_md.exists():
            content = skill_md.read_text(encoding="utf-8")
            for line in content.split("\n"):
                if line.startswith("description:"):
                    info["description"] = line.split(":", 1)[1].strip()[:80]
                    break

        info["registered"] = _is_skill_registered(skill_dir.name)
        skills.append(info)

    return skills


def _is_skill_registered(skill_name: str) -> bool:
    """Check if a skill is registered in settings.json."""
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
    """Compare installed plugins with marketplace latest state."""
    result = {
        "installed": [],
        "marketplaces": [],
        "updates_available": [],
    }

    if INSTALLED_PLUGINS_FILE.exists():
        try:
            data = json.loads(INSTALLED_PLUGINS_FILE.read_text(encoding="utf-8"))
            plugins = data.get("plugins", {})
            for plugin_id, installs in plugins.items():
                for inst in installs:
                    result["installed"].append(
                        {
                            "id": plugin_id,
                            "version": inst.get("version", "unknown"),
                            "scope": inst.get("scope", "unknown"),
                            "installed_at": inst.get("installedAt", ""),
                        }
                    )
        except (OSError, json.JSONDecodeError) as e:
            print(f"  Error reading plugin file: {e}")

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
                        ["git", "log", "--oneline", "-1"], cwd=str(mkt_path)
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

        fetch_result = run(["git", "fetch", "--dry-run"], cwd=str(mkt_path))
        if fetch_result.returncode != 0:
            continue

        diff_result = run(
            ["git", "rev-list", "--count", "HEAD..origin/main"],
            cwd=str(mkt_path),
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
    """Check SuperClaude command status."""
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
    """Update a marketplace via git pull."""
    path = Path(mkt_path)
    if not path.exists():
        return f"Path not found: {mkt_path}"

    result = run(["git", "pull", "--ff-only"], cwd=str(path))
    if result.returncode == 0:
        return f"Updated: {result.stdout.strip()}"
    return f"Update failed: {result.stderr.strip()}"


def update_plugin_cache(plugin_id: str, marketplace_name: str) -> str:
    """Refresh plugin cache to marketplace latest version."""
    mkt_path = MARKETPLACES_DIR / marketplace_name
    if not mkt_path.exists():
        return f"Marketplace not found: {marketplace_name}"

    sha_result = run(["git", "rev-parse", "--short", "HEAD"], cwd=str(mkt_path))
    if sha_result.returncode != 0:
        return "SHA check failed"
    new_sha = sha_result.stdout.strip()

    full_sha_result = run(["git", "rev-parse", "HEAD"], cwd=str(mkt_path))
    new_full_sha = full_sha_result.stdout.strip()

    plugin_name = plugin_id.split("@")[0]

    skills_src = mkt_path / "skills"
    if not skills_src.exists():
        return f"Skills source not found: {skills_src}"

    cache_dest = CACHE_DIR / marketplace_name / plugin_name / new_sha

    if cache_dest.exists():
        return f"Already up to date: {new_sha}"

    cache_dest.mkdir(parents=True, exist_ok=True)

    dest_skills = cache_dest / "skills"
    shutil.copytree(str(skills_src), str(dest_skills), dirs_exist_ok=True)

    if INSTALLED_PLUGINS_FILE.exists():
        try:
            data = json.loads(INSTALLED_PLUGINS_FILE.read_text(encoding="utf-8"))
            if plugin_id in data.get("plugins", {}):
                for inst in data["plugins"][plugin_id]:
                    inst["version"] = new_sha
                    inst["gitCommitSha"] = new_full_sha
                    inst["installPath"] = str(cache_dest)
                    inst["lastUpdated"] = datetime.now(timezone.utc).isoformat()
                INSTALLED_PLUGINS_FILE.write_text(
                    json.dumps(data, indent=2), encoding="utf-8"
                )
        except (OSError, json.JSONDecodeError) as e:
            return f"installed_plugins.json update failed: {e}"

    return f"Cache refreshed: {plugin_name} -> {new_sha}"


def update_superclaude() -> str:
    """Update SuperClaude to latest version."""
    result = run(["superclaude", "update"], capture=True)
    output = result.stdout.strip()
    if result.stderr.strip():
        output += "\n" + result.stderr.strip()
    if result.returncode == 0:
        return f"SuperClaude updated:\n{output}"
    return f"SuperClaude update failed:\n{output}"


def run_skill() -> None:
    """Run full skill/plugin/SuperClaude check and update."""
    # -- 1. User Skills --
    print_section("User Skills")
    user_skills = check_user_skills()
    if user_skills:
        for sk in user_skills:
            status = "Registered" if sk["registered"] else "Not registered"
            desc = sk.get("description", "No description")
            print(f"\n  [{status}] {sk['name']}")
            print(f"    Path: {sk['path']}")
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
    else:
        print("\n  No user skills found")

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
