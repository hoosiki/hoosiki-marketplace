"""Tests for the snapshot-tmux skill script."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Make the skill scripts directory importable.
_SCRIPTS_DIR = str(
    Path(__file__).resolve().parent.parent / "plugins" / "lazy2work" / "skills" / "snapshot-tmux" / "scripts"
)
sys.path.insert(0, _SCRIPTS_DIR)

import snapshot_tmux as st  # noqa: E402

# A config in the same shape as a hand-written tmuxp workspace: header, window
# comments, pane comments, an nvim command that needs quoting.
_SAMPLE = """\
# =============================================================================
#  tmuxp Session Config — ClaudeResearches
#  Usage: tmuxp load tmux_init.yaml
# =============================================================================

session_name: claude-research
start_directory: /Users/me
suppress_history: true

# tmux options (session-level)
options:
  default-command: zsh

windows:
  # ── Window 1: research ─────────────────────────────────────────────────
  - window_name: research
    start_directory: /Users/me/research
    layout: even-horizontal
    panes:
      # Pane 1 (left): Claude Code CLI
      - shell_command:
          - claude --dangerously-skip-permissions
        focus: true
      # Pane 2 (right): nvim — 가장 최근 편집 파일 자동 열기
      - shell_command:
          - nvim -c "'0"
  # ── Window 2: docker ──────────────────────────────────────────────────────
  - window_name: docker
    start_directory: /Users/me/docker
    layout: even-horizontal
    panes:
      # Pane 1 (left): Claude Code CLI
      - shell_command:
          - claude --dangerously-skip-permissions
  # ── Window 3: job ─────────────────────────────────────────────────────────
  - window_name: job
    start_directory: /Users/me/job
    layout: even-horizontal
    panes:
      # Pane 1 (left): Claude Code CLI
      - shell_command:
          - claude --dangerously-skip-permissions
