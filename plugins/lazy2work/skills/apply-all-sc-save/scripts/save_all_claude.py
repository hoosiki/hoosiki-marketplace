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
_TMUX_TIMEOUT: int = 5
_DEFAULT_COMMAND: str = "/sc:save"


class TmuxError(Exception):
    """A tmux command exited non-zero or timed out.

    Examples:
        >>> raise TmuxError("can't find pane: s:9.1")
        Traceback (most recent call last):
            ...
        TmuxError: can't find pane: s:9.1
    """

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
    """Run a tmux command and return stripped stdout.

    Args:
        *args: tmux subcommand and its arguments.

    Returns:
        The command's stdout with surrounding whitespace removed.

    Raises:
        TmuxError: If tmux exits non-zero or does not answer within the timeout.

    Examples:
        >>> _run_tmux("display-message", "-p", "#{session_name}")
        'claude-research'
    """
    try:
        result = subprocess.run(
            [_TMUX_CMD, *args],
            capture_output=True,
            text=True,
            timeout=_TMUX_TIMEOUT,
        )
    except subprocess.TimeoutExpired as exc:
        raise TmuxError(f"timed out after {_TMUX_TIMEOUT}s: tmux {' '.join(args)}") from exc
    if result.returncode != 0:
        raise TmuxError(result.stderr.strip() or f"tmux {args[0]} exited {result.returncode}")
    return result.stdout.strip()


def _is_in_mode(target: str) -> bool:
    """Return True if the pane is in copy mode or any other tmux mode.

    Args:
        target: tmux pane target (e.g. session:window.pane).

    Returns:
        True while keys sent to the pane would go to the mode instead of the program.

    Examples:
        >>> _is_in_mode("claude-research:5.1")
        False
    """
    return _run_tmux("display-message", "-p", "-t", target, "#{pane_in_mode}") == "1"


def _leave_pane_mode(target: str) -> bool:
    """Take a pane out of copy mode (or any other mode) so keys reach its program.

    A pane scrolled back in copy mode swallows send-keys: `/` opens a search
    prompt there and the keystrokes never reach Claude.

    Args:
        target: tmux pane target (e.g. session:window.pane).

    Returns:
        True if the pane is now in normal mode.

    Raises:
        TmuxError: If a tmux call fails.

    Examples:
        >>> _leave_pane_mode("claude-research:5.1")
        True
    """
    if not _is_in_mode(target):
        return True
    _run_tmux("copy-mode", "-q", "-t", target)
    return not _is_in_mode(target)


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


def send_command(target: str, command: str, *, dry_run: bool = False) -> bool:
    """Send a command string followed by Enter to a tmux pane.

    Leaves copy mode first. A failure is reported and returned rather than
    raised, so one stuck pane does not stop the rest of the run.

    Args:
        target: tmux pane target (e.g. session:window.pane).
        command: text to send.
        dry_run: if True, print instead of sending.

    Returns:
        True if the command was sent (or would be, in a dry run).

    Examples:
        >>> send_command("claude-research:5.1", "/sc:save")
          sent '/sc:save' to claude-research:5.1
        True
    """
    if dry_run:
        print(f"  [dry-run] would send '{command}' to {target}")
        return True
    try:
        if not _leave_pane_mode(target):
            print(f"  skipped {target}: pane is still in a tmux mode", file=sys.stderr)
            return False
        _run_tmux("send-keys", "-t", target, command, "Enter")
    except TmuxError as exc:
        print(f"  failed {target}: {exc}", file=sys.stderr)
        return False
    print(f"  sent '{command}' to {target}")
    return True


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

    try:
        current_pane = get_current_pane_id()
        session = None if args.all_sessions else get_current_session()

        scope = "all sessions" if args.all_sessions else f"session '{session}'"
        print(f"Scanning {scope} for Claude panes (excluding self: {current_pane})...")

        panes = find_claude_panes(session=session, exclude_pane=current_pane)
    except TmuxError as exc:
        print(f"tmux error: {exc}", file=sys.stderr)
        sys.exit(1)

    if not panes:
        print("No Claude panes found.")
        return

    print(f"Found {len(panes)} Claude pane(s):")
    failed = [p["target"] for p in panes if not send_command(p["target"], args.command, dry_run=args.dry_run)]

    if failed:
        print(f"Done, but {len(failed)} pane(s) did not get the command: {', '.join(failed)}", file=sys.stderr)
        sys.exit(1)
    print("Done.")


if __name__ == "__main__":
    main()
