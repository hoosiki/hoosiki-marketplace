---
name: snapshot-tmux
description: Snapshot the current tmux session into a tmuxp config (default ~/.config/tmux/tmux_init.yaml) so a launcher such as `claude-research` or `tmuxp load` rebuilds the same windows, pane splits, working directories and pane commands. Unchanged windows keep their YAML block byte for byte, Claude panes are written as `claude ...` without the launcher's per-run `--rc <name>`, the file is validated by tmuxp before it is written, and the previous version is backed up. Use when the user says "snapshot tmux", "save tmux session", "save tmux layout", "update tmux_init.yaml", "tmux 세션 저장", "tmux 스냅샷", "현재 세션 상태 저장", "tmux_init.yaml 업데이트", "claude-research로 복구", "세션 복구용 설정 갱신", or wants the tmuxp config to match the windows they have open now.
---

# snapshot-tmux

Read the live tmux session and rewrite the `windows:` section of a tmuxp config so the session can be rebuilt from it later. For the `claude-research` launcher, that means `claude-research` recreates the session as it looks now.

## Behavioral Flow

1. Find the session to read: `--session`, else the session of the current pane, else the config's `session_name`
2. For each window, read its name, layout and panes. For each pane, read its working directory and the real argv of its foreground program (sysctl on macOS, `/proc` on Linux). A pane at an idle prompt becomes a blank pane
3. Normalize commands: Claude Code becomes `claude ...` whatever path started it, and `--rc` / `--remote-control <name>` is dropped, because the launcher injects the current window name on every run. Arguments are quoted only as much as the shell needs (`nvim -c "'0"`)
4. Layouts: an even split is written as `even-horizontal` / `even-vertical`. Anything else (a hand-resized split) is written as tmux's own layout string, with the pane IDs removed so it stays the same across rebuilds
5. Merge into the existing file: everything above `windows:` stays as written. A window that tmuxp would already build identically keeps its block verbatim, comments included (only its `# ── Window N` number is fixed if windows moved). Changed and new windows get a block in the same comment style, reusing the existing pane description when the command is the same
6. Show the per-window status (kept / changed / new / removed), warnings and a unified diff, validate the result with tmuxp's own schema check, then write it

## Usage

Run the bundled script:

```bash
python3 scripts/snapshot_tmux.py --dry-run   # always look first
python3 scripts/snapshot_tmux.py             # then write
```

### Options

| Flag | Description |
|------|-------------|
| `--dry-run` | Show the status table, warnings and diff without writing |
| `--session NAME` | Read this tmux session instead of the current one |
| `--config PATH` | tmuxp config to update (default `~/.config/tmux/tmux_init.yaml`) |
| `--exclude-window NAME` | Leave a window out of the config (repeatable) |
| `--keep-rc` | Keep `--rc` / `--remote-control` on Claude commands |
| `--no-backup` | Do not back up the previous config |
| `--no-validate` | Skip the tmuxp schema check |

## Workflow for Claude

1. Run with `--dry-run` and show the user the status table.
2. If the output has **Warnings**, **Review** items, or **removed** windows, list them and ask before writing. Typical decisions:
   - A window whose pane 1 is not Claude (`claude-research` types `/sc:load` into pane 1 of every window): keep it, or drop it with `--exclude-window`.
   - A command under "Review" runs again on every load (`make deploy`, a long training job): keep it, or drop the window.
   - A removed window was closed on purpose, or by accident.
3. Otherwise, write without asking: the user asked for the update, and the old file is backed up.
4. Report what changed, the backup path, and how to restore:
   - `claude-research` when the session is gone (after a reboot or `tmux kill-server`). `claude-research -k` kills the running session first, including the Claude instance running this skill, so the user should run it themselves.
   - `tmuxp load ~/.config/tmux/tmux_init.yaml` without the launcher.

## Important Notes

- **What is restored**: windows and their order, names, pane splits (preset or exact sizes), working directories, the active pane of each multi-pane window, and the command each pane was running.
- **What is not restored**: Claude Code conversations (each Claude pane starts a new conversation; `claude-research` then sends `/sc:load`), scrollback, shell history, the state inside running programs, the active window, and zoom.
- A command is captured from the process itself, so it runs again on load exactly as it was started. That is why the Review list exists.
- The config may be a symlink into a dotfiles repo (`~/.config/tmux/tmux_init.yaml` → `~/Documents/MyConfig/tmux/tmux_init.yaml`). The link's target is replaced atomically and the link stays.
- Backups go to `$XDG_STATE_HOME/snapshot-tmux/` (default `~/.local/state/snapshot-tmux/`), outside the dotfiles repo, and the newest 10 are kept.
- tmuxp validation runs under tmuxp's own interpreter (found from the `tmuxp` shebang). If tmuxp rejects the result, nothing is written. If tmuxp is not installed, the check is skipped and said so.
- Window-level or pane-level keys the snapshot cannot observe (`options`, `shell_command_before`, `environment`, ...) survive only in windows that stay unchanged. When such a window is regenerated, the run lists the keys it dropped.