"""

_CLAUDE = "claude --dangerously-skip-permissions"
_NVIM = "nvim -c \"'0\""


def _window(name: str, path: str, *panes: st.PaneSpec, layout: str = "even-horizontal") -> st.WindowSpec:
    """Build a WindowSpec for tests."""
    return st.WindowSpec(name=name, start_directory=path, layout=layout, panes=list(panes))


def _pane(*commands: str, start_directory: str | None = None, focus: bool = False) -> st.PaneSpec:
    """Build a PaneSpec for tests."""
    return st.PaneSpec(commands=list(commands), start_directory=start_directory, focus=focus)


def _sample_live() -> list[st.WindowSpec]:
    """Live windows that match _SAMPLE exactly."""
    return [
        _window("research", "/Users/me/research", _pane(_CLAUDE, focus=True), _pane(_NVIM)),
        _window("docker", "/Users/me/docker", _pane(_CLAUDE, focus=True)),
        _window("job", "/Users/me/job", _pane(_CLAUDE, focus=True)),
    ]


# ── Process inspection ───────────────────────────────────────────


class TestParseProcargs2:
    """macOS KERN_PROCARGS2 buffer parsing."""

    def test_parse_procargs2_with_padding_and_env_returns_argv_only(self):
        """_parse_procargs2 skips the exec path, NUL padding and environment."""
        raw = (3).to_bytes(4, sys.byteorder) + b"/usr/bin/nvim\0\0\0\0nvim\0-c\0'0\0HOME=/Users/me\0"
        assert st._parse_procargs2(raw) == ["nvim", "-c", "'0"]

    def test_parse_procargs2_with_short_buffer_returns_empty(self):
        """_parse_procargs2 returns [] for a truncated buffer."""
        assert st._parse_procargs2(b"\x01") == []


class TestPickForeground:
    """Foreground process selection from `ps -o pid=,pgid=,tpgid=`."""

    def test_pick_foreground_with_idle_shell_returns_none(self):
        """_pick_foreground returns None when the shell owns the terminal."""
        assert st._pick_foreground(" 2552  2552  2552\n", shell_pid=2552) is None

    def test_pick_foreground_with_running_program_returns_group_leader(self):
        """_pick_foreground returns the foreground group leader, not its children."""
        out = " 2236  2236  2562\n 2562  2562  2562\n 3960  2562  2562\n"
        assert st._pick_foreground(out, shell_pid=2236) == 2562


class TestNormalizeCommand:
    """Turning a process argv into a restorable command line."""

    @pytest.mark.parametrize(
        ("argv", "expected"),
        [
            (["claude", "--dangerously-skip-permissions", "--rc", "research"], _CLAUDE),
            (["claude", "--rc=research", "--dangerously-skip-permissions"], _CLAUDE),
            (["claude", "--remote-control", "my job", "--dangerously-skip-permissions"], _CLAUDE),
            (["claude", "--rc", "--dangerously-skip-permissions"], _CLAUDE),
            (["/Users/me/.local/bin/claude", "--dangerously-skip-permissions"], _CLAUDE),
            (["/Users/me/.local/share/claude/versions/2.1.303", "--dangerously-skip-permissions"], _CLAUDE),
            (["node", "/opt/node_modules/@anthropic-ai/claude-code/cli.js", "--dangerously-skip-permissions"], _CLAUDE),
            (["nvim", "-c", "'0"], _NVIM),
            (["ssh", "my host"], "ssh 'my host'"),
        ],
        ids=[
            "rc-space", "rc-equals", "remote-control", "rc-without-name",
            "abs-path", "version-path", "node", "nvim", "space",
        ],
    )
    def test_normalize_command_strips_rc_and_quotes_args(self, argv: list[str], expected: str):
        """normalize_command strips --rc, renames the Claude binary and quotes arguments."""
        assert st.normalize_command(argv) == expected

    def test_normalize_command_with_keep_rc_keeps_name(self):
        """normalize_command keeps --rc when asked to."""
        assert st.normalize_command(["claude", "--rc", "job"], keep_rc=True) == "claude --rc job"


# ── Quoting ──────────────────────────────────────────────────────


class TestShellQuote:
    """Shell quoting that stays readable."""

    @pytest.mark.parametrize(
        ("arg", "expected"),
        [
            ("--dangerously-skip-permissions", "--dangerously-skip-permissions"),
            ("'0", "\"'0\""),
            ("a b", "'a b'"),
            ("it's $HOME", "'it'\\''s $HOME'"),
            ("~/x", "'~/x'"),
            ("", "''"),
        ],
        ids=["safe", "single-quote", "space", "quote-and-dollar", "tilde", "empty"],
    )
    def test_shell_quote_returns_minimal_quoting(self, arg: str, expected: str):
        """_shell_quote leaves safe words bare and quotes the rest."""
        assert st._shell_quote(arg) == expected


class TestYamlScalar:
    """YAML scalar emission."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (_NVIM, _NVIM),
            ("/Users/me/research", "/Users/me/research"),
            ('{"V":2}', "'{\"V\":2}'"),
            ("true", "'true'"),
            ("2024", "'2024'"),
            ("a: b", "'a: b'"),
            ("x # y", "'x # y'"),
            ("it's: here", "'it''s: here'"),
        ],
        ids=["command", "path", "json", "bool", "number", "colon", "comment", "quote-escape"],
    )
    def test_yaml_scalar_quotes_only_when_needed(self, value: str, expected: str):
        """_yaml_scalar emits a plain scalar unless YAML would misread it."""
        assert st._yaml_scalar(value) == expected


# ── Layout ───────────────────────────────────────────────────────


_JSON_EVEN_H = (
    '{"V":2,"L":{"t":"h","w":136,"h":33,"x":0,"y":0,"c":['
    '{"t":"p","w":68,"h":33,"x":0,"y":0,"a":true,"i":1,"I":"%1"},'
    '{"t":"p","w":67,"h":33,"x":69,"y":0,"l":0,"i":2,"I":"%2"}]}}'
)
_JSON_EVEN_V = (
    '{"V":2,"L":{"t":"v","w":136,"h":33,"x":0,"y":0,"c":['
    '{"t":"p","w":136,"h":16,"x":0,"y":0,"i":1,"I":"%1"},'
    '{"t":"p","w":136,"h":16,"x":0,"y":17,"i":2,"I":"%2"}]}}'
)
_JSON_UNEVEN = (
    '{"V":2,"L":{"t":"h","w":136,"h":33,"x":0,"y":0,"c":['
    '{"t":"p","w":100,"h":33,"x":0,"y":0,"i":1,"I":"%1"},'
    '{"t":"p","w":35,"h":33,"x":101,"y":0,"i":2,"I":"%2"}]}}'
)
_JSON_UNEVEN_STABLE = (
    '{"V":2,"L":{"t":"h","w":136,"h":33,"x":0,"y":0,"c":['
    '{"t":"p","w":100,"h":33,"x":0,"y":0,"i":1},'
    '{"t":"p","w":35,"h":33,"x":101,"y":0,"i":2}]}}'
)
_JSON_SINGLE = '{"V":2,"L":{"t":"p","w":136,"h":33,"x":0,"y":0,"a":true,"i":1,"I":"%5"}}'


