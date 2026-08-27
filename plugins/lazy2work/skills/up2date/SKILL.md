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
- `brew upgrade --cask --greedy` (upgrade casks, including auto-updating ones)
- `brew cleanup --prune=all` (clean cache)
- `brew autoremove` (drop orphaned dependencies)
- **Caskroom `.pkg` sweep** — `brew cleanup` does *not* remove the installer a
  pkg-based cask keeps beside its installed version, so those are deleted here
- Outputs before/after comparison summary

### Skills/Plugins Only

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/up2date.py --skill
```

- `~/.claude/skills/` user skill list and registration status
- **Global agent skills** → `npx skills@latest update -g -y` updates every globally
  installed skill (e.g. mattpocock/skills under `~/.agents/skills/`), then
  **removes skills deleted upstream** that the non-interactive updater only warns
  about (parsed from its "deleted upstream" output → `npx skills remove <names> -g -y`)
- `~/.claude/plugins/` plugin status and marketplace currency. Staleness is
  *detected* from git (`N commits behind`), but the update itself is delegated to
  Claude Code's own CLI: `claude plugin marketplace update <name>`, then
  `claude plugin update <plugin> --scope <scope> --yes` for each installed plugin
  from a stale marketplace
- **Plugin skill inventory** — skills are enumerated from each installed plugin's
  `installPath`, checking `skills/` first and falling back to `.claude/skills/`
  for plugins that nest them there. An install with neither is listed under a
  "Skipped … no skills dir" line instead of vanishing from the count
- `~/.claude/commands/sc/` SuperClaude command list → `superclaude update`

Add `--no-skill-prune` to update global skills **without** removing the dead ones:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/up2date.py --skill --no-skill-prune
```

## Notes

- If no flag is given, both `--brew` and `--skill` run in sequence
- Plugin updates go through the official `claude plugin` CLI — the script never
  writes `installed_plugins.json` or the plugin cache itself. Claude Code owns
  that layout; hand-editing it drifts the moment the schema changes
- `--scope` is taken from the plugin's own recorded scope (`user` by default),
  so a user-scope install stays user-scope
- `--yes` is **required**, not cosmetic: the CLI demands it whenever stdin or
  stdout is not a TTY, which is always true here
- Updated plugins land in the cache but do **not** affect the running session —
  Claude Code must be restarted to load them
- Plugin updates are skipped with a notice if the `claude` executable is absent
- SuperClaude updates use `superclaude update`
- User skills (`~/.claude/skills/`) are manually managed; only status checks are performed
- The plugin skill scan covers two layouts, in order: `<installPath>/skills/`
  (most plugins) and `<installPath>/.claude/skills/` (e.g. `ui-ux-pro-max`).
  Only the first match is read, so a plugin shipping both is not double-counted
- Global agent-skill update needs `npx` (Node.js 18+); it is skipped with a notice if `npx` is absent
- Dead-skill pruning is **on by default** with `--skill`; pass `--no-skill-prune` to keep them
- `brew upgrade --cask --greedy` upgrades all casks including those with `auto_updates=true`
- `brew cleanup --prune=all` removes cached downloads, but **not** Caskroom
  `.pkg` installers — Homebrew treats those as live data belonging to the
  installed version. Measured on a real machine, `cleanup` freed 629 B while
  10.2 GB of `.pkg` sat in the Caskroom. The sweep removes only `*.pkg` under
  the Caskroom tree; the app itself is already installed and the pkg is
  re-downloaded on demand
- Summarize script output and report to the user
