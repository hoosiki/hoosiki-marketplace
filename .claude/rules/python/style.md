# Python Style Rules

> PEP 8 based coding style. Uses ruff as linter/formatter.

## Core Principles

- Follow PEP 8 as the base style guide.
- Delegate auto-fixable rules to ruff.
- This document only specifies rules not covered by ruff.
- All functions and classes must have Google style docstrings.

## Formatting

- Indentation: 4 spaces (no tabs)
- Max line length: 120 characters (ruff `line-length = 120`)
- Strings: double quotes (`"`) by default (ruff `quote-style = "double"`)
- Trailing comma: always add in multiline collections
- Blank lines: 2 between top-level definitions, 1 between methods in a class

## Naming

| Target | Convention | Example |
|--------|-----------|---------|
| Module/Package | `snake_case` | `webhook.py`, `notify_stop.py` |
| Function/Variable | `snake_case` | `build_message()`, `event_type` |
| Class | `PascalCase` | `WebhookClient`, `EventHandler` |
| Constant | `UPPER_SNAKE_CASE` | `MAX_RETRIES`, `DEFAULT_TIMEOUT` |
| Private | `_` prefix | `_validate_url()`, `_internal_state` |
| Boolean variable | `is_`/`has_`/`can_` prefix | `is_valid`, `has_token`, `can_retry` |

## Import Rules

```python
# 1. Standard library
import os
import sys
from pathlib import Path

# 2. Third-party
import pytest
from unittest.mock import patch

# 3. Local/Project
from webhook import build_message
```

- One blank line between import groups
- Auto-sort with ruff's `isort` rule (`I`)
- No wildcard imports (`from x import *`)
- No circular imports
- No unused imports (`F401`)

## Functions/Methods

- Each function has a single responsibility (Single Responsibility Principle).
- Function length should be under 50 lines.
- Nested functions limited to 2 levels.
- Parameters limited to 5. Use dataclass or TypedDict if more are needed.
- Prefer early return to reduce nesting.

```python
# Good — early return
def process_event(event: Event) -> str:
    """Process an event and return a result message.

    Args:
        event: The event object to process.

    Returns:
        A result message string.

    Examples:
        >>> process_event(Event(type="webhook", data="hello"))
        "Processed: hello"
        >>> process_event(Event(type="unknown", data=""))
        "Skipped: unknown type"
    """
    if not event.data:
        return "Skipped: empty data"
    if event.type == "unknown":
        return f"Skipped: {event.type} type"
    return f"Processed: {event.data}"


# Bad — deep nesting
def process_event(event):
    if event.data:
        if event.type != "unknown":
            return f"Processed: {event.data}"
        else:
            return f"Skipped: {event.type} type"
    else:
        return "Skipped: empty data"
```

## Docstring Rules (Google Style) — Required

### Scope

- **All functions** (public and private) must have docstrings.
- **All classes** must have docstrings.
- **Modules** should have a brief docstring at the top.

### Structure

Every docstring must include the following sections (where applicable):

1. **Summary** (first line, required) — one-line description of what it does
2. **Extended description** (optional) — additional details for complex logic
3. **Args** (required if parameters exist) — description of each parameter
4. **Returns** (required if return value exists) — description of return value
5. **Raises** (required if exceptions are raised) — possible exceptions
6. **Examples** (required) — concrete input/output examples

### Full Example

```python
def build_payload(message: str, format_type: str) -> dict[str, str]:
    """Convert a message into a format-specific payload.

    Maps the message to the appropriate key name based on the
    webhook service's expected format.

    Args:
        message: The message body to send. Empty strings are not allowed.
        format_type: Webhook format. One of "discord", "slack", "generic".

    Returns:
        A payload dictionary matching the specified format.

    Raises:
        ValueError: If format_type is unsupported or message is empty.

    Examples:
        >>> build_payload("server started", "discord")
        {"content": "server started"}

        >>> build_payload("deploy complete", "slack")
        {"text": "deploy complete"}

        >>> build_payload("notification", "generic")
        {"text": "notification"}

        >>> build_payload("", "generic")
        Traceback (most recent call last):
            ...
        ValueError: message must not be empty
    """
```

### Simple Functions

Even simple functions must have docstring + Examples:

