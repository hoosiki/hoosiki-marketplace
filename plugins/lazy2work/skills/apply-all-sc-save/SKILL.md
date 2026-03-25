---
name: apply-all-sc-save
description: Send /sc:save command to all Claude Code panes running in the current tmux session. Use when user wants to save all Claude sessions at once, says "save all claude", "sc:save all", "tmux save all", "모든 claude 세션 저장", "전체 세션 save", or wants to broadcast /sc:save across tmux panes. Requires tmux to be running.
---

# apply-all-sc-save

Send `/sc:save` to all Claude Code panes in the current tmux session, excluding the pane executing this skill.

## Behavioral Flow

1. Detect the current tmux session and own pane ID
2. Scan all panes in the session for `pane_current_command == "claude"`
3. Exclude the current pane (self)
4. Send `/sc:save` + Enter to each discovered Claude pane via `tmux send-keys`
5. Report results

## Usage

Run the bundled script:

```bash
python3 scripts/save_all_claude.py
```

### Options

| Flag | Description |
|------|-------------|
| `--dry-run` | Print targets without actually sending commands |
| `--all-sessions` | Target all tmux sessions, not just the current one |
| `--command CMD` | Send a custom command instead of `/sc:save` |

### Examples

```bash
# Default: /sc:save to all Claude panes in current session
python3 scripts/save_all_claude.py

# Preview which panes would receive the command
python3 scripts/save_all_claude.py --dry-run

# Target all tmux sessions
python3 scripts/save_all_claude.py --all-sessions

# Send a different command
python3 scripts/save_all_claude.py --command "/help"
```

## Important Notes

- The target Claude instance must be in an **idle state** (waiting for user input) to process the command. If Claude is mid-execution, the keys will be buffered and may execute when it becomes idle.
- The script uses `$TMUX_PANE` environment variable to identify self. This is automatically set by tmux.
- Only panes where `pane_current_command` is exactly `claude` are targeted.
