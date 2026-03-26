---
name: up2date
description: Unified update skill for Homebrew packages and Claude Code skills/plugins/SuperClaude.
  Triggers on "update", "brew update", "brew upgrade", "brew manage",
  "package update", "homebrew check", "brew cleanup",
  "skill update", "plugin update", "SuperClaude update",
  "skill check", "full update", "up2date".
---

# up2date

Unified updater for Homebrew packages and Claude Code skills/plugins/SuperClaude commands.

## Workflow

### Run All Updates

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/up2date.py
```

Runs both Homebrew and skill/plugin updates in sequence.

### Homebrew Only

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/up2date.py --brew
```

- Collects installed formulae/casks via `brew list`
- Checks for outdated packages via `brew outdated`
- Runs `brew doctor` for diagnostics
- `brew update` (update Homebrew itself)
- `brew upgrade --formula` (upgrade formulae)
- `brew upgrade --cask` (upgrade casks)
- `brew cleanup --prune=all` (clean cache)
- Outputs before/after comparison summary

### Skills/Plugins Only

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/up2date.py --skill
```

- `~/.claude/skills/` user skill list and registration status
- `~/.claude/plugins/` plugin installation status and marketplace currency → `git pull` marketplaces
- `~/.claude/commands/sc/` SuperClaude command list → `superclaude update`

## Notes

- If no flag is given, both `--brew` and `--skill` run in sequence
- Marketplace updates use `git pull --ff-only` for safety
- SuperClaude updates use `superclaude update`
- User skills (`~/.claude/skills/`) are manually managed; only status checks are performed
- `brew upgrade --cask --greedy` upgrades all casks including those with `auto_updates=true`
- `brew cleanup --prune=all` removes all cached downloads
- Summarize script output and report to the user
