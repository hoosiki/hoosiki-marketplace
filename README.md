# hoosiki-marketplace

> Curated Claude Code plugins by Junsang Park — productivity tools, MCP installers, and workflow automation.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](plugins/lazy2work/LICENSE)

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
| [**lazy2work**](plugins/lazy2work/) | 1.0.0 | One-command SuperClaude environment setup — MCP server installers, webhook notification hooks, and productivity skills |

---

## lazy2work

> One plugin to set up your entire SuperClaude environment — MCP servers, webhook hooks, and productivity skills.

### Prerequisites

- [Claude Code](https://claude.ai) 1.0.33+
- [SuperClaude](https://github.com/SuperClaude-Org/SuperClaude_Framework.git)
- Python 3.10+ (for skills scripts and webhook hooks)
- Node.js 18+ (for MCP setup commands that use `npx`)

### Skills (2)

| Skill | Command | Description |
|-------|---------|-------------|
| **up2date** | `/lazy2work:up2date` | Unified updater — checks and updates Homebrew packages, Claude Code skills/plugins, and SuperClaude commands in one go (`--brew` for Homebrew only, `--skill` for skills only) |
| **analyze-arxiv** | `/lazy2work:analyze-arxiv` | Study arXiv papers — fetches paper content, generates structured summaries, and creates prerequisite knowledge documents for deeper understanding |

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

### Hooks (2)

Pre-configured webhook notifications triggered on Claude Code lifecycle events:

| Hook | Event | Message |
|------|-------|---------|
| `notify_waiting` | `Notification` | Sends "Waiting for you!" when Claude needs user input |
| `notify_stop` | `Stop` | Sends "Task completed!" when a task finishes |

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

## Repository Structure

```
hoosiki-marketplace/
├── .claude-plugin/
│   └── marketplace.json            ← marketplace manifest
├── plugins/
│   └── lazy2work/
│       ├── .claude-plugin/
│       │   └── plugin.json         ← plugin manifest
│       ├── skills/
│       │   ├── analyze-arxiv/
│       │   │   ├── SKILL.md
│       │   │   └── references/
│       │   └── up2date/
│       │       ├── SKILL.md
│       │       ├── scripts/
│       │       └── references/
│       ├── commands/
│       │   └── setup/
│       │       └── (7 MCP install commands)
│       ├── hooks/
│       │   └── hooks.json
│       ├── scripts/
│       │   ├── webhook.py
│       │   ├── notify_stop.py
│       │   ├── notify_waiting.py
│       │   └── .env.example
│       └── LICENSE
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

## License

Each plugin includes its own license. See individual plugin directories for details.
