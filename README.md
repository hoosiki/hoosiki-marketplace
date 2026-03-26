# hoosiki-marketplace

> Curated Claude Code plugins by Junsang Park — productivity tools, MCP installers, and workflow automation.

[![Version](https://img.shields.io/badge/version-1.12.0-green.svg)](https://github.com/hoosiki/hoosiki-marketplace)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](plugins/lazy2work/LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![C++](https://img.shields.io/badge/C++-20-00599C.svg?logo=cplusplus&logoColor=white)](https://isocpp.org)
[![Claude Code](https://img.shields.io/badge/Claude_Code-Plugin-blueviolet.svg)](https://claude.ai)

## Quick Start

```bash
# 1. Add the marketplace
/plugin marketplace add hoosiki/hoosiki-marketplace

# 2. Install a plugin
/plugin install lazy2work@hoosiki-marketplace
```

Or install directly via CLI:

```bash
claude plugin marketplace add hoosiki/hoosiki-marketplace
claude plugin install lazy2work@hoosiki-marketplace
```

## Available Plugins

| Plugin | Version | Description |
|--------|---------|-------------|
| [**lazy2work**](plugins/lazy2work/) | 1.12.0 | One-command SuperClaude environment setup — MCP server installers, webhook notification hooks, and productivity skills |

---

## lazy2work

> One plugin to set up your entire SuperClaude environment — MCP servers, webhook hooks, and productivity skills.

### Prerequisites

- [Claude Code](https://claude.ai) 1.0.33+
- [SuperClaude](https://github.com/SuperClaude-Org/SuperClaude_Framework.git)
- Python 3.10+ (for skills scripts and webhook hooks)
- Node.js 18+ (for MCP setup commands that use `npx`)

### Skills (6)

| Skill | Command | Description |
|-------|---------|-------------|
| **up2date** | `/lazy2work:up2date` | Unified updater — checks and updates Homebrew packages, Claude Code skills/plugins, and SuperClaude commands in one go (`--brew` for Homebrew only, `--skill` for skills only) |
| **analyze-arxiv** | `/lazy2work:analyze-arxiv` | Study arXiv papers — fetches paper content, generates structured summaries, and creates prerequisite knowledge documents for deeper understanding |
| **constitution-generator** | `/lazy2work:constitution-generator` | Generate optimized `/speckit.constitution` prompts — gathers project info (tech stack, architecture, conventions), detects brownfield patterns, and outputs a verifiable constitution with validation checklist |
| **generate-optimized-spec-kit-prompt** | `/lazy2work:generate-optimized-spec-kit-prompt` | Generate complete Spec Kit prompts (specify/plan/tasks/implement) for all features — splits project into 1-5 day features, generates 4-stage prompts per feature, outputs grouped into files of 5 features each |
| **pyright-setup** | `/lazy2work:pyright-setup` | Auto-configure Pyright for Python projects — detects Python version from venv, adds `[tool.pyright]` to pyproject.toml, resolves "Import could not be resolved" LSP errors in Neovim/VS Code |
| **apply-all-sc-save** | `/lazy2work:apply-all-sc-save` | Broadcast `/sc:save` to all Claude Code panes in the current tmux session — auto-detects Claude panes, excludes self, supports `--dry-run`, `--all-sessions`, and custom commands |

<details>
<summary><strong>up2date — Usage Examples</strong></summary>

**Run all updates (Homebrew + Skills/Plugins + SuperClaude):**

```
/lazy2work:up2date
```

**Homebrew only:**

```
/lazy2work:up2date --brew
```

**Skills/Plugins only:**

```
/lazy2work:up2date --skill
```

Expected output:

```
============================================================
  up2date  (2026-03-14 15:30:00)
============================================================

============================================================
  Homebrew Package Check
============================================================

  Homebrew: Homebrew 4.5.0
  Installed Formulae: 142
  Installed Casks:    38
  Total:              180

============================================================
  Updatable Packages
============================================================

  Formulae (2):
    - node 22.1.0 < 22.2.0
    - python@3.12 3.12.3 < 3.12.4

  Casks: all up to date
  Updates needed: 2

  ...

============================================================
  User Skills
============================================================

  [Registered] analyze-arxiv
    Path: /Users/you/.claude/skills/analyze-arxiv
    Description: Analyze arXiv papers by fetching HTML content
    Resources: references

  [Registered] up2date
    Path: /Users/you/.claude/skills/up2date
    Description: Unified update skill for Homebrew packages
    Resources: scripts, references

============================================================
  Plugins
============================================================

  Installed plugins: 1

    lazy2work@hoosiki-marketplace
      Version: a1b2c3d
      Scope: user
      Installed: 2026-03-14

  Marketplaces: all up to date

============================================================
  SuperClaude
============================================================

  Status: Installed
  Commands: 28

============================================================
  Update Complete
============================================================
```

</details>

<details>
<summary><strong>analyze-arxiv — Usage Examples</strong></summary>

**Analyze a paper by URL:**

```
/lazy2work:analyze-arxiv https://arxiv.org/abs/2301.12345
```

**Analyze by arXiv ID:**

```
/lazy2work:analyze-arxiv 2401.04088
```

**Analyze with a prompt (Korean/English both work):**

```
/lazy2work:analyze-arxiv https://arxiv.org/abs/2005.14165 이 논문 분석해줘
```

Workflow:

1. Extracts arXiv ID → fetches full paper from ar5iv HTML
2. Reads all sections (Abstract, Method, Experiments, Results, ...)
3. Generates **summary document** with:
   - Problem Statement, Key Contribution, Methodology
   - Experiments (datasets, baselines, metrics)
   - Results (reproduced tables with concrete numbers)
   - Limitations and future directions
4. Identifies **3-7 prerequisite concepts** and researches each
5. Generates **prerequisite knowledge document**

Output files:

```
papers/
├── summary/
│   └── LLM/
│       └── 20260314/
│           └── attention_is_all_you_need_20260314.md    ← 150-200+ lines
└── prerequisite/
    └── LLM/
        └── 20260314/
            └── research_attention_is_all_you_20260314.md
```

Final report example:

```
Documents generated:
  1. papers/summary/LLM/20260314/attention_is_all_you_need_20260314.md
  2. papers/prerequisite/LLM/20260314/research_attention_is_all_you_20260314.md

Key points:
  - Proposes the Transformer architecture based entirely on attention mechanisms
  - Achieves 28.4 BLEU on WMT 2014 EN-DE, outperforming all prior models
  - Reduces training cost to 1/4 of previous SOTA while improving quality

Prerequisites covered:
  - Self-Attention / Scaled Dot-Product Attention
  - Multi-Head Attention
  - Positional Encoding
  - Sequence-to-Sequence Models
  - BLEU Score
```

</details>

<details>
<summary><strong>constitution-generator — Usage Examples</strong></summary>

**Generate a constitution for a new project:**

```
/lazy2work:constitution-generator Django 6.x + Celery + HTMX project
```

**Brownfield project (auto-detects existing patterns):**

```
/lazy2work:constitution-generator analyze this existing codebase
```

Workflow:

1. Gathers project info (name, tech stack, project type)
2. For brownfield: reads project structure and detects conventions
3. Generates a complete `/speckit.constitution` prompt with:
   - Tech Stack (locked with versions)
   - Architecture Principles
   - Coding Conventions
   - Testing Requirements
   - Security Principles
   - Prohibitions (minimum 3 items)
   - Deployment Target
4. Validates against anti-patterns (vague rules, missing versions, etc.)

Output: A ready-to-use `/speckit.constitution` prompt text. Every rule is verifiable — no vague guidelines like "write good code."

Validation checklist:

```
| Check                                          | Pass? |
|------------------------------------------------|-------|
| All rules are verifiable                       |  ✅   |
| Tech stack has specific versions               |  ✅   |
| Prohibitions section exists and is non-empty   |  ✅   |
| No feature requirements (belongs in /specify)  |  ✅   |
| No implementation details (belongs in /plan)   |  ✅   |
| Each section has 3-7 rules                     |  ✅   |
```

</details>

<details>
<summary><strong>generate-optimized-spec-kit-prompt — Usage Examples</strong></summary>

**Generate Spec Kit prompts from a constitution file:**

```
/lazy2work:generate-optimized-spec-kit-prompt @path/to/speckit.constitution
```

**Generate from a PRD or project description:**

```
/lazy2work:generate-optimized-spec-kit-prompt @path/to/project-description.md
```

Workflow:

1. Reads project information from the provided file
2. Decomposes into features (1-5 day units, independently testable)
3. Generates 4 optimized prompts per feature:
   - `/speckit.specify` — What + Why (tech-neutral, ends with "What questions do you have?")
   - `/speckit.plan` — How (tech stack, architecture, file refs, exclusions)
   - `/speckit.tasks` — Order (sequence, deps, `[NEW]`/`[MODIFY]`/`[TEST]` tags, 1 task = 1 commit)
   - `/speckit.implement` — Rules (scope `--tasks N-M`, commit strategy, failure behavior)
4. Writes output to `claudedocs/speckit/{date}/` grouped 5 features per file

Output structure:

```
claudedocs/speckit/20260324/
├── features_01-05_20260324.md
├── features_06-10_20260324.md
└── features_11-12_20260324.md
```

Each prompt follows strict stage separation — specify never mentions tech, plan never repeats features, tasks never makes tech decisions, implement never changes design.

</details>

<details>
<summary><strong>pyright-setup — Usage Examples</strong></summary>

**Auto-configure pyright for current project:**

```
/lazy2work:pyright-setup
```

**Configure for a specific project path:**

```
/lazy2work:pyright-setup /path/to/project
```

What it does:

1. Detects Python version (priority: `.venv` interpreter → `requires-python` in pyproject.toml → system python3)
2. Detects virtual environment directory (`.venv`, `venv`, `.env`, `env`)
3. Adds `[tool.pyright]` section to `pyproject.toml`
4. Skips if `[tool.pyright]` already exists
5. Inserts before `[tool.mypy]` if present, otherwise appends

Generated config:

```toml
# ==== pyright ====

[tool.pyright]
venvPath = "."
venv = ".venv"
pythonVersion = "3.13"
```

Fixes common issues:
- "Import X could not be resolved" in Neovim (basedpyright) or VS Code (pylance)
- Pyright not finding packages installed in virtual environment
- Wrong Python version detection by LSP

</details>

<details>
<summary><strong>apply-all-sc-save — Usage Examples</strong></summary>

**Save all Claude sessions in current tmux session:**

```
/lazy2work:apply-all-sc-save
```

**Preview which panes would receive the command:**

```
/lazy2work:apply-all-sc-save --dry-run
```

**Target all tmux sessions:**

```
/lazy2work:apply-all-sc-save --all-sessions
```

**Send a custom command instead:**

```
/lazy2work:apply-all-sc-save --command "/help"
```

Workflow:

1. Detects current tmux session and own pane ID (`$TMUX_PANE`)
2. Scans all panes for `pane_current_command == "claude"`
3. Excludes the current pane (self) to avoid recursive invocation
4. Sends `/sc:save` + Enter to each discovered Claude pane via `tmux send-keys`
5. Reports how many panes received the command

Example output:

```
Scanning session 'claude-research' for Claude panes (excluding self: %3)...
Found 2 Claude pane(s):
  sent '/sc:save' to claude-research:1.1
  sent '/sc:save' to claude-research:2.1
Done.
```

Notes:
- Target Claude instances must be in an **idle state** (waiting for user input)
- If Claude is mid-execution, keys are buffered and execute when idle
- Requires tmux to be running

</details>

### Setup Commands (7)

One-command MCP server installers accessible via `/lazy2work:setup:*`:

| Command | Description | Requires |
|---------|-------------|----------|
| `install-tavily-mcp` | Install [Tavily MCP](https://tavily.com) for web search/research | `TAVILY_API_KEY` |
| `install-serena-mcp` | Install [Serena MCP](https://github.com/oraios/serena) for semantic code intelligence | `uv` |
| `install-context7-mcp` | Install [Context7 MCP](https://github.com/upstash/context7) for library docs lookup | `npx` |
| `install-sequential-thinking-mcp` | Install Sequential Thinking MCP for structured reasoning | `npx` |
| `install-morph-mcp` | Install [Morph MCP](https://morphllm.com) for fast file editing | `MORPH_API_KEY` |
| `install-morph-fast-apply` | Install Morph Fast Apply MCP for bulk code transformations | `MORPH_API_KEY` |
| `install-tavily-skill` | Install [Tavily Skills](https://github.com/tavily-ai/skills) pack | `npx` |

#### API Key Setup

Some MCP servers require API keys. Add these to your shell profile (`~/.zshrc` or `~/.bashrc`) so they persist across sessions:

```bash
# ~/.zshrc or ~/.bashrc

# Tavily — https://app.tavily.com/home (sign up for a free API key)
export TAVILY_API_KEY="tvly-xxxxxxxxxxxxxxxxxxxxx"

# Morph — https://morphllm.com (sign up and generate an API key)
export MORPH_API_KEY="morph-xxxxxxxxxxxxxxxxxxxxx"
```

After editing, apply the changes:

```bash
# For zsh (default on macOS)
source ~/.zshrc

# For bash
source ~/.bashrc
```

### Hooks (3)

Pre-configured hooks triggered on Claude Code lifecycle events:

| Hook | Event | Description |
|------|-------|-------------|
| `log_prompt` | `UserPromptSubmit` | Logs every prompt with session/system/git metadata to an external API |
| `notify_waiting` | `Notification` | Sends "Waiting for you!" when Claude needs user input |
| `notify_stop` | `Stop` | Sends "Task completed!" when a task finishes |

### Prompt Logging Configuration

The `log_prompt` hook sends prompt metadata to an external API on every `UserPromptSubmit` event. Both environment variables must be set; without either, the hook silently skips.

| Variable | Required | Description |
|----------|----------|-------------|
| `CLAUDE_PROMPT_LOG_URL` | Yes | Logging API endpoint URL |
| `CLAUDE_PROMPT_LOG_API_KEY` | Yes | Bearer token for API authentication |

```bash
# ~/.zshrc or ~/.bashrc
export CLAUDE_PROMPT_LOG_URL="https://agents.maic.co.kr/api/logging/prompts/"
export CLAUDE_PROMPT_LOG_API_KEY="your-api-key-here"
```

<details>
<summary><strong>Collected metadata fields</strong></summary>

| Category | Fields |
|----------|--------|
| **Hook input** | `prompt`, `session_id`, `cwd`, `permission_mode`, `hook_event_name`, `transcript_path` |
| **Claude Code env** | `project_dir`, `user_email`, `account_uuid`, `organization_uuid`, `team_name`, `model`, `is_remote` |
| **System** | `hostname`, `os_system`, `os_release`, `os_machine`, `system_user` |
| **Git** | `git_branch`, `git_remote`, `git_commit` |
| **Timestamps** | `timestamp` (UTC), `local_timestamp` |

</details>

### Webhook Configuration

Hooks require environment variables to be set. Without them, hooks silently skip.

| Variable | Required | Description |
|----------|----------|-------------|
| `CLAUDE_WEBHOOK_URL` | Yes | Webhook endpoint URL |
| `CLAUDE_WEBHOOK_TOKEN` | No | Auth token |
| `CLAUDE_WEBHOOK_FORMAT` | No | Payload format (default: `generic`) |

Add these to your shell profile (`~/.zshrc` or `~/.bashrc`) so they persist across sessions:

```bash
# ~/.zshrc or ~/.bashrc

# Webhook endpoint URL (required — without this, hooks silently skip)
export CLAUDE_WEBHOOK_URL="https://hooks.slack.com/services/T00/B00/xxx"

# Auth token (optional)
export CLAUDE_WEBHOOK_TOKEN="your-token-here"

# Payload format: generic, slack, discord, or synology (optional, default: generic)
export CLAUDE_WEBHOOK_FORMAT="slack"
```

After editing, apply the changes:

```bash
source ~/.zshrc   # or source ~/.bashrc
```

#### Supported Formats

| Format | Service | Token Handling |
|--------|---------|----------------|
| `generic` | Any webhook endpoint | `Authorization: Bearer <token>` header |
| `slack` | Slack Incoming Webhooks | `Authorization: Bearer <token>` header |
| `discord` | Discord Webhooks | `Authorization: Bearer <token>` header |
| `synology` | Synology Chat | Sent as `token=<value>` in POST body |

<details>
<summary><strong>Configuration Examples</strong></summary>

**Slack:**
```bash
export CLAUDE_WEBHOOK_URL="https://hooks.slack.com/services/T00/B00/xxx"
export CLAUDE_WEBHOOK_FORMAT="slack"
```

**Discord:**
```bash
export CLAUDE_WEBHOOK_URL="https://discord.com/api/webhooks/123/abc"
export CLAUDE_WEBHOOK_FORMAT="discord"
```

**Synology Chat:**
```bash
export CLAUDE_WEBHOOK_URL="https://your-nas.synology.me:5001/webapi/entry.cgi?api=SYNO.Chat.External&method=incoming&version=2"
export CLAUDE_WEBHOOK_TOKEN="your-token-here"
export CLAUDE_WEBHOOK_FORMAT="synology"
```

</details>

## Coding Rules

Language-specific coding rules bundled inside the plugin and distributed on install. Each rule file includes path-based frontmatter so it only activates for matching file types.

```
plugins/lazy2work/rules/             ← Source of truth (distributed with plugin)
├── python/                          # **/*.py, **/*.pyi
│   ├── tdd.md                       # TDD workflow (Red-Green-Refactor, pytest)
│   ├── style.md                     # PEP 8 + ruff, Google style docstrings with Examples
│   └── typing.md                    # Gradual typing (pyright + ruff, Protocol, TypeGuard)
├── cpp/                             # **/*.cpp, **/*.cc, **/*.h, **/*.hpp
│   ├── style.md                     # Google C++ Style Guide, C++20, const correctness
│   ├── testing.md                   # Google Test TDD, GMock, parameterized/typed/death tests
│   ├── build.md                     # CMake 3.20+, presets, sanitizers, clang-tidy
│   └── memory-safety.md            # RAII, smart pointers, std::expected, concurrency safety
├── js/                              # **/*.js, **/*.mjs
│   └── django-vanilla-js.md        # ES modules, CSRF fetch, event delegation, JSDoc
└── html/                            # **/*.html, **/templates/**
    └── django-template.md           # Django templates, HTMX, Tailwind CSS, accessibility

.claude/rules/                       ← Symlinks (auto-loaded by Claude Code)
├── python → ../../plugins/lazy2work/rules/python
├── cpp    → ../../plugins/lazy2work/rules/cpp
├── js     → ../../plugins/lazy2work/rules/js
└── html   → ../../plugins/lazy2work/rules/html
```

### Using Rules in Other Projects

After installing the plugin, create symlinks from the cached rules to your project:

```bash
# Find the plugin cache path
RULES_SRC=~/.claude/plugins/cache/hoosiki-marketplace/lazy2work/1.4.0/rules

# Symlink into your project
mkdir -p .claude/rules
ln -s $RULES_SRC/python .claude/rules/python
ln -s $RULES_SRC/cpp    .claude/rules/cpp
ln -s $RULES_SRC/js     .claude/rules/js
ln -s $RULES_SRC/html   .claude/rules/html
```

Or apply globally (all projects):

```bash
ln -s $RULES_SRC/python ~/.claude/rules/python
```

## Repository Structure

```
hoosiki-marketplace/
├── .claude/
│   └── rules/                          ← symlinks to plugin rules
│       ├── python → ../../plugins/lazy2work/rules/python
│       ├── cpp    → ../../plugins/lazy2work/rules/cpp
│       ├── js     → ../../plugins/lazy2work/rules/js
│       └── html   → ../../plugins/lazy2work/rules/html
├── .claude-plugin/
│   └── marketplace.json                ← marketplace manifest
├── plugins/
│   └── lazy2work/
│       ├── .claude-plugin/
│       │   └── plugin.json             ← plugin manifest
│       ├── skills/
│       │   ├── analyze-arxiv/
│       │   │   ├── SKILL.md
│       │   │   └── references/
│       │   ├── constitution-generator/
│       │   │   ├── SKILL.md
│       │   │   └── references/
│       │   ├── generate-optimized-spec-kit-prompt/
│       │   │   ├── SKILL.md
│       │   │   └── references/
│       │   ├── pyright-setup/
│       │   │   ├── SKILL.md
│       │   │   └── scripts/
│       │   ├── apply-all-sc-save/
│       │   │   ├── SKILL.md
│       │   │   └── scripts/
│       │   └── up2date/
│       │       ├── SKILL.md
│       │       ├── scripts/
│       │       └── references/
│       ├── commands/
│       │   └── setup/
│       │       └── (7 MCP install commands)
│       ├── hooks/
│       │   └── hooks.json
│       ├── rules/                      ← coding rules (distributed with plugin)
│       │   ├── python/
│       │   ├── cpp/
│       │   ├── js/
│       │   └── html/
│       ├── scripts/
│       │   ├── webhook.py
│       │   ├── log_prompt.py
│       │   ├── notify_stop.py
│       │   └── notify_waiting.py
│       └── LICENSE
├── tests/
│   └── test_log_prompt.py
└── README.md
```

## Adding More Plugins

To add a new plugin to this marketplace, create a directory under `plugins/` with the standard Claude Code plugin structure, then add an entry to `.claude-plugin/marketplace.json`:

```json
{
  "name": "your-plugin",
  "source": "./your-plugin",
  "description": "What your plugin does",
  "version": "1.0.0",
  "category": "utilities"
}
```

## Changelog

### v1.12.0 (2026-03-26)

- **up2date: code quality improvements** — added subprocess timeout protection (brew=300s, git=60s) to prevent infinite hangs, atomic writes for `installed_plugins.json` via `tempfile` + `os.replace()`, and consolidated repeated file reads into `_read_installed_plugins()` / `_write_installed_plugins()` helpers
- **up2date: Google style docstrings** — all 22 functions now have complete docstrings with Args, Returns, Raises, and Examples sections per project Python style rules
- **up2date: test suite** — added `tests/test_up2date.py` with 35 tests covering `run()`, `get_installed()`, `get_outdated()`, `_read_installed_plugins()`, `_write_installed_plugins()`, `_is_skill_registered()`, `_find_plugin_source()`, `update_marketplace()`, `update_plugin_cache()`, `_print_skill_info()`, and `check_superclaude()`
- **Version bump**: 1.11.0 → 1.12.0

### v1.11.0 (2026-03-26)

- **up2date: greedy cask upgrades** — `brew upgrade --cask` now uses `--greedy` flag to upgrade all casks including those with `auto_updates=true` (e.g. Docker Desktop, CLion, Claude). `brew outdated --cask` also uses `--greedy` for accurate detection
- **up2date: reliable marketplace update detection** — replaced `git fetch --dry-run` with real `git fetch` so remote refs are always current. Added automatic remote branch detection (main/master) for correct behind-count comparison
- **up2date: SHA-aware cache refresh** — `update_plugin_cache()` now compares both version and git SHA. Same version with different SHA triggers cache re-sync instead of falsely reporting "Already up to date"
- **up2date: root-source marketplace layout** — new `_find_plugin_source()` supports marketplaces where `marketplace.json` defines `source: "./"` (e.g. anthropic-agent-skills). Fixes "Plugin source not found" errors for non-standard marketplace layouts
- **Version bump**: 1.10.0 → 1.11.0

### v1.10.0 (2026-03-25)

- **New skill: apply-all-sc-save** — broadcasts `/sc:save` to all Claude Code panes in the current tmux session. Auto-detects Claude panes via `pane_current_command`, excludes self, supports `--dry-run`, `--all-sessions`, and custom commands via `--command`
- **Version bump**: 1.9.0 → 1.10.0

### v1.9.0 (2026-03-24)

- **New skill: pyright-setup** — auto-configures Pyright for Python projects by detecting Python version from venv and adding `[tool.pyright]` to pyproject.toml. Fixes "Import could not be resolved" LSP errors in Neovim/VS Code
- **Version bump**: 1.8.0 → 1.9.0

### v1.8.0 (2026-03-24)

- **generate-optimized-spec-kit-prompt: speckit command format** — updated all prompts to use official Spec Kit command syntax (`/speckit.specify`, `/speckit.plan`, `/speckit.tasks`, `/speckit.implement`) instead of bare `/specify`, `/plan`, `/tasks`, `/implement`
- **Version bump**: 1.7.0 → 1.8.0

### v1.7.0 (2026-03-24)

- **New skill: generate-optimized-spec-kit-prompt** — generates complete Spec Kit prompts (specify/plan/tasks/implement) for all project features. Splits project into 1-5 day features, enforces strict 4-stage separation, outputs grouped 5 features per file
- **Version bump**: 1.6.0 → 1.7.0

### v1.6.0 (2026-03-24)

- **up2date: plugin skill detection** — `--skill` now scans and displays skills installed via plugin marketplaces (from `~/.claude/plugins/cache/`), grouped by plugin with version info
- **up2date: improved cache refresh** — `update_plugin_cache()` now finds plugin source under `plugins/{name}/` layout, reads version from `plugin.json`, and copies all plugin contents (skills, hooks, commands, rules)
- **up2date: symlink support** — user skills in `~/.claude/skills/` that are symlinks are now properly resolved and displayed
- **Version bump**: 1.5.0 → 1.6.0

### v1.5.0 (2026-03-24)

- **New skill: constitution-generator** — generates optimized `/speckit.constitution` prompts from project information. Supports greenfield and brownfield projects with automatic convention detection, verifiable rules, and validation checklist
- **English translation**: Converted all constitution-generator skill files from Korean to English
- **Version bump**: 1.4.0 → 1.5.0

### v1.4.0 (2026-03-23)

- **Rules distribution**: Moved all coding rules into `plugins/lazy2work/rules/` so they are distributed when the plugin is installed. `.claude/rules/` now uses symlinks pointing to the plugin directory
- **Symlink guide**: Added instructions in README for symlinking rules into other projects from the plugin cache
- **Version bump**: 1.3.0 → 1.4.0

### v1.3.0 (2026-03-23)

- **JS rules**: Added Vanilla JavaScript rules for Django + Tailwind CSS stack — ES modules, CSRF fetch wrapper, event delegation with `data-*` attributes, XSS prevention, Tailwind class management, JSDoc with `@example`
- **HTML rules**: Added Django Template + HTMX rules — template inheritance, HTMX partials/OOB swaps, Tailwind CSS integration, semantic HTML, accessibility (ARIA), security (`json_script`, auto-escape)
- **Path frontmatter**: All rule files now include YAML `paths:` frontmatter for automatic file-type scoping (Python: `*.py`/`*.pyi`, C++: `*.cpp`/`*.h`/`*.hpp`, JS: `*.js`/`*.mjs`, HTML: `*.html`/`templates/**`)
- **Version bump**: 1.2.0 → 1.3.0

### v1.2.0 (2026-03-23)

- **Coding rules**: Added language-specific rules under `.claude/rules/` (Python: TDD, style, typing; C++: style, testing, build, memory-safety)
- **Python rules**: Google style docstrings with Examples required on all functions, gradual typing with pyright + ruff, PEP 8 enforcement via ruff `D` rules
- **C++ rules**: Google C++ Style Guide with C++20 features (concepts, ranges, `std::expected`), Google Test TDD with GMock/parameterized/typed/death tests, CMake presets with sanitizer integration, RAII/smart pointer memory safety with concurrency guidelines
- **Version bump**: 1.1.0 → 1.2.0

### v1.1.0 (2026-03-17)

- **Prompt logging**: Added `UserPromptSubmit` hook for logging prompts with session/system/git metadata to external APIs
- **Python TDD**: Added TDD rules for test-driven development workflow

### v1.0.0 (2026-03-14)

- Initial release with lazy2work plugin
- Skills: up2date, analyze-arxiv
- Setup commands: 7 MCP server installers
- Hooks: webhook notifications (notify_waiting, notify_stop)

## License

Each plugin includes its own license. See individual plugin directories for details.
