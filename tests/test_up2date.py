"""Tests for the up2date skill script."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Make the skill scripts directory importable.
_SCRIPTS_DIR = str(
    Path(__file__).resolve().parent.parent
    / "plugins"
    / "lazy2work"
    / "skills"
    / "up2date"
    / "scripts"
)
sys.path.insert(0, _SCRIPTS_DIR)

import up2date  # noqa: E402


# ── Fixtures ─────────────────────────────────────────────────────


@pytest.fixture()
def mock_run():
    """Patch up2date.run to avoid real subprocess calls."""
    with patch.object(up2date, "run") as m:
        m.return_value = subprocess.CompletedProcess(
            [], returncode=0, stdout="", stderr=""
        )
        yield m


@pytest.fixture()
def tmp_plugins(tmp_path):
    """Create a temporary plugin directory structure."""
    plugins_dir = tmp_path / "plugins"
    cache_dir = plugins_dir / "cache"
    mkt_dir = plugins_dir / "marketplaces"
    plugins_dir.mkdir()
    cache_dir.mkdir()
    mkt_dir.mkdir()
    return {
        "plugins_dir": plugins_dir,
        "cache_dir": cache_dir,
        "mkt_dir": mkt_dir,
        "root": tmp_path,
    }


@pytest.fixture()
def installed_plugins_file(tmp_path):
    """Create a temporary installed_plugins.json."""
    f = tmp_path / "installed_plugins.json"
    data = {
        "version": 2,
        "plugins": {
            "lazy2work@hoosiki-marketplace": [
                {
                    "scope": "user",
                    "installPath": "/tmp/cache/hoosiki-marketplace/lazy2work/1.0.0",
                    "version": "1.0.0",
                    "installedAt": "2026-03-14T08:00:00Z",
                    "lastUpdated": "2026-03-14T08:00:00Z",
                    "gitCommitSha": "abc1234567890",
                }
            ]
        },
    }
    f.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return f


# ── run() ────────────────────────────────────────────────────────


class TestRun:
    """Tests for the run() subprocess wrapper."""

    def test_run_captures_stdout(self) -> None:
        """run returns captured stdout from the command."""
        result = up2date.run(["echo", "hello"])
        assert result.stdout.strip() == "hello"
        assert result.returncode == 0

    def test_run_returns_nonzero_on_failure(self) -> None:
        """run returns non-zero returncode on command failure."""
        result = up2date.run(["false"])
        assert result.returncode != 0

    def test_run_returns_synthetic_result_on_timeout(self) -> None:
        """run returns returncode=1 and stderr='timeout' on timeout."""
        result = up2date.run(["sleep", "10"], timeout=1)
        assert result.returncode == 1
        assert result.stderr == "timeout"

    def test_run_respects_cwd(self, tmp_path: Path) -> None:
        """run executes command in the specified working directory."""
        result = up2date.run(["pwd"], cwd=str(tmp_path))
        assert result.stdout.strip() == str(tmp_path)


# ── print_section() ──────────────────────────────────────────────


class TestPrintSection:
    """Tests for print_section()."""

    def test_print_section_contains_title(self, capsys: pytest.CaptureFixture[str]) -> None:
        """print_section output contains the title text."""
        up2date.print_section("My Title")
        captured = capsys.readouterr()
        assert "My Title" in captured.out

    def test_print_section_has_separator_lines(self, capsys: pytest.CaptureFixture[str]) -> None:
        """print_section output contains separator lines."""
        up2date.print_section("Test")
        captured = capsys.readouterr()
        assert "=" * 60 in captured.out


# ── get_installed() ──────────────────────────────────────────────


class TestGetInstalled:
    """Tests for get_installed()."""

    def test_returns_empty_list_on_failure(self, mock_run: MagicMock) -> None:
        """get_installed returns empty list when brew command fails."""
        mock_run.return_value = subprocess.CompletedProcess(
            [], returncode=1, stdout="", stderr=""
        )
        result = up2date.get_installed("formula")
        assert result == []

    def test_parses_formula_list(self, mock_run: MagicMock) -> None:
        """get_installed parses newline-separated package names."""
        mock_run.return_value = subprocess.CompletedProcess(
            [], returncode=0, stdout="git\npython@3.12\nnode\n", stderr=""
        )
        result = up2date.get_installed("formula")
        assert result == ["git", "python@3.12", "node"]

    def test_skips_empty_lines(self, mock_run: MagicMock) -> None:
        """get_installed skips blank lines in output."""
        mock_run.return_value = subprocess.CompletedProcess(
            [], returncode=0, stdout="git\n\n\nnode\n", stderr=""
        )
        result = up2date.get_installed("formula")
        assert result == ["git", "node"]


# ── get_outdated() ───────────────────────────────────────────────


class TestGetOutdated:
    """Tests for get_outdated()."""

    def test_returns_empty_on_no_outdated(self, mock_run: MagicMock) -> None:
        """get_outdated returns empty list when nothing is outdated."""
        mock_run.return_value = subprocess.CompletedProcess(
            [], returncode=0, stdout="", stderr=""
        )
        result = up2date.get_outdated("formula")
        assert result == []

    def test_parses_outdated_output(self, mock_run: MagicMock) -> None:
        """get_outdated parses package name from verbose output."""
        mock_run.return_value = subprocess.CompletedProcess(
            [],
            returncode=0,
            stdout="node (22.1.0) < 22.2.0\npython@3.12 (3.12.3) < 3.12.4\n",
            stderr="",
        )
        result = up2date.get_outdated("formula")
        assert len(result) == 2
        assert result[0]["name"] == "node"
        assert result[1]["name"] == "python@3.12"

    def test_cask_uses_greedy_flag(self, mock_run: MagicMock) -> None:
        """get_outdated passes --greedy flag for cask kind."""
        mock_run.return_value = subprocess.CompletedProcess(
            [], returncode=0, stdout="", stderr=""
        )
        up2date.get_outdated("cask")
        cmd = mock_run.call_args[0][0]
        assert "--greedy" in cmd
        assert "--cask" in cmd

    def test_formula_does_not_use_greedy(self, mock_run: MagicMock) -> None:
        """get_outdated does not pass --greedy for formula kind."""
        mock_run.return_value = subprocess.CompletedProcess(
            [], returncode=0, stdout="", stderr=""
        )
        up2date.get_outdated("formula")
        cmd = mock_run.call_args[0][0]
        assert "--greedy" not in cmd


# ── _read_installed_plugins() ────────────────────────────────────


class TestReadInstalledPlugins:
    """Tests for _read_installed_plugins()."""

    def test_returns_empty_structure_when_file_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """_read_installed_plugins returns empty plugins on missing file."""
        monkeypatch.setattr(up2date, "INSTALLED_PLUGINS_FILE", Path("/nonexistent/file.json"))
        result = up2date._read_installed_plugins()
        assert result == {"version": 2, "plugins": {}}

    def test_reads_valid_json(self, installed_plugins_file: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """_read_installed_plugins correctly parses valid JSON."""
        monkeypatch.setattr(up2date, "INSTALLED_PLUGINS_FILE", installed_plugins_file)
        result = up2date._read_installed_plugins()
        assert "lazy2work@hoosiki-marketplace" in result["plugins"]

    def test_returns_empty_structure_on_invalid_json(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """_read_installed_plugins returns empty plugins on malformed JSON."""
        bad_file = tmp_path / "installed_plugins.json"
        bad_file.write_text("{invalid json", encoding="utf-8")
        monkeypatch.setattr(up2date, "INSTALLED_PLUGINS_FILE", bad_file)
        result = up2date._read_installed_plugins()
        assert result == {"version": 2, "plugins": {}}


# ── _is_skill_registered() ──────────────────────────────────────


class TestIsSkillRegistered:
    """Tests for _is_skill_registered()."""

    def test_returns_false_when_settings_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """_is_skill_registered returns False when settings.json is missing."""
        monkeypatch.setattr(up2date, "SETTINGS_FILE", Path("/nonexistent/settings.json"))
        assert up2date._is_skill_registered("my-skill") is False

    def test_returns_true_when_skill_in_allow_list(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """_is_skill_registered returns True when skill is in permissions.allow."""
        settings = tmp_path / "settings.json"
        settings.write_text(
            json.dumps({"permissions": {"allow": ["Skill(my-skill)"]}}),
            encoding="utf-8",
        )
        monkeypatch.setattr(up2date, "SETTINGS_FILE", settings)
        assert up2date._is_skill_registered("my-skill") is True

    def test_returns_false_when_skill_not_in_list(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """_is_skill_registered returns False when skill is not in allow list."""
        settings = tmp_path / "settings.json"
        settings.write_text(
            json.dumps({"permissions": {"allow": ["Skill(other-skill)"]}}),
            encoding="utf-8",
        )
        monkeypatch.setattr(up2date, "SETTINGS_FILE", settings)
        assert up2date._is_skill_registered("my-skill") is False


# ── _human_bytes() ──────────────────────────────────────────────


class TestHumanBytes:
    """Tests for _human_bytes()."""

    def test_zero(self) -> None:
        """_human_bytes renders zero without a decimal."""
        assert up2date._human_bytes(0) == "0 B"

    def test_kilobytes(self) -> None:
        """_human_bytes steps up to KB past 1024."""
        assert up2date._human_bytes(1536) == "1.5 KB"

    def test_gigabytes_do_not_overflow_to_a_larger_unit(self) -> None:
        """GB is the top unit — a huge value stays in GB rather than wrapping."""
        assert up2date._human_bytes(10 * 1024**3) == "10.0 GB"
        assert up2date._human_bytes(4096 * 1024**3).endswith("GB")


# ── brew_cleanup_caskroom() ─────────────────────────────────────


class TestBrewCleanupCaskroom:
    """Tests for brew_cleanup_caskroom()."""

    def test_returns_zero_when_prefix_lookup_fails(self, mock_run: MagicMock) -> None:
        """A failed `brew --prefix` yields no deletions rather than an exception."""
        mock_run.return_value = subprocess.CompletedProcess([], returncode=1, stdout="", stderr="")
        assert up2date.brew_cleanup_caskroom() == (0, 0)

    def test_returns_zero_when_caskroom_absent(
        self, tmp_path: Path, mock_run: MagicMock
    ) -> None:
        """A prefix without a Caskroom directory is a no-op."""
        mock_run.return_value = subprocess.CompletedProcess(
            [], returncode=0, stdout=str(tmp_path), stderr=""
        )
        assert up2date.brew_cleanup_caskroom() == (0, 0)

    def test_removes_pkg_and_reports_bytes(self, tmp_path: Path, mock_run: MagicMock) -> None:
        """Leftover .pkg files are deleted and their combined size reported."""
        pkg_dir = tmp_path / "Caskroom" / "mactex" / "2026.0324"
        pkg_dir.mkdir(parents=True)
        pkg = pkg_dir / "mactex.pkg"
        pkg.write_bytes(b"x" * 2048)
        mock_run.return_value = subprocess.CompletedProcess(
            [], returncode=0, stdout=str(tmp_path), stderr=""
        )

        assert up2date.brew_cleanup_caskroom() == (1, 2048)
        assert not pkg.exists()

    def test_leaves_non_pkg_files_alone(self, tmp_path: Path, mock_run: MagicMock) -> None:
        """Only *.pkg is removed — app bundles and metadata survive."""
        cask = tmp_path / "Caskroom" / "obsidian" / "1.0"
        cask.mkdir(parents=True)
        keep = cask / "Obsidian.app"
        keep.mkdir()
        receipt = cask / "INSTALL_RECEIPT.json"
        receipt.write_text("{}")
        mock_run.return_value = subprocess.CompletedProcess(
            [], returncode=0, stdout=str(tmp_path), stderr=""
        )

        assert up2date.brew_cleanup_caskroom() == (0, 0)
        assert keep.exists()
        assert receipt.exists()


# ── _claude_cli_available() ─────────────────────────────────────


class TestClaudeCliAvailable:
    """Tests for _claude_cli_available()."""

    def test_true_when_claude_on_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """_claude_cli_available is True when shutil.which resolves claude."""
        monkeypatch.setattr(up2date.shutil, "which", lambda _: "/usr/local/bin/claude")
        assert up2date._claude_cli_available() is True

    def test_false_when_claude_absent(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """_claude_cli_available is False when claude is not installed."""
        monkeypatch.setattr(up2date.shutil, "which", lambda _: None)
        assert up2date._claude_cli_available() is False


# ── update_marketplace() ────────────────────────────────────────


class TestUpdateMarketplace:
    """Tests for update_marketplace()."""

    def test_reports_missing_cli(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """update_marketplace refuses to guess when claude is absent."""
        monkeypatch.setattr(up2date, "_claude_cli_available", lambda: False)
        assert up2date.update_marketplace("mkt") == (
            "claude CLI not found — cannot update marketplaces"
        )

    def test_returns_updated_on_success(
        self, monkeypatch: pytest.MonkeyPatch, mock_run: MagicMock
    ) -> None:
        """update_marketplace returns success message on exit 0."""
        monkeypatch.setattr(up2date, "_claude_cli_available", lambda: True)
        mock_run.return_value = subprocess.CompletedProcess(
            [], returncode=0, stdout="Updated marketplace mkt", stderr=""
        )
        assert up2date.update_marketplace("mkt").startswith("Updated:")

    def test_invokes_official_cli(
        self, monkeypatch: pytest.MonkeyPatch, mock_run: MagicMock
    ) -> None:
        """update_marketplace shells out to `claude plugin marketplace update`."""
        monkeypatch.setattr(up2date, "_claude_cli_available", lambda: True)
        mock_run.return_value = subprocess.CompletedProcess([], returncode=0, stdout="", stderr="")
        up2date.update_marketplace("mkt")
        assert mock_run.call_args[0][0] == [
            "claude",
            "plugin",
            "marketplace",
            "update",
            "mkt",
        ]

    def test_returns_failed_on_error(
        self, monkeypatch: pytest.MonkeyPatch, mock_run: MagicMock
    ) -> None:
        """update_marketplace surfaces stderr on a non-zero exit."""
        monkeypatch.setattr(up2date, "_claude_cli_available", lambda: True)
        mock_run.return_value = subprocess.CompletedProcess(
            [], returncode=1, stdout="", stderr="unknown marketplace"
        )
        assert up2date.update_marketplace("mkt").startswith("Update failed:")


# ── update_plugin() ─────────────────────────────────────────────


class TestUpdatePlugin:
    """Tests for update_plugin()."""

    def test_reports_missing_cli(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """update_plugin refuses to guess when claude is absent."""
        monkeypatch.setattr(up2date, "_claude_cli_available", lambda: False)
        assert up2date.update_plugin("p@mkt") == "claude CLI not found — cannot update plugins"

    def test_defaults_to_user_scope_and_passes_yes(
        self, monkeypatch: pytest.MonkeyPatch, mock_run: MagicMock
    ) -> None:
        """update_plugin targets user scope and always passes --yes.

        --yes is required whenever stdin/stdout is not a TTY, which is always
        true for this script.
        """
        monkeypatch.setattr(up2date, "_claude_cli_available", lambda: True)
        mock_run.return_value = subprocess.CompletedProcess([], returncode=0, stdout="", stderr="")
        up2date.update_plugin("p@mkt")
        assert mock_run.call_args[0][0] == [
            "claude",
            "plugin",
            "update",
            "p@mkt",
            "--scope",
            "user",
            "--yes",
        ]

    def test_honors_explicit_scope(
        self, monkeypatch: pytest.MonkeyPatch, mock_run: MagicMock
    ) -> None:
        """update_plugin forwards a non-default scope."""
        monkeypatch.setattr(up2date, "_claude_cli_available", lambda: True)
        mock_run.return_value = subprocess.CompletedProcess([], returncode=0, stdout="", stderr="")
        up2date.update_plugin("p@mkt", "project")
        assert "project" in mock_run.call_args[0][0]

    def test_returns_failed_on_error(
        self, monkeypatch: pytest.MonkeyPatch, mock_run: MagicMock
    ) -> None:
        """update_plugin surfaces stderr on a non-zero exit."""
        monkeypatch.setattr(up2date, "_claude_cli_available", lambda: True)
        mock_run.return_value = subprocess.CompletedProcess(
            [], returncode=1, stdout="", stderr="plugin not installed"
        )
        assert up2date.update_plugin("p@mkt").startswith("Update failed:")


# ── _print_skill_info() ─────────────────────────────────────────


class TestPrintSkillInfo:
    """Tests for _print_skill_info()."""

    def test_prints_basic_info(self, capsys: pytest.CaptureFixture[str]) -> None:
        """_print_skill_info prints name, path, and source."""
        sk = {
            "name": "test-skill",
            "path": "/tmp/test",
            "source": "user",
            "has_scripts": True,
            "has_references": False,
            "has_assets": False,
        }
        up2date._print_skill_info(sk)
        captured = capsys.readouterr()
        assert "test-skill" in captured.out
        assert "/tmp/test" in captured.out
        assert "scripts" in captured.out

    def test_prints_plugin_info_when_present(self, capsys: pytest.CaptureFixture[str]) -> None:
        """_print_skill_info prints plugin ID when available."""
        sk = {
            "name": "test-skill",
            "path": "/tmp/test",
            "source": "plugin",
            "plugin_id": "test@mkt",
            "plugin_version": "1.0.0",
            "has_scripts": False,
            "has_references": False,
            "has_assets": False,
        }
        up2date._print_skill_info(sk)
        captured = capsys.readouterr()
        assert "test@mkt" in captured.out

    def test_prints_symlink_target(self, capsys: pytest.CaptureFixture[str]) -> None:
        """_print_skill_info prints symlink target when present."""
        sk = {
            "name": "test-skill",
            "path": "/tmp/link",
            "source": "user",
            "symlink_target": "/real/path",
            "has_scripts": False,
            "has_references": False,
            "has_assets": False,
        }
        up2date._print_skill_info(sk)
        captured = capsys.readouterr()
        assert "/real/path" in captured.out


# ── check_superclaude() ─────────────────────────────────────────


class TestCheckSuperclaude:
    """Tests for check_superclaude()."""

    def test_returns_not_installed_when_dir_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """check_superclaude returns installed=False when sc dir is missing."""
        monkeypatch.setattr(up2date, "COMMANDS_DIR", Path("/nonexistent"))
        result = up2date.check_superclaude()
        assert result["installed"] is False
        assert result["commands"] == []
        assert result["total"] == 0

    def test_lists_commands_from_md_files(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """check_superclaude lists command names from .md files."""
        sc_dir = tmp_path / "sc"
        sc_dir.mkdir()
        (sc_dir / "analyze.md").write_text("# analyze", encoding="utf-8")
        (sc_dir / "build.md").write_text("# build", encoding="utf-8")
        (sc_dir / "README.md").write_text("# readme", encoding="utf-8")
        monkeypatch.setattr(up2date, "COMMANDS_DIR", tmp_path)
        result = up2date.check_superclaude()
        assert result["installed"] is True
        assert result["total"] == 3
        assert "analyze" in result["commands"]
        assert "build" in result["commands"]


# ── SuperClaude package upgrade ─────────────────────────────────


def _cp(stdout: str = "", returncode: int = 0, stderr: str = "") -> subprocess.CompletedProcess[str]:
    """Build a CompletedProcess for a mocked run() call."""
    return subprocess.CompletedProcess([], returncode=returncode, stdout=stdout, stderr=stderr)


def _make_tool_install(root: Path, method: str, venv_name: str = "superclaude") -> Path:
    """Lay out a pipx/uv tool venv plus the bin-dir symlink pointing into it.

    Returns the symlink path, i.e. what ``shutil.which("superclaude")`` returns.
    """
    marker = {"pipx": "pipx_metadata.json", "uv": "uv-receipt.toml"}[method]
    venv = root / method / "venvs" / venv_name
    (venv / "bin").mkdir(parents=True)
    (venv / marker).write_text("{}", encoding="utf-8")
    target = venv / "bin" / "superclaude"
    target.write_text("#!" + str(venv / "bin" / "python") + "\n", encoding="utf-8")
    bin_dir = root / "local-bin"
    bin_dir.mkdir(exist_ok=True)
    link = bin_dir / "superclaude"
    link.symlink_to(target)
    return link


def _make_pip_install(root: Path, interpreter: str = "/opt/homebrew/opt/python@3.14/bin/python3.14") -> Path:
    """Create a pip-style console script whose shebang names its interpreter."""
    bin_dir = root / "pybin"
    bin_dir.mkdir(parents=True)
    script = bin_dir / "superclaude"
    script.write_text(f"#!{interpreter}\nimport sys\n", encoding="utf-8")
    return script


def _which(paths: dict[str, str]):
    """Return a shutil.which stand-in that only knows the given executables."""
    return lambda name: paths.get(name)


class TestParseSuperclaudeVersion:
    """Tests for _parse_superclaude_version()."""

    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("SuperClaude, version 4.2.0", "4.2.0"),
            ("SuperClaude version 4.3.0\n", "4.3.0"),
            ("SuperClaude, version 4.4.0rc1", "4.4.0rc1"),
            ("command not found", ""),
            ("", ""),
        ],
        ids=["click-version-option", "version-subcommand", "pre-release", "no-version", "empty"],
    )
    def test_extracts_version(self, text: str, expected: str) -> None:
        """_parse_superclaude_version pulls the version out of CLI output."""
        assert up2date._parse_superclaude_version(text) == expected


class TestDetectSuperclaudeInstall:
    """Tests for _detect_superclaude_install()."""

    def test_detects_pipx_venv_through_symlink(self, tmp_path: Path) -> None:
        """A bin-dir symlink into a venv carrying pipx_metadata.json is pipx."""
        link = _make_tool_install(tmp_path, "pipx")
        result = up2date._detect_superclaude_install(str(link))
        assert (result["method"], result["package"]) == ("pipx", "superclaude")

    def test_detects_uv_tool_venv_through_symlink(self, tmp_path: Path) -> None:
        """A bin-dir symlink into a venv carrying uv-receipt.toml is uv tool."""
        link = _make_tool_install(tmp_path, "uv")
        result = up2date._detect_superclaude_install(str(link))
        assert (result["method"], result["package"]) == ("uv", "superclaude")

    def test_package_is_venv_name_so_pipx_suffix_survives(self, tmp_path: Path) -> None:
        """The upgrade target is the venv name, which carries a pipx --suffix."""
        link = _make_tool_install(tmp_path, "pipx", venv_name="superclaude_beta")
        assert up2date._detect_superclaude_install(str(link))["package"] == "superclaude_beta"

    def test_plain_script_is_pip_with_shebang_interpreter(self, tmp_path: Path) -> None:
        """A console script outside any tool venv is pip, owned by its shebang's Python."""
        script = _make_pip_install(tmp_path)
        result = up2date._detect_superclaude_install(str(script))
        assert result == {
            "method": "pip",
            "package": "superclaude",
            "location": "/opt/homebrew/opt/python@3.14/bin/python3.14",
        }

    def test_env_shebang_yields_the_named_python(self, tmp_path: Path) -> None:
        """`#!/usr/bin/env python3` resolves to `python3`, not to `env`."""
        script = _make_pip_install(tmp_path, interpreter="/usr/bin/env python3")
        assert up2date._detect_superclaude_install(str(script))["location"] == "python3"


