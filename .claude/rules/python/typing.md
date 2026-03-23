# Python Type Hints Rules

> Gradual typing policy. Validated with pyright + ruff.

## Core Principles

- Apply type hints **gradually**. Do not enforce on all code at once.
- Type hints are **required** for all newly written code.
- When modifying **existing code**, add type hints to the affected functions/classes.
- Use pyright as the type checker with ruff's type-related rules as supplementary.

## Scope

### Required (New Code)

- All function parameters and return types (public + private)
- Class attributes (especially instance variables defined in `__init__`)
- Module-level constants/variables

```python
def send_webhook(url: str, token: str, payload: dict[str, str]) -> bool:
    """Send a webhook notification.

    Args:
        url: The webhook endpoint URL.
        token: Authentication token.
        payload: Data to send.

    Returns:
        Whether the delivery was successful.

    Examples:
        >>> send_webhook("https://example.com/hook", "tok", {"text": "hi"})
        True
    """
    ...


class WebhookClient:
    """Webhook client.

    Attributes:
        base_url: The webhook endpoint URL.
        timeout: Request timeout in seconds.

    Examples:
        >>> client = WebhookClient("https://hooks.example.com")
        >>> client.timeout
        30
    """

    base_url: str
    timeout: int

    def __init__(self, base_url: str, timeout: int = 30) -> None:
        """Initialize WebhookClient.

        Args:
            base_url: The webhook endpoint URL.
            timeout: Request timeout in seconds. Defaults to 30.

        Examples:
            >>> client = WebhookClient("https://hooks.example.com", timeout=10)
            >>> client.base_url
            "https://hooks.example.com"
        """
        self.base_url = base_url
        self.timeout = timeout
```

### Recommended (When Modifying Existing Code)

- Add type hints to the function being modified
- Add type hints to internal helpers called by that function when possible

### Optional (Later)

- Test code (fixture return types, etc.)
- Simple scripts / one-off code
- Local variables (where pyright can infer the type)

## Type Annotation Rules

### Use Modern Syntax (Python 3.10+)

```python
# Good — use built-in types directly
def process(items: list[str]) -> dict[str, int]:
    """Process items and return a frequency dictionary.

    Args:
        items: List of strings to process.

    Returns:
        A dictionary mapping each string to its occurrence count.

    Examples:
        >>> process(["a", "b", "a"])
        {"a": 2, "b": 1}
    """
    result: str | None = None
    ...


# Bad — import from typing module
from typing import List, Dict, Optional
def process(items: List[str]) -> Dict[str, int]:
    result: Optional[str] = None
```

### Common Patterns

```python
from collections.abc import Callable, Sequence, Mapping, Iterator
from typing import Any, TypeAlias, TypeGuard

# Union → | operator
value: str | int | None

# Callable
handler: Callable[[str, int], bool]

# TypeAlias (complex types)
Payload: TypeAlias = dict[str, str | int | list[str]]

# TypedDict (structured dicts)
from typing import TypedDict

class WebhookConfig(TypedDict):
    url: str
    token: str
    format: str
    timeout: int
```

### Advanced Patterns

#### Protocol (Structural Subtyping)

Use Protocol instead of interfaces to express duck typing in a type-safe way:

```python
from typing import Protocol


class Sendable(Protocol):
    """Protocol for objects capable of sending messages.

    Examples:
        >>> class SlackSender:
        ...     def send(self, message: str) -> bool:
        ...         return True
        >>> sender: Sendable = SlackSender()  # OK — structurally compatible
    """

    def send(self, message: str) -> bool: ...


def notify(sender: Sendable, message: str) -> None:
    """Send a message using any object implementing the Sendable protocol.

    Args:
        sender: An object with a send() method.
        message: The message to send.

    Examples:
        >>> class MockSender:
        ...     def send(self, message: str) -> bool:
        ...         return True
        >>> notify(MockSender(), "hello")  # works
    """
    sender.send(message)
```

#### TypeGuard (Type Narrowing)

```python
from typing import TypeGuard


def is_string_list(val: list[object]) -> TypeGuard[list[str]]:
    """Check whether all elements in a list are strings.

    Args:
        val: The list to check.

    Returns:
        True if all elements are str.

    Examples:
        >>> is_string_list(["a", "b"])
        True
        >>> is_string_list(["a", 1])
        False
    """
    return all(isinstance(x, str) for x in val)
```

#### overload (Overloaded Signatures)

```python
from typing import overload


@overload
def get_value(key: str, default: None = None) -> str | None: ...
@overload
def get_value(key: str, default: str) -> str: ...
def get_value(key: str, default: str | None = None) -> str | None:
    """Return the value for the given key.

    Args:
        key: The key to look up.
        default: Value to return if key is not found.

    Returns:
        The value for the key, or the default.

    Examples:
        >>> get_value("name")  # default=None → str | None
        >>> get_value("name", "unknown")  # default=str → str
        "unknown"
    """
    ...
```

## pyright Configuration

Place `pyrightconfig.json` at the project root:

```json
{
  "typeCheckingMode": "basic",
  "pythonVersion": "3.10",
  "reportMissingTypeStubs": false,
  "reportUnknownMemberType": false,
  "reportUnnecessaryTypeIgnoreComment": true,
  "reportUnusedImport": true,
  "include": ["plugins", "tests"],
  "exclude": ["**/__pycache__", ".ruff_cache", ".pytest_cache"]
}
```

- Start with `basic` mode, gradually upgrade to `standard`.
- Update `include` when adding new modules.
- `reportUnnecessaryTypeIgnoreComment` detects stale `type: ignore` comments.

## ruff Integration

Type-related rules to activate in ruff:

```toml
[tool.ruff.lint]
select = [
    "UP",   # pyupgrade — auto-convert legacy type annotations to modern syntax
    "ANN",  # flake8-annotations — warn on missing type hints
    "TCH",  # flake8-type-checking — optimize TYPE_CHECKING blocks
    "RET",  # flake8-return — return type consistency
]

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["ANN"]  # skip annotation warnings in test code
```

## Prohibited

- Do not overuse `Any` for convenience. Use it only when truly any type is needed.
- Do not use `# type: ignore` without a reason. Always specify the justification.
  ```python
  result = external_lib.call()  # type: ignore[no-untyped-call]  # library has no stubs
  ```
- Do not overuse `cast()`. Prefer type narrowing (`isinstance`, pattern matching).
- Do not overuse `dict[str, Any]`. Use `TypedDict` for dicts with known structure.
- Do not omit `-> None` return type. Always make it explicit.
