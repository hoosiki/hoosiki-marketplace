#!/usr/bin/env python3
"""Snapshot a live tmux session into a tmuxp workspace config.

Reads every window of a tmux session (name, layout, pane working directories
and each pane's foreground command) and rewrites the `windows:` section of a
tmuxp config so `tmuxp load` (or a launcher built on it, such as
`claude-research`) rebuilds the same session. Everything above `windows:` is
kept as written, and a window that has not changed keeps its block byte for
byte, comments included.

Usage:
    python3 snapshot_tmux.py [--session NAME] [--config PATH] [--dry-run]
                             [--exclude-window NAME ...] [--keep-rc]
                             [--no-backup] [--no-validate]

Environment:
    TMUX, TMUX_PANE  — identify the current session (set automatically by tmux)
    XDG_STATE_HOME   — backup location root (default ~/.local/state)
"""
from __future__ import annotations

import argparse
import ctypes
import ctypes.util
import difflib
import json
import os
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

_TMUX_CMD: str = "tmux"
_TMUX_TIMEOUT: int = 5
_DEFAULT_CONFIG: str = "~/.config/tmux/tmux_init.yaml"
_BACKUP_KEEP: int = 10
_COMMENT_WIDTH: int = 78

# Flags a launcher injects per run (`claude --rc <window_name>`). Writing them
# back would freeze one run's name into the config and stop the launcher from
# injecting the current one.
_RC_FLAGS: tuple[str, ...] = ("--rc", "--remote-control")

# Programs that are safe to start again on restore without a second look.
_KNOWN_PROGRAMS: frozenset[str] = frozenset(
    {"claude", "nvim", "vim", "vi", "nano", "emacs", "hx", "micro", "htop", "btop", "top", "lazygit", "yazi"}
)
_SHELLS: frozenset[str] = frozenset(
    {"zsh", "bash", "fish", "sh", "dash", "ksh", "tcsh", "csh", "nu", "xonsh", "elvish"}
)

_CLAUDE_VERSION_RE: re.Pattern[str] = re.compile(r"^\d+\.\d+\.\d+")
_SAFE_WORD_RE: re.Pattern[str] = re.compile(r"^[A-Za-z0-9_@%+:,./-][A-Za-z0-9_@%+=:,./-]*$")
_YAML_RESERVED_RE: re.Pattern[str] = re.compile(
    r"^(?:~|null|Null|NULL|true|True|TRUE|false|False|FALSE|yes|Yes|YES|no|No|NO|on|On|ON|off|Off|OFF|y|Y|n|N)$"
)
_YAML_NUMBER_RE: re.Pattern[str] = re.compile(
    r"^[-+]?(?:\d[\d_]*(?:\.\d*)?(?:[eE][-+]?\d+)?|\.\d+|0x[0-9a-fA-F]+|0o[0-7]+|\.inf|\.nan)$"
)
_WINDOW_COMMENT_RE: re.Pattern[str] = re.compile(r"^(\s*)#\s*──\s*Window\s+(\d+):\s*(.*?)\s*─*\s*$")
_PANE_COMMENT_RE: re.Pattern[str] = re.compile(r"^#\s*Pane\s+\d+\s*(?:\([^)]*\))?\s*:\s*(.+?)\s*$")
_KEY_RE: re.Pattern[str] = re.compile(r"^([A-Za-z_][\w-]*):(?:\s+(.*)|\s*)$")
_BLANK_PANES: frozenset[str] = frozenset({"", "blank", "pane", "null", "~"})
_WINDOW_KEYS: frozenset[str] = frozenset({"window_name", "start_directory", "layout", "panes", "focus"})
_PANE_KEYS: frozenset[str] = frozenset({"shell_command", "start_directory", "focus"})

_VALIDATE_SNIPPET: str = """\
import sys, yaml
from tmuxp.workspace import loader, validation
workspace = yaml.safe_load(sys.stdin.read())
validation.validate_schema(workspace)
loader.expand(workspace, cwd=sys.argv[1])
"""


class TmuxError(Exception):
    """A tmux command exited non-zero or timed out.

    Examples:
        >>> raise TmuxError("can't find session: x")  # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
            ...
        TmuxError: can't find session: x
    """


@dataclass
class PaneSpec:
    """One pane as tmuxp creates it.

    Attributes:
        commands: Commands typed into the pane on load; empty for a plain shell.
        start_directory: Pane working directory, or None to inherit the window's.
        focus: Whether the pane is the window's active pane.
        description: Text of the pane's `# Pane N (...):` comment, if known.

    Examples:
        >>> PaneSpec(commands=["htop"]).start_directory is None
        True
    """

    commands: list[str]
    start_directory: str | None = None
    focus: bool = False
    description: str | None = None


@dataclass
class WindowSpec:
    """One window as tmuxp creates it.

    Attributes:
        name: Window name.
        start_directory: Working directory of the window's first pane.
        layout: A tmux layout preset name or a layout string from `list-windows`.
        panes: Panes in index order.
        extra_keys: Keys of a parsed config block that a snapshot cannot reproduce.

    Examples:
        >>> WindowSpec("w", "/tmp", "even-horizontal", [PaneSpec([])]).extra_keys
        []
    """

    name: str
    start_directory: str | None
    layout: str | None
    panes: list[PaneSpec]
    extra_keys: list[str] = field(default_factory=list)


@dataclass
class RenderReport:
    """What render_config did to each window.

    Attributes:
        status: Window name → "kept" (block reused verbatim), "changed" or "new".
        removed: Names of config windows that no longer exist in the session.
        dropped_keys: Window name → config keys lost because the block was regenerated.

    Examples:
        >>> RenderReport().removed
        []
    """

    status: dict[str, str] = field(default_factory=dict)
    removed: list[str] = field(default_factory=list)
    dropped_keys: dict[str, list[str]] = field(default_factory=dict)


# ── tmux and process inspection ──────────────────────────────────


def _run_tmux(*args: str) -> str:
    """Run a tmux command and return stripped stdout.

    Args:
        *args: tmux subcommand and its arguments.

    Returns:
        The command's stdout with surrounding whitespace removed.

    Raises:
        TmuxError: If tmux exits non-zero or does not answer within the timeout.

    Examples:
        >>> _run_tmux("display-message", "-p", "#{session_name}")  # doctest: +SKIP
        'claude-research'
    """
    try:
        result = subprocess.run([_TMUX_CMD, *args], capture_output=True, text=True, timeout=_TMUX_TIMEOUT)
    except subprocess.TimeoutExpired as exc:
        raise TmuxError(f"timed out after {_TMUX_TIMEOUT}s: tmux {' '.join(args)}") from exc
    except FileNotFoundError as exc:
        raise TmuxError("tmux is not installed") from exc
    if result.returncode != 0:
        raise TmuxError(result.stderr.strip() or f"tmux {args[0]} exited {result.returncode}")
    return result.stdout.strip()