class TestDetectLayout:
    """Mapping a tmux layout string to a preset name when possible."""

    @pytest.mark.parametrize(
        ("layout", "expected"),
        [
            (_JSON_SINGLE, "even-horizontal"),
            (_JSON_EVEN_H, "even-horizontal"),
            (_JSON_EVEN_V, "even-vertical"),
            (_JSON_UNEVEN, _JSON_UNEVEN_STABLE),
            ("a5f1,136x33,0,0{68x33,0,0,1,67x33,69,0,2}", "even-horizontal"),
            ("a5f1,136x33,0,0[136x16,0,0,1,136x16,0,17,2]", "even-vertical"),
            ("not a layout", "not a layout"),
        ],
        ids=["single", "json-h", "json-v", "json-uneven", "legacy-h", "legacy-v", "garbage"],
    )
    def test_detect_layout_returns_preset_or_raw_layout(self, layout: str, expected: str):
        """detect_layout names even splits and keeps anything else verbatim."""
        assert st.detect_layout(layout) == expected


# ── Existing config ──────────────────────────────────────────────


class TestSplitConfig:
    """Splitting a config into header, window blocks and footer."""

    def test_split_config_keeps_header_through_windows_key(self):
        """split_config returns everything up to and including `windows:` as the header."""
        header, _, _ = st.split_config(_SAMPLE)
        assert header.endswith("  default-command: zsh\n\nwindows:\n")

    def test_split_config_attaches_window_comment_to_its_block(self):
        """split_config puts each `# ── Window N` comment at the top of its own block."""
        _, blocks, _ = st.split_config(_SAMPLE)
        banners = [b.splitlines()[0].strip()[:14] for b in blocks]
        assert banners == ["# ── Window 1:", "# ── Window 2:", "# ── Window 3:"]

    def test_split_config_round_trips_text(self):
        """split_config loses no characters."""
        header, blocks, footer = st.split_config(_SAMPLE)
        assert header + "".join(blocks) + footer == _SAMPLE


class TestParseWindowBlock:
    """Reading a window block back into a WindowSpec."""

    def test_parse_window_block_reads_name_path_layout_and_commands(self):
        """parse_window_block recovers the fields the snapshot compares."""
        _, blocks, _ = st.split_config(_SAMPLE)
        spec = st.parse_window_block(blocks[0])
        assert (spec.name, spec.start_directory, spec.layout, [p.commands for p in spec.panes]) == (
            "research",
            "/Users/me/research",
            "even-horizontal",
            [[_CLAUDE], [_NVIM]],
        )

    def test_parse_window_block_reads_pane_descriptions(self):
        """parse_window_block keeps the text of each `# Pane N (...):` comment."""
        _, blocks, _ = st.split_config(_SAMPLE)
        spec = st.parse_window_block(blocks[0])
        assert [p.description for p in spec.panes] == ["Claude Code CLI", "nvim — 가장 최근 편집 파일 자동 열기"]

    def test_parse_window_block_reports_unknown_keys(self):
        """parse_window_block lists window keys the snapshot cannot reproduce."""
        block = "  - window_name: w\n    options:\n      main-pane-width: 60\n    panes:\n      - blank\n"
        assert st.parse_window_block(block).extra_keys == ["options"]

    @pytest.mark.parametrize(
        "pane",
        ["- blank", "- null", "- shell_command: []", "- shell_command:"],
        ids=["blank", "null", "empty-list", "empty-key"],
    )
    def test_parse_window_block_reads_blank_panes(self, pane: str):
        """parse_window_block treats tmuxp's blank-pane spellings as no command."""
        block = f"  - window_name: w\n    panes:\n      {pane}\n"
        assert st.parse_window_block(block).panes[0].commands == []


