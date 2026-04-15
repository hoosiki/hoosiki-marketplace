#!/usr/bin/env python3
"""Send /sc:save to all Claude panes in the current tmux session, excluding self.

Usage:
    python3 save_all_claude.py [--dry-run] [--all-sessions] [--command CMD]

Environment:
    TMUX_PANE  — current pane ID (set automatically by tmux)
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys

_TMUX_CMD: str = "tmux"
_DEFAULT_COMMAND: str = "/sc:save"

# Claude Code reports `pane_current_command` as either the literal string
# "claude" (older builds) or its semantic version string "X.Y.Z" (modern
# builds, e.g. "2.1.107"). Match both so detection survives Claude updates.
_CLAUDE_CMD_PATTERN: re.Pattern[str] = re.compile(r"^(claude|\d+\.\d+\.\d+)")


def _is_claude_command(command: str) -> bool:
    """Return True if a tmux pane_current_command identifies a Claude Code pane.

    Args:
        command: Raw value of the `pane_current_command` format variable.

    Returns:
        True when the command is either literal "claude" or a semver-like
        version string such as "2.1.107".

    Examples:
        >>> _is_claude_command("claude")
        True
        >>> _is_claude_command("2.1.107")
        True
        >>> _is_claude_command("nvim")
        False
    """
    return bool(_CLAUDE_CMD_PATTERN.match(command))


def _run_tmux(*args: str) -> str:
    """Run a tmux command and return stripped stdout."""
    result = subprocess.run(
        [_TMUX_CMD, *args],
        capture_output=True,
        text=True,
        timeout=5,
    )
    if result.returncode != 0:
        print(f"tmux error: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()


def get_current_session() -> str:
    """Get the current tmux session name."""
    return _run_tmux("display-message", "-p", "#{session_name}")


def get_current_pane_id() -> str:
    """Get the current pane ID from environment or tmux."""
    pane_id = os.environ.get("TMUX_PANE")
    if pane_id:
        return pane_id
    return _run_tmux("display-message", "-p", "#{pane_id}")


def find_claude_panes(
    session: str | None = None,
    exclude_pane: str | None = None,
) -> list[dict[str, str]]:
    """Find all panes running Claude in the given session (or all sessions).

    Args:
        session: tmux session name to search. None for all sessions.
        exclude_pane: pane ID to exclude (typically self).

    Returns:
        List of dicts with keys: target, command, session, window, pane.
    """
    fmt = "#{session_name}:#{window_index}.#{pane_index}\t#{pane_id}\t#{pane_current_command}"
    if session:
        raw = _run_tmux("list-panes", "-s", "-t", session, "-F", fmt)
    else:
        raw = _run_tmux("list-panes", "-a", "-F", fmt)

    panes: list[dict[str, str]] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        target, pane_id, command = parts
        if not _is_claude_command(command):
            continue
        if exclude_pane and pane_id == exclude_pane:
            continue
        panes.append({"target": target, "pane_id": pane_id, "command": command})
    return panes


def send_command(target: str, command: str, *, dry_run: bool = False) -> None:
    """Send a command string followed by Enter to a tmux pane.

    Args:
        target: tmux pane target (e.g. session:window.pane).
        command: text to send.
        dry_run: if True, print instead of sending.
    """
    if dry_run:
        print(f"  [dry-run] would send '{command}' to {target}")
        return
    _run_tmux("send-keys", "-t", target, command, "Enter")
    print(f"  sent '{command}' to {target}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Send /sc:save to all Claude panes in current tmux session.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print targets without sending commands.",
    )
    parser.add_argument(
        "--all-sessions",
        action="store_true",
        help="Target all tmux sessions, not just the current one.",
    )
    parser.add_argument(
        "--command",
        default=_DEFAULT_COMMAND,
        help=f"Command to send (default: {_DEFAULT_COMMAND}).",
    )
    args = parser.parse_args()

    current_pane = get_current_pane_id()
    session = None if args.all_sessions else get_current_session()

    scope = "all sessions" if args.all_sessions else f"session '{session}'"
    print(f"Scanning {scope} for Claude panes (excluding self: {current_pane})...")

    panes = find_claude_panes(session=session, exclude_pane=current_pane)

    if not panes:
        print("No Claude panes found.")
        return

    print(f"Found {len(panes)} Claude pane(s):")
    for pane in panes:
        send_command(pane["target"], args.command, dry_run=args.dry_run)

    print("Done.")


if __name__ == "__main__":
    main()
