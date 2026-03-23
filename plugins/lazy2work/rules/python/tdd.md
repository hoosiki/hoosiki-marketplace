---
paths:
  - "**/*.py"
  - "**/*.pyi"
---

# Python TDD (Test-Driven Development) Rules

> Apply TDD principles to all Python files in this project.

## Core Principle: Red-Green-Refactor

1. **Red** — Write a failing test first
2. **Green** — Write the minimum code to make the test pass
3. **Refactor** — Clean up the code while keeping tests passing

## Required Rules

### 1. Write Tests First

- **Before** implementing any new function, class, or module, write the test first.
- When modifying existing code, **first** add or update tests to verify the change.
- When fixing a bug, **first** write a test that reproduces the bug.

### 2. Test File Structure

```
tests/
├── conftest.py              # Shared fixtures
├── __init__.py
├── test_webhook.py          # plugins/lazy2work/scripts/webhook.py
├── test_notify_waiting.py   # plugins/lazy2work/scripts/notify_waiting.py
├── test_notify_stop.py      # plugins/lazy2work/scripts/notify_stop.py
├── test_log_prompt.py       # plugins/lazy2work/scripts/log_prompt.py
└── test_up2date.py          # plugins/lazy2work/skills/up2date/scripts/up2date.py
```

- Test files go in the `tests/` directory.
- Test file names use the `test_` prefix: `test_{module_name}.py`
- Maintain a 1:1 mapping between source files and test files.
- Define shared fixtures in `conftest.py`.

### 3. Test Writing Rules

```python
# Test function naming: test_{action}_{condition}_{expected_result}
def test_build_message_with_valid_event_returns_formatted_string():
    """build_message returns a formatted string for a valid event."""
    ...


def test_validate_url_with_ftp_scheme_returns_false():
    """validate_url returns False for an ftp scheme URL."""
    ...


def test_send_webhook_with_invalid_url_raises_system_exit():
    """send_webhook raises SystemExit for an invalid URL."""
    ...
```

- Use **pytest** as the test framework.
- Test function names start with `test_` and clearly express the test intent.
- Naming pattern: `test_{action}_{condition}_{expected_result}`
- Every test function must have a one-line docstring.
- Each test verifies a single behavior (Single Assertion Principle).
- Follow the `Arrange-Act-Assert` (AAA) pattern.

```python
def test_build_payload_with_discord_format_uses_content_key():
    """build_payload uses the content key for discord format."""
    # Arrange
    message = "hello"
    format_type = "discord"

    # Act
    result = build_payload(message, format_type)

    # Assert
    assert result == {"content": "hello"}
```

### 4. Test Coverage

- Every public function must have at least one test.
- Test both the happy path and error paths.
- Include boundary values and edge cases.
- Mock external dependencies (network, filesystem, environment variables).

### 5. Mocks and Fixtures

#### conftest.py Shared Fixtures

```python
# tests/conftest.py
import pytest


@pytest.fixture
def webhook_env(monkeypatch):
    """Set up environment variables required for webhook tests."""
    monkeypatch.setenv("CLAUDE_WEBHOOK_URL", "https://hooks.example.com/test")
    monkeypatch.setenv("CLAUDE_WEBHOOK_TOKEN", "test-token")
    monkeypatch.setenv("CLAUDE_WEBHOOK_FORMAT", "generic")


@pytest.fixture
def sample_event():
    """Return sample event data for testing."""
    return {
        "type": "webhook",
        "data": "test message",
        "timestamp": "2026-01-01T00:00:00Z",
    }
```

#### Fixture Scope Guide

| Scope | Use Case | Example |
|-------|----------|---------|
| `function` (default) | Create fresh per test | mocks, env vars, temp data |
| `class` | Share within class | DB connection (read-only) |
| `module` | Share within file | Heavy initialization |
| `session` | Share across all tests | Rarely used |

```python
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def mock_env(monkeypatch):
    """Shared environment variable fixture."""
    monkeypatch.setenv("CLAUDE_WEBHOOK_URL", "https://example.com/hook")
    monkeypatch.setenv("CLAUDE_WEBHOOK_FORMAT", "generic")


@patch("webhook.urlopen")
def test_send_webhook_calls_urlopen(mock_urlopen):
    """send_webhook calls urlopen."""
    ...
```

- Network calls (`urlopen`, `subprocess.run`, etc.) must always be mocked.
- Isolate environment variables with `monkeypatch.setenv()`.
- Use `tmp_path` fixture or mocks for filesystem access.
- Define shared fixtures in `conftest.py`.

### 6. Parametrize

Consolidate similar test cases with `@pytest.mark.parametrize`:

```python
class TestValidateUrl:
    """URL validation tests."""

    @pytest.mark.parametrize(
        ("url", "expected"),
        [
            ("https://example.com", True),
            ("http://example.com/path", True),
            ("ftp://example.com", False),
            ("file:///etc/passwd", False),
            ("not-a-url", False),
            ("", False),
        ],
        ids=[
            "https-valid",
            "http-with-path-valid",
            "ftp-invalid",
            "file-scheme-invalid",
            "no-scheme-invalid",
            "empty-string-invalid",
        ],
    )
    def test_url_validation(self, url: str, expected: bool):
        """URL validation returns the correct result."""
        from webhook import _validate_url
        assert _validate_url(url) == expected
```

