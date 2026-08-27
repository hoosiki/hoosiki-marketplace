# up2date API Reference

## CLI Options

| Flag | Description |
|------|-------------|
| *(none)* | Run all updates (Homebrew + skills/plugins/SuperClaude) |
| `--brew` | Run Homebrew update only |
| `--skill` | Run skill/plugin/SuperClaude update only |

## Homebrew Commands Used

| Command | Purpose |
|---------|---------|
| `brew list --formula` | List installed formulae |
| `brew list --cask` | List installed casks |
| `brew outdated --formula --verbose` | Show updatable formulae with version info |
| `brew outdated --cask --verbose` | Show updatable casks with version info |
| `brew doctor` | Diagnose Homebrew issues |
| `brew update` | Update Homebrew itself |
| `brew upgrade --formula` | Upgrade all formulae |
| `brew upgrade --cask --greedy` | Upgrade all casks, including `auto_updates=true` ones |
| `brew cleanup --prune=all` | Remove cached downloads (**not** Caskroom `.pkg`) |
| `brew autoremove` | Uninstall orphaned dependency-only formulae |
| `brew --prefix` | Locate the Caskroom for the leftover-`.pkg` sweep |

## Claude Code Commands Used

Plugin and marketplace updates are delegated to Claude Code's own CLI rather
than reimplemented. The script only *detects* staleness from git.

| Command | Purpose |
|---------|---------|
| `claude plugin marketplace update <name>` | Refresh one marketplace from its source |
| `claude plugin update <plugin> --scope <scope> --yes` | Update an installed plugin in place |

`--scope` accepts `user` (default), `project`, `local`, or `managed`, and is read
from the plugin's own registry entry. `--yes` is mandatory when stdin/stdout is
not a TTY. Neither command affects the running session — restart Claude Code to
load an updated plugin.

## Claude Code Paths

| Path | Purpose |
|------|---------|
| `~/.claude/skills/` | User-defined skills |
| `~/.claude/plugins/` | Installed plugins and marketplaces |
| `~/.claude/plugins/installed_plugins.json` | Plugin registry (**read-only** — written by the `claude` CLI) |
| `~/.claude/plugins/known_marketplaces.json` | Marketplace registry |
| `~/.claude/commands/sc/` | SuperClaude commands |
| `~/.claude/settings.json` | Skill registration check |
