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


# ── _write_installed_plugins() ───────────────────────────────────


class TestWriteInstalledPlugins:
    """Tests for _write_installed_plugins()."""

    def test_writes_json_atomically(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """_write_installed_plugins creates valid JSON file."""
        target = tmp_path / "installed_plugins.json"
        monkeypatch.setattr(up2date, "INSTALLED_PLUGINS_FILE", target)
        data = {"version": 2, "plugins": {"test@mkt": []}}
        up2date._write_installed_plugins(data)
        written = json.loads(target.read_text(encoding="utf-8"))
        assert written == data

    def test_no_temp_file_left_on_success(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """_write_installed_plugins leaves no temp files after success."""
        target = tmp_path / "installed_plugins.json"
        monkeypatch.setattr(up2date, "INSTALLED_PLUGINS_FILE", target)
        up2date._write_installed_plugins({"version": 2, "plugins": {}})
        tmp_files = list(tmp_path.glob("*.tmp"))
        assert tmp_files == []


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


# ── _find_plugin_source() ───────────────────────────────────────


class TestFindPluginSource:
    """Tests for _find_plugin_source()."""

    def test_standard_layout(self, tmp_path: Path) -> None:
        """_find_plugin_source finds plugin under plugins/ directory."""
        (tmp_path / "plugins" / "my-plugin").mkdir(parents=True)
        result = up2date._find_plugin_source(tmp_path, "my-plugin")
        assert result == tmp_path / "plugins" / "my-plugin"

    def test_flat_layout(self, tmp_path: Path) -> None:
        """_find_plugin_source finds plugin as direct subdirectory."""
        (tmp_path / "my-plugin").mkdir()
        result = up2date._find_plugin_source(tmp_path, "my-plugin")
        assert result == tmp_path / "my-plugin"

    def test_root_source_layout(self, tmp_path: Path) -> None:
        """_find_plugin_source resolves source './' from marketplace.json."""
        claude_plugin = tmp_path / ".claude-plugin"
        claude_plugin.mkdir()
        mkt_json = claude_plugin / "marketplace.json"
        mkt_json.write_text(
            json.dumps({"plugins": [{"name": "doc-skills", "source": "./"}]}),
            encoding="utf-8",
        )
        result = up2date._find_plugin_source(tmp_path, "doc-skills")
        assert result == tmp_path

    def test_returns_none_when_not_found(self, tmp_path: Path) -> None:
        """_find_plugin_source returns None when plugin cannot be located."""
        result = up2date._find_plugin_source(tmp_path, "nonexistent")
        assert result is None

    def test_standard_takes_precedence_over_flat(self, tmp_path: Path) -> None:
        """_find_plugin_source prefers standard layout over flat."""
        (tmp_path / "plugins" / "my-plugin").mkdir(parents=True)
        (tmp_path / "my-plugin").mkdir()
        result = up2date._find_plugin_source(tmp_path, "my-plugin")
        assert result == tmp_path / "plugins" / "my-plugin"


# ── update_marketplace() ────────────────────────────────────────


class TestUpdateMarketplace:
    """Tests for update_marketplace()."""

    def test_returns_path_not_found_for_missing_dir(self) -> None:
        """update_marketplace returns error for nonexistent path."""
        result = up2date.update_marketplace("test", "/nonexistent/path")
        assert result == "Path not found: /nonexistent/path"

    def test_returns_updated_on_success(self, tmp_path: Path, mock_run: MagicMock) -> None:
        """update_marketplace returns success message on git pull success."""
        mock_run.return_value = subprocess.CompletedProcess(
            [], returncode=0, stdout="Already up to date.", stderr=""
        )
        result = up2date.update_marketplace("test", str(tmp_path))
        assert result.startswith("Updated:")

    def test_returns_failed_on_git_error(self, tmp_path: Path, mock_run: MagicMock) -> None:
        """update_marketplace returns failure message on git error."""
        mock_run.return_value = subprocess.CompletedProcess(
            [], returncode=1, stdout="", stderr="fatal: not a git repo"
        )
        result = up2date.update_marketplace("test", str(tmp_path))
        assert result.startswith("Update failed:")


# ── update_plugin_cache() ───────────────────────────────────────


class TestUpdatePluginCache:
    """Tests for update_plugin_cache()."""

    def test_returns_error_for_missing_marketplace(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """update_plugin_cache returns error when marketplace dir is missing."""
        monkeypatch.setattr(up2date, "MARKETPLACES_DIR", Path("/nonexistent"))
        result = up2date.update_plugin_cache("test@mkt", "mkt")
        assert result == "Marketplace not found: mkt"


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
