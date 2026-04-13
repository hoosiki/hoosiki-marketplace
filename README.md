# hoosiki-marketplace

> Curated Claude Code plugins by Junsang Park — productivity tools, MCP installers, and workflow automation.

[![Version](https://img.shields.io/badge/version-1.20.0-green.svg)](https://github.com/hoosiki/hoosiki-marketplace)
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
| [**lazy2work**](plugins/lazy2work/) | 1.20.0 | One-command SuperClaude environment setup — MCP server installers, webhook notification hooks, productivity skills, and Hamilton spec-driven pipelines |

---

## lazy2work

> One plugin to set up your entire SuperClaude environment — MCP servers, webhook hooks, and productivity skills.

### Prerequisites

- [Claude Code](https://claude.ai) 1.0.33+
- [SuperClaude](https://github.com/SuperClaude-Org/SuperClaude_Framework.git)
- Python 3.10+ (for skills scripts and webhook hooks)
- Node.js 18+ (for MCP setup commands that use `npx`)

### Skills (8)

| Skill | Command | Description |
|-------|---------|-------------|
| **up2date** | `/lazy2work:up2date` | Unified updater — checks and updates Homebrew packages, Claude Code skills/plugins, and SuperClaude commands in one go (`--brew` for Homebrew only, `--skill` for skills only) |
| **analyze-arxiv** | `/lazy2work:analyze-arxiv` | Study arXiv papers — fetches paper content, generates structured summaries, and creates prerequisite knowledge documents for deeper understanding |
| **constitution-generator** | `/lazy2work:constitution-generator` | Generate optimized `/speckit.constitution` prompts — gathers project info (tech stack, architecture, conventions), detects brownfield patterns, and outputs a verifiable constitution with validation checklist |
| **generate-optimized-spec-kit-prompt** | `/lazy2work:generate-optimized-spec-kit-prompt` | Generate complete Spec Kit prompts (specify/clarify/plan/tasks/implement/commit) for all features — splits project into 1-5 day features, generates 6-stage prompts per feature with Mermaid diagrams and auto-clarify/auto-commit steps |
| **pyright-setup** | `/lazy2work:pyright-setup` | Auto-configure Pyright for Python projects — detects Python version from venv, adds `[tool.pyright]` to pyproject.toml, resolves "Import could not be resolved" LSP errors in Neovim/VS Code |
| **apply-all-sc-save** | `/lazy2work:apply-all-sc-save` | Broadcast `/sc:save` to all Claude Code panes in the current tmux session — auto-detects Claude panes, excludes self, supports `--dry-run`, `--all-sessions`, and custom commands |
| **fix-mermaid** | `/lazy2work:fix-mermaid` | Fix Mermaid diagram syntax errors in Markdown files — detects reserved word conflicts, Unicode/Langium parser issues, message escaping problems. Bundled Python script for automated lint and auto-fix (`--fix`) |
| **hamilton-harness** | `/lazy2work:hamilton-harness` | Build Hamilton data pipelines through a spec-driven workflow — 4 modes (prompt→YAML, validate, stub+viz, modify), Pydantic schemas, Mermaid/Graphviz/Hamilton rendering, 3 domain examples (ETL/ML/RAG). Self-contained — no plugin-level hooks or rules needed |

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
2. Extracts Mermaid diagrams and classifies them by stage placement
3. Decomposes into features (1-5 day units, independently testable)
4. Generates 6 prompts per feature following strict stage separation
5. Writes output to `.speckit-prompts/` with feature-based folder structure

#### 6-Stage Role Separation

| Stage | Role | Prompt Focus | MUST NOT Include |
|-------|------|-------------|-----------------|
| `/speckit.specify` | **What + Why** | Features, users, scenarios, constraints | Tech stack, architecture, code |
| `/speckit.clarify` | **Refine** | Auto-accept recommended options for spec ambiguities | Manual intervention (auto mode) |
| `/speckit.plan` | **How** | Tech stack, architecture, existing code refs | Feature requirements (in spec) |
| `/speckit.tasks` | **Order** | Impl sequence, deps, TDD, task size | Tech decisions (in plan) |
| `/speckit.implement` | **Rules** | Scope, commit strategy, code style | Design changes (go back to plan) |
| `/sc:git commit` | **Commit** | Create git commit after implementation | Design changes, new features |

#### Mermaid Diagram Classification

Placement test: "Does this diagram remain valid if the tech stack changes?" — Yes → specify, No → plan.

| Diagram Type | Stage | Rationale |
|-------------|-------|-----------|
| User workflow (flowchart, no tech terms) | **specify** | WHAT — user behavior flow |
| User-system sequence (actor ↔ system) | **specify** | WHAT — user scenario visualization |
| Business process flow | **specify** | WHAT — business process |
| System architecture (components, layers) | **plan** | HOW — technical structure |
| API sequence (client ↔ server ↔ DB) | **plan** | HOW — API call chain |
| ERD / data model (erDiagram) | **plan** | HOW — database schema |
| Data flow (service-to-service) | **plan** | HOW — data movement paths |
| State machine (stateDiagram) | **plan** | HOW — entity state transitions |
| Deployment structure (Docker, cloud) | **plan** | HOW — infrastructure |

#### Output Structure

```
.speckit-prompts/
├── feature-001-user-authentication/
│   ├── 01_specify.md
│   ├── 02_clarify.md
│   ├── 03_plan.md
│   ├── 04_tasks.md
│   ├── 05_implement.md
│   └── 06_commit.md
├── feature-002-dashboard/
│   └── ...
└── feature-003-api-endpoints/
    └── ...
```

#### Quality Checklist

Every generated feature is verified against:

| Check | Rule |
|-------|------|
| /speckit.specify has no tech terms | Tech-neutral (survives stack change) |
| /speckit.specify ends with "What questions do you have?" | Always present |
| /speckit.specify has Out of Scope section | Prevents AI scope creep |
| /speckit.specify Mermaid has no tech terms | No Django, PostgreSQL, etc. in nodes |
| /speckit.plan references specific file paths | Not vague "follow patterns" |
| /speckit.plan has architecture + API sequence diagrams | Mermaid with explanation text |
| /speckit.plan has explicit exclusions | Prevents AI adding Docker/CI/CD |
| /speckit.tasks uses `[NEW]`/`[MODIFY]`/`[TEST]` tags | Every task tagged |
| /speckit.tasks has 1 task = 1 commit size | Not too large |
| /speckit.implement uses `--tasks N-M` | Never all tasks at once |
| /speckit.implement has failure behavior | Stop and report on failure |
| Each Mermaid block = one concern | No combined architecture + ERD blocks |
| Success criteria are measurable | "< 1s" not "fast" |

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

<details>
<summary><strong>fix-mermaid — Usage Examples</strong></summary>

**Lint a file (report issues without changing):**

```bash
python3 plugins/lazy2work/skills/fix-mermaid/scripts/fix_mermaid.py docs/PROJECT_ANALYSIS.md
```

**Auto-fix in place:**

```bash
python3 plugins/lazy2work/skills/fix-mermaid/scripts/fix_mermaid.py docs/PROJECT_ANALYSIS.md --fix
```

**Scan an entire directory:**

```bash
python3 plugins/lazy2work/skills/fix-mermaid/scripts/fix_mermaid.py docs/ --fix
```

**JSON output (for CI/scripts):**

```bash
python3 plugins/lazy2work/skills/fix-mermaid/scripts/fix_mermaid.py docs/ --json
```

**Or invoke as a skill in Claude Code:**

```
/lazy2work:fix-mermaid
```

> Just mention "mermaid 오류", "mermaid fix", "diagram broken", or "Syntax error in text mermaid version" in your prompt and the skill will trigger automatically.

What the script detects and fixes:

| Category | Examples |
|----------|---------|
| **Reserved words** | `participant OPT as Optuna` → `participant OPTA as Optuna` (13 reserved words) |
| **Message escaping** | `V-->>C: 200 OK {id}` → `V-->>C: 200 OK #123;id#125;` |
| **Unicode issues** | Smart quotes `""` → `""`, fullwidth CJK `（）` → `()`, invisible chars removed |
| **Typographic dashes** | Em dash `—` → `--`, en dash `–` → `-` |

Example output:

```
Found 5 issue(s):

Block | Line | Rule                 | Before
--------------------------------------------------------------------------------
    1 |    7 | reserved-word        | participant OPT as Optuna
    1 |    9 | message-escape       | CEL->>OPTA: create_study(direction="minimize")
    2 |   19 | message-escape       | C->>V: POST /api/users/{id}/ {name: "test"}
    2 |   20 | message-escape       | V-->>C: 200 OK {status: "ok", data: [1, 2]}
    3 |   27 | fullwidth-cjk        | A["데이터（원본）"] --> B

Run with --fix to apply corrections.
```

Reference documentation: `references/mermaid-v11-syntax.md` covers 18 sections including all diagram types, arrow syntax, Unicode replacement tables, reserved word list, and entity escaping guide.

</details>

<details>
<summary><strong>hamilton-harness — Usage Examples</strong></summary>

**One-time setup (Python deps + Graphviz binary):**

```bash
uv pip install "sf-hamilton[visualization,pandera]" pydantic hypothesis pyyaml jsonschema networkx
brew install graphviz   # macOS
# Ubuntu: sudo apt-get install -y graphviz
```

Verify: `python -c "import hamilton, pydantic, hypothesis; print('ok')"` and `dot -V`.

---

**Target project layout** (full reference: skill's [`LAYOUT.md`](plugins/lazy2work/skills/hamilton-harness/LAYOUT.md)):

```
your-project/
├── CLAUDE.md                          # Project rules; mentions hamilton-harness
└── hamilton_pipeline/                 # All pipeline assets live here
    ├── dag_specs/*.yaml               # Single source of truth (human-edited)
    ├── src/
    │   ├── pipelines/*.py             # Hamilton modules (one per pipeline)
    │   └── schemas.py                 # Generated Pydantic models
    ├── tests/
    │   ├── test_dag_matches_spec.py   # L1 structural equivalence (auto-gen)
    │   └── test_properties/test_*.py  # L3 Hypothesis property tests
    ├── build/                         # gitignored; regenerable
    │   ├── stubs/                     # YAML → Python stubs (F3 output)
    │   ├── dags/{spec,impl,diff}/     # rendered diagrams
    │   ├── reports/                   # pytest + hypothesis reports
    │   └── metrics/                   # session-*.json
    └── runs/{YYYYMMDD}/{feature}/     # Committed; execution artifacts
        ├── input_snapshot.parquet
        ├── output.parquet
        └── hamilton_tracker.json
```

**Guardrails:**

- **`dag_specs/` is human-only** — Claude proposes changes via F4 but writes only after user confirms the diff.
- **`build/` is throwaway** — must regenerate from `dag_specs/` + `src/`; never commit it.
- **`runs/` is the audit trail** — execution artifacts are reproducibility anchors; commit them.
- **`src/schemas.py` is generated** — regenerate through F3 rather than hand-editing.

**Bootstrap a fresh project:**

```bash
mkdir -p hamilton_pipeline/{dag_specs,src/pipelines,tests/test_properties,runs}
touch hamilton_pipeline/src/__init__.py hamilton_pipeline/src/pipelines/__init__.py

cp "$CLAUDE_SKILL_DIR/templates/project-layout/CLAUDE.md.tpl"   CLAUDE.md
cp "$CLAUDE_SKILL_DIR/templates/project-layout/.gitignore.tpl"  .gitignore
cp "$CLAUDE_SKILL_DIR/templates/project-layout/README.md.tpl"   README.md
```

---

> **Working directory convention**: All CLI commands assume `cd hamilton_pipeline/` first — the scripts' CWD-relative `build/` output lands inside the pipeline folder, not the repo root. All pipeline assets live under `<project-root>/hamilton_pipeline/` (see the skill's `LAYOUT.md`).

**F1 — Natural-language → YAML spec:**

```
/lazy2work:hamilton-harness 주문 로그 CSV를 읽어서 일자별 매출 집계 Parquet를 만드는 파이프라인 만들어줘
```

Claude follows the 6-step extraction protocol (intent → inputs → outputs → intermediates → types → invariants) and writes `hamilton_pipeline/dag_specs/orders_etl.yaml`. Asks clarifying questions if the input source, output form, or stage count is ambiguous.

---

**F2 — Validate an existing YAML:**

```bash
cd hamilton_pipeline
python "$CLAUDE_SKILL_DIR/scripts/validate.py" dag_specs/orders_etl.yaml
```

Seven-layer validation (L1 schema → L7 invariant syntax). Failure report cites the failing layer and suggests a fix. F3 is blocked until F2 passes.

---

**F3 — Generate Hamilton stub + render DAG:**

```bash
cd hamilton_pipeline

# Stub only
python "$CLAUDE_SKILL_DIR/scripts/viz.py" dag_specs/orders_etl.yaml --stub-only

# Stub + Mermaid
python "$CLAUDE_SKILL_DIR/scripts/viz.py" dag_specs/orders_etl.yaml --format mermaid

# Stub + PNG via Graphviz
python "$CLAUDE_SKILL_DIR/scripts/viz.py" dag_specs/orders_etl.yaml --format graphviz

# All three formats (mermaid, graphviz, hamilton)
python "$CLAUDE_SKILL_DIR/scripts/viz.py" dag_specs/orders_etl.yaml --format all
```

Writes (all inside `hamilton_pipeline/`):

```
build/stubs/orders_etl_stub.py          # Hamilton function stubs + Pydantic schemas
build/dags/spec/orders_etl.mmd          # Mermaid source
build/dags/spec/orders_etl.png          # Graphviz render
build/dags/spec/orders_etl.meta.json    # Driver metadata (for CI diffs)
```

---

**F4 — Modify an existing spec (diff-first):**

```
/lazy2work:hamilton-harness hamilton_pipeline/dag_specs/orders_etl.yaml 에 'avg_order_value' 노드 추가해줘. clean_orders 를 입력으로 받고 범위는 [0, 100000].
```

Claude shows a unified YAML diff + destructive-change impact summary ("this breaks 2 downstream nodes: X, Y") and requires explicit confirmation before writing. Re-runs F2 before the write lands.

---

**Quickstart — ETL example end-to-end:**

```
/lazy2work:hamilton-harness Walk me through the ETL example. Explain the spec and render it as a Mermaid diagram.
```

Reads `examples/etl/dag_specs/orders_etl.yaml`, explains each node, and pastes a Mermaid diagram inline. Three domains shipped:

| Directory | Domain | Nodes |
|-----------|--------|-------|
| `examples/etl/` | Order log → daily aggregated Parquet | Input CSV → clean → enrich → daily aggregate |
| `examples/ml-training/` | Churn prediction feature engineering + training | Raw events → features → train/test split → model |
| `examples/rag/` | Documents → chunks → embeddings → vector index | Docs → chunker → embedder → vector store |

---

**Workflow — 7 stages for high-complexity requests:**

Hamilton-harness scores the user's request against 6 signals (pipeline keywords, stage count, external systems, node count, regulation, speed hints). **Score ≥ 3** enforces the full 7-stage flow:

```
1. SPEC             → F1 writes dag_specs/<name>.yaml
2. VALIDATE         → F2 must pass
3. STRUCTURE GATE   → F3 renders for review
4. PBT SCAFFOLD     → Hypothesis property tests from invariants
5. IMPLEMENT        → fill function bodies
6. RUNTIME CHECK    → Hamilton Driver executes, @check_output verifies
7. LINEAGE DEBUG    → dr.what_is_upstream_of(node) on failure
```

**Score < 3** → collapses to F1 → F3 (`--stub-only`) → implement.

The complexity score is logged to `build/metrics/session-<timestamp>.json` for audit.

---

**Supporting docs inside the skill** (read on demand):

| File | Purpose |
|------|---------|
| `SPEC.md` | Full YAML schema reference (read before writing a spec) |
| `LAYOUT.md` | Target project layout the skill scaffolds into |
| `QUICKSTART.md` | 10-minute onboarding tutorial |
| `DEBUG.md` | Decision tree for three common failure modes |
| `METRICS.md` | Session metrics logging schema |
| `CHANGELOG.md` | Skill-independent SemVer history (currently 1.2.0) |

**Trigger phrases (Korean + English)** — the skill auto-activates on: `파이프라인 만들어`, `DAG 설계`, `DAG 시각화`, `시각화해줘`, `YAML 스펙 검증`, `Hamilton으로`, `ETL 구현`, `feature engineering`, `RAG 인덱싱`, `ML 학습 파이프라인`, `data pipeline`.

**Self-contained design**: no plugin-level hooks, commands, or rules are required. All assets live under `${CLAUDE_SKILL_DIR}` and visualization is **pull-based** — it only renders when the user explicitly asks.

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
│       │   ├── fix-mermaid/
│       │   │   ├── SKILL.md
│       │   │   ├── scripts/
│       │   │   └── references/
│       │   ├── hamilton-harness/          ← scaffolds `hamilton_pipeline/` in user projects
│       │   │   ├── SKILL.md
│       │   │   ├── SPEC.md                ← YAML schema reference
│       │   │   ├── LAYOUT.md              ← target layout (user's `hamilton_pipeline/`)
│       │   │   ├── QUICKSTART.md          ← 10-minute onboarding
│       │   │   ├── DEBUG.md               ← failure-mode decision tree
│       │   │   ├── METRICS.md             ← session metrics schema
│       │   │   ├── CHANGELOG.md           ← skill-independent SemVer
│       │   │   ├── scripts/               ← viz.py, validate.py, yaml_to_*.py
│       │   │   ├── templates/             ← JSON Schema + CI + project-layout
│       │   │   ├── examples/              ← etl, ml-training, rag
│       │   │   └── tests/
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

### v1.20.0 (2026-04-13)

- **hamilton-harness → skill 1.1.0: top-level `hamilton_pipeline/` folder wrapper** — all pipeline assets (`specs/`, `src/`, `tests/`, `build/`, `runs/`) moved under a single `hamilton_pipeline/` directory at the user's project root, keeping them isolated from Django apps, notebooks, web UI, and other repo contents. Scripts keep CWD-relative behavior; the convention is `cd hamilton_pipeline/` before invoking `validate.py`/`viz.py`. Clean migration: `mkdir -p hamilton_pipeline && git mv specs src tests build runs hamilton_pipeline/`
- **hamilton-harness → skill 1.2.0: `specs/` → `dag_specs/` rename** — the spec directory renamed to make it immediately clear the YAML files describe a DAG (vs. test specs, OpenAPI specs, or other "spec" folders that can appear elsewhere in the repo). Contents and schema unchanged. Migration: `cd hamilton_pipeline && git mv specs dag_specs` (+ CI config path updates)
- **hamilton-harness: docs synchronized with the new layout** — `LAYOUT.md` (tree re-rooted under `hamilton_pipeline/dag_specs/`, "Why a dedicated folder" rationale, bootstrap command, working-directory convention), `SKILL.md` Paths and conventions, `QUICKSTART.md`, `DEBUG.md` (`cd hamilton_pipeline/` in validation and upstream-display examples), `METRICS.md` (`hamilton_pipeline/build/metrics/` path), `SPEC.md`
- **hamilton-harness: templates scoped to `hamilton_pipeline/dag_specs/`** — `CLAUDE.md.tpl` rules, `README.md.tpl`, `.gitignore.tpl` (`hamilton_pipeline/build/`), `pre-commit-config.yaml` regex (`^hamilton_pipeline/dag_specs/.*\.yaml$`), `github-workflow-dag-gate.yml` (`defaults.run.working-directory: hamilton_pipeline` + prefixed trigger paths and `upload-artifact` paths)
- **hamilton-harness: examples renamed on disk** — `examples/{etl,ml-training,rag}/specs/` → `dag_specs/` via `git mv` (history preserved); example READMEs show `cp -r "$CLAUDE_SKILL_DIR/examples/<domain>/"* hamilton_pipeline/` + `cd hamilton_pipeline` as the recommended bootstrap
- **hamilton-harness: skill CHANGELOG** — bumped to 1.2.0 with per-version migration guides (1.0.0 → 1.1.0 → 1.2.0)
- **hamilton-harness: `viz.py` stub loading fix** — register the dynamically loaded stub module in `sys.modules` before `exec_module`, so relative imports inside the stub resolve correctly during Hamilton Driver rendering
- **README: hamilton-harness usage examples synced** — F1/F2/F3/F4 blocks use `cd hamilton_pipeline` convention and `hamilton_pipeline/dag_specs/*.yaml` paths; new **Target project layout** section (tree + 4 Guardrails + bootstrap command) mirrors `LAYOUT.md` so readers see the structure without digging into the skill folder; Supporting docs table reflects skill at 1.2.0
- **Version bump**: 1.19.0 → 1.20.0

### v1.19.0 (2026-04-13)

- **New skill: hamilton-harness** (initial release at skill 1.0.0) — spec-driven workflow for building Hamilton data pipelines. Four operating modes: F1 (prompt → YAML spec), F2 (validate via 7-layer check: schema → name uniqueness → cycle → orphan → dangling reference → type resolution → invariant syntax), F3 (generate Hamilton function stubs + Pydantic schemas with optional Mermaid/Graphviz/Hamilton rendering), F4 (diff-first YAML modification with destructive-change classification)
- **hamilton-harness: 7-stage workflow** — complexity-score gate (≥ 3 enforces SPEC → VALIDATE → STRUCTURE GATE → PBT SCAFFOLD → IMPLEMENT → RUNTIME CHECK → LINEAGE DEBUG; < 3 allows F1 → F3 `--stub-only` → implement)
- **hamilton-harness: four invariant kinds** — `range: [min, max]`, `no_nulls: true`, `values: [...]`, `regex: "..."` mapped onto `@check_output` decorators at runtime and Hypothesis property-test generation at build time
- **hamilton-harness: self-contained design** — no plugin-level hooks, commands, or rules are wired; assets live entirely under `${CLAUDE_SKILL_DIR}`. Visualization is **pull-based** (natural-language keyword + context-window + negation-filter safety rules) to avoid false triggers
- **hamilton-harness: three example domains** — `examples/etl/` (order log → daily aggregated Parquet), `examples/ml-training/` (churn prediction feature engineering + training), `examples/rag/` (documents → chunks → embeddings → vector index)
- **hamilton-harness: supporting docs** — `SPEC.md` (schema reference), `LAYOUT.md` (target project layout), `QUICKSTART.md` (10-minute onboarding), `DEBUG.md` (three common failure modes), `METRICS.md` (session logging schema), plus skill-independent `CHANGELOG.md`
- **hamilton-harness: scripts** — `viz.py` (F3 orchestrator), `validate.py` (F2 standalone), `yaml_to_mermaid.py`, `yaml_to_graphviz.py`, `yaml_to_hamilton_stub.py`, `dump_impl_meta.py` (CI Driver metadata diff), `row_validator.py` (Pydantic sample-based DataFrame validator, default n=100)
- **README: hamilton-harness usage examples** — added a dedicated `<details>` section covering one-time deps setup, F1 (prompt→YAML), F2 (validate), F3 (stub+viz with `--format mermaid|graphviz|hamilton|all`), F4 (diff-first modify), quickstart walkthrough, the 7-stage workflow with complexity scoring, and the list of trigger phrases (Korean + English)
- **README: Repository Structure** — added `hamilton-harness/` tree with `SPEC.md`, `LAYOUT.md`, `QUICKSTART.md`, `DEBUG.md`, `METRICS.md`, `CHANGELOG.md`, `scripts/`, `templates/`, `examples/`, and `tests/`
- **marketplace.json sync** — caught up from 1.10.0 → 1.19.0 (metadata + plugins[0]) and updated its description/tags/keywords to reflect the Hamilton and Mermaid additions
- **Version bump**: 1.18.0 → 1.19.0

### v1.18.0 (2026-03-31)

- **New skill: fix-mermaid** — Mermaid diagram linter and auto-fixer for Markdown files. Detects and fixes sequence diagram reserved word conflicts (13 keywords including `opt`, `alt`, `par`, `end`), Unicode/Langium parser issues (smart quotes, fullwidth CJK punctuation, invisible characters, typographic dashes), and message text escaping (`{}[]"` → Mermaid entities). Bundled Python script (`scripts/fix_mermaid.py`) supports lint-only, `--fix`, and `--json` modes
- **fix-mermaid reference**: Comprehensive `mermaid-v11-syntax.md` (18 sections, 966 lines) covering all diagram types, arrow syntax, reserved words, Unicode replacement tables, and entity escaping
- **Version bump**: 1.17.0 → 1.18.0

### v1.17.0 (2026-03-28)

- **README: enriched generate-optimized-spec-kit-prompt documentation** — added 6-stage role separation table, Mermaid diagram classification table with placement test, and full quality checklist (13 checks) to README details section. Consolidated output structure example
- **Version bump**: 1.16.0 → 1.17.0

### v1.16.0 (2026-03-28)

- **generate-optimized-spec-kit-prompt: 6-stage pipeline** — expanded from 4 files to 6 files per feature. Added `02_clarify.md` (`/speckit.clarify auto-accept all recommended options`) for automatic spec ambiguity resolution before planning, and `06_commit.md` (`/sc:git commit`) for post-implementation commit. Renumbered existing files: plan → 03, tasks → 04, implement → 05
- **Version bump**: 1.15.0 → 1.16.0

### v1.15.0 (2026-03-28)

- **generate-optimized-spec-kit-prompt: Mermaid diagram support** — added Mermaid diagram extraction, classification, and stage-aware placement. User workflows (flowchart, sequence without tech terms) go into specify; architecture, API sequences, ERD, data flow, and state machines go into plan. Includes placement test ("does diagram survive stack change?"), anti-pattern guide, and updated specify/plan templates with Mermaid examples
- **generate-optimized-spec-kit-prompt: enriched plan template** — plan now includes API Endpoints, API Sequence (sequenceDiagram), Data Model (erDiagram), and Architecture (graph TB) sections
- **Quality checklist expanded** — 3 new Mermaid validation checks: no tech terms in specify diagrams, architecture/API diagrams present in plan, one concern per Mermaid block
- **Version bump**: 1.14.0 → 1.15.0

### v1.14.0 (2026-03-27)

- **generate-optimized-spec-kit-prompt: remove frontmatter** — prompt files no longer include YAML frontmatter (`feature`, `stage`, `generated`); each file starts directly with the `/speckit.*` command for immediate copy-paste use
- **English translation** — all plugin files (SKILL.md, references) translated from Korean to English for international accessibility
- **Version bump**: 1.13.0 → 1.14.0

### v1.13.0 (2026-03-27)

- **generate-optimized-spec-kit-prompt: feature-based folder output** — changed output from batch files (`claudedocs/speckit/{date}/features_01-05.md`) to feature-based folders (`.speckit-prompts/feature-{NNN}-{name}/`) with individual `01_specify.md`, `02_plan.md`, `03_tasks.md`, `04_implement.md` files per feature
- **Version bump**: 1.12.0 → 1.13.0

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

- **New skill: generate-optimized-spec-kit-prompt** — generates complete Spec Kit prompts (specify/plan/tasks/implement) for all project features. Splits project into 1-5 day features, enforces strict 4-stage separation
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
