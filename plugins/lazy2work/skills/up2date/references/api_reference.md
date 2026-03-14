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
| `brew upgrade --cask` | Upgrade all casks |
| `brew cleanup --prune=all` | Remove all cached downloads |

## Claude Code Paths

| Path | Purpose |
|------|---------|
| `~/.claude/skills/` | User-defined skills |
| `~/.claude/plugins/` | Installed plugins and marketplaces |
| `~/.claude/plugins/installed_plugins.json` | Plugin registry |
| `~/.claude/plugins/known_marketplaces.json` | Marketplace registry |
| `~/.claude/commands/sc/` | SuperClaude commands |
| `~/.claude/settings.json` | Skill registration check |