# ── Rendering ────────────────────────────────────────────────────


class TestRenderConfig:
    """Producing the new config text."""

    def test_render_config_with_unchanged_session_returns_identical_text(self):
        """render_config keeps every unchanged window byte for byte."""
        text, _ = st.render_config(_SAMPLE, _sample_live(), session_name="claude-research")
        assert text == _SAMPLE

    def test_render_config_with_new_window_appends_generated_block(self):
        """render_config appends a new window in the file's comment style."""
        live = [*_sample_live(), _window("zsh", "/Users/me", _pane())]
        text, _ = st.render_config(_SAMPLE, live, session_name="claude-research")
        assert text.endswith(
            "  # ── Window 4: zsh ─────────────────────────────────────────────────────────\n"
            "  - window_name: zsh\n"
            "    start_directory: /Users/me\n"
            "    layout: even-horizontal\n"
            "    panes:\n"
            "      # Pane 1: shell\n"
            "      - blank\n"
        )

    def test_render_config_with_removed_window_renumbers_later_blocks(self):
        """render_config drops a closed window and renumbers the comments after it."""
        live = [w for w in _sample_live() if w.name != "docker"]
        text, _ = st.render_config(_SAMPLE, live, session_name="claude-research")
        assert ("window_name: docker" not in text, "# ── Window 2: job ─" in text) == (True, True)

    def test_render_config_with_changed_window_reuses_known_pane_description(self):
        """render_config regenerates a changed window and reuses the description of a known command."""
        live = _sample_live()
        live[1] = _window("docker", "/Users/me/docker", _pane(_CLAUDE, focus=True), _pane(_NVIM))
        text, _ = st.render_config(_SAMPLE, live, session_name="claude-research")
        assert "      # Pane 2 (right): nvim — 가장 최근 편집 파일 자동 열기\n" in text.split("window_name: docker")[1]

    def test_render_config_marks_focus_only_in_multi_pane_windows(self):
        """render_config writes focus: true for the active pane of a regenerated multi-pane window."""
        live = [_window("w", "/x", _pane(_CLAUDE), _pane(_NVIM, focus=True))]
        text, _ = st.render_config(None, live, session_name="s")
        assert text.count("focus: true") == 1 and text.index("focus: true") > text.index("nvim")

    def test_render_config_without_existing_file_writes_default_header(self):
        """render_config writes a minimal tmuxp header when there is no config yet."""
        text, _ = st.render_config(None, [_window("w", "/x", _pane())], session_name="claude-research")
        assert "session_name: claude-research\n" in text and "\nwindows:\n" in text

    def test_render_config_reports_window_status(self):
        """render_config reports which windows were kept, changed, added and removed."""
        live = _sample_live()[:2] + [_window("zsh", "/Users/me", _pane())]
        live[1] = _window("docker", "/Users/me/docker", _pane("htop"))
        _, report = st.render_config(_SAMPLE, live, session_name="claude-research")
        assert (report.status, report.removed) == ({"research": "kept", "docker": "changed", "zsh": "new"}, ["job"])

    def test_render_config_with_layout_differing_only_in_pane_ids_keeps_block(self):
        """render_config compares custom layouts by geometry, not by the pane IDs tmux embeds."""
        existing = (
            "session_name: s\nwindows:\n  - window_name: w\n    start_directory: /x\n"
            "    layout: a1b2,136x33,0,0{100x33,0,0,1,35x33,101,0,2}\n    panes:\n      - blank\n      - blank\n"
        )
        live = [_window("w", "/x", _pane(), _pane(), layout="c3d4,136x33,0,0{100x33,0,0,7,35x33,101,0,8}")]
        _, report = st.render_config(existing, live, session_name="s")
        assert report.status == {"w": "kept"}

    def test_render_config_writes_pane_start_directory_when_it_differs(self):
        """render_config adds a pane-level start_directory only when the pane left the window's directory."""
        live = [_window("w", "/x", _pane(_CLAUDE), _pane(start_directory="/tmp"))]
        text, _ = st.render_config(None, live, session_name="s")
        assert text.count("start_directory: /tmp") == 1


# ── Capture ──────────────────────────────────────────────────────