class TestUpdateSuperclaude:
    """Tests for update_superclaude() — upgrade the package, then re-install."""

    def test_skips_when_cli_absent(self, monkeypatch: pytest.MonkeyPatch, mock_run: MagicMock) -> None:
        """No superclaude on PATH: nothing runs and the result says why."""
        monkeypatch.setattr(up2date.shutil, "which", _which({}))
        result = up2date.update_superclaude()
        assert result["available"] is False
        assert "not found" in result["error"]
        mock_run.assert_not_called()

    def test_pipx_upgrades_then_reinstalls(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mock_run: MagicMock
    ) -> None:
        """pipx install: `pipx upgrade superclaude` runs before `superclaude update`."""
        link = _make_tool_install(tmp_path, "pipx")
        monkeypatch.setattr(up2date.shutil, "which", _which({"superclaude": str(link), "pipx": "/x/pipx"}))
        mock_run.side_effect = [
            _cp("SuperClaude, version 4.2.0"),
            _cp("upgraded package superclaude from 4.2.0 to 4.3.0"),
            _cp("SuperClaude, version 4.3.0"),
            _cp("✅ Installed 31 commands"),
        ]

        result = up2date.update_superclaude()

        cmds = [c.args[0] for c in mock_run.call_args_list]
        assert cmds[1] == ["pipx", "upgrade", "superclaude"]
        assert cmds[3] == [str(link), "update"]
        assert (result["before"], result["after"]) == ("4.2.0", "4.3.0")
        assert result["reinstalled"] is True

    def test_pipx_upgrade_uses_tool_upgrade_timeout(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mock_run: MagicMock
    ) -> None:
        """The network-bound upgrade gets the long timeout, like brew and npx."""
        link = _make_tool_install(tmp_path, "pipx")
        monkeypatch.setattr(up2date.shutil, "which", _which({"superclaude": str(link), "pipx": "/x/pipx"}))
        mock_run.side_effect = [_cp("4.2.0"), _cp(), _cp("4.3.0"), _cp()]
        up2date.update_superclaude()
        assert mock_run.call_args_list[1].kwargs["timeout"] == up2date._TOOL_UPGRADE_TIMEOUT

    def test_uv_tool_upgrades_then_reinstalls(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mock_run: MagicMock
    ) -> None:
        """uv tool install: `uv tool upgrade superclaude` runs before the re-install."""
        link = _make_tool_install(tmp_path, "uv")
        monkeypatch.setattr(up2date.shutil, "which", _which({"superclaude": str(link), "uv": "/x/uv"}))
        mock_run.side_effect = [
            _cp("SuperClaude, version 4.2.0"),
            _cp("Updated superclaude v4.2.0 -> v4.3.0"),
            _cp("SuperClaude, version 4.3.0"),
            _cp("✅ Installed 31 commands"),
        ]

        result = up2date.update_superclaude()

        cmds = [c.args[0] for c in mock_run.call_args_list]
        assert cmds[1] == ["uv", "tool", "upgrade", "superclaude"]
        assert cmds[3] == [str(link), "update"]
        assert (result["method"], result["after"]) == ("uv", "4.3.0")

    def test_already_current_still_reinstalls(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mock_run: MagicMock
    ) -> None:
        """An upgrade that finds nothing newer still re-installs the commands."""
        link = _make_tool_install(tmp_path, "pipx")
        monkeypatch.setattr(up2date.shutil, "which", _which({"superclaude": str(link), "pipx": "/x/pipx"}))
        mock_run.side_effect = [
            _cp("SuperClaude, version 4.3.0"),
            _cp("superclaude is already at latest version 4.3.0"),
            _cp("SuperClaude, version 4.3.0"),
            _cp("✅ Installed 31 commands"),
        ]

        result = up2date.update_superclaude()

        assert (result["before"], result["after"], result["reinstalled"]) == ("4.3.0", "4.3.0", True)

    def test_pip_install_prints_hint_and_never_runs_pip(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mock_run: MagicMock
    ) -> None:
        """A pip install is not upgraded automatically (PEP 668) — only a hint."""
        script = _make_pip_install(tmp_path)
        monkeypatch.setattr(up2date.shutil, "which", _which({"superclaude": str(script)}))
        mock_run.side_effect = [_cp("SuperClaude, version 4.2.0"), _cp("✅ Installed 31 commands")]

        result = up2date.update_superclaude()

        cmds = [c.args[0] for c in mock_run.call_args_list]
        assert cmds == [[str(script), "--version"], [str(script), "update"]]
        assert result["upgrade"] == "manual"
        assert "python3.14 -m pip install --upgrade superclaude" in result["hint"]
        assert result["after"] == "4.2.0"

    def test_missing_manager_falls_back_to_hint(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mock_run: MagicMock
    ) -> None:
        """A pipx venv with no pipx on PATH gets a hint instead of a crash."""
        link = _make_tool_install(tmp_path, "pipx")
        monkeypatch.setattr(up2date.shutil, "which", _which({"superclaude": str(link)}))
        mock_run.side_effect = [_cp("SuperClaude, version 4.2.0"), _cp("ok")]

        result = up2date.update_superclaude()

        assert result["upgrade"] == "manual"
        assert "pipx upgrade superclaude" in result["hint"]
        assert mock_run.call_count == 2

    def test_upgrade_failure_skips_reinstall(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mock_run: MagicMock
    ) -> None:
        """A failed upgrade is reported and the commands are left untouched."""
        link = _make_tool_install(tmp_path, "pipx")
        monkeypatch.setattr(up2date.shutil, "which", _which({"superclaude": str(link), "pipx": "/x/pipx"}))
        mock_run.side_effect = [
            _cp("SuperClaude, version 4.2.0"),
            _cp(returncode=1, stderr="Could not find a version that satisfies superclaude"),
        ]

        result = up2date.update_superclaude()

        assert result["upgrade"] == "failed"
        assert "Could not find a version" in result["error"]
        assert result["reinstalled"] is False
        assert (result["before"], result["after"]) == ("4.2.0", "4.2.0")
        assert mock_run.call_count == 2

    def test_reinstall_failure_is_reported(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mock_run: MagicMock
    ) -> None:
        """A non-zero `superclaude update` surfaces as an error, not success."""
        link = _make_tool_install(tmp_path, "uv")
        monkeypatch.setattr(up2date.shutil, "which", _which({"superclaude": str(link), "uv": "/x/uv"}))
        mock_run.side_effect = [_cp("4.3.0"), _cp(), _cp("4.3.0"), _cp(returncode=1, stderr="boom")]

        result = up2date.update_superclaude()

        assert result["reinstalled"] is False
        assert "boom" in result["error"]