def _parse_procargs2(raw: bytes) -> list[str]:
    """Extract argv from a macOS KERN_PROCARGS2 buffer.

    The buffer is argc (int32), the executable path, NUL padding, argv, then
    the environment.

    Args:
        raw: Bytes returned by sysctl({CTL_KERN, KERN_PROCARGS2, pid}).

    Returns:
        The process's argv, or [] if the buffer is malformed.

    Examples:
        >>> _parse_procargs2((2).to_bytes(4, sys.byteorder) + b"/bin/ls\\0\\0ls\\0-l\\0HOME=/\\0")
        ['ls', '-l']
    """
    if len(raw) < 4:
        return []
    argc = int.from_bytes(raw[:4], sys.byteorder)
    rest = raw[4:]
    pos = rest.find(b"\0")
    if pos < 0:
        return []
    while pos < len(rest) and rest[pos] == 0:
        pos += 1
    argv: list[str] = []
    while len(argv) < argc and pos < len(rest):
        end = rest.find(b"\0", pos)
        end = len(rest) if end < 0 else end
        argv.append(rest[pos:end].decode("utf-8", "replace"))
        pos = end + 1
    return argv


def _read_argv_darwin(pid: int) -> list[str]:
    """Read a process's exact argv on macOS through sysctl.

    Args:
        pid: Process ID.

    Returns:
        The argv, or [] if it cannot be read.

    Examples:
        >>> _read_argv_darwin(os.getpid())[0].endswith("python3")  # doctest: +SKIP
        True
    """
    libc_path = ctypes.util.find_library("c")
    if libc_path is None:
        return []
    libc = ctypes.CDLL(libc_path, use_errno=True)
    mib = (ctypes.c_int * 3)(1, 49, pid)  # CTL_KERN, KERN_PROCARGS2
    size = ctypes.c_size_t(0)
    if libc.sysctl(mib, 3, None, ctypes.byref(size), None, 0) != 0:
        return []
    buf = ctypes.create_string_buffer(size.value)
    if libc.sysctl(mib, 3, buf, ctypes.byref(size), None, 0) != 0:
        return []
    return _parse_procargs2(buf.raw[: size.value])