- Use the `ids` parameter to give meaningful names to each case.
- Specify parameter names as a tuple: `("input", "expected")`

### 7. Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run a specific module
pytest tests/test_webhook.py -v

# Run a specific class/function
pytest tests/test_webhook.py::TestBuildPayload -v
pytest tests/test_webhook.py::TestBuildPayload::test_discord_format_uses_content_key -v

# Re-run only the last failed tests
pytest tests/ --lf

# Coverage report
pytest tests/ --cov=plugins --cov-report=term-missing

# Set minimum coverage threshold
pytest tests/ --cov=plugins --cov-fail-under=80
```

- After every code change, run the related tests and verify they pass.
- Run the full test suite before any PR/commit.

## Implementation Workflow

### Adding a New Feature

```
1. Analyze requirements
2. Create/modify test file → write a failing test (Red)
3. Run pytest → verify test failure
4. Write the minimum implementation code (Green)
5. Run pytest → verify test passes
6. Refactor the code (Refactor)
7. Run pytest → verify tests still pass
8. Repeat for the next test case
```

### Fixing a Bug

```
1. Write a test that reproduces the bug (Red)
2. Run pytest → verify test failure (bug reproduced)
3. Write the bug fix (Green)
4. Run pytest → verify test passes
5. Keep as a regression test
```

### Refactoring

```
1. Verify all existing tests pass
2. Perform the refactoring
3. Verify all existing tests still pass
4. Refactor tests alongside if needed
```

## Project Test Guide

### webhook.py Test Example

```python
# tests/test_webhook.py
"""Webhook module tests."""
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def webhook_env(monkeypatch):
    """Set up webhook test environment variables."""
    monkeypatch.setenv("CLAUDE_WEBHOOK_URL", "https://hooks.example.com/test")
    monkeypatch.setenv("CLAUDE_WEBHOOK_TOKEN", "test-token")
    monkeypatch.setenv("CLAUDE_WEBHOOK_FORMAT", "generic")


class TestBuildMessage:
    """Tests for build_message function."""

    @patch("webhook.get_hostname", return_value="myhost")
    @patch("webhook.get_cwd_name", return_value="myproject")
    def test_includes_hostname_and_cwd(self, mock_cwd, mock_host):
        """Message includes hostname and working directory."""
        from webhook import build_message
        result = build_message("Hello!")
        assert result == "[myhost] myproject: Hello!"


class TestBuildPayload:
    """Tests for build_payload function."""

    def test_discord_format_uses_content_key(self):
        """Discord format uses the content key."""
        from webhook import build_payload
        result = build_payload("msg", "discord")
        assert result == {"content": "msg"}

    def test_generic_format_uses_text_key(self):
        """Generic format uses the text key."""
        from webhook import build_payload
        result = build_payload("msg", "generic")
        assert result == {"text": "msg"}


class TestValidateUrl:
    """URL validation tests."""

    @pytest.mark.parametrize(
        ("url", "expected"),
        [
            ("https://example.com", True),
            ("http://example.com/path", True),
            ("ftp://example.com", False),
            ("file:///etc/passwd", False),
            ("not-a-url", False),
        ],
        ids=["https", "http-path", "ftp", "file-scheme", "no-scheme"],
    )
    def test_url_validation(self, url: str, expected: bool):
        """URL validation returns the correct result."""
        from webhook import _validate_url
        assert _validate_url(url) == expected


class TestSendWebhook:
    """Tests for send_webhook function."""

    @patch("webhook.urlopen")
    def test_sends_json_post_for_generic(self, mock_urlopen):
        """Sends a JSON POST request for generic format."""
        from webhook import send_webhook
        send_webhook("https://example.com", "", {"text": "hi"}, "generic")
        mock_urlopen.assert_called_once()


class TestRun:
    """Tests for run function."""

    @patch("webhook.send_webhook")
    def test_skips_when_no_url(self, mock_send, monkeypatch):
        """Skips delivery when the URL environment variable is not set."""
        monkeypatch.delenv("CLAUDE_WEBHOOK_URL", raising=False)
        from webhook import run
        run("test")
        mock_send.assert_not_called()
```

## Recommended pytest Configuration

Add pytest settings to `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --strict-markers --tb=short"
markers = [
    "slow: long-running tests",
    "integration: integration tests",
]
```

## Prohibited

- Do not commit new Python code without tests.
- Do not commit with ignored (`skip`, `xfail`) failing tests without a clear reason comment.
- Do not call real external services (webhook URLs, APIs, etc.) in tests.
- Do not use `time.sleep()` in tests.
- Do not create state sharing or execution order dependencies between tests.
- Do not commit test functions without docstrings.
- Do not use meaningless assertions like `assert True` or `assert result`.