class TestPrintSuperclaudeUpdate:
    """Tests for _print_superclaude_update()."""

    def _result(self, **overrides: object) -> dict[str, object]:
        """Return a successful pipx result, with any field overridden."""
        base: dict[str, object] = {
            "available": True,
            "method": "pipx",
            "package": "superclaude",
            "location": "/x/venvs/superclaude",
            "before": "4.2.0",
            "after": "4.3.0",
            "upgrade": "ok",
            "upgrade_output": "upgraded package superclaude from 4.2.0 to 4.3.0",
            "hint": "",
            "reinstalled": True,
            "output": "✅ Installed 31 commands",
            "error": "",
        }
        base.update(overrides)
        return base

    def test_summary_shows_before_and_after(self, capsys: pytest.CaptureFixture[str]) -> None:
        """The summary reports the version change as `before → after`."""
        up2date._print_superclaude_update(self._result())
        out = capsys.readouterr().out
        assert "SuperClaude Summary" in out
        assert "4.2.0 → 4.3.0 (upgraded)" in out

    def test_summary_marks_unchanged_version_current(self, capsys: pytest.CaptureFixture[str]) -> None:
        """No version change after a clean upgrade reads as already current."""
        up2date._print_superclaude_update(self._result(before="4.3.0", after="4.3.0"))
        assert "4.3.0 (already current)" in capsys.readouterr().out

    def test_skip_notice_when_cli_absent(self, capsys: pytest.CaptureFixture[str]) -> None:
        """An unavailable CLI prints a skip notice and no summary."""
        up2date._print_superclaude_update(
            {"available": False, "error": "superclaude CLI not found on PATH"}
        )
        out = capsys.readouterr().out
        assert "Skipped: superclaude CLI not found on PATH" in out
        assert "SuperClaude Summary" not in out

    def test_failed_upgrade_says_commands_untouched(self, capsys: pytest.CaptureFixture[str]) -> None:
        """A failed upgrade is labelled and the re-install is reported as skipped."""
        up2date._print_superclaude_update(
            self._result(upgrade="failed", after="4.2.0", reinstalled=False, error="pipx upgrade failed")
        )
        out = capsys.readouterr().out
        assert "4.2.0 → 4.2.0 (upgrade failed)" in out
        assert "not re-installed" in out

    def test_manual_hint_is_printed(self, capsys: pytest.CaptureFixture[str]) -> None:
        """A pip install's manual-upgrade hint reaches the output."""
        hint = "python3 -m pip install --upgrade superclaude"
        up2date._print_superclaude_update(
            self._result(method="pip", upgrade="manual", hint=hint, after="4.2.0")
        )
        out = capsys.readouterr().out
        assert hint in out
        assert "4.2.0 (not upgraded" in out