```python
def _validate_url(url: str) -> bool:
    """Validate that a URL uses the http or https scheme.

    Args:
        url: The URL string to validate.

    Returns:
        True if the URL is http/https, False otherwise.

    Examples:
        >>> _validate_url("https://example.com")
        True
        >>> _validate_url("ftp://example.com")
        False
        >>> _validate_url("not-a-url")
        False
    """
    return url.startswith(("http://", "https://"))
```

### Class Docstrings

```python
class WebhookClient:
    """Client for sending messages to external webhook services.

    Supports multiple webhook formats (Discord, Slack, Generic)
    with built-in retry logic and timeout handling.

    Attributes:
        base_url: The webhook endpoint URL.
        timeout: Request timeout in seconds. Defaults to 30.
        format_type: The webhook format type.

    Examples:
        >>> client = WebhookClient("https://hooks.example.com", format_type="slack")
        >>> client.send("deploy complete")
        True

        >>> client = WebhookClient("https://invalid.url", timeout=5)
        >>> client.send("test")
        False
    """

    def __init__(self, base_url: str, timeout: int = 30, format_type: str = "generic") -> None:
        """Initialize WebhookClient.

        Args:
            base_url: The webhook endpoint URL.
            timeout: Request timeout in seconds. Defaults to 30.
            format_type: Webhook format. Defaults to "generic".

        Raises:
            ValueError: If base_url does not use http/https scheme.

        Examples:
            >>> client = WebhookClient("https://hooks.slack.com/services/xxx")
            >>> client.timeout
            30
        """
```

### Module Docstrings

```python
"""Webhook delivery module.

Sends notifications to external webhook services when
Claude Code events occur.

Key functions:
    - send_webhook: Send a payload to a webhook URL.
    - build_payload: Create a format-specific payload.
    - run: Read environment variables and execute webhook delivery.
"""
```

## Error Handling

- Catch specific exception types (`except ValueError:`, `except OSError:`).
- Distinguish between recoverable errors and programming errors.
- Always handle exceptions for external calls (network, filesystem, etc.).
- Define custom exceptions per domain, inheriting from `Exception`.

```python
class WebhookError(Exception):
    """Base exception for webhook delivery failures.

    Examples:
        >>> raise WebhookError("delivery failed")
        Traceback (most recent call last):
            ...
        WebhookError: delivery failed
    """


class WebhookTimeoutError(WebhookError):
    """Exception raised when a webhook request times out.

    Examples:
        >>> raise WebhookTimeoutError("exceeded 30s")
        Traceback (most recent call last):
            ...
        WebhookTimeoutError: exceeded 30s
    """
```

## Logging

- Use the `logging` module instead of `print()`.
- Create a logger per module: `logger = logging.getLogger(__name__)`
- Log levels: `DEBUG` (development), `INFO` (operational), `WARNING` (caution), `ERROR` (failure)
- Use `%s` formatting instead of f-strings (lazy evaluation).

```python
import logging

logger = logging.getLogger(__name__)

# Good — lazy evaluation
logger.info("Webhook sent to %s (status=%d)", url, status_code)

# Bad — always formats
logger.info(f"Webhook sent to {url} (status={status_code})")
```

## Recommended ruff Configuration

Activate the following rules in `pyproject.toml` or `ruff.toml`:

```toml
[tool.ruff]
line-length = 120
target-version = "py310"

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "I",    # isort
    "N",    # pep8-naming
    "UP",   # pyupgrade
    "B",    # flake8-bugbear
    "SIM",  # flake8-simplify
    "RUF",  # ruff-specific rules
    "D",    # pydocstyle (enforce docstrings)
]

[tool.ruff.lint.pydocstyle]
convention = "google"
```

## Running ruff

```bash
# Lint check
ruff check .

# Auto-fix
ruff check --fix .

# Format
ruff format .

# Docstring check only
ruff check --select D .
```

## Prohibited

- Do not commit `print()` debugging code (use logging).
- Do not use mutable default arguments (`def f(items=[])`).
- Do not use bare `except:` (at minimum use `except Exception:`).
- Do not share state through global variables.
- Do not commit functions/classes without docstrings.
- Do not commit functions without an Examples section in the docstring.
- `TODO` comments must include author and reason: `# TODO(hoosiki): reason`
