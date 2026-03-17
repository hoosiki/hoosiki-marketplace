"""Tests for the log_prompt hook script."""

from __future__ import annotations

import json
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Make the scripts directory importable.
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "plugins" / "lazy2work" / "scripts")
sys.path.insert(0, _SCRIPTS_DIR)

import log_prompt  # noqa: E402


# ── _cmd ──────────────────────────────────────────────────────────


def test_cmd_returns_stdout() -> None:
    result = log_prompt._cmd(["echo", "hello"])
    assert result == "hello"


def test_cmd_returns_empty_on_failure() -> None:
    result = log_prompt._cmd(["false"])
    assert result == ""


def test_cmd_returns_empty_on_timeout() -> None:
    result = log_prompt._cmd(["sleep", "10"], cwd="/tmp")
    # _cmd has a 3-second timeout, so this should fail gracefully
    assert result == ""


def test_cmd_returns_empty_on_missing_binary() -> None:
    result = log_prompt._cmd(["nonexistent_binary_xyz"])
    assert result == ""


# ── collect_metadata ──────────────────────────────────────────────


def test_collect_metadata_includes_hook_fields() -> None:
    hook_input = {
        "prompt": "test prompt",
        "session_id": "sess-123",
        "cwd": "/tmp",
        "permission_mode": "default",
        "hook_event_name": "UserPromptSubmit",
        "transcript_path": "/some/path.jsonl",
    }
    result = log_prompt.collect_metadata(hook_input)

    assert result["prompt"] == "test prompt"
    assert result["session_id"] == "sess-123"
    assert result["cwd"] == "/tmp"
    assert result["permission_mode"] == "default"
    assert result["hook_event_name"] == "UserPromptSubmit"
    assert result["transcript_path"] == "/some/path.jsonl"


def test_collect_metadata_includes_system_info() -> None:
    result = log_prompt.collect_metadata({})

    assert result["hostname"] != ""
    assert result["os_system"] != ""
    assert result["os_machine"] != ""
    assert "timestamp" in result
    assert "local_timestamp" in result


@patch.dict("os.environ", {
    "CLAUDE_PROJECT_DIR": "/my/project",
    "CLAUDE_CODE_USER_EMAIL": "test@example.com",
    "ANTHROPIC_MODEL": "claude-opus-4-6",
})
def test_collect_metadata_includes_env_vars() -> None:
    result = log_prompt.collect_metadata({})

    assert result["project_dir"] == "/my/project"
    assert result["user_email"] == "test@example.com"
    assert result["model"] == "claude-opus-4-6"


def test_collect_metadata_defaults_cwd_when_missing() -> None:
    import os
    result = log_prompt.collect_metadata({})
    assert result["cwd"] == os.getcwd()


# ── send_to_api ───────────────────────────────────────────────────


@patch.object(log_prompt, "_API_KEY", "")
def test_send_to_api_returns_false_without_api_key() -> None:
    assert log_prompt.send_to_api({"prompt": "test"}) is False


@patch.object(log_prompt, "_API_URL", "")
@patch.object(log_prompt, "_API_KEY", "test-key-12345")
def test_send_to_api_returns_false_without_api_url() -> None:
    assert log_prompt.send_to_api({"prompt": "test"}) is False


@patch.object(log_prompt, "_API_URL", "")
@patch.object(log_prompt, "_API_KEY", "")
def test_send_to_api_returns_false_without_both_env_vars() -> None:
    assert log_prompt.send_to_api({"prompt": "test"}) is False


@patch("log_prompt.urlopen")
@patch.object(log_prompt, "_API_URL", "https://example.com/api/prompts/")
@patch.object(log_prompt, "_API_KEY", "test-key-12345")
def test_send_to_api_returns_true_on_201(mock_urlopen: MagicMock) -> None:
    mock_resp = MagicMock()
    mock_resp.status = 201
    mock_resp.__enter__ = lambda s: mock_resp
    mock_resp.__exit__ = MagicMock(return_value=False)
    mock_urlopen.return_value = mock_resp

    result = log_prompt.send_to_api({"prompt": "test"})

    assert result is True
    mock_urlopen.assert_called_once()

    # Verify the request payload
    req = mock_urlopen.call_args[0][0]
    assert req.get_header("Authorization") == "Bearer test-key-12345"
    assert req.get_header("Content-type") == "application/json"
    body = json.loads(req.data.decode("utf-8"))
    assert body["prompt"] == "test"


@patch("log_prompt.urlopen", side_effect=log_prompt.URLError("connection refused"))
@patch.object(log_prompt, "_API_URL", "https://example.com/api/prompts/")
@patch.object(log_prompt, "_API_KEY", "test-key-12345")
def test_send_to_api_returns_false_on_network_error(mock_urlopen: MagicMock) -> None:
    assert log_prompt.send_to_api({"prompt": "test"}) is False


# ── main ──────────────────────────────────────────────────────────


@patch("log_prompt.send_to_api", return_value=True)
def test_main_reads_stdin_and_sends(mock_send: MagicMock) -> None:
    hook_input = {"prompt": "hello", "session_id": "s1", "cwd": "/tmp"}
    fake_stdin = StringIO(json.dumps(hook_input))

    with patch("sys.stdin", fake_stdin), pytest.raises(SystemExit) as exc_info:
        log_prompt.main()

    assert exc_info.value.code == 0
    mock_send.assert_called_once()

    payload = mock_send.call_args[0][0]
    assert payload["prompt"] == "hello"
    assert payload["session_id"] == "s1"


@patch("log_prompt.send_to_api", return_value=False)
def test_main_exits_zero_even_on_api_failure(mock_send: MagicMock) -> None:
    fake_stdin = StringIO("{}")

    with patch("sys.stdin", fake_stdin), pytest.raises(SystemExit) as exc_info:
        log_prompt.main()

    assert exc_info.value.code == 0


@patch("log_prompt.send_to_api", return_value=False)
def test_main_handles_invalid_json_stdin(mock_send: MagicMock) -> None:
    fake_stdin = StringIO("not json")

    with patch("sys.stdin", fake_stdin), pytest.raises(SystemExit) as exc_info:
        log_prompt.main()

    assert exc_info.value.code == 0
    mock_send.assert_called_once()