# ── Global agent skills (npx skills) ─────────────────────────────


class TestStripAnsi:
    """Tests for _strip_ansi."""

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("\x1b[38;5;145mhello\x1b[0m", "hello"),
            ("\x1b[1mUpdated\x1b[0m 3 skill(s)", "Updated 3 skill(s)"),
            ("plain text", "plain text"),
            ("", ""),
        ],
        ids=["colored", "bold-mixed", "plain", "empty"],
    )
    def test_removes_ansi_codes(self, raw: str, expected: str) -> None:
        """_strip_ansi removes ANSI escape sequences."""
        assert up2date._strip_ansi(raw) == expected


class TestParseDeadSkills:
    """Tests for _parse_dead_skills."""

    def test_single_source_extracts_bullets(self) -> None:
        """_parse_dead_skills extracts skill names from one source block."""
        output = (
            "Checking skills from source: mattpocock/skills\n"
            "Warning: The following skills from mattpocock/skills "
            "appear to have been deleted upstream:\n"
            "  • write-a-skill\n"
            "  • zoom-out\n"
            "Skipping deletion in non-interactive mode.\n"
            "✓ Updated 3 skill(s)\n"
        )
        assert up2date._parse_dead_skills(output) == ["write-a-skill", "zoom-out"]

    def test_multiple_source_blocks_merge_and_dedupe(self) -> None:
        """_parse_dead_skills merges bullets across blocks and dedupes."""
        output = (
            "appear to have been deleted upstream:\n"
            "  • alpha\n"
            "  • beta\n"
            "Skipping deletion in non-interactive mode.\n"
            "Checking skills from source: other/repo\n"
            "appear to have been deleted upstream:\n"
            "  • beta\n"
            "  • gamma\n"
            "done\n"
        )
        assert up2date._parse_dead_skills(output) == ["alpha", "beta", "gamma"]

    def test_ignores_non_deleted_bullets(self) -> None:
        """_parse_dead_skills ignores bullets under other warnings."""
        output = (
            "5 project skill(s) cannot be updated automatically:\n"
            "  • crawl\n"
            "    To refresh: npx skills add tavily-ai/skills -y\n"
        )
        assert up2date._parse_dead_skills(output) == []

    def test_no_dead_returns_empty(self) -> None:
        """_parse_dead_skills returns [] when no deletion warning is present."""
        assert up2date._parse_dead_skills("✓ Updated 3 skill(s)\n") == []


