"""Tests for the apply-all-sc-save skill script."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Make the skill scripts directory importable.
_SCRIPTS_DIR = str(
    Path(__file__).resolve().parent.parent
    / "plugins"
    / "lazy2work"
    / "skills"
    / "apply-all-sc-save"
    / "scripts"
)
sys.path.insert(0, _SCRIPTS_DIR)

import save_all_claude  # noqa: E402


# ── Helpers ──────────────────────────────────────────────────────


class FakeTmux:
    """Stand-in for _run_tmux that records calls and simulates pane modes."""

    def __init__(self, in_mode: dict[str, list[str]] | None = None, fail_send: set[str] | None = None) -> None:
        """Set up the fake.

        Args:
            in_mode: Per target, the successive `#{pane_in_mode}` answers ("1" or "0").
            fail_send: Targets whose `send-keys` raises TmuxError.
        """
        self.in_mode = {t: list(v) for t, v in (in_mode or {}).items()}
        self.fail_send = fail_send or set()
        self.calls: list[tuple[str, ...]] = []

    def __call__(self, *args: str) -> str:
        """Record the call and answer like tmux would."""
        self.calls.append(args)
        if args[:1] == ("display-message",) and args[-1] == "#{pane_in_mode}":
            answers = self.in_mode.get(args[args.index("-t") + 1], [])
            return answers.pop(0) if answers else "0"
        if args[:1] == ("send-keys",) and args[args.index("-t") + 1] in self.fail_send:
            raise save_all_claude.TmuxError("timed out after 5s")
        return ""

    def sent_to(self) -> list[str]:
        """Return the targets that received send-keys, in order."""
        return [c[c.index("-t") + 1] for c in self.calls if c[:1] == ("send-keys",)]


# ── _is_claude_command ───────────────────────────────────────────


class TestIsClaudeCommand:
    """Claude pane detection."""

    @pytest.mark.parametrize(
        ("command", "expected"),
        [("claude", True), ("2.1.300", True), ("nvim", False), ("zsh", False), ("codex", False)],
        ids=["literal", "version", "nvim", "zsh", "codex"],
    )
    def test_is_claude_command_matches_claude_and_versions_only(self, command: str, expected: bool):
        """_is_claude_command accepts "claude" and version strings only."""
        assert save_all_claude._is_claude_command(command) is expected


# ── _run_tmux ────────────────────────────────────────────────────


class TestRunTmux:
    """tmux invocation errors become TmuxError instead of exiting."""

    def test_run_tmux_with_timeout_raises_tmux_error(self):
        """_run_tmux raises TmuxError when tmux times out."""
        with (
            patch.object(save_all_claude.subprocess, "run", side_effect=subprocess.TimeoutExpired("tmux", 5)),
            pytest.raises(save_all_claude.TmuxError),
        ):
            save_all_claude._run_tmux("send-keys", "-t", "s:1.1", "x")

    def test_run_tmux_with_nonzero_exit_raises_tmux_error(self):
        """_run_tmux raises TmuxError when tmux exits non-zero."""
        failed = subprocess.CompletedProcess([], returncode=1, stdout="", stderr="can't find pane")
        with (
            patch.object(save_all_claude.subprocess, "run", return_value=failed),
            pytest.raises(save_all_claude.TmuxError, match="can't find pane"),
        ):
            save_all_claude._run_tmux("display-message", "-p", "x")


# ── send_command ─────────────────────────────────────────────────


class TestSendCommand:
    """Sending the command to one pane."""

    def test_send_command_in_copy_mode_exits_mode_before_sending(self):
        """send_command cancels copy mode before send-keys."""
        fake = FakeTmux(in_mode={"s:5.1": ["1", "0"]})
        with patch.object(save_all_claude, "_run_tmux", fake):
            save_all_claude.send_command("s:5.1", "/sc:save")
        verbs = [c[0] for c in fake.calls if c[0] != "display-message"]
        assert verbs == ["copy-mode", "send-keys"]

    def test_send_command_in_normal_mode_does_not_touch_mode(self):
        """send_command leaves a pane that is not in a mode alone."""
        fake = FakeTmux()
        with patch.object(save_all_claude, "_run_tmux", fake):
            save_all_claude.send_command("s:6.1", "/sc:save")
        assert not any(c[0] == "copy-mode" for c in fake.calls)

    def test_send_command_still_in_mode_skips_pane(self):
        """send_command returns False without sending when the mode will not exit."""
        fake = FakeTmux(in_mode={"s:5.1": ["1", "1"]})
        with patch.object(save_all_claude, "_run_tmux", fake):
            ok = save_all_claude.send_command("s:5.1", "/sc:save")
        assert (ok, fake.sent_to()) == (False, [])

    def test_send_command_with_tmux_failure_returns_false(self):
        """send_command returns False instead of raising when send-keys fails."""
        fake = FakeTmux(fail_send={"s:5.1"})
        with patch.object(save_all_claude, "_run_tmux", fake):
            assert save_all_claude.send_command("s:5.1", "/sc:save") is False

    def test_send_command_dry_run_sends_nothing(self):
        """send_command with dry_run makes no tmux calls."""
        fake = FakeTmux()
        with patch.object(save_all_claude, "_run_tmux", fake):
            save_all_claude.send_command("s:5.1", "/sc:save", dry_run=True)
        assert fake.calls == []


# ── main ─────────────────────────────────────────────────────────


class TestMain:
    """End-to-end flow across several panes."""

    @pytest.fixture()
    def panes(self):
        """Three Claude panes, the middle one stuck."""
        return [{"target": f"s:{w}.1", "pane_id": f"%{w}", "command": "2.1.300"} for w in (3, 5, 6)]

    def test_main_with_failed_pane_still_sends_to_later_panes(self, panes, monkeypatch):
        """main keeps going after one pane fails."""
        fake = FakeTmux(fail_send={"s:5.1"})
        monkeypatch.setattr(sys, "argv", ["save_all_claude.py"])
        with (
            patch.object(save_all_claude, "_run_tmux", fake),
            patch.object(save_all_claude, "get_current_pane_id", return_value="%1"),
            patch.object(save_all_claude, "get_current_session", return_value="s"),
            patch.object(save_all_claude, "find_claude_panes", return_value=panes),
            pytest.raises(SystemExit),
        ):
            save_all_claude.main()
        assert fake.sent_to() == ["s:3.1", "s:5.1", "s:6.1"]

    def test_main_with_failed_pane_exits_nonzero(self, panes, monkeypatch):
        """main exits with status 1 when any pane failed."""
        fake = FakeTmux(fail_send={"s:5.1"})
        monkeypatch.setattr(sys, "argv", ["save_all_claude.py"])
        with (
            patch.object(save_all_claude, "_run_tmux", fake),
            patch.object(save_all_claude, "get_current_pane_id", return_value="%1"),
            patch.object(save_all_claude, "get_current_session", return_value="s"),
            patch.object(save_all_claude, "find_claude_panes", return_value=panes),
            pytest.raises(SystemExit) as exc,
        ):
            save_all_claude.main()
        assert exc.value.code == 1
