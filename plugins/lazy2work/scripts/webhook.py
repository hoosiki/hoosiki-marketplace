#!/usr/bin/env python3
"""Shared webhook utilities for Claude Code notification hooks.

Provides common functions for building and sending webhook payloads
to various services (Slack, Discord, Synology Chat, generic endpoints).

Environment Variables:
    CLAUDE_WEBHOOK_URL: Webhook endpoint URL (required).
    CLAUDE_WEBHOOK_TOKEN: Auth token (optional).
    CLAUDE_WEBHOOK_FORMAT: Payload format — ``generic``, ``slack``,
        ``discord``, or ``synology``. Defaults to ``generic``.
"""

from __future__ import annotations

import json
import os
import socket
import sys
from pathlib import Path
from urllib.error import URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

# Supported webhook payload formats.
SUPPORTED_FORMATS: tuple[str, ...] = ("generic", "slack", "discord", "synology")

# Default HTTP request timeout in seconds (configurable via env, clamped 1–60).
_REQUEST_TIMEOUT: int = max(1, min(int(os.environ.get("CLAUDE_WEBHOOK_TIMEOUT", "10")), 60))


def get_hostname() -> str:
    """Return the hostname of the current machine.

    Returns:
        The machine's hostname as reported by ``socket.gethostname()``.
    """
    return socket.gethostname()


def get_cwd_name() -> str:
    """Return the name of the current working directory.

    Returns:
        The final component of the current working directory path.
    """
    return Path(os.getcwd()).name


def _validate_url(url: str) -> bool:
    """Check that *url* uses an allowed scheme and has a hostname.

    Only ``http`` and ``https`` schemes are permitted to prevent SSRF
    via ``file://``, ``ftp://``, or other dangerous schemes.

    Args:
        url: The URL to validate.

    Returns:
        ``True`` if the URL is acceptable, ``False`` otherwise.
    """
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    if parsed.scheme not in ("http", "https"):
        return False
    if not parsed.hostname:
        return False
    return True


def build_message(event_text: str) -> str:
    """Build a notification message with hostname and directory context.

    Args:
        event_text: The event-specific message body
            (e.g. ``"Task completed!"``).

    Returns:
        A formatted string like ``[hostname] cwd: event_text``.
    """
    hostname: str = get_hostname()
    cwd: str = get_cwd_name()
    return f"[{hostname}] {cwd}: {event_text}"


def build_payload(message: str, fmt: str) -> dict[str, str]:
    """Build a webhook payload dict appropriate for the target service.

    Args:
        message: The notification message to send.
        fmt: The webhook format — one of ``generic``, ``slack``,
            ``discord``, or ``synology``.

    Returns:
        A dictionary suitable for JSON serialisation as the webhook body.
    """
    if fmt == "discord":
        return {"content": message}
    # generic, slack, synology all use {"text": ...}
    return {"text": message}


def send_webhook(
    url: str,
    token: str,
    payload: dict[str, str],
    fmt: str,
) -> None:
    """Send a webhook HTTP POST request.

    For Synology format the payload and optional token are sent as
    form-encoded POST body fields.  For all other formats the payload
    is JSON-encoded and the token (if provided) is sent as a ``Bearer``
    authorization header.

    Args:
        url: The webhook endpoint URL.
        token: An authentication token.  Pass an empty string to skip.
        payload: The message payload dictionary.
        fmt: The webhook format (see ``SUPPORTED_FORMATS``).

    Raises:
        SystemExit: If the HTTP request fails.
    """
    headers: dict[str, str]
    data: bytes

    if fmt == "synology":
        form_parts: list[str] = [f"payload={quote(json.dumps(payload))}"]
        if token:
            form_parts.append(f"token={quote(token)}")
        data = "&".join(form_parts).encode("utf-8")
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
    else:
        data = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

    req = Request(url, data=data, headers=headers, method="POST")
    try:
        with urlopen(req, timeout=_REQUEST_TIMEOUT):
            pass
    except URLError as exc:
        print(f"Webhook request failed: {exc}", file=sys.stderr)
        sys.exit(1)


def run(event_text: str) -> None:
    """Entry-point helper: read env vars, build message, and send webhook.

    Silently returns if ``CLAUDE_WEBHOOK_URL`` is not set.

    Args:
        event_text: The event-specific message body
            (e.g. ``"Task completed!"``).
    """
    url: str = os.environ.get("CLAUDE_WEBHOOK_URL", "")
    if not url:
        return

    if not _validate_url(url):
        print(
            "Webhook URL invalid: only http/https with a valid hostname are allowed.",
            file=sys.stderr,
        )
        return

    token: str = os.environ.get("CLAUDE_WEBHOOK_TOKEN", "")
    fmt: str = os.environ.get("CLAUDE_WEBHOOK_FORMAT", "generic").lower()

    if fmt not in SUPPORTED_FORMATS:
        print(
            f"Unknown webhook format '{fmt}'. "
            f"Supported: {', '.join(SUPPORTED_FORMATS)}",
            file=sys.stderr,
        )
        return

    message: str = build_message(event_text)
    payload: dict[str, str] = build_payload(message, fmt)
    send_webhook(url, token, payload, fmt)