class TestParseUpdatedCount:
    """Tests for _parse_updated_count."""

    @pytest.mark.parametrize(
        ("output", "expected"),
        [
            ("✓ Updated 11 skill(s)", 11),
            ("Updated 1 skill(s)", 1),
            ("No project skills can be updated in place.", 0),
            ("", 0),
        ],
        ids=["eleven", "one", "none", "empty"],
    )
    def test_parses_count(self, output: str, expected: int) -> None:
        """_parse_updated_count extracts the updated skill count."""
        assert up2date._parse_updated_count(output) == expected


class TestUpdateGlobalSkills:
    """Tests for update_global_skills."""

    def test_returns_unavailable_when_npx_missing(self) -> None:
        """update_global_skills reports unavailable when npx is absent."""
        with patch.object(up2date.shutil, "which", return_value=None):
            result = up2date.update_global_skills()
        assert result["available"] is False
        assert result["updated"] == 0
        assert result["dead"] == []
        assert result["removed"] == []

    def test_parses_updated_and_dead(self) -> None:
        """update_global_skills parses updated count and dead skills."""
        update_out = subprocess.CompletedProcess(
            [], returncode=0,
            stdout=(
                "appear to have been deleted upstream:\n"
                "  • zoom-out\n"
                "Skipping deletion in non-interactive mode.\n"
                "✓ Updated 4 skill(s)\n"
            ),
            stderr="",
        )
        remove_out = subprocess.CompletedProcess([], returncode=0, stdout="ok", stderr="")
        with patch.object(up2date.shutil, "which", return_value="/usr/bin/npx"), \
                patch.object(up2date, "run", side_effect=[update_out, remove_out]) as mrun:
            result = up2date.update_global_skills(remove_dead=True)
        assert result["available"] is True
        assert result["updated"] == 4
        assert result["dead"] == ["zoom-out"]
        assert result["removed"] == ["zoom-out"]
        # Second call must be the remove command including the dead skill name.
        remove_call_args = mrun.call_args_list[1].args[0]
        assert "remove" in remove_call_args
        assert "zoom-out" in remove_call_args

    def test_skips_removal_when_disabled(self) -> None:
        """update_global_skills does not remove dead skills when remove_dead=False."""
        update_out = subprocess.CompletedProcess(
            [], returncode=0,
            stdout=(
                "appear to have been deleted upstream:\n"
                "  • zoom-out\n"
                "✓ Updated 0 skill(s)\n"
            ),
            stderr="",
        )
        with patch.object(up2date.shutil, "which", return_value="/usr/bin/npx"), \
                patch.object(up2date, "run", side_effect=[update_out]) as mrun:
            result = up2date.update_global_skills(remove_dead=False)
        assert result["dead"] == ["zoom-out"]
        assert result["removed"] == []
        assert mrun.call_count == 1  # only the update call, no remove

    def test_no_dead_skips_remove_call(self) -> None:
        """update_global_skills makes no remove call when there are no dead skills."""
        update_out = subprocess.CompletedProcess(
            [], returncode=0, stdout="✓ Updated 2 skill(s)\n", stderr=""
        )
        with patch.object(up2date.shutil, "which", return_value="/usr/bin/npx"), \
                patch.object(up2date, "run", side_effect=[update_out]) as mrun:
            result = up2date.update_global_skills(remove_dead=True)
        assert result["dead"] == []
        assert result["removed"] == []
        assert mrun.call_count == 1