def read_argv(pid: int) -> list[str]:
    """Read a process's argv, keeping arguments that contain spaces intact.

    `ps -o args` joins argv with spaces, so `nvim -c "'0"` and an argument such
    as `my host` cannot be told apart from separate words. This reads the real
    argv (sysctl on macOS, /proc on Linux) and only falls back to `ps`.

    Args:
        pid: Process ID.

    Returns:
        The argv, or [] if nothing could be read.

    Examples:
        >>> read_argv(os.getpid())[0].endswith("python3")  # doctest: +SKIP
        True
    """
    argv: list[str] = []
    if sys.platform == "darwin":
        argv = _read_argv_darwin(pid)
    else:
        cmdline = Path(f"/proc/{pid}/cmdline")
        try:
            argv = [a.decode("utf-8", "replace") for a in cmdline.read_bytes().split(b"\0") if a]
        except OSError:
            argv = []
    if argv:
        return argv
    try:
        result = subprocess.run(["ps", "-o", "args=", "-p", str(pid)], capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        return []
    return result.stdout.split()


def _pick_foreground(ps_output: str, shell_pid: int) -> int | None:
    """Choose a terminal's foreground program from `ps -o pid=,pgid=,tpgid=` output.

    Args:
        ps_output: Output of `ps -t <tty> -o pid=,pgid=,tpgid=`.
        shell_pid: PID of the pane's shell (`#{pane_pid}`).

    Returns:
        The foreground process group leader, or None while the shell itself
        owns the terminal (an idle prompt).

    Examples:
        >>> _pick_foreground(" 10 10 12\\n 12 12 12\\n 13 12 12\\n", shell_pid=10)
        12
        >>> _pick_foreground(" 10 10 10\\n", shell_pid=10) is None
        True
    """
    rows: list[tuple[int, int, int]] = []
    for line in ps_output.splitlines():
        fields = line.split()
        if len(fields) != 3:
            continue
        try:
            pid, pgid, tpgid = (int(f) for f in fields)
        except ValueError:
            continue
        rows.append((pid, pgid, tpgid))
    if not rows:
        return None
    tpgid = rows[0][2]
    if tpgid <= 0 or tpgid == shell_pid:
        return None
    if any(pid == tpgid for pid, _, _ in rows):
        return tpgid
    members = sorted(pid for pid, pgid, _ in rows if pgid == tpgid)
    return members[0] if members else None


def foreground_pid(tty: str, shell_pid: int) -> int | None:
    """Return the PID of the program running in the foreground of a pane.

    Args:
        tty: The pane's terminal (`#{pane_tty}`, e.g. /dev/ttys002).
        shell_pid: PID of the pane's shell (`#{pane_pid}`).

    Returns:
        The foreground program's PID, or None for an idle shell.

    Examples:
        >>> foreground_pid("/dev/ttys002", 2236)  # doctest: +SKIP
        2562
    """
    try:
        result = subprocess.run(
            ["ps", "-t", tty.removeprefix("/dev/"), "-o", "pid=,pgid=,tpgid="],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return _pick_foreground(result.stdout, shell_pid)


# ── Command lines ────────────────────────────────────────────────


def _shell_quote(arg: str) -> str:
    """Quote one argument for an interactive shell, as readably as possible.

    Args:
        arg: A single argv element.

    Returns:
        The argument bare when that is safe, in double quotes when it holds a
        single quote and nothing double quotes would expand, otherwise in
        single quotes.

    Examples:
        >>> _shell_quote("--verbose")
        '--verbose'
        >>> _shell_quote("'0")
        '"\\'0"'
        >>> _shell_quote("a b")
        "'a b'"
    """
    if _SAFE_WORD_RE.match(arg):
        return arg
    if "'" in arg and not re.search(r'["$`\\!]', arg):
        return f'"{arg}"'
    return "'" + arg.replace("'", "'\\''") + "'"


def _shell_join(argv: list[str]) -> str:
    """Join argv into a command line.

    Args:
        argv: Arguments to join.

    Returns:
        A command line that reproduces argv when typed into a shell.

    Examples:
        >>> _shell_join(["nvim", "-c", "'0"])
        'nvim -c "\\'0"'
    """
    return " ".join(_shell_quote(a) for a in argv)


def _is_claude_argv(argv: list[str]) -> bool:
    """Return True if argv starts Claude Code.

    Args:
        argv: A process's argv.

    Returns:
        True for `claude`, a native-installer version path, or node running the npm package.

    Examples:
        >>> _is_claude_argv(["/Users/me/.local/share/claude/versions/2.1.303"])
        True
        >>> _is_claude_argv(["nvim"])
        False
    """
    if not argv:
        return False
    name = os.path.basename(argv[0])
    if name == "claude":
        return True
    if _CLAUDE_VERSION_RE.match(name) and "/claude/versions/" in argv[0]:
        return True
    if name in ("node", "bun") and len(argv) > 1:
        return os.path.basename(argv[1]) == "claude" or "@anthropic-ai/claude-code" in argv[1]
    return False


def _strip_rc(args: list[str]) -> list[str]:
    """Remove `--rc NAME`, `--rc=NAME` and the `--remote-control` spellings.

    Args:
        args: Claude Code arguments (without the program).

    Returns:
        The arguments without Remote Control naming flags.

    Examples:
        >>> _strip_rc(["--rc", "job", "--verbose"])
        ['--verbose']
    """
    out: list[str] = []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in _RC_FLAGS:
            i += 1
            if i < len(args) and not args[i].startswith("-"):
                i += 1
            continue
        if arg.startswith(tuple(f"{flag}=" for flag in _RC_FLAGS)):
            i += 1
            continue
        out.append(arg)
        i += 1
    return out


def normalize_command(argv: list[str], *, keep_rc: bool = False) -> str:
    """Turn a running process's argv into the command line to restore it.

    Claude Code is always written as `claude ...` (whatever path or runtime
    started it), so a launcher that recognises `- claude` lines keeps working,
    and its per-run `--rc <name>` is dropped unless keep_rc is set.

    Args:
        argv: The process's argv.
        keep_rc: Keep `--rc`/`--remote-control` on Claude commands.

    Returns:
        A shell command line.

    Examples:
        >>> normalize_command(["claude", "--dangerously-skip-permissions", "--rc", "job"])
        'claude --dangerously-skip-permissions'
        >>> normalize_command(["nvim", "-c", "'0"])
        'nvim -c "\\'0"'
    """
    if not _is_claude_argv(argv):
        return _shell_join(argv)
    rest = argv[2:] if os.path.basename(argv[0]) in ("node", "bun") else argv[1:]
    return _shell_join(["claude", *(rest if keep_rc else _strip_rc(rest))])


def _is_shell(argv: list[str]) -> bool:
    """Return True if argv is an interactive shell (login shells start with `-`).

    Args:
        argv: A process's argv.

    Returns:
        True for zsh, bash, fish and the other common shells.

    Examples:
        >>> _is_shell(["-zsh"])
        True
        >>> _is_shell(["sleep", "10"])
        False
    """
    return bool(argv) and os.path.basename(argv[0]).lstrip("-") in _SHELLS


def _pane_argv(tty: str, shell_pid: int) -> list[str]:
    """Return the argv of the program a pane is running, or [] for an idle shell.

    A pane created with a command (`split-window 'htop'`) has no shell: its
    own process is the program, so it is the terminal's foreground group too.

    Args:
        tty: The pane's terminal (`#{pane_tty}`).
        shell_pid: The pane's own process (`#{pane_pid}`).

    Returns:
        The foreground program's argv.

    Examples:
        >>> _pane_argv("/dev/ttys002", 2236)  # doctest: +SKIP
        ['claude', '--dangerously-skip-permissions', '--rc', 'research']
    """
    pid = foreground_pid(tty, shell_pid)
    if pid is not None:
        return read_argv(pid)
    own = read_argv(shell_pid)
    return [] if not own or _is_shell(own) else own


def _program(command: str) -> str:
    """Return the program name of a command line.

    Args:
        command: A shell command line.

    Returns:
        The basename of its first word, or "" for an empty command.

    Examples:
        >>> _program("/usr/bin/ssh host")
        'ssh'
    """
    try:
        words = shlex.split(command)
    except ValueError:
        words = command.split()
    return os.path.basename(words[0]) if words else ""


# ── YAML ─────────────────────────────────────────────────────────


def _yaml_scalar(value: str) -> str:
    """Emit a string as a YAML scalar, quoting only when YAML would misread it.

    Args:
        value: The string to emit.

    Returns:
        A plain scalar, or a single-quoted one.

    Examples:
        >>> _yaml_scalar("nvim -c \\"'0\\"")
        'nvim -c "\\'0"'
        >>> _yaml_scalar("true")
        "'true'"
    """
    plain_ok = (
        bool(value)
        and value == value.strip()
        and value[0] not in "-?:,[]{}#&*!|>'\"%@`"
        and ": " not in value
        and " #" not in value
        and not value.endswith(":")
        and "\t" not in value
        and "\n" not in value
        and not _YAML_RESERVED_RE.match(value)
        and not _YAML_NUMBER_RE.match(value)
    )
    if plain_ok:
        return value
    return "'" + value.replace("'", "''") + "'"


def _yaml_unscalar(text: str) -> str:
    """Read back a one-line YAML scalar.

    Args:
        text: The scalar as written after `key:` or `- `.

    Returns:
        Its string value.

    Examples:
        >>> _yaml_unscalar("'it''s'")
        "it's"
        >>> _yaml_unscalar("nvim  # editor")
        'nvim'
    """
    text = text.strip()
    if len(text) >= 2 and text[0] == text[-1] == "'":
        return text[1:-1].replace("''", "'")
    if len(text) >= 2 and text[0] == text[-1] == '"':
        try:
            return str(json.loads(text))
        except ValueError:
            return text[1:-1]
    return re.split(r"\s+#", text, maxsplit=1)[0].rstrip()


def _yaml_flow_list(text: str) -> list[str] | None:
    """Read a one-line YAML flow list of plain or quoted strings.

    Args:
        text: Text such as `[]` or `[a, 'b c']`.

    Returns:
        The items, or None if text is not a flow list.

    Examples:
        >>> _yaml_flow_list("[]")
        []
        >>> _yaml_flow_list("[htop, 'echo hi']")
        ['htop', 'echo hi']
    """
    text = re.split(r"\s+#", text.strip(), maxsplit=1)[0].rstrip()
    if not (text.startswith("[") and text.endswith("]")):
        return None
    inner = text[1:-1].strip()
    if not inner:
        return []
    return [_yaml_unscalar(item) for item in re.findall(r"""'(?:[^']|'')*'|"(?:[^"\\]|\\.)*"|[^,]+""", inner)]


# ── Layout ───────────────────────────────────────────────────────


def _layout_geometry(layout: str) -> tuple[tuple[int, int], list[tuple[int, int, int, int]]] | None:
    """Read window size and pane rectangles from a tmux layout string.

    Handles both the JSON layout of tmux 3.8+ and the older checksum format.

    Args:
        layout: `#{window_layout}` value.

    Returns:
        ((width, height), [(x, y, width, height), ...]), or None if unreadable.

    Examples:
        >>> _layout_geometry("a5f1,136x33,0,0{68x33,0,0,1,67x33,69,0,2}")
        ((136, 33), [(0, 0, 68, 33), (69, 0, 67, 33)])
    """
    text = layout.strip()
    if text.startswith("{"):
        try:
            root = json.loads(text)["L"]
            leaves: list[tuple[int, int, int, int]] = []
            stack = [root]
            while stack:
                node = stack.pop()
                if node.get("t") == "p":
                    leaves.append((int(node["x"]), int(node["y"]), int(node["w"]), int(node["h"])))
                else:
                    stack.extend(reversed(node.get("c", [])))
            return (int(root["w"]), int(root["h"])), leaves
        except (ValueError, KeyError, TypeError, AttributeError):
            return None
    match = re.match(r"^[0-9a-f]{4},(\d+)x(\d+),\d+,\d+", text)
    if not match:
        return None
    leaves = [(int(x), int(y), int(w), int(h)) for w, h, x, y in re.findall(r"(\d+)x(\d+),(\d+),(\d+),\d+", text[5:])]
    return (int(match.group(1)), int(match.group(2))), leaves


def _stable_layout(layout: str) -> str:
    """Drop the per-server fields from a tmux 3.8+ JSON layout.

    `I` (pane ID such as %12), `a` (active) and `l` (last) change every time
    the session is rebuilt, and select-layout does not need them. `i` (pane
    index) is required and stays. The older checksum format is returned as is.

    Args:
        layout: `#{window_layout}` value.

    Returns:
        The layout with volatile fields removed.

    Examples:
        >>> _stable_layout('{"V":2,"L":{"t":"p","w":80,"h":24,"x":0,"y":0,"a":true,"i":1,"I":"%5"}}')
        '{"V":2,"L":{"t":"p","w":80,"h":24,"x":0,"y":0,"i":1}}'
    """
    if not layout.lstrip().startswith("{"):
        return layout
    try:
        data = json.loads(layout)
    except ValueError:
        return layout

    def strip(node: object) -> object:
        """Remove volatile keys from a layout node and its children."""
        if isinstance(node, dict):
            return {k: strip(v) for k, v in node.items() if k not in ("I", "a", "l")}
        if isinstance(node, list):
            return [strip(v) for v in node]
        return node

    return json.dumps(strip(data), separators=(",", ":"), ensure_ascii=False)


def _layout_key(layout: str | None) -> object:
    """Reduce a layout to what determines the pane arrangement.

    Args:
        layout: A preset name or a layout string.

    Returns:
        The pane geometry for a layout string, or the value itself for a preset.

    Examples:
        >>> _layout_key("a1b2,80x24,0,0,1") == _layout_key("c3d4,80x24,0,0,9")
        True
    """
    geometry = _layout_geometry(layout) if layout else None
    return geometry if geometry is not None else layout


def detect_layout(layout: str) -> str:
    """Name a layout when it is an even split, otherwise keep its geometry.

    A preset name survives a different terminal size and pane count; a raw
    layout string keeps hand-resized splits exact.

    Args:
        layout: `#{window_layout}` value.

    Returns:
        "even-horizontal", "even-vertical", or the layout string without per-server fields.

    Examples:
        >>> detect_layout("a5f1,136x33,0,0{68x33,0,0,1,67x33,69,0,2}")
        'even-horizontal'
        >>> detect_layout("b25f,136x33,0,0,5")
        'even-horizontal'
    """
    geometry = _layout_geometry(layout)
    if geometry is None:
        return layout
    (width, height), leaves = geometry
    if len(leaves) <= 1:
        return "even-horizontal"
    widths = [w for _, _, w, _ in leaves]
    heights = [h for _, _, _, h in leaves]
    if all(y == 0 and h == height for _, y, _, h in leaves) and max(widths) - min(widths) <= 1:
        return "even-horizontal"
    if all(x == 0 and w == width for x, _, w, _ in leaves) and max(heights) - min(heights) <= 1:
        return "even-vertical"
    return _stable_layout(layout)


# ── Capture ──────────────────────────────────────────────────────


def capture_session(session: str, *, keep_rc: bool = False) -> list[WindowSpec]:
    """Read every window of a tmux session.

    Args:
        session: tmux session name (matched exactly).
        keep_rc: Keep `--rc` on Claude commands.

    Returns:
        Windows in index order.

    Raises:
        TmuxError: If tmux cannot list the session.

    Examples:
        >>> [w.name for w in capture_session("claude-research")]  # doctest: +SKIP
        ['research', 'marketplace', 'daq-project']
    """
    raw = _run_tmux("list-windows", "-t", f"={session}", "-F", "#{window_id}\t#{window_name}\t#{window_layout}")
    windows: list[WindowSpec] = []
    for line in raw.splitlines():
        parts = line.split("\t", 2)
        if len(parts) != 3:
            continue
        window_id, name, layout = parts
        pane_raw = _run_tmux(
            "list-panes", "-t", window_id, "-F", "#{pane_pid}\t#{pane_tty}\t#{pane_current_path}\t#{pane_active}"
        )
        panes: list[PaneSpec] = []
        root: str | None = None
        for pane_line in pane_raw.splitlines():
            fields = pane_line.split("\t")
            if len(fields) != 4:
                continue
            shell_pid, tty, path, active = fields
            root = path if root is None else root
            argv = _pane_argv(tty, int(shell_pid))
            commands = [normalize_command(argv, keep_rc=keep_rc)] if argv else []
            own_dir = None if path == root else path
            panes.append(PaneSpec(commands=commands, start_directory=own_dir, focus=active == "1"))
        windows.append(WindowSpec(name=name, start_directory=root, layout=detect_layout(layout), panes=panes))
    return windows


# ── Existing config ──────────────────────────────────────────────


def _indent(line: str) -> int:
    """Return the number of leading spaces of a line.

    Args:
        line: A text line.

    Returns:
        Leading space count.

    Examples:
        >>> _indent("    a")
        4
    """
    return len(line) - len(line.lstrip(" "))


def split_config(text: str) -> tuple[str, list[str], str]:
    """Split a tmuxp config into header, one text block per window, and footer.

    The header runs through the top-level `windows:` line. A comment at the
    windows-list indentation belongs to the window after it, so each
    `# ── Window N` banner travels with its window.

    Args:
        text: Config file content.

    Returns:
        (header, window blocks, footer); concatenated they equal text.

    Examples:
        >>> split_config("session_name: s\\nwindows:\\n  - window_name: a\\n  - window_name: b\\n")[1]
        ['  - window_name: a\\n', '  - window_name: b\\n']
    """
    lines = text.splitlines(keepends=True)
    start = next((i for i, line in enumerate(lines) if re.match(r"^windows:", line)), None)
    if start is None:
        return text, [], ""
    end = next(
        (
            j
            for j in range(start + 1, len(lines))
            if lines[j].strip() and not lines[j].lstrip().startswith("#") and _indent(lines[j]) == 0
        ),
        len(lines),
    )
    header = "".join(lines[: start + 1])
    body = lines[start + 1 : end]
    footer = "".join(lines[end:])
    item_indent = next((_indent(line) for line in body if re.match(r"^\s*-(\s|$)", line)), None)
    if item_indent is None:
        return header + "".join(body), [], footer

    blocks: list[str] = []
    current: list[str] = []
    pending: list[str] = []
    for line in body:
        stripped = line.strip()
        if _indent(line) == item_indent and re.match(r"^\s*-(\s|$)", line):
            if current:
                blocks.append("".join(current))
            current, pending = [*pending, line], []
        elif not stripped or (stripped.startswith("#") and _indent(line) <= item_indent):
            pending.append(line)
        else:
            current.extend(pending)
            pending = []
            current.append(line)
    if current:
        blocks.append("".join([*current, *pending]))
    else:
        header += "".join(pending)
    return header, blocks, footer


def _mapping_entries(lines: list[str], key_indent: int) -> list[tuple[str, str | None, list[str]]]:
    """Group mapping lines into (key, inline value, nested lines).

    Args:
        lines: Lines of the mapping; the first may still carry its `- ` marker.
        key_indent: Indentation of the mapping's keys.

    Returns:
        One entry per key, in order. Comment lines stay with the nested lines.

    Examples:
        >>> _mapping_entries(["  - a: 1\\n", "    b:\\n", "      - x\\n"], 4)
        [('a', '1', []), ('b', None, ['      - x\\n'])]
    """
    entries: list[tuple[str, str | None, list[str]]] = []
    for i, line in enumerate(lines):
        content = line.strip()
        if i == 0:
            content = content[1:].strip() if content.startswith("-") else content
        elif _indent(line) != key_indent or content.startswith("#") or not content:
            if entries:
                entries[-1][2].append(line)
            continue
        match = _KEY_RE.match(content)
        if match is None:
            if entries:
                entries[-1][2].append(line)
            continue
        entries.append((match.group(1), match.group(2), []))
    return entries


def _parse_pane(lines: list[str], pane_indent: int, description: str | None) -> tuple[PaneSpec, list[str]]:
    """Parse one pane item of a tmuxp `panes:` list.

    Args:
        lines: The pane item's lines, starting with its `- ` line.
        pane_indent: Indentation of the pane's `- ` marker.
        description: Text of the comment just above the pane, if any.

    Returns:
        (pane, keys this parser does not reproduce).

    Examples:
        >>> _parse_pane(["- shell_command:\\n", "    - htop\\n"], 0, None)[0].commands
        ['htop']
    """
    first = lines[0].strip()[1:].strip()
    if not _KEY_RE.match(first):
        value = _yaml_unscalar(first)
        commands = [] if value in _BLANK_PANES else [value]
        return PaneSpec(commands=commands, description=description), []

    pane = PaneSpec(commands=[], description=description)
    unknown: list[str] = []
    for key, value, nested in _mapping_entries(lines, pane_indent + 2):
        if key == "shell_command":
            flow = _yaml_flow_list(value) if value else None
            if flow is not None:
                pane.commands = [c for c in flow if c]
            elif value:
                pane.commands = [] if _yaml_unscalar(value) in _BLANK_PANES else [_yaml_unscalar(value)]
            else:
                items = [re.match(r"^\s*-\s*(.*)$", n) for n in nested if not n.strip().startswith("#")]
                pane.commands = [_yaml_unscalar(m.group(1)) for m in items if m and _yaml_unscalar(m.group(1))]
        elif key == "start_directory" and value:
            pane.start_directory = _yaml_unscalar(value)
        elif key == "focus" and value:
            pane.focus = _yaml_unscalar(value).lower() == "true"
        elif key not in _PANE_KEYS:
            unknown.append(f"panes.{key}")
    return pane, unknown


def _parse_panes(lines: list[str]) -> tuple[list[PaneSpec], list[str]]:
    """Parse the nested lines of a window's `panes:` key.

    Args:
        lines: Lines below `panes:`.

    Returns:
        (panes, keys this parser does not reproduce).

    Examples:
        >>> [p.commands for p in _parse_panes(["  - blank\\n", "  - htop\\n"])[0]]
        [[], ['htop']]
    """
    pane_indent = next((_indent(line) for line in lines if re.match(r"^\s*-(\s|$)", line)), None)
    if pane_indent is None:
        return [], []
    panes: list[PaneSpec] = []
    unknown: list[str] = []
    item: list[str] = []
    comment: str | None = None
    description: str | None = None

    def flush() -> None:
        """Parse the collected pane item, if any."""
        if item:
            pane, keys = _parse_pane(item, pane_indent, description)
            panes.append(pane)
            unknown.extend(keys)

    for line in lines:
        stripped = line.strip()
        if _indent(line) == pane_indent and re.match(r"^\s*-(\s|$)", line):
            flush()
            item, description, comment = [line], comment, None
        elif stripped.startswith("#"):
            match = _PANE_COMMENT_RE.match(stripped)
            comment = match.group(1) if match else None
        elif stripped:
            comment = None
            item.append(line)
    flush()
    return panes, unknown


def parse_window_block(block: str) -> WindowSpec | None:
    """Read a window block of a tmuxp config back into a WindowSpec.

    Covers the shapes tmuxp documents for windows and panes; anything else is
    reported in extra_keys so a regenerated block can say what it dropped.

    Args:
        block: One block from split_config.

    Returns:
        The window, or None if the block has no list item.

    Examples:
        >>> parse_window_block("  - window_name: w\\n    panes:\\n      - htop\\n").panes[0].commands
        ['htop']
    """
    lines = block.splitlines(keepends=True)
    start = next((i for i, line in enumerate(lines) if re.match(r"^\s*-(\s|$)", line)), None)
    if start is None:
        return None
    spec = WindowSpec(name="", start_directory=None, layout=None, panes=[])
    for key, value, nested in _mapping_entries(lines[start:], _indent(lines[start]) + 2):
        if key == "window_name":
            spec.name = _yaml_unscalar(value or "")
        elif key == "start_directory":
            spec.start_directory = _yaml_unscalar(value or "") or None
        elif key == "layout":
            spec.layout = _yaml_unscalar(value or "") or None
        elif key == "panes":
            spec.panes, unknown = _parse_panes(nested)
            spec.extra_keys.extend(unknown)
        elif key not in _WINDOW_KEYS:
            spec.extra_keys.append(key)
    return spec


# ── Rendering ────────────────────────────────────────────────────


def _norm_path(path: str | None) -> str:
    """Normalize a path for comparison.

    Args:
        path: A path, possibly with `~`, or None.

    Returns:
        The expanded, normalized path, or "" for None.

    Examples:
        >>> _norm_path("/tmp/x/")
        '/tmp/x'
    """
    return os.path.normpath(os.path.expanduser(path)) if path else ""


def _comparable(spec: WindowSpec) -> tuple[object, ...]:
    """Reduce a window to the fields a snapshot can observe.

    Focus and comments are ignored, and the layout of a one-pane window does
    not matter.

    Args:
        spec: A live or parsed window.

    Returns:
        A tuple that is equal for windows tmuxp would build identically.

    Examples:
        >>> _comparable(WindowSpec("w", "/x/", "tiled", [PaneSpec([])]))
        ('w', '/x', '', (((), None),))
    """
    root = _norm_path(spec.start_directory)
    panes = tuple(
        (tuple(p.commands), _norm_path(p.start_directory) if _norm_path(p.start_directory) not in ("", root) else None)
        for p in spec.panes
    )
    layout = _layout_key(spec.layout) if len(spec.panes) > 1 else ""
    return (spec.name, root, layout, panes)


def _window_comment(number: int, name: str, indent: int) -> str:
    """Build a `# ── Window N: name ───` banner line.

    Args:
        number: 1-based window position.
        name: Window name.
        indent: Indentation of the windows list.

    Returns:
        The banner, padded with `─` to the file's comment width, with newline.

    Examples:
        >>> len(_window_comment(4, "zsh", 2).rstrip())
        78
    """
    prefix = f"{' ' * indent}# ── Window {number}: {name} "
    return prefix + "─" * max(3, _COMMENT_WIDTH - len(prefix)) + "\n"


def _renumber_block(block: str, number: int) -> str:
    """Fix the number in a reused block's window banner.

    Args:
        block: A window block.
        number: The window's new 1-based position.

    Returns:
        The block, with its banner rebuilt only if the number changed.

    Examples:
        >>> _renumber_block("  # ── Window 3: job ───\\n  - window_name: job\\n", 3).count("Window 3")
        1
    """
    out: list[str] = []
    for line in block.splitlines(keepends=True):
        match = _WINDOW_COMMENT_RE.match(line.rstrip("\n"))
        if match and int(match.group(2)) != number:
            line = _window_comment(number, match.group(3), len(match.group(1)))
        out.append(line)
    return "".join(out)


def _positions(layout: str | None, count: int) -> list[str]:
    """Label pane positions for the `# Pane N (...)` comments.

    Args:
        layout: The window's layout.
        count: Number of panes.

    Returns:
        One label per pane, or "" where no label applies.

    Examples:
        >>> _positions("even-horizontal", 3)
        ['left', 'middle', 'right']
    """
    ends = {"even-horizontal": ("left", "right"), "even-vertical": ("top", "bottom")}.get(layout or "")
    if count < 2 or ends is None:
        return [""] * count
    return [ends[0], *["middle"] * (count - 2), ends[1]]


def _describe(pane: PaneSpec, known: dict[tuple[str, ...], str]) -> str:
    """Choose the description for a pane comment.

    Args:
        pane: The pane.
        known: Descriptions harvested from the existing config, by commands.

    Returns:
        The existing description for the same commands, else a generic one.

    Examples:
        >>> _describe(PaneSpec(["claude"]), {})
        'Claude Code CLI'
    """
    if tuple(pane.commands) in known:
        return known[tuple(pane.commands)]
    if not pane.commands:
        return "shell"
    program = _program(pane.commands[0])
    return "Claude Code CLI" if program == "claude" else program


def render_window(spec: WindowSpec, number: int, known: dict[tuple[str, ...], str], indent: int = 2) -> str:
    """Render one window block in the style of a hand-written tmuxp config.

    Args:
        spec: The window.
        number: 1-based window position, for the banner.
        known: Pane descriptions harvested from the existing config.
        indent: Indentation of the windows list.

    Returns:
        The block text.

    Examples:
        >>> print(render_window(WindowSpec("w", "/x", "even-horizontal", [PaneSpec([])]), 1, {}), end="")
          # ── Window 1: w ───────────────────────────────────────────────────────────
          - window_name: w
            start_directory: /x
            layout: even-horizontal
            panes:
              # Pane 1: shell
              - blank
    """
    pad = " " * indent
    lines = [_window_comment(number, spec.name, indent), f"{pad}- window_name: {_yaml_scalar(spec.name)}\n"]
    if spec.start_directory:
        lines.append(f"{pad}  start_directory: {_yaml_scalar(spec.start_directory)}\n")
    if spec.layout:
        lines.append(f"{pad}  layout: {_yaml_scalar(spec.layout)}\n")
    lines.append(f"{pad}  panes:\n")
    multi = len(spec.panes) > 1
    root = _norm_path(spec.start_directory)
    for i, (pane, position) in enumerate(zip(spec.panes, _positions(spec.layout, len(spec.panes)), strict=True), 1):
        label = f" ({position})" if position else ""
        lines.append(f"{pad}    # Pane {i}{label}: {_describe(pane, known)}\n")
        focus = multi and pane.focus
        own_dir = pane.start_directory if _norm_path(pane.start_directory) not in ("", root) else None
        if pane.commands:
            lines.append(f"{pad}    - shell_command:\n")
            lines.extend(f"{pad}        - {_yaml_scalar(c)}\n" for c in pane.commands)
        elif focus or own_dir:
            lines.append(f"{pad}    - shell_command: []\n")
        else:
            lines.append(f"{pad}    - blank\n")
        if own_dir:
            lines.append(f"{pad}      start_directory: {_yaml_scalar(own_dir)}\n")
        if focus:
            lines.append(f"{pad}      focus: true\n")
    return "".join(lines)


def _default_header(session_name: str, config_name: str) -> str:
    """Build the header for a config that does not exist yet.

    Args:
        session_name: tmux session name tmuxp should create.
        config_name: File name, for the usage line.

    Returns:
        Header text ending with `windows:`.

    Examples:
        >>> "session_name: s\\n" in _default_header("s", "x.yaml")
        True
    """
    rule = "# " + "=" * 77 + "\n"
    return (
        f"{rule}#  tmuxp Session Config — {session_name}\n#  Usage: tmuxp load {config_name}\n{rule}\n"
        f"session_name: {_yaml_scalar(session_name)}\n"
        f"start_directory: {_yaml_scalar(str(Path.home()))}\n"
        "suppress_history: true\n\nwindows:\n"
    )


def render_config(
    existing: str | None,
    windows: list[WindowSpec],
    *,
    session_name: str,
    config_name: str = "tmux_init.yaml",
) -> tuple[str, RenderReport]:
    """Produce the new config text from the live windows.

    Everything above `windows:` is kept. A live window whose config block
    describes it already keeps that block verbatim (only its banner number
    may change); any other window gets a freshly rendered block.

    Args:
        existing: Current config content, or None if there is none.
        windows: Live windows, in order.
        session_name: Session name for a new header.
        config_name: Config file name, for a new header.

    Returns:
        (config text, report).

    Examples:
        >>> text, report = render_config(None, [WindowSpec("w", "/x", "even-horizontal", [PaneSpec([])])],
        ...                              session_name="s")
        >>> report.status
        {'w': 'new'}
    """
    if not existing or not existing.strip():
        header, blocks, footer = _default_header(session_name, config_name), [], ""
    else:
        header, blocks, footer = split_config(existing)
        if not re.search(r"(?m)^windows:", header):
            header = header.rstrip("\n") + "\n\nwindows:\n"
        elif re.search(r"(?m)^windows:\s*\[\s*\]", header):
            header = re.sub(r"(?m)^windows:.*$", "windows:", header)

    parsed = [(block, parse_window_block(block)) for block in blocks]
    by_name: dict[str, list[tuple[str, WindowSpec]]] = {}
    known: dict[tuple[str, ...], str] = {}
    for block, spec in parsed:
        if spec is None:
            continue
        by_name.setdefault(spec.name, []).append((block, spec))
        for pane in spec.panes:
            if pane.description:
                known.setdefault(tuple(pane.commands), pane.description)
    indent = next((_indent(line) for b in blocks for line in b.splitlines() if re.match(r"^\s*-\s", line)), 2)

    report = RenderReport()
    out: list[str] = []
    for number, window in enumerate(windows, 1):
        candidates = by_name.get(window.name, [])
        old = candidates.pop(0) if candidates else None
        if old is not None and _comparable(old[1]) == _comparable(window):
            out.append(_renumber_block(old[0], number))
            report.status[window.name] = "kept"
            continue
        report.status[window.name] = "changed" if old is not None else "new"
        if old is not None and old[1].extra_keys:
            report.dropped_keys[window.name] = old[1].extra_keys
        out.append(render_window(window, number, known, indent))
    report.removed = [spec.name for leftovers in by_name.values() for _, spec in leftovers]
    if not header.endswith("\n"):
        header += "\n"
    return header + "".join(out) + footer, report


# ── Validation and writing ───────────────────────────────────────


def _tmuxp_python() -> str | None:
    """Find the interpreter tmuxp runs under, from its shebang.

    Returns:
        Path of tmuxp's Python, or None if tmuxp is not installed.

    Examples:
        >>> _tmuxp_python()  # doctest: +SKIP
        '/opt/homebrew/Cellar/tmuxp/1.74.0/libexec/bin/python'
    """
    exe = shutil.which("tmuxp")
    if exe is None:
        return None
    try:
        first = Path(exe).resolve().read_bytes()[:512].split(b"\n", 1)[0].decode("utf-8", "replace")
    except OSError:
        return None
    if not first.startswith("#!"):
        return None
    words = first[2:].split()
    if words and os.path.basename(words[0]) == "env":
        words = [w for w in words[1:] if not w.startswith("-")]
        return shutil.which(words[0]) if words else None
    return words[0] if words else None


def validate_with_tmuxp(text: str, cwd: Path) -> tuple[bool | None, str]:
    """Check a config with tmuxp's own schema validation and expansion.

    Args:
        text: Config content.
        cwd: Directory relative start_directory values resolve against.

    Returns:
        (True, "ok"), (False, error message), or (None, reason) if tmuxp is unavailable.

    Examples:
        >>> validate_with_tmuxp("session_name: s\\n", Path("."))  # doctest: +SKIP
        (False, 'tmuxp.workspace.validation.WindowListMissingValidationError: workspace requires list of "windows"')
    """
    python = _tmuxp_python()
    if python is None:
        return None, "tmuxp not found, skipped"
    try:
        result = subprocess.run(
            [python, "-I", "-c", _VALIDATE_SNIPPET, str(cwd)],
            input=text,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, f"could not run tmuxp's Python: {exc}"
    if result.returncode == 0:
        return True, "ok"
    last = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else f"exit {result.returncode}"
    if "ModuleNotFoundError" in last:
        return None, f"tmuxp's Python could not import tmuxp, skipped ({last})"
    return False, last


def _backup_dir() -> Path:
    """Return the directory for config backups.

    Returns:
        $XDG_STATE_HOME/snapshot-tmux, defaulting to ~/.local/state/snapshot-tmux.

    Examples:
        >>> _backup_dir().name
        'snapshot-tmux'
    """
    return Path(os.environ.get("XDG_STATE_HOME") or "~/.local/state").expanduser() / "snapshot-tmux"


def write_config(path: Path, text: str, *, backup_dir: Path | None) -> Path | None:
    """Write the config atomically, through a symlink, after backing it up.

    The link's target is replaced, never the link itself, so a config kept in
    a dotfiles repo and linked into ~/.config stays linked.

    Args:
        path: Config path (may be a symlink).
        text: New content.
        backup_dir: Where to copy the previous content, or None for no backup.

    Returns:
        The backup path, or None if nothing was backed up.

    Examples:
        >>> write_config(Path("~/.config/tmux/tmux_init.yaml").expanduser(), "...", backup_dir=None)  # doctest: +SKIP
    """
    target = path.expanduser().resolve()
    backup: Path | None = None
    if backup_dir is not None and target.exists():
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup = backup_dir / f"{target.name}.{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        shutil.copy2(target, backup)
        old = sorted(backup_dir.glob(f"{target.name}.*"))
        for stale in old[: max(0, len(old) - _BACKUP_KEEP)]:
            stale.unlink()
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=target.parent, prefix=f".{target.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        if target.exists():
            os.chmod(tmp, stat.S_IMODE(target.stat().st_mode))
        os.replace(tmp, target)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
    return backup


# ── CLI ──────────────────────────────────────────────────────────


def _current_session() -> str | None:
    """Return the session of the pane this script runs in.

    Returns:
        The session name, or None outside tmux.

    Raises:
        TmuxError: If tmux cannot answer.

    Examples:
        >>> _current_session()  # doctest: +SKIP
        'claude-research'
    """
    if not os.environ.get("TMUX"):
        return None
    pane = os.environ.get("TMUX_PANE")
    target = ["-t", pane] if pane else []
    return _run_tmux("display-message", "-p", *target, "#{session_name}") or None


def _header_session_name(text: str | None) -> str | None:
    """Read the top-level session_name of a config.

    Args:
        text: Config content, or None.

    Returns:
        The session name, or None.

    Examples:
        >>> _header_session_name("session_name: claude-research\\nwindows:\\n")
        'claude-research'
    """
    match = re.search(r"(?m)^session_name:\s*(.+)$", text or "")
    return _yaml_unscalar(match.group(1)) if match else None


def collect_warnings(windows: list[WindowSpec]) -> tuple[list[str], list[str]]:
    """List what the user should look at before relying on the snapshot.

    Args:
        windows: Live windows that will be written.

    Returns:
        (warnings, review items). Review items are commands that will run again on load.

    Examples:
        >>> collect_warnings([WindowSpec("w", "/x", "even-horizontal", [PaneSpec(["make deploy"])])])[1]
        ["window 'w' pane 1 will run `make deploy` on load"]
    """
    warnings: list[str] = []
    review: list[str] = []
    for window in windows:
        first = window.panes[0].commands if window.panes else []
        if not first or _program(first[0]) != "claude":
            shown = f"`{first[0]}`" if first else "a plain shell"
            warnings.append(
                f"window '{window.name}': pane 1 runs {shown}, not Claude Code. A launcher that sends "
                "/sc:load to pane 1 of every window (claude-research does) will type it into this pane."
            )
        for i, pane in enumerate(window.panes, 1):
            for command in pane.commands:
                if _program(command) not in _KNOWN_PROGRAMS:
                    review.append(f"window '{window.name}' pane {i} will run `{command}` on load")
    return warnings, review


def main() -> None:
    """Capture the session, show the change, validate it, and write the config.

    Examples:
        >>> main()  # doctest: +SKIP
    """
    parser = argparse.ArgumentParser(description="Snapshot a tmux session into a tmuxp config.")
    parser.add_argument("--session", help="tmux session to read (default: the current one)")
    parser.add_argument(
        "--config", default=_DEFAULT_CONFIG, help=f"tmuxp config to update (default: {_DEFAULT_CONFIG})"
    )
    parser.add_argument("--dry-run", action="store_true", help="show the diff without writing")
    parser.add_argument(
        "--exclude-window", action="append", default=[], metavar="NAME", help="leave a window out (repeatable)"
    )
    parser.add_argument("--keep-rc", action="store_true", help="keep --rc/--remote-control on Claude commands")
    parser.add_argument("--no-backup", action="store_true", help="do not back up the previous config")
    parser.add_argument("--no-validate", action="store_true", help="skip the tmuxp schema check")
    args = parser.parse_args()

    config = Path(args.config).expanduser()
    existing = config.read_text(encoding="utf-8") if config.exists() else None
    header_session = _header_session_name(existing)
    try:
        session = args.session or _current_session() or header_session
        if not session:
            print("error: not inside tmux and no session_name in the config; pass --session", file=sys.stderr)
            sys.exit(2)
        windows = capture_session(session, keep_rc=args.keep_rc)
    except TmuxError as exc:
        print(f"tmux error: {exc}", file=sys.stderr)
        sys.exit(1)

    excluded = set(args.exclude_window)
    windows = [w for w in windows if w.name not in excluded]
    if not windows:
        print(f"error: no windows left to write from session '{session}'", file=sys.stderr)
        sys.exit(2)

    text, report = render_config(existing, windows, session_name=header_session or session, config_name=config.name)
    pane_count = sum(len(w.panes) for w in windows)
    print(f"Snapshot of tmux session '{session}': {len(windows)} window(s), {pane_count} pane(s)")
    for number, window in enumerate(windows, 1):
        panes = f"{len(window.panes)} pane{'s' if len(window.panes) != 1 else ''}"
        print(f"  {number:>2} {window.name:<20} {report.status[window.name]:<8} {panes:<8} {window.start_directory}")
    for name in report.removed:
        print(f"   - {name:<20} removed  (no longer in the session)")
    for name in excluded:
        print(f"   - {name:<20} excluded (--exclude-window)")

    warnings, review = collect_warnings(windows)
    if header_session and header_session != session:
        warnings.append(
            f"the config creates session '{header_session}' but the snapshot came from '{session}'; "
            "the header is kept, so loading still creates the config's session name"
        )
    for name, keys in report.dropped_keys.items():
        warnings.append(f"window '{name}': regenerated, so its config keys {', '.join(keys)} are no longer written")
    for heading, items in (("Warnings", warnings), ("Review: these commands run again on load", review)):
        if items:
            print(f"\n{heading}:")
            for item in items:
                print(f"  - {item}")

    if text == existing:
        print(f"\nNo changes: {config} already matches the session.")
        return

    print()
    sys.stdout.writelines(
        difflib.unified_diff(
            (existing or "").splitlines(keepends=True),
            text.splitlines(keepends=True),
            fromfile=str(config),
            tofile=f"{config} (snapshot)",
        )
    )

    if not args.no_validate:
        ok, message = validate_with_tmuxp(text, cwd=config.resolve().parent)
        print(f"\ntmuxp validation: {message}")
        if ok is False:
            print("Refusing to write a config tmuxp rejects.", file=sys.stderr)
            sys.exit(1)

    if args.dry_run:
        print("\nDry run: nothing written.")
        return
    backup = write_config(config, text, backup_dir=None if args.no_backup else _backup_dir())
    target = config.resolve()
    via = f" (via {config})" if target != config.absolute() else ""
    print(f"\nWrote {target}{via}")
    if backup is not None:
        print(f"Backup: {backup}")


if __name__ == "__main__":
    main()
