#!/usr/bin/env python3
"""Send a webhook notification when a Claude Code session stops.

This script is intended to be invoked as a Claude Code ``Stop`` hook.
It reads webhook configuration from environment variables and posts
a "Task completed!" message to the configured endpoint.

Environment Variables:
    CLAUDE_WEBHOOK_URL: Webhook endpoint URL (required).
    CLAUDE_WEBHOOK_TOKEN: Auth token (optional).
    CLAUDE_WEBHOOK_FORMAT: Payload format — ``generic``, ``slack``,
        ``discord``, or ``synology``. Defaults to ``generic``.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the scripts directory is importable.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import webhook  # noqa: E402


def main() -> None:
    """Send a 'Task completed!' webhook notification."""
    webhook.run("Task completed!")


if __name__ == "__main__":
    main()