# ── _plugin_skills_dir() / check_plugin_skills() ─────────────────


def _write_installed(path: Path, entries: dict) -> None:
    """Write an installed_plugins.json holding the given plugin entries."""
    path.write_text(json.dumps({"version": 2, "plugins": entries}), encoding="utf-8")


def _make_skill(skills_dir: Path, name: str, description: str = "A test skill") -> None:
    """Create a minimal skill directory with a SKILL.md carrying a description."""
    d = skills_dir / name
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {description}\n---\n", encoding="utf-8"
    )


class TestPluginSkillsDir:
    """Tests for _plugin_skills_dir()."""

    def test_returns_none_when_no_skills_dir(self, tmp_path: Path) -> None:
        """A plugin shipping no skills directory resolves to None."""
        assert up2date._plugin_skills_dir(tmp_path) is None

    def test_finds_plain_skills_dir(self, tmp_path: Path) -> None:
        """The common installPath/skills/ layout is found."""
        (tmp_path / "skills").mkdir()
        assert up2date._plugin_skills_dir(tmp_path) == tmp_path / "skills"

    def test_falls_back_to_dot_claude_layout(self, tmp_path: Path) -> None:
        """installPath/.claude/skills/ is found when skills/ is absent."""
        nested = tmp_path / ".claude" / "skills"
        nested.mkdir(parents=True)
        assert up2date._plugin_skills_dir(tmp_path) == nested

    def test_plain_layout_wins_over_dot_claude(self, tmp_path: Path) -> None:
        """When both layouts exist, skills/ takes priority."""
        (tmp_path / "skills").mkdir()
        (tmp_path / ".claude" / "skills").mkdir(parents=True)
        assert up2date._plugin_skills_dir(tmp_path) == tmp_path / "skills"

    def test_ignores_a_file_named_skills(self, tmp_path: Path) -> None:
        """A regular file named 'skills' is not mistaken for the directory."""
        (tmp_path / "skills").write_text("not a dir", encoding="utf-8")
        assert up2date._plugin_skills_dir(tmp_path) is None


