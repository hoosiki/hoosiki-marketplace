#!/usr/bin/env python3
"""Claude Code UserPromptSubmit Hook: prompt + metadata logging.

Reads the hook's stdin JSON, enriches it with environment and system
metadata, and POSTs the combined payload to an external logging API.

The script exits with code 0 regardless of success or failure so that
it never blocks the user's prompt from reaching Claude.

Environment Variables:
    CLAUDE_PROMPT_LOG_URL: Logging API endpoint URL (required).
    CLAUDE_PROMPT_LOG_API_KEY: Bearer token for the API (required).

    Both variables must be set; the script silently exits if either is missing.
"""

from __future__ import annotations

import json
import os
import platform
import socket
import subprocess
import sys
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# ── Configuration ──────────────────────────────────────────────────
_API_URL: str = os.environ.get("CLAUDE_PROMPT_LOG_URL", "")
_API_KEY: str = os.environ.get("CLAUDE_PROMPT_LOG_API_KEY", "")
_REQUEST_TIMEOUT: int = 5


def _cmd(args: list[str], cwd: str | None = None) -> str:
    """Run a command and return stripped stdout.

    Args:
        args: Command and arguments as a list (no shell interpolation).
        cwd: Working directory for the command.

    Returns:
        Stripped stdout output, or an empty string on any failure.
    """
    try:
        return subprocess.check_output(
            args,
            stderr=subprocess.DEVNULL,
            cwd=cwd,
            timeout=3,
        ).decode().strip()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired,
            FileNotFoundError, UnicodeDecodeError):
        return ""


def collect_metadata(hook_input: dict[str, str]) -> dict[str, object]:
    """Merge hook stdin JSON with environment and system metadata.

    Args:
        hook_input: The JSON object received on stdin from Claude Code.

    Returns:
        A combined dict ready to be JSON-serialised and sent to the API.
    """
    cwd: str = hook_input.get("cwd", os.getcwd())

    return {
        # ── Hook stdin fields ──
        "prompt": hook_input.get("prompt", ""),
        "session_id": hook_input.get("session_id", ""),
        "cwd": cwd,
        "permission_mode": hook_input.get("permission_mode", ""),
        "hook_event_name": hook_input.get("hook_event_name", ""),
        "transcript_path": hook_input.get("transcript_path", ""),

        # ── Claude Code environment variables ──
        "project_dir": os.environ.get("CLAUDE_PROJECT_DIR", ""),
        "user_email": os.environ.get("CLAUDE_CODE_USER_EMAIL", ""),
        "account_uuid": os.environ.get("CLAUDE_CODE_ACCOUNT_UUID", ""),
        "organization_uuid": os.environ.get("CLAUDE_CODE_ORGANIZATION_UUID", ""),
        "team_name": os.environ.get("CLAUDE_CODE_TEAM_NAME", ""),
        "model": os.environ.get("ANTHROPIC_MODEL", ""),
        "is_remote": os.environ.get("CLAUDE_CODE_REMOTE", "false"),

        # ── System info ──
        "hostname": socket.gethostname(),
        "os_system": platform.system(),
        "os_release": platform.release(),
        "os_machine": platform.machine(),
        "system_user": os.environ.get("USER", os.environ.get("USERNAME", "")),

        # ── Git info ──
        "git_branch": _cmd(["git", "branch", "--show-current"], cwd=cwd),
        "git_remote": _cmd(["git", "remote", "get-url", "origin"], cwd=cwd),
        "git_commit": _cmd(["git", "rev-parse", "--short", "HEAD"], cwd=cwd),

        # ── Timestamps ──
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "local_timestamp": datetime.now().isoformat(),
    }


def send_to_api(payload: dict[str, object]) -> bool:
    """POST the payload to the logging API.

    Args:
        payload: The metadata dict to send.

    Returns:
        ``True`` if the server responded with 2xx, ``False`` otherwise.
    """
    if not _API_URL or not _API_KEY:
        return False

    data: bytes = json.dumps(payload).encode("utf-8")
    headers: dict[str, str] = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {_API_KEY}",
    }
    req = Request(_API_URL, data=data, headers=headers, method="POST")

    try:
        with urlopen(req, timeout=_REQUEST_TIMEOUT) as resp:
            return 200 <= resp.status < 300
    except (HTTPError, URLError, OSError):
        return False


def main() -> None:
    """Entry point: read stdin, collect metadata, send to API."""
    try:
        hook_input: dict[str, str] = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        hook_input = {}

    payload: dict[str, object] = collect_metadata(hook_input)
    send_to_api(payload)

    # Always exit 0 so the prompt is never blocked.
    sys.exit(0)


if __name__ == "__main__":
    main()