class FakeTmux:
    """Stand-in for _run_tmux answering list-windows and list-panes."""

    def __call__(self, *args: str) -> str:
        """Answer like tmux would for a two-window session."""
        if args[0] == "list-windows":
            return f"@1\tresearch\t{_JSON_EVEN_H}\n@2\tjob\t{_JSON_SINGLE}\n"
        if args[args.index("-t") + 1] == "@1":
            return "100\t/dev/ttys001\t/r\t1\n200\t/dev/ttys002\t/r\t0\n"
        return "300\t/dev/ttys003\t/j\t1\n"


class TestCaptureSession:
    """Reading a live session through tmux."""

    def test_capture_session_builds_windows_from_tmux_and_processes(self):
        """capture_session combines tmux geometry with each pane's foreground command."""
        argv = {100: ["claude", "--dangerously-skip-permissions", "--rc", "research"], 200: ["nvim", "-c", "'0"]}
        with (
            patch.object(st, "_run_tmux", FakeTmux()),
            patch.object(st, "foreground_pid", side_effect=lambda tty, pid: pid if pid in argv else None),
            patch.object(st, "read_argv", side_effect=lambda pid: argv.get(pid, ["-zsh"])),
        ):
            windows = st.capture_session("s")
        assert windows == [
            _window("research", "/r", _pane(_CLAUDE, focus=True), _pane(_NVIM)),
            _window("job", "/j", _pane(focus=True)),
        ]

    def test_capture_session_with_pane_started_as_command_captures_it(self):
        """capture_session records a pane whose own process is a program, not a shell."""
        with (
            patch.object(st, "_run_tmux", FakeTmux()),
            patch.object(st, "foreground_pid", return_value=None),
            patch.object(st, "read_argv", side_effect=lambda pid: ["sleep", "1000"] if pid == 300 else ["zsh"]),
        ):
            windows = st.capture_session("s")
        assert windows[1].panes[0].commands == ["sleep 1000"]


# ── Writing ──────────────────────────────────────────────────────


class TestWriteConfig:
    """Writing through a symlinked config with a backup."""

    def test_write_config_through_symlink_keeps_the_link(self, tmp_path: Path):
        """write_config replaces the link's target and leaves the link in place."""
        target = tmp_path / "real" / "tmux_init.yaml"
        target.parent.mkdir()
        target.write_text("old\n")
        link = tmp_path / "tmux_init.yaml"
        link.symlink_to(target)
        st.write_config(link, "new\n", backup_dir=tmp_path / "backups")
        assert (link.is_symlink(), target.read_text()) == (True, "new\n")

    def test_write_config_backs_up_previous_content(self, tmp_path: Path):
        """write_config copies the old file into the backup directory first."""
        config = tmp_path / "tmux_init.yaml"
        config.write_text("old\n")
        backup = st.write_config(config, "new\n", backup_dir=tmp_path / "backups")
        assert backup is not None and backup.read_text() == "old\n"

    def test_write_config_prunes_old_backups(self, tmp_path: Path):
        """write_config keeps only the newest backups."""
        backups = tmp_path / "backups"
        backups.mkdir()
        for i in range(st._BACKUP_KEEP + 3):
            (backups / f"tmux_init.yaml.20260101-0000{i:02d}").write_text("x")
        config = tmp_path / "tmux_init.yaml"
        config.write_text("old\n")
        st.write_config(config, "new\n", backup_dir=backups)
        assert len(list(backups.iterdir())) == st._BACKUP_KEEP


# ── tmuxp validation ─────────────────────────────────────────────


@pytest.mark.skipif(shutil.which("tmuxp") is None, reason="tmuxp not installed")
class TestValidateWithTmuxp:
    """Schema check through tmuxp's own interpreter."""

    def test_validate_with_tmuxp_accepts_rendered_config(self):
        """validate_with_tmuxp passes a config rendered by this script."""
        text, _ = st.render_config(_SAMPLE, [*_sample_live(), _window("zsh", "/tmp", _pane())], session_name="s")
        assert st.validate_with_tmuxp(text, cwd=Path(os.getcwd())) == (True, "ok")

    def test_validate_with_tmuxp_rejects_config_without_windows(self):
        """validate_with_tmuxp reports a schema error."""
        ok, _ = st.validate_with_tmuxp("session_name: s\n", cwd=Path(os.getcwd()))
        assert ok is False