class TestCheckPluginSkills:
    """Tests for check_plugin_skills()."""

    def test_empty_when_no_plugins(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """No installed plugins yields empty skills and skipped lists."""
        f = tmp_path / "installed_plugins.json"
        _write_installed(f, {})
        monkeypatch.setattr(up2date, "INSTALLED_PLUGINS_FILE", f)
        assert up2date.check_plugin_skills() == {"skills": [], "skipped": []}

    def test_collects_skills_from_plain_layout(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Skills under installPath/skills/ are collected with their metadata."""
        install = tmp_path / "cache" / "demo" / "1.0.0"
        _make_skill(install / "skills", "alpha", "Does alpha things")
        f = tmp_path / "installed_plugins.json"
        _write_installed(
            f,
            {"demo@mkt": [{"installPath": str(install), "version": "1.0.0"}]},
        )
        monkeypatch.setattr(up2date, "INSTALLED_PLUGINS_FILE", f)

        result = up2date.check_plugin_skills()

        assert result["skipped"] == []
        assert len(result["skills"]) == 1
        skill = result["skills"][0]
        assert skill["name"] == "alpha"
        assert skill["source"] == "plugin"
        assert skill["plugin_id"] == "demo@mkt"
        assert skill["plugin_version"] == "1.0.0"
        assert skill["description"] == "Does alpha things"

    def test_collects_skills_from_dot_claude_layout(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Skills nested under .claude/skills/ are no longer dropped."""
        install = tmp_path / "cache" / "nested" / "2.13.0"
        _make_skill(install / ".claude" / "skills", "design")
        _make_skill(install / ".claude" / "skills", "ui-styling")
        f = tmp_path / "installed_plugins.json"
        _write_installed(
            f,
            {"nested@mkt": [{"installPath": str(install), "version": "2.13.0"}]},
        )
        monkeypatch.setattr(up2date, "INSTALLED_PLUGINS_FILE", f)

        result = up2date.check_plugin_skills()

        assert result["skipped"] == []
        assert sorted(s["name"] for s in result["skills"]) == ["design", "ui-styling"]

    def test_reports_plugin_without_skills_as_skipped(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An install with neither layout is reported, not silently dropped."""
        install = tmp_path / "cache" / "bare" / "0.1.0"
        install.mkdir(parents=True)
        f = tmp_path / "installed_plugins.json"
        _write_installed(
            f,
            {"bare@mkt": [{"installPath": str(install), "version": "0.1.0"}]},
        )
        monkeypatch.setattr(up2date, "INSTALLED_PLUGINS_FILE", f)

        result = up2date.check_plugin_skills()

        assert result["skills"] == []
        assert result["skipped"] == [
            {
                "plugin_id": "bare@mkt",
                "version": "0.1.0",
                "install_path": str(install),
            }
        ]

    def test_skipped_version_defaults_to_unknown(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A skipped entry missing its version records 'unknown'."""
        install = tmp_path / "cache" / "bare" / "x"
        install.mkdir(parents=True)
        f = tmp_path / "installed_plugins.json"
        _write_installed(f, {"bare@mkt": [{"installPath": str(install)}]})
        monkeypatch.setattr(up2date, "INSTALLED_PLUGINS_FILE", f)

        assert up2date.check_plugin_skills()["skipped"][0]["version"] == "unknown"

    def test_mixed_layouts_are_all_counted(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Plain, nested, and skill-less plugins are each handled in one pass."""
        plain = tmp_path / "plain"
        _make_skill(plain / "skills", "one")
        nested = tmp_path / "nested"
        _make_skill(nested / ".claude" / "skills", "two")
        bare = tmp_path / "bare"
        bare.mkdir()
        f = tmp_path / "installed_plugins.json"
        _write_installed(
            f,
            {
                "plain@mkt": [{"installPath": str(plain), "version": "1.0.0"}],
                "nested@mkt": [{"installPath": str(nested), "version": "2.0.0"}],
                "bare@mkt": [{"installPath": str(bare), "version": "3.0.0"}],
            },
        )
        monkeypatch.setattr(up2date, "INSTALLED_PLUGINS_FILE", f)

        result = up2date.check_plugin_skills()

        assert sorted(s["name"] for s in result["skills"]) == ["one", "two"]
        assert [s["plugin_id"] for s in result["skipped"]] == ["bare@mkt"]

    def test_ignores_non_directory_entries(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Loose files inside a skills directory are not treated as skills."""
        install = tmp_path / "demo"
        skills = install / "skills"
        _make_skill(skills, "real")
        (skills / "README.md").write_text("not a skill", encoding="utf-8")
        f = tmp_path / "installed_plugins.json"
        _write_installed(
            f, {"demo@mkt": [{"installPath": str(install), "version": "1.0.0"}]}
        )
        monkeypatch.setattr(up2date, "INSTALLED_PLUGINS_FILE", f)

        result = up2date.check_plugin_skills()

        assert [s["name"] for s in result["skills"]] == ["real"]
