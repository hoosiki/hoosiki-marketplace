# hoosiki-marketplace

> Curated Claude Code plugins by Junsang Park — productivity tools, MCP installers, and workflow automation.

[![Version](https://img.shields.io/badge/version-1.40.0-green.svg)](https://github.com/hoosiki/hoosiki-marketplace)
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
| [**lazy2work**](plugins/lazy2work/) | 1.40.0 | One-command SuperClaude environment setup — MCP server installers, webhook notification hooks, productivity skills, Hamilton spec-driven pipelines, a document→reveal.js presentation builder, and PRD/SpecKit→Linear hierarchy publishers |

---

## lazy2work

> One plugin to set up your entire SuperClaude environment — MCP servers, webhook hooks, and productivity skills.

### Prerequisites

- [Claude Code](https://claude.ai) 1.0.33+
- [SuperClaude](https://github.com/SuperClaude-Org/SuperClaude_Framework.git)
- Python 3.10+ (for skills scripts and webhook hooks)
- Node.js 18+ (for MCP setup commands that use `npx`)

### Skills (12)

| Skill | Command | Description |
|-------|---------|-------------|
| **up2date** | `/lazy2work:up2date` | Unified updater — checks and updates Homebrew packages, Claude Code skills/plugins, and SuperClaude commands in one go (`--brew` for Homebrew only, `--skill` for skills only). The `--skill` path also runs **`npx skills@latest update -g -y`** to refresh global agent skills (e.g. mattpocock/skills) and **prunes skills deleted upstream** by parsing the updater's warning and calling `npx skills remove` (opt out with `--no-skill-prune`) |
| **analyze-arxiv** | `/lazy2work:analyze-arxiv` | Study arXiv papers — fetches paper content, generates structured summaries, and creates prerequisite knowledge documents for deeper understanding |
| **constitution-generator** | `/lazy2work:constitution-generator` | Generate optimized `/speckit.constitution` prompts — gathers project info (tech stack, project stage, conventions), detects brownfield patterns, and outputs a **minimal-but-enforceable** constitution: 6–12 non-negotiable principles in MUST/NO language, each with a `(Rationale: …)`, prototype-stage gate stripping, and a validation checklist |
| **generate-optimized-spec-kit-prompt** | `/lazy2work:generate-optimized-spec-kit-prompt` | Generate complete Spec Kit prompts for the full 8-stage flow (specify → clarify → plan → checklist → tasks → analyze → implement → converge, + commit) from a PRD + pre-sliced issue files — 1 issue = 1 feature (no re-slicing), Mermaid diagrams, `/speckit.tasks` command-only (no hand-authored tasks), and auto-accept prompts for clarify/checklist/analyze/converge. Also installs a headless runner at `utilities/speckit_pipeline.sh` to execute the generated prompts via `claude -p` |
| **pyright-setup** | `/lazy2work:pyright-setup` | Auto-configure Pyright for Python projects — detects Python version from venv, adds `[tool.pyright]` to pyproject.toml, resolves "Import could not be resolved" LSP errors in Neovim/VS Code |
| **apply-all-sc-save** | `/lazy2work:apply-all-sc-save` | Broadcast `/sc:save` to all Claude Code panes in the current tmux session — auto-detects Claude panes, excludes self, supports `--dry-run`, `--all-sessions`, and custom commands |
| **fix-mermaid** | `/lazy2work:fix-mermaid` | Fix Markdown rendering issues that break Mermaid diagrams or pandoc PDF conversion — Mermaid v11 syntax (reserved words, Unicode/Langium issues, message escaping) **and** pandoc PDF pitfalls (blank-line compliance before lists/tables/fences as auto-fixed errors, long-mixed-cell overflow as warnings, always-on Unicode glyph map covering U+2212/U+2717/U+2718, **currency-dollar auto-escape** for `$100`/`$76.4억` that prevents `Bad math environment delimiter` errors, **unsafe-inline-code warnings** for `` `pass^k` ``-style content that collides with the `\seqsplit` wrapper and causes `Missing number, treated as zero`, **closing-dollar-trailing-space auto-fix** for `$\mathcal{H}_1 = $ rest` patterns that violate pandoc's `tex_math_dollars` rule and cause `\symcal allowed only in math mode`, plus opt-in **`--latin1-normalize`** for Latin-1 Supplement diacritics like `á é ñ ü ß`). Three bundled Python scripts (`fix_mermaid.py`, `fix_pandoc_blanks.py`, `validate_mermaid.py`) with lint / `--fix` / `--json` modes, plus optional **`--with-mmdc` feedback loop** that renders each diagram with Mermaid CLI and iterates targeted fixes until clean |
| **hamilton-harness** | `/lazy2work:hamilton-harness` | Build Hamilton data pipelines through a spec-driven workflow — 4 modes (prompt→YAML, validate, stub+viz, modify), Pydantic schemas, Mermaid/Graphviz/Hamilton rendering, 3 domain examples (ETL/ML/RAG). Artifacts land under **`spec_build/`** (renamed from `build/` in v1.27.0 to avoid colliding with Python packaging / Sphinx / CMake build directories). Self-contained — no plugin-level hooks or rules needed |
| **make-ppt-html** | `/lazy2work:make-ppt-html` | Convert any document (research note, report, README, storyboard) into a presentation-quality **reveal.js 5.2.1 + Tailwind CSS** single-file HTML deck with a **light↔dark theme toggle** (button + `D` key + localStorage). Follows bundled design guidelines — assertion-style slide titles, 60-30-10 single-accent color system, WCAG-verified contrast pairs, Pretendard, speaker notes, `?print-pdf` export — and ships a browser-verified `template.html` that pre-solves the reveal×Tailwind integration traps (Meyer-reset border-style kill, `Reveal.sync()` background re-theming, print-mode toggle hiding, dark-variant class pairing) |
| **from-grill-me-to-linear** | `/lazy2work:from-grill-me-to-linear` | Publish grill-me/grill-with-docs outputs (PRD + vertical-slice issue files) into a Linear team as a **Project→Milestone→Issue→Sub-issue** hierarchy via the linear-server MCP — filters non-issue noise (user stories, decisions, glossary → project brief/links), preserves the dependency DAG with `blocked-by` relations (no false milestone serialization), and enforces **dry-run approval + idempotent upsert** (query-reuse-update so re-runs never duplicate labels or issues). Requires the Linear MCP integration |
| **from-speckit-to-linear** | `/lazy2work:from-speckit-to-linear` | Publish GitHub Spec Kit outputs (`spec.md` + `plan.md` + `tasks.md`) into a Linear team as a **Project→Milestone→Issue→Sub-issue** hierarchy via the linear-server MCP — **mirrors the tasks.md phase structure instead of re-slicing** (Setup+Foundational → an `M0 Foundation` milestone that blocks every story, User Stories P1/P2/P3 → milestones whose "done" = each story's Independent Test, tasks → verb-first issues keyed by their **T-ID for idempotent re-runs**), keeps the 40–50 FRs as acceptance-criteria checklists instead of issues, and blocks publication while `[NEEDS CLARIFICATION]` markers remain (routes to `/speckit.clarify` first). Sibling of from-grill-me-to-linear — same publish engine, SpecKit-specific parser. Requires the Linear MCP integration |
| **update-readme** | `/lazy2work:update-readme` | Audit and refresh a project's `README.md` against README best practices while reconciling it with the current code — reads the existing README, discovers real state from manifests/git/docs, then walks a bundled best-practice checklist (required backbone → recommended → anti-patterns → security "never include" → README-vs-AGENTS split → staleness). **Grilling-style**: resolves facts from the codebase directly and asks the user only decision gaps **one question at a time** (each with a recommended answer); sections the user says are unneeded are omitted, and raw answers are rewritten into clean scannable prose. Routes dev/build/CHANGELOG/full-API content *out* of the README instead of inlining, and flags any leaked secrets rather than keeping them |

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

1. Gathers project info (name, tech stack, project type, **project stage: prototype or production**)
2. For brownfield: reads project structure and detects conventions
3. Generates a **minimal-but-enforceable** `/speckit.constitution` prompt — sections are a menu, not a quota (6–12 principles total, hard cap 15):
   - Tech Stack (locked with versions)
   - Prohibitions (minimum 3 explicit NO items)
   - Architecture / Coding Conventions / Testing / Security — only where a genuine non-negotiable exists
   - Deployment Target — production stage only; prototypes explicitly exclude CI/CD, deployment, and performance-budget articles
4. Validates against anti-patterns (over-constraint, missing Rationale, vague rules, missing versions, etc.)

Output: A ready-to-use `/speckit.constitution` prompt text. Every principle is written in enforceable **MUST/NO** language with quantified thresholds (coverage ≥ 80%, P95 < 200ms) and carries a `(Rationale: …)` — agents follow rules better when they understand why.

Validation checklist:

```
| Check                                                    | Pass? |
|----------------------------------------------------------|-------|
| All rules verifiable, in MUST/NO language                |  ✅   |
| Every principle carries a (Rationale: …)                 |  ✅   |
| Thresholds quantified (≥ 80%, P95 < 200ms)               |  ✅   |
| Total principles ≤ 12, all non-negotiable                |  ✅   |
| Stage match: prototype has no CI/CD / perf-budget rules  |  ✅   |
| Tech stack has specific versions                         |  ✅   |
| Prohibitions section exists and has ≥ 3 items            |  ✅   |
| No feature requirements (belongs in /specify)            |  ✅   |
| No implementation details (belongs in /plan)             |  ✅   |
```

</details>

<details>
<summary><strong>generate-optimized-spec-kit-prompt — Usage Examples</strong></summary>

**Generate Spec Kit prompts from a PRD + pre-sliced issues directory:**

```
/lazy2work:generate-optimized-spec-kit-prompt @docs/prd-japanese-tutor.md @docs/issues
```

Inputs:

- **PRD file** — global context shared by every feature: problem statement, user stories, implementation/testing decisions, out of scope
- **Issues directory** — pre-sliced vertical features, one `NN-slug.md` file per feature (the first issue is typically the environment/prefactor setup slice); a `README.md` in the directory is used only as a dependency-order index, never as a feature

Workflow:

1. Reads the PRD and every issue file — **1 issue file = 1 feature**, never merged or re-split
2. Extracts Mermaid diagrams and classifies them by stage placement
3. Generates 8 stage prompts (+ commit) per feature following strict stage separation (specify ← issue scope + acceptance criteria + referenced PRD user stories; plan ← PRD decisions + issue tech details). `/speckit.tasks` is command-only — tasks are generated from spec + plan, never hand-authored; clarify/checklist/analyze/converge lead with `auto-accept all recommended options`
4. Writes output to `.speckit-prompts/{prd-name}/{NNN}-{slug}/` folders — the parent folder name is derived from the PRD (short kebab-case project name), the issue number is zero-padded to 3 digits
5. Installs the bundled headless runner at `<project>/utilities/speckit_pipeline.sh` (copied verbatim + `chmod +x`) — runs each feature through `01_specify → … → 08_converge → commit` via `claude -p` with per-stage model/effort, `--dry-run`, `--only`, `--from`, and `--resume`

#### 8-Stage Role Separation (+ commit)

Based on the exhaustive Spec Kit prompting research (2026-07-21). Think in detail up front (specify/plan), act briefly at the back (tasks/analyze/implement/converge).

| Stage | Role | Prompt Focus | MUST NOT Include |
|-------|------|-------------|-----------------|
| `/speckit.specify` | **What + Why** | Features, users, scenarios, constraints | Tech stack, architecture, code |
| `/speckit.clarify` | **Refine** | `auto-accept all recommended options` — resolve spec ambiguities | Manual intervention |
| `/speckit.plan` | **How** | Tech stack, architecture, file paths, stop-guard | Feature requirements; starting tasks/code |
| `/speckit.checklist` | **Requirements QA** | `auto-accept` — completeness/clarity/consistency | Implementation detail |
| `/speckit.tasks` | **Order (generated)** | Command only — derive tasks from spec + plan | Hand-authored `T001…`; tech decisions |
| `/speckit.analyze` | **Cross-check** | `auto-accept` — 4-way consistency, fix at correct layer | Hand-editing tasks.md |
| `/speckit.implement` | **Rules** | All tasks in one pass, per-task commit, failure behavior | Design changes |
| `/speckit.converge` | **Close gaps** | `auto-accept` loop — converge → implement → converge | Manual gap triage |
| `/sc:git commit` | **Commit** | Final commit after convergence | Design changes, new features |

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
<project-root>/
├── .speckit-prompts/
│   └── japanese-tutor/              ← parent name derived from the PRD
│       ├── 000-env-compat-gate/
│       │   ├── 01_specify.md
│       │   ├── 02_clarify.md
│       │   ├── 03_plan.md
│       │   ├── 04_checklist.md
│       │   ├── 05_tasks.md
│       │   ├── 06_analyze.md
│       │   ├── 07_implement.md
│       │   ├── 08_converge.md
│       │   └── 09_commit.md
│       ├── 001-sync-chat-http/
│       │   └── ... (same 9 files)
│       └── 002-persistence-auth/
│           └── ... (same 9 files)
└── utilities/
    └── speckit_pipeline.sh         ← headless runner (copied from skill assets, chmod +x)
```

Folder naming: `{prd-name}/{NNN}-{kebab-case-name}` — `{prd-name}` is a short kebab-case project name derived from the PRD title/product name (e.g. "일본어 학습 튜터 챗봇" → `japanese-tutor`), `{NNN}` is the source issue number zero-padded to 3 digits (`00-env-compat-gate.md` → `{prd-name}/000-env-compat-gate/`).

Run the generated prompts headlessly with the installed runner:

```bash
./utilities/speckit_pipeline.sh .speckit-prompts/japanese-tutor            # all features
./utilities/speckit_pipeline.sh .speckit-prompts/japanese-tutor --dry-run  # preview plan
./utilities/speckit_pipeline.sh .speckit-prompts/japanese-tutor --only 002 # one feature
```

#### Quality Checklist

Every generated feature is verified against:

| Check | Rule |
|-------|------|
| 1 issue file = 1 feature folder | No merging or re-splitting of issues |
| Parent folder named from the PRD | Short kebab-case project name (e.g. `japanese-tutor`), never a literal `feature` |
| 9 stage files per folder in order | `01_specify … 09_commit` — filenames encode run order |
| Folder number matches issue number | `00-env-compat-gate.md` → `{prd-name}/000-env-compat-gate/` |
| Issue acceptance criteria appear in spec | Every criterion maps to a `FR-NNN` or `SC-NNN` |
| /speckit.specify has no tech terms | Tech-neutral (survives stack change) |
| /speckit.specify uses official spec-template structure | Prioritized user stories + Given/When/Then + FR-NNN/SC-NNN; no trailing questions |
| /speckit.specify has Out of Scope section | Prevents AI scope creep |
| /speckit.specify Mermaid has no tech terms | No Django, PostgreSQL, etc. in nodes |
| /speckit.clarify leads with auto-accept | `auto-accept all recommended options` |
| /speckit.plan references specific file paths | Not vague "follow patterns" |
| /speckit.plan has architecture + API sequence diagrams | Mermaid with explanation text |
| /speckit.plan has explicit exclusions + stop-guard | Prevents Docker/CI/CD creep; "generate plan.md only" |
| /speckit.checklist leads with auto-accept | Requirements-quality gate, non-interactive |
| /speckit.tasks is command-only | No hand-authored `T001…`; derived from spec+plan, never hand-edited |
| /speckit.analyze leads with auto-accept + layer guard | Fix plan/spec then regenerate tasks — never edit tasks.md |
| /speckit.implement runs all tasks in one pass | Execute the whole task list at once, per-task verify+commit |
| /speckit.implement has failure behavior | Stop and report on failure |
| /speckit.converge leads with auto-accept loop | converge → implement → converge until "converged" |
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

The skill bundles **three scripts** covering different Markdown rendering pitfalls:

- `fix_mermaid.py` — Mermaid diagram syntax (reserved words, Unicode, message escaping) with optional mmdc feedback loop
- `fix_pandoc_blanks.py` — Pandoc PDF rendering pitfalls (blank-line compliance, long-mixed-cell warnings, Unicode glyph map, currency-dollar auto-escape, unsafe-inline-code warnings)
- `validate_mermaid.py` — Mermaid CLI wrapper that extracts blocks, renders each via `mmdc`, and surfaces parse errors as structured data (consumed by `fix_mermaid.py --with-mmdc`)

### Workflow A — Mermaid Syntax

**Lint a file (report issues without changing):**

```bash
python3 plugins/lazy2work/skills/fix-mermaid/scripts/fix_mermaid.py docs/PROJECT_ANALYSIS.md
```

**Auto-fix in place:**

```bash
python3 plugins/lazy2work/skills/fix-mermaid/scripts/fix_mermaid.py docs/PROJECT_ANALYSIS.md --fix
```

**Scan a directory / emit JSON:**

```bash
python3 plugins/lazy2work/skills/fix-mermaid/scripts/fix_mermaid.py docs/ --fix
python3 plugins/lazy2work/skills/fix-mermaid/scripts/fix_mermaid.py docs/ --json
```

What it detects and fixes:

| Category | Examples |
|----------|---------|
| **Reserved words** | `participant OPT as Optuna` → `participant OPTA as Optuna` (13 reserved words) |
| **Message escaping** | `V-->>C: 200 OK {id}` → `V-->>C: 200 OK #123;id#125;` |
| **Unicode issues** | Smart quotes `""` → `""`, fullwidth CJK `（）` → `()`, invisible chars removed |
| **Typographic dashes** | Em dash `—` → `--`, en dash `–` → `-` |

**With mmdc feedback loop** — runs the Mermaid CLI after static fixes, parses every `Parse error on line N`, and iterates targeted fixes until clean (max 3 iterations, early-exit when errors stop changing):

```bash
# Prerequisite: npm i -g @mermaid-js/mermaid-cli

python3 plugins/lazy2work/skills/fix-mermaid/scripts/fix_mermaid.py docs/architecture.md --with-mmdc
python3 plugins/lazy2work/skills/fix-mermaid/scripts/fix_mermaid.py docs/ --with-mmdc --json
```

Example output:

```
=== docs/architecture.md ===
  iterations: 1
  static fixes applied: 3
  mmdc: all blocks render successfully.
```

Or, when automatic fixes are exhausted:

```
=== docs/broken.md ===
  iterations: 2
  static fixes applied: 0
  mmdc errors remaining: 1
    - block #0 line 5: got 'PS'
  suggestions:
    * unquoted-label: wrap the node label in double quotes — it contains
      unescaped (, ), [, ], {, or }
```

Recognised mmdc error patterns:

| mmdc signal | Rule | Auto-fix |
|---|---|---|
| `got 'end' / 'opt' / 'alt' / …` expecting `participant` | `reserved-word` | ✅ renames via `SAFE_RENAMES` |
| `got 'PS' / 'SQS'` expecting `'SQE', 'PE', …` | `unquoted-label` | ❌ flagged for manual quoting |
| Other | *unknown* | ❌ reported verbatim |

Standalone validator (no fixing):

```bash
python3 plugins/lazy2work/skills/fix-mermaid/scripts/validate_mermaid.py docs/architecture.md
python3 plugins/lazy2work/skills/fix-mermaid/scripts/validate_mermaid.py docs/api.md --json
```

### Workflow B — Pandoc PDF Rendering

**Lint (reports errors + warnings):**

```bash
python3 plugins/lazy2work/skills/fix-mermaid/scripts/fix_pandoc_blanks.py report.md
```

**Auto-fix blank-line + unicode-glyph + currency-dollar errors (warnings are never modified):**

```bash
python3 plugins/lazy2work/skills/fix-mermaid/scripts/fix_pandoc_blanks.py report.md --fix
```

**Opt-in: romanize Latin-1 Supplement diacritics (`Román → Roman`):**

Apple SD Gothic Neo and similar CJK-oriented mainfonts silently drop accented Latin letters. Enable only when the trade-off (lossy romanization on proper nouns) is acceptable.

```bash
# Detect only
python3 plugins/lazy2work/skills/fix-mermaid/scripts/fix_pandoc_blanks.py report.md --latin1-normalize

# Apply romanization
python3 plugins/lazy2work/skills/fix-mermaid/scripts/fix_pandoc_blanks.py report.md --fix --latin1-normalize
```

What it detects:

| Rule | Severity | Auto-fix | Trigger |
|------|---------|---------|---------|
| `missing-blank-before-list` | error | ✅ | Bullet/numbered list without preceding blank line |
| `missing-blank-before-table` | error | ✅ | Pipe table row without preceding blank line |
| `missing-blank-before-fence` | error | ✅ | ` ``` ` or `~~~` fence without preceding blank line |
| `unicode-glyph-missing` | error | ✅ | Always-on map: U+2212 MINUS SIGN, U+2717/U+2718 BALLOT X that CJK fonts silently drop |
| `unescaped-currency-dollar` | error | ✅ | `$<digit>` (e.g., `$100`, `$76.4억`) parsed by pandoc as math; odd counts leak math mode and produce `Bad math environment delimiter`. Skips fenced code, inline backticks, and already-escaped `\$` |
| `latin1-supplement-glyph` | error | ✅ (opt-in) | Latin-1 Supplement diacritics (á, é, í, ó, ú, ñ, ü, ß, …) — only reported with `--latin1-normalize` |
| `long-mixed-cell` | warning | ❌ (manual) | Table cell ≥ 25 chars mixing `**bold**` with risky symbols (`·`, `—`, `+`, parens) that trigger LaTeX overfull hbox |
| `unsafe-inline-code-escape` | warning | ❌ (manual) | Inline backtick code containing `^`, `~`, `&`, `$`, `%` — pandoc escapes are split per-character by the pdf-korean.yaml `\seqsplit` wrapper, causing `Missing number, treated as zero`. Three valid fixes (math mode, drop backticks, swap `\seqsplit` for `\detokenize`) need human choice |
| `closing-dollar-trailing-space` | error | ✅ | Inline math whose closing `$` has whitespace immediately before it (e.g., `$\mathcal{H}_1 = $ rest`). Pandoc treats both `$` as literal `\$`, leaving any math-mode commands (`\mathcal`, `\frac`, ...) in text mode and triggering `\symcal allowed only in math mode`. Auto-fix strips the trailing whitespace inside the math span — visually identical because LaTeX normalizes math-mode operator spacing |

Example output:

```
Found 5 error(s), 3 warning(s):

Sev      |  Line | Rule                             | Context
------------------------------------------------------------------------
error    |    77 | missing-blank-before-list        | - React 프론트엔드...
error    |   192 | missing-blank-before-table       | | 모델 | Google-BLEU | ...
error    |   775 | missing-blank-before-fence       | ```
error    |   209 | unescaped-currency-dollar        | budget $100K~$1M 사
error    |   299 | unescaped-currency-dollar        | 시총 $1B 이상 → 현재
warning  |   197 | long-mixed-cell                  | **Fine-tuned GPT-4o**
warning  |   198 | long-mixed-cell                  | Up to **+40%** (7B·8B)
warning  |   398 | unsafe-inline-code-escape        | `pass^k`

Warnings require manual review (not auto-fixable).
Run with --fix to apply blank-line corrections.
```

### Invoke as a Skill

```
/lazy2work:fix-mermaid
```

> Trigger phrases: "mermaid 오류", "mermaid fix", "diagram broken", "Syntax error in text mermaid version", "pandoc 테이블 깨짐", "md pdf 변환 문제", "테이블이 렌더링 안됨", "overfull hbox", "Bad math environment delimiter", "통화 달러 이스케이프", "Missing number treated as zero", "seqsplit 충돌", "pass^k 에러".

Reference documentation:

- `references/mermaid-v11-syntax.md` — 18 sections covering all diagram types, arrow syntax, Unicode replacement tables, reserved words, entity escaping
- `references/pandoc-pdf-pitfalls.md` — 8 sections covering blank-line compliance, long-mixed-cell overflow, font fallback, Unicode glyph missing in CJK fonts, unescaped currency dollar sign, unsafe LaTeX characters in inline code, closing dollar preceded by whitespace, and a pre-conversion checklist

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
    ├── spec_build/                    # gitignored; regenerable (renamed from build/ in v1.27.0)
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
- **`spec_build/` is throwaway** — must regenerate from `dag_specs/` + `src/`; never commit it.
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

> **Working directory convention**: All CLI commands assume `cd hamilton_pipeline/` first — the scripts' CWD-relative `spec_build/` output lands inside the pipeline folder, not the repo root. All pipeline assets live under `<project-root>/hamilton_pipeline/` (see the skill's `LAYOUT.md`).

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
spec_build/stubs/orders_etl_stub.py          # Hamilton function stubs + Pydantic schemas
spec_build/dags/spec/orders_etl.mmd          # Mermaid source
spec_build/dags/spec/orders_etl.png          # Graphviz render
spec_build/dags/spec/orders_etl.meta.json    # Driver metadata (for CI diffs)
```

> The default output directory is `spec_build/` (renamed from `build/` in v1.27.0). Override with `--output-dir <path>` if you need the legacy location or a different folder.

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

The complexity score is logged to `spec_build/metrics/session-<timestamp>.json` for audit.

---

**Supporting docs inside the skill** (read on demand):

| File | Purpose |
|------|---------|
| `SPEC.md` | Full YAML schema reference (read before writing a spec) |
| `LAYOUT.md` | Target project layout the skill scaffolds into |
| `QUICKSTART.md` | 10-minute onboarding tutorial |
| `DEBUG.md` | Decision tree for three common failure modes |
| `METRICS.md` | Session metrics logging schema |
| `CHANGELOG.md` | Skill-independent SemVer history (currently 1.27.0) |

**Trigger phrases (Korean + English)** — the skill auto-activates on: `파이프라인 만들어`, `DAG 설계`, `DAG 시각화`, `시각화해줘`, `YAML 스펙 검증`, `Hamilton으로`, `ETL 구현`, `feature engineering`, `RAG 인덱싱`, `ML 학습 파이프라인`, `data pipeline`.

**Self-contained design**: no plugin-level hooks, commands, or rules are required. All assets live under `${CLAUDE_SKILL_DIR}` and visualization is **pull-based** — it only renders when the user explicitly asks.

</details>

<details>
<summary><strong>make-ppt-html — Usage Examples</strong></summary>

**Convert a research document into a slide deck:**

```
/lazy2work:make-ppt-html @claudedocs/research_monitoring_stack_20260608.md 를 발표자료로 만들어줘
```

**Natural-language trigger (no slash command needed):**

```
이 문서를 ppt로 만들어줘. 라이트/다크 토글도 넣어줘 @docs/quarterly-report.md
```

**Output** — a single self-contained HTML file (`presentation_<topic>_<YYYYMMDD>.html`, written next to the input document):

| Feature | Detail |
|---|---|
| Slides | 10–20 slides, every title an **assertion sentence** (주장 문장), one protagonist element per slide, speaker notes on content slides (`S` key) |
| Theme toggle | Top-right button or `D` key; choice persisted via localStorage; reveal slide backgrounds re-synced live via `Reveal.sync()` |
| Design system | Light `slate-50`/`slate-800`/`blue-600` ↔ dark `slate-900`/`slate-100`/`sky-400`; semantic ✓/✗/⚠ colors with icon double-cues; WCAG-checked contrast pairs |
| PDF export | `?print-pdf` → Chrome print (Landscape · no margins · background graphics ON); toggle button auto-hidden; `pdfMaxPagesPerSlide: 1` preset |
| Tech | reveal.js **5.2.1 pinned** + Tailwind Play CDN (Strategy A — no built-in theme) + Pretendard; highlights/dividers alternate backgrounds via `data-bg-role="divider"` |

**Keyboard controls in the deck:** `D` theme toggle · `S` speaker notes · `ESC`/`O` overview · `G` jump to slide · arrows navigate.

**Why it ships a template** — `assets/template.html` encodes fixes that are invisible until they bite:

- reveal's Meyer `reset.css` beats Tailwind Preflight on specificity and silently zeroes **every** border utility → one load-bearing `border-style: solid` override restores them
- the light/dark toggle rewrites each leaf section's `data-background-color` and calls `Reveal.sync()` — wrapper sections of vertical stacks must stay attribute-free
- contrast traps verified by computation: `slate-500` on the divider background fails 4.5:1; `amber-600`/`emerald-600` text on white fail below 24px (use the `-700` shades); `slate-400` is a dark-mode-only text token

**Built-in verification:** static checks (every color class `dark:`-paired, no `md:`/`vh`/`vw`, leaf-only backgrounds, ≤2 accent spots per slide) plus optional browser checks (per-slide overflow ≤ 680px, console clean, `?print-pdf` page count) when chrome-devtools MCP or Playwright is available.

**Benchmark** (skill-creator eval, 2 documents × with/without skill): with-skill passed **20/20** structural assertions vs **10/20** baseline — baselines omitted speaker notes and PDF config on both runs, and without the word "reveal.js" in the prompt the baseline invented a custom slide framework entirely.

> ⚠️ Tailwind Play CDN and the Pretendard CDN are for prototyping — bundle locally before presenting offline (the skill reminds you).

</details>

<details>
<summary><strong>from-grill-me-to-linear — Usage Examples</strong></summary>

**Purpose** — `grill-me`/`grill-with-docs` chains produce a PRD plus vertical-slice issue files, but even when the tracker is set to Linear they only create flat issues. This skill fills the structuring gap: it converts those outputs into a proper **Project→Milestone→Issue→Sub-issue** hierarchy under a team you name, filtering out everything that should *not* become an issue.

**Prerequisite** — the **linear-server MCP** integration must be connected (the skill verifies with `list_teams` and stops with guidance if unavailable).

**Publish a PRD + issue files to a Linear team:**

```
/lazy2work:from-grill-me-to-linear test 팀에 @PRD.md 와 @issues/ 를 linear로 정리해서 발행해줘
```

**Natural-language trigger (no slash command needed):**

```
이 PRD랑 이슈 파일들을 WertIntelligence 팀 아래 linear에 기록해줘 @PRD.md @issues/
```

**What lands where** (the noise filter is half the value — ❌ rows never become issues):

| grill-me artifact | → Linear |
|---|---|
| PRD (whole) | **Project** (PRD as description, single owner) |
| User-story narration | ❌ → project brief |
| tracer-bullet vertical slice | **Issue** (verb-first title) — big slices promote to **Milestone** |
| Scaffold/boilerplate splits | **Sub-issue** (1 level max) |
| Decisions / glossary / open questions / out-of-scope | ❌ → ADR·repo links / triage / summary line |
| "tests pass" clauses | ❌ → the issue's **DoD checklist** |
| `Blocked by` references | **blocked-by relations** (DAG, published in topological order) |
| HITL/AFK markers | labels `mode:hitl` / `mode:afk` (optional `delegate: "Linear"`) |

**Safety rails:**

- **Gate ①** — blocks un-grilled first drafts (unresolved TODO/TBD decisions)
- **Gate ②** — prints the full create/update/reuse plan as a table and waits for approval before any write
- **Idempotent upsert** — queries existing projects/milestones/labels/issues first and updates by id; re-runs never duplicate (guards against real-world label drift like `type:bug` vs `Bug` coexisting)
- **Resumable** — every write's returned ID is logged, so an interrupted run continues as updates

**Output** — a summary report: created/updated/reused counts per object type, the project URL, dependency edges established, and where each filtered-out fragment went (brief / docs link / comment).

> Also works with any generic `PRD.md` + `issues/*.md` pair following the same shape (What to build / Acceptance criteria / Blocked by). Conversion rules live in the skill's [`references/mapping-rules.md`](plugins/lazy2work/skills/from-grill-me-to-linear/references/mapping-rules.md).

</details>

<details>
<summary><strong>from-speckit-to-linear — Usage Examples</strong></summary>

**Purpose** — Spec Kit finishes the slicing work (`/speckit.specify` → vertical User Stories, `/speckit.tasks` → per-story tasks + an isolated Foundational phase), but nothing carries that structure into Linear: `/speckit.taskstoissues` produces flat GitHub issues, and GitHub↔Linear sync drops milestones/hierarchy/blocked-by entirely. This skill is the structure-preserving path: it **mirrors** the phase structure into a **Project→Milestone→Issue→Sub-issue** hierarchy under a team you name — it never re-slices.

**Prerequisite** — the **linear-server MCP** integration must be connected (the skill verifies with `list_teams` and stops with guidance if unavailable).

**Publish a spec directory to a Linear team:**

```
/lazy2work:from-speckit-to-linear test 팀에 @specs/001-user-auth/ 를 linear로 정리해서 발행해줘
```

**Natural-language trigger (no slash command needed):**

```
이 speckit 결과물(spec.md, tasks.md)을 WertIntelligence 팀 아래 linear에 기록해줘 @specs/002-payments/
```

**What lands where** (mirror, don't re-slice — ❌ rows never become issues):

| Spec Kit artifact | → Linear |
|---|---|
| Feature spec (`spec.md`) | **Project** (spec/plan linked, single owner) |
| **Phase Setup + Phase Foundational** | **Milestone "M0 Foundation"** — the only legal horizontal slice; blocks every story; close first |
| User Story P1 (🎯 MVP) / P2 / P3 | **Milestones M1/M2/M3** — "done" = each story's Independent Test criterion |
| Task line `- [ ] T001 [P] [US1] …` | **Issue** in the story's milestone, verb-first title, `SpecKit: T001` footer |
| `[P]` splits / scaffold detail | **Sub-issue** (1 level max) — only when independently tracked |
| Functional Requirements (40–50/spec) | ❌ → **acceptance-criteria checklists** inside issue bodies |
| User-story narration | ❌ → milestone name/description + project brief |
| `plan.md` / `constitution.md` | ❌ → project document links (files stay SSOT) |
| Story dependencies | **blocked-by relations** (DAG, topological publish; parallel stories stay parallel) |

**Safety rails:**

- **Gate ①** — blocks publication while `[NEEDS CLARIFICATION]` markers remain (routes to `/speckit.clarify` first)
- **Gate ②** — prints the full create/update/reuse plan (with T-IDs) as a table and waits for approval before any write
- **T-ID idempotency** — issues carry a `SpecKit: T001` footer, so re-runs match by stable ID even after titles get rephrased; existing projects/milestones/labels are reused (guards against real-world label drift like `type:bug` vs `Bug` coexisting)
- **Scale-aware** — tiny specs (1–2 stories) skip milestones in favor of `story:USn` labels; multi-spec features get offered an Initiative
- **Resumable** — every write's returned ID is logged, so an interrupted run continues as updates

**Output** — a summary report: created/updated/reused counts, the project URL, dependency edges, the **T-ID → Linear-ID mapping table**, and where each filtered fragment went (FR → which issue's AC, plan.md → link).

> Sibling skill: [`from-grill-me-to-linear`](plugins/lazy2work/skills/from-grill-me-to-linear/SKILL.md) — same publish engine, grill-me/PRD-specific parser. Conversion rules live in this skill's [`references/mapping-rules.md`](plugins/lazy2work/skills/from-speckit-to-linear/references/mapping-rules.md).

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
│       │   │   ├── references/
│       │   │   └── assets/               ← speckit_pipeline.sh (headless runner, copied into user projects)
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
│       │   ├── make-ppt-html/             ← document → reveal.js+Tailwind deck w/ light·dark toggle
│       │   │   ├── SKILL.md
│       │   │   ├── references/            ← design-guidelines.md (색상·폰트·배치 규격)
│       │   │   └── assets/                ← template.html (browser-verified boilerplate)
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

### v1.40.0 (2026-07-21)

- **generate-optimized-spec-kit-prompt: headless runner runs with explicit `bypassPermissions`** — every `claude -p` invocation in the bundled `assets/speckit_pipeline.sh` (both the 8-stage runner and the commit runner) now passes `--permission-mode bypassPermissions` alongside the existing `--dangerously-skip-permissions`, so all permission checks are skipped for fully unattended pipeline runs. The two flags are equivalent per the docs, but keeping both makes the bypass intent explicit while `--dangerously-skip-permissions` also clears the first-run acceptance dialog. Header comment and `references/api_reference.md` now document the behavior and its guardrails: the runner refuses to start as root/sudo and should run as a normal user in an isolated environment (container/VM/dev container), since `bypassPermissions` offers no protection against prompt injection or unintended actions. No change to the security posture — the runner already bypassed permissions via `--dangerously-skip-permissions`
- **Version bump**: 1.39.0 → 1.40.0

### v1.39.0 (2026-07-21)

- **generate-optimized-spec-kit-prompt: converge runs on Opus + higher turn budget** — in the headless runner (`assets/speckit_pipeline.sh`), `CONVERGE_MODEL` default changed from `claude-sonnet-5` to `claude-opus-4-8`. Converge verifies planned work and judges whether remaining gaps need re-implementation — quality-critical reasoning — so it now sits in the Opus reasoning group alongside specify/clarify/plan/checklist/analyze; only tasks and implement stay on Sonnet. Still env-overridable via `CONVERGE_MODEL`/`CONVERGE_EFFORT`
- **generate-optimized-spec-kit-prompt: `MAX_TURNS` default raised 300 → 1000** — the shared max-turns budget inherited by the plan, tasks, implement, and converge stages is raised to 1000 so long features (especially the converge → implement → converge loop) don't hit the turn cap mid-run. The fixed light stages (specify=30, clarify/checklist/analyze=50) are unchanged; override with `--max-turns N`. SKILL.md, `references/api_reference.md` per-stage table, and inline help/comments updated to match
- **Version bump**: 1.38.0 → 1.39.0

### v1.38.0 (2026-07-21)

- **generate-optimized-spec-kit-prompt: expanded to the full 8-stage Spec Kit flow** — the skill now generates prompts for `/speckit.specify → clarify → plan → checklist → tasks → analyze → implement → converge` (+ a final `/sc:git commit`), up from the previous 6-stage flow. Three stages are new: **`04_checklist`** (requirements-quality gate after plan), **`06_analyze`** (constitution↔spec↔plan↔tasks consistency check before implement), and **`08_converge`** (verify-and-close-gaps loop after implement). Per-feature folders now hold **9 files** (`01_specify … 09_commit`) whose numeric prefixes encode the sequential run order. Applies the 2026-07-21 exhaustive Spec Kit prompting research
- **generate-optimized-spec-kit-prompt: `/speckit.tasks` is command-only (no hand-authored tasks)** — per the research (§6, "tasks are generated, never hand-authored"), `05_tasks.md` no longer pre-writes a `Phase 1 (Setup): T001…` enumeration. It is now just `/speckit.tasks` with guidance to derive `tasks.md` from spec + plan and never hand-edit it (fix `plan.md` and regenerate instead)
- **generate-optimized-spec-kit-prompt: auto-accept gates for clarify/checklist/analyze/converge** — each of the four refine/verify stages now leads with `auto-accept all recommended options` so the pipeline runs non-interactively. `/speckit.analyze` carries a layer guard (apply fixes to plan/spec and regenerate tasks — never hand-edit `tasks.md`); `/speckit.converge` carries a loop instruction (converge → implement → converge until "converged"); `/speckit.plan` gains a stop-guard ("generate plan.md only, no tasks/code" — research trap #1011)
- **generate-optimized-spec-kit-prompt: headless runner updated to 8 stages** — `assets/speckit_pipeline.sh` `STEPS` array, per-step model/effort/max-turns getters, help text, and log headers all updated. New env-overridable per-stage defaults: `CHECKLIST_*` (opus-4-8/high), `ANALYZE_*` (opus-4-8/xhigh), `CONVERGE_*` (sonnet-5/xhigh); reasoning group = Opus, execution group = Sonnet. `references/speckit-prompt-guide.md` and `references/api_reference.md` rewritten to match (new stage templates, cross-stage EARS principles, expanded anti-pattern table)
- **Version bump**: 1.37.0 → 1.38.0

### v1.37.0 (2026-07-21)

- **constitution-generator: "minimal but enforceable" rework** — the skill now follows the exhaustive Spec Kit prompting research (2026-07-21): constitutions carry **only non-negotiable guardrails** (6–12 principles, hard cap 15; sections are a menu, not a quota) because over-constraint is the #1 constitution trap (agent over-compliance → unnecessary artifacts, context drift — Martin Fowler / den.dev). Every principle is now written in enforceable **MUST/NO** language with quantified thresholds (coverage ≥ 80%, P95 < 200ms) and carries a mandatory **`(Rationale: …)`** (agents comply better when they understand why). New required intake question: **project stage** — prototype constitutions explicitly strip CI/CD, deployment, and performance-budget articles; production keeps them. Generated prompts also instruct the agent to delete non-applicable template sections instead of padding. `references/constitution-guide.md` rewritten to match: over-constraint trap section, Rationale how-to, prototype-vs-production table, section menu (replaces the old "Required Sections (8)"), expanded anti-pattern table, and all three examples updated to the new format
- **Version bump**: 1.36.0 → 1.37.0

### v1.36.0 (2026-07-09)

- **New skill: update-readme** (`/lazy2work:update-readme`) — a grilling-style skill that audits and refreshes a project's `README.md` against README best practices while reconciling it with the current code. It reads the existing README, discovers real state from manifests/git/docs/structure, then walks a bundled rubric (`references/readme-checklist.md`, distilled from an exhaustive best-practices research report) covering the required backbone (title/pitch/why/requirements/install/usage/license/contributing), recommended sections, anti-patterns, the security "never include" list (secrets/internal URLs/PII → flag, never keep), the README-vs-AGENTS.md split, and staleness. Behavior mirrors the `grilling` pattern: **facts are resolved from the codebase directly, only decision gaps are asked — one question at a time, each with a recommended answer**; sections the user says are unneeded are omitted; raw answers are rewritten into clean scannable prose; dev/build/CHANGELOG/full-API content is routed *out* of the README rather than inlined. Skill count 11 → 12
- **Version bump**: 1.35.0 → 1.36.0

### v1.35.0 (2026-07-07)

- **generate-optimized-spec-kit-prompt: bundled headless runner** — the skill now installs `<project>/utilities/speckit_pipeline.sh` (a new bundled `assets/speckit_pipeline.sh`, copied verbatim + `chmod +x`) that executes the generated prompts end-to-end via `claude -p`. It iterates the `NNN-<slug>` feature folders under `.speckit-prompts/{prd-name}/` and runs `01_specify → … → 05_implement → commit` per feature, with per-stage model/effort (reasoning stages = opus-4-8, execution stages = sonnet-5, env-overridable), timestamped logs under `.speckit-logs/`, and `--dry-run`/`--only`/`--from`/`--resume`/`--skip-clarify`/`--no-commit` flags. SKILL.md gains a "Drop the Headless Runner Script" workflow step + checklist row; api_reference documents usage and per-stage defaults
- **generate-optimized-spec-kit-prompt: `/speckit.implement` runs all tasks in one pass** — the implement stage no longer emits `--tasks N-M` partial slicing; the generated `05_implement.md` starts with a bare `/speckit.implement` and instructs execution of the whole task list at once. Removed the "all tasks at once" anti-pattern and updated the critical rules, quality checklist, and README mirror accordingly (per-task test-and-stop verification is retained)
- **Version bump**: 1.34.0 → 1.35.0

### v1.34.0 (2026-07-06)

- **generate-optimized-spec-kit-prompt: PRD-derived parent folder name** — the output parent folder is no longer a literal `feature/`; the skill now reads the PRD and derives a short kebab-case project name itself (2-4 words, generic words like "PRD" stripped — e.g. PRD titled "일본어 학습 튜터 챗봇" → `japanese-tutor`). Output layout is now `.speckit-prompts/{prd-name}/{NNN}-{slug}/`; per-issue folder naming (issue number zero-padded to 3 digits + filename slug) is unchanged
- **generate-optimized-spec-kit-prompt: templates + checklist synced** — `references/api_reference.md` directory structure and naming convention updated to `{prd-name}/`, and the quality checklist gains a "Parent folder named from the PRD" check (README mirror updated to match)
- **Version bump**: 1.33.0 → 1.34.0

### v1.33.0 (2026-07-06)

- **generate-optimized-spec-kit-prompt: align prompt rules with official Spec Kit** — the reference guide was verified claim-by-claim against `github/spec-kit` main (command prompt sources `templates/commands/*.md` + `spec-template.md`/`tasks-template.md`); validation findings fixed:
  - `/speckit.specify` required fields and the 01_specify template now follow the official spec-template **mandatory structure**: prioritized user stories (P1/P2/P3) with an **Independent Test** statement, **Given/When/Then** acceptance scenarios, `FR-NNN` functional requirements ("System MUST ..."), measurable technology-agnostic `SC-NNN` success criteria, and Edge Cases. Open unknowns are marked inline with `[NEEDS CLARIFICATION: ...]`
  - **Removed the custom "What questions do you have?" trailing question** from specify prompts — ambiguity resolution belongs to `/speckit.clarify` in the official flow, so trailing questions are now an explicit anti-rule
  - `/speckit.tasks` switched from local `[NEW]`/`[MODIFY]`/`[TEST]` tags to the **official `[ID] [P?] [Story]` task-line format** with exact file paths (e.g. `- [ ] T012 [P] [US1] Create model in src/models/user.py`); the 04_tasks template now follows the official phase layout (Setup → Foundational (blocks all user stories) → one phase per user story in priority order)
  - `/speckit.clarify` docs corrected: the official ambiguity taxonomy has **10 categories, not 11** (all 10 now listed: Functional Scope & Behavior, Domain & Data Model, Interaction & UX Flow, Non-Functional Quality Attributes, Integration & External Dependencies, Edge Cases & Failure Handling, Constraints & Tradeoffs, Terminology & Consistency, Completion Signals, Misc/Placeholders)
  - SKILL.md critical rules + quality checklist (and the README mirror) synced to the new rules so the skill is internally consistent
- **Version bump**: 1.32.0 → 1.33.0

### v1.32.0 (2026-07-06)

- **generate-optimized-spec-kit-prompt: PRD + pre-sliced issues input** — the skill now takes two inputs (a PRD file for global context and an issues directory of vertically sliced features, one `NN-slug.md` per feature with the first issue as the environment/prefactor slice) instead of a single constitution/project file. The "Decompose into Features" step is removed — **1 issue file = 1 feature**, never merged or re-split; the issues `README.md` is treated as a dependency-order index, not a feature
- **generate-optimized-spec-kit-prompt: input → stage mapping** — `/speckit.specify` ← issue "What to build" + acceptance criteria + referenced PRD user stories (tech terms stripped to stay tech-neutral); `/speckit.plan` ← PRD implementation/testing decisions + issue tech details; `/speckit.tasks` ← issue acceptance criteria as task acceptance and issue "Blocked by" as dependency context
- **generate-optimized-spec-kit-prompt: new output layout** — feature folders now live under a single `feature/` parent as `.speckit-prompts/feature/{NNN}-{slug}/` with `{NNN}` = source issue number zero-padded to 3 digits (`00-env-compat-gate.md` → `feature/000-env-compat-gate/`), replacing the flat `feature-{NNN}-{name}/` prefix layout. Quality checklist gains 3 checks: 1:1 issue↔folder mapping, folder number = issue number, acceptance criteria present in tasks
- **Version bump**: 1.31.0 → 1.32.0

### v1.31.0 (2026-07-06)

- **up2date: global agent-skill update + dead-skill pruning** — the `--skill` path now runs **`npx skills@latest update -g -y`** to refresh every globally installed agent skill (e.g. mattpocock/skills under `~/.agents/skills/`), not just marketplace plugins and SuperClaude. Because the non-interactive updater only *warns* about skills deleted upstream ("Skipping deletion in non-interactive mode"), up2date parses that warning and **removes the dead skills itself** via `npx skills remove <names> -g -y`. Verified live: the parser correctly identified 6 upstream-deleted skills (`write-a-skill`, `zoom-out`, `diagnose`, `caveman`, `decision-mapping`, `review`) from real updater output
- **up2date: `--no-skill-prune` flag** — updates global skills but keeps the upstream-deleted ones in place (pruning is on by default with `--skill`). Global-skill update is skipped with a notice when `npx` (Node.js 18+) is unavailable
- **up2date: new helpers** — `update_global_skills()` (npx orchestration + structured result), `_parse_dead_skills()` (multi-source, deduped, ignores non-deletion bullets), `_parse_updated_count()`, and `_strip_ansi()` (ANSI-code-safe parsing of colored CLI output). 16 new TDD tests (parametrized ANSI stripping, dead-skill parsing across single/multiple/none cases, updated-count parsing, and `update_global_skills` npx-missing / parse / remove-enabled / remove-disabled / no-dead paths) — full up2date suite: 51 passing
- **Version bump**: 1.30.0 → 1.31.0

### v1.30.0 (2026-07-04)

- **NEW skill: from-speckit-to-linear** — publishes GitHub Spec Kit outputs (`spec.md` + `plan.md` + `tasks.md` from `/speckit.specify`/`plan`/`tasks`) into a Linear team as a **Project→Milestone→Issue→Sub-issue hierarchy** via the linear-server MCP. Takes a team name, verifies it with `list_teams`, then converts and records the Spec Kit artifacts Linear-appropriately. Triggers on "speckit을 linear에", "tasks.md를 linear로 발행", "spec을 linear에 정리", "publish spec kit to Linear" and similar phrasings. Sibling of from-grill-me-to-linear — same publish engine (two HITL gates, idempotent upsert, blocked-by DAG in topological order), SpecKit-specific parser and mapping
- **from-speckit-to-linear: mirror, don't re-slice** — SpecKit already finished vertical slicing (User Stories) and horizontal-foundation isolation (Foundational phase), so the skill performs a structure-preserving transfer: Setup+Foundational → an **M0 Foundation milestone** that blocks every story's first issue, User Stories P1/P2/P3 → milestones whose "done" = each story's Independent Test criterion, task lines → verb-first issues, `[P]` splits/scaffold → 1-level sub-issues. Layer-based re-decomposition (Backend/Frontend/DB issues) is an enforced anti-pattern
- **from-speckit-to-linear: SpecKit-specific rails** — parses `- [ ] T001 [P] [US1]` task lines with loose phase-header matching (SpecKit versions vary), keeps **T-IDs as the idempotency key** via a `SpecKit: T001` body footer (re-runs match by stable ID even after title rephrasing — sturdier than the title matching the grill-me sibling falls back to), folds the 40–50 FRs into acceptance-criteria checklists instead of issues, blocks publication while `[NEEDS CLARIFICATION]` markers remain (Gate ① routes to `/speckit.clarify`), and branches by scale (tiny specs skip milestones → `story:USn` labels; multi-spec features get offered an Initiative). Ships `references/mapping-rules.md` with the full conversion table, parsing rules, guardrails, and live MCP parameter notes
- **README: from-speckit-to-linear usage examples** — added a dedicated `<details>` section covering purpose (the structure-preserving path `/speckit.taskstoissues` + GitHub sync can't provide), the linear-server MCP prerequisite, slash-command and natural-language triggers, the what-lands-where mapping table, safety rails, and the T-ID → Linear-ID report format
- **Version bump**: 1.29.0 → 1.30.0

### v1.29.0 (2026-07-03)

- **NEW skill: from-grill-me-to-linear** — publishes grill-me/grill-with-docs outputs (PRD + vertical-slice issue files) into a Linear team as a **Project→Milestone→Issue→Sub-issue hierarchy** via the linear-server MCP. Takes a team name, verifies it with `list_teams`, then converts and records the PRD/issues Linear-appropriately. Triggers on "linear에 발행", "linear로 정리", "PRD를 linear에", "publish PRD to Linear" and similar phrasings
- **from-grill-me-to-linear: noise filter** — user stories, implementation/testing decisions, glossary entries, open questions, and out-of-scope items are **never created as Issues** (Linear's official anti-pattern); they are absorbed into the project brief or left as repo/ADR links. Issue titles are rewritten verb-first (`Add Stripe webhook`), and "tests pass" clauses fold into each issue's DoD checklist instead of becoming standalone issues
- **from-grill-me-to-linear: safety rails** — two HITL gates (input sanity + dry-run plan table before any write), idempotent upsert contract (`list_projects`/`list_milestones`/`list_issue_labels`/`list_issues` → reuse → update-by-id, so re-runs never duplicate — guards against real-world label drift like `type:bug` vs `Bug` coexisting), dependency DAG preserved via `blockedBy` relations published in topological order (no false milestone serialization), and a per-write ID log for resumable runs. Ships `references/mapping-rules.md` with the full conversion table, anti-pattern guardrails, and live MCP parameter notes
- **README: from-grill-me-to-linear usage examples** — added a dedicated `<details>` section covering purpose (fills the structuring gap `/to-issues` leaves), the linear-server MCP prerequisite, slash-command and natural-language triggers, the what-lands-where mapping table with the ❌ noise-filter rows, safety rails (two gates, idempotent upsert, resumable ID log), and the output report format
- **Version bump**: 1.28.0 → 1.29.0

### v1.28.0 (2026-06-12)

- **NEW skill: make-ppt-html** — converts any input document (research note, report, README, storyboard) into a presentation-quality **reveal.js 5.2.1 + Tailwind CSS single-file HTML deck with a light↔dark theme toggle** (top-right button + `D` shortcut + localStorage persistence). Triggers on "ppt로 만들어", "발표자료로", "슬라이드로 변환", "html 프레젠테이션", "make slides from this doc" and similar phrasings
- **make-ppt-html: SKILL.md workflow** — ① read document → plan 10–20 assertion-titled slides (one protagonist per slide, details into speaker notes) ② copy the bundled template ③ apply the light/dark token-pair table (every color utility outside theme-stable code cards must carry its `dark:` counterpart) ④ run static + optional browser verification. Contrast traps verified by WCAG computation are documented inline: `slate-500`-on-divider 4.34:1 fail → `slate-600`; `amber-600`/`emerald-600` text on white fail below 24px → `-700` shades; `slate-400` reserved for dark mode
- **make-ppt-html: assets/template.html** — browser-verified boilerplate with 9 slide-pattern exemplars (title, assertion+evidence, code card, comparison, table, divider/highlight, process flow, vertical appendix, conclusion). Pre-solves the reveal×Tailwind integration traps discovered during real deck production: Meyer-reset `div{border:0}` beating Preflight's universal `border-style: solid` (computed border widths forced to 0 — fixed by a scoped override), theme toggle re-syncing per-section `data-background-color` via `Reveal.sync()` (wrapper sections must stay attribute-free), `position:fixed` toggle button hidden in `?print-pdf`/`@media print`, `D`-key guard against reveal's jump-to-slide input, and UI-chrome (slide number/progress/controls) colors for both themes
- **make-ppt-html: references/design-guidelines.md** — bundled copy of the reveal.js+Tailwind slide design guideline (60-30-10 single-accent rule, contrast 7:1 target, Pretendard typography scale, hierarchy levers, layout-per-information-type mapping, prohibition list, production checklist)
- **make-ppt-html: benchmarked via skill-creator** — 2 eval documents (unicode-conversion research, monitoring-stack research) × with/without skill: with-skill passed **20/20** structural assertions (reveal structure, working dark-class toggle with persistence, `dark:` pairing, no responsive prefixes, PDF config, speaker notes, sane slide count, leaf-section backgrounds, no inline styles) vs **10/20** baseline; both baselines omitted speaker notes/PDF config, and the baseline without an explicit "reveal.js" mention invented a custom slide framework
- **marketplace.json + plugin.json sync** — descriptions mention the presentation builder; keywords extended with `reveal.js`, `tailwind`, `presentation`, `slides`; tags extended with `presentation-builder`; both manifests bumped in lockstep
- **Version bump**: 1.27.0 → 1.28.0

### v1.27.0 (2026-05-27)

- **hamilton-harness → skill 1.27.0: artifact directory renamed `build/` → `spec_build/`** — visualization and stub-generation artifacts (`stubs/`, `dags/{spec,impl,diff}/`, `reports/`, `metrics/`) now land under `hamilton_pipeline/spec_build/` instead of `hamilton_pipeline/build/`. Motivation: `build/` collides with conventional output directories used by Python packaging (`setuptools`, `hatch`, `pdm-build`), Sphinx, CMake, and many JS/TS toolchains when the pipeline lives in a polyglot repo. The directory's internal structure and contents are unchanged
- **hamilton-harness: `scripts/viz.py` default flipped** — `--output-dir` default changed from `Path("build")` to `Path("spec_build")` (one-line code change, help text updated). Users who explicitly pass `--output-dir build` get the legacy location, so existing CI scripts that already supplied the flag continue to work without modification
- **hamilton-harness: docs synchronized** — `SKILL.md` (Paths and conventions + complexity-score metrics path), `LAYOUT.md` (target-layout tree + Guardrails + working-directory note + scaffolding bullet), `DEBUG.md` (`display_upstream_of` example), `QUICKSTART.md` (Step 4 + Step 5 artifact paths), `METRICS.md` (file location and `/sc:analyze` example) all reference `spec_build/` instead of `build/`
- **hamilton-harness: templates updated** — `.gitignore.tpl` now ignores `hamilton_pipeline/spec_build/`; `CLAUDE.md.tpl` core rules and `README.md.tpl` key-directories list reference `spec_build/`; `github-workflow-dag-gate.yml` `mkdir` calls, `dump_impl_meta.py` output paths, and `upload-artifact.path` globs all use `spec_build/`
- **hamilton-harness: examples updated** — `examples/etl/README.md` (`cp spec_build/stubs/...` step) and `examples/ml-training/README.md` (PNG location) updated; example YAMLs and Python source unchanged
- **hamilton-harness: TDD regression coverage** — new `test_f3_default_output_dir_is_spec_build` asserts that running `viz.py` without `--output-dir` writes to `./spec_build/` and does **not** create a stray `./build/`; existing `test_f3_stub_is_importable` and `test_f3_mermaid_renders` migrated to `tmp_path / "spec_build"` for consistency. Full skill suite: **15 tests pass**
- **hamilton-harness: pre-existing test drift fixed** — `test_example_specs_validate` was still looking for `examples/<domain>/specs/` after the v1.20.0 `specs/ → dag_specs/` rename, causing three parametrized failures unrelated to the rename. The path is now `examples/<domain>/dag_specs/`, restoring the suite to a green baseline before the new regression test was added
- **hamilton-harness: skill CHANGELOG entry 1.27.0** — added with rationale, file-by-file change list, and a one-command migration: `cd hamilton_pipeline && git mv build spec_build` (preserves history) plus `.gitignore` and CI path updates. No Python source changes required because Hamilton modules in `src/pipelines/*.py` never imported from `build/` — only CLI invocations, CI workflows, and documentation referenced the directory
- **README: hamilton-harness skill description** — Skills table entry now mentions the `spec_build/` rename and motivation; the Target project layout tree, Guardrails bullets, F3 output paths, working-directory note, and 7-stage workflow metrics path all reference `spec_build/`; Supporting docs table updated from `currently 1.2.0` to `currently 1.27.0`
- **marketplace.json + plugin.json sync** — both manifests bumped from 1.26.0 to 1.27.0 in lockstep with the badge and plugin table
- **Version bump**: 1.26.0 → 1.27.0

### v1.26.0 (2026-05-03)

- **fix-mermaid: closing-dollar-trailing-space auto-fix (Workflow G)** — new `closing-dollar-trailing-space` rule in `fix_pandoc_blanks.py` detects inline math whose closing `$` is immediately preceded by whitespace (e.g., `$\mathcal{H}_1 = $ rest`). Pandoc's `tex_math_dollars` rule rejects such patterns, treating both `$` as literal characters and leaving any math-mode commands (`\mathcal`, `\frac`, `\hat`, `\sum`, ...) in text mode — producing fatal `! LaTeX Error: \symcal allowed only in math mode` (or similar). Auto-fix strips the offending whitespace inside the math span; visually identical because LaTeX normalizes math-mode operator spacing automatically. Skips fenced code blocks and currency-dollar patterns (handled separately by `unescaped-currency-dollar`)
- **fix-mermaid: SKILL.md Workflow G** — decision tree expanded with `\symcal allowed only in math mode` symptom; full workflow section with WRONG/CORRECT examples, root-cause table of pandoc strict-rule positions (opening `$` non-whitespace right, closing `$` non-whitespace left, closing `$` non-digit right), comparison table vs Workflows E (currency) and F (inline-code escape). Trigger keywords expanded with `symcal allowed only in math mode`, `tex_math_dollars`, `수식 닫는 달러 공백`, `닫는 $ 앞 공백`, `math mode error`
- **fix-mermaid: references/pandoc-pdf-pitfalls.md §8** — new section "Closing Dollar Preceded by Whitespace" with rule comparison matrix (§6 vs §7 vs §8), diagnostic grep patterns, prevention guidelines, and detailed explanation of why LaTeX renders `$x =$` and `$x = $` identically (math-mode operator spacing normalization)
- **fix-mermaid: README rule table + sections count** — Skills table description updated; Workflow B rule table now lists `closing-dollar-trailing-space` (error, ✅) alongside the existing six rules; `references/pandoc-pdf-pitfalls.md` section count updated from 7 to 8
- **fix-mermaid: math-aware `$` pair parser** — both `unescaped-currency-dollar` and `closing-dollar-trailing-space` rules now share `_parse_dollar_pairs(line)`, which sequentially pairs unescaped `$` characters and validates each pair against pandoc's three `tex_math_dollars` constraints (opening followed by non-whitespace, closing preceded by non-whitespace, closing not followed by digit). This **fixes critical false positives** in v1.25.0's currency-dollar rule which previously broke valid math like `$1$`, `$0, 1, 2, \ldots$`, `$1/2$`, `$0$`. The closing-dollar rule similarly avoids flagging adjacent valid math spans like `$q$와 운동량 $p$`
- **tests: `tests/test_fix_pandoc_blanks.py`** — 27 new pytest cases across `TestCheckClosingDollarTrailingSpace`, `TestFixClosingDollarTrailingSpace`, `TestCheckCurrencyDollarMathAware`, `TestCheckClosingDollarMathAware`, `TestProcessFileClosingDollarTrailingSpace` (TDD Red → Green). Covers single/multiple-space detection, currency-dollar exclusion, fenced-code skip, opening-`$`-followed-by-space exclusion, real QFT-file pattern, math-aware regression cases (`$1$`, `$0, 1, 2$`, `$1/2$`, table-row math, adjacent math spans), and the integration round-trip. Full suite: **234 tests pass** (previous 207 + new 27)
- **incident reference**: `claudedocs/quantum-computing/20260320/research_qft_first_second_quantization_exhaustive_20260320.md` lines 193 & 202 — auto-fix successfully resolves the original `\symcal allowed only in math mode` failure
- **Version bump**: 1.25.0 → 1.26.0

### v1.25.0 (2026-04-29)

- **fix-mermaid: currency-dollar auto-escape (Workflow E)** — new `unescaped-currency-dollar` rule in `fix_pandoc_blanks.py` detects every `$<digit>` that pandoc's `tex_math_dollars` extension would parse as math (e.g., `$100K`, `$76.4억`, `$1B`, `$2.58억`) and rewrites it to `\$<digit>`. Eliminates the `! LaTeX Error: Bad math environment delimiter` failure caused by odd-count currency markers leaking math mode into downstream pipe tables. Skips fenced code blocks, inline backtick spans, and already-escaped `\$`. Real math (`$x_1$`, `$\alpha$`) is provably untouched because pandoc's own rule invalidates math whose closing `$` is followed by a digit
- **fix-mermaid: unsafe-inline-code warning (Workflow F)** — new `unsafe-inline-code-escape` rule flags inline backtick code containing LaTeX-risky characters (`^`, `~`, `&`, `$`, `%`). Documents the three-layer collision behind `! Missing number, treated as zero`: pandoc escapes `^` as `\^{}`, the `pdf-korean.yaml` `\seqsplit` wrapper splits the escape per-character, and LaTeX's `\futurelet` then expects a numeric argument. Warning-only because the right fix depends on intent — three valid remediations (math mode `$\text{pass}^k$`, drop backticks, or replace `\seqsplit` with `\detokenize` in pdf-korean.yaml)
- **fix-mermaid: SKILL.md workflows E & F** — decision tree expanded; full step-by-step workflow sections added with WRONG/CORRECT examples, root-cause traces, diagnostic commands, and remediation priority order. Trigger keywords expanded to include `Bad math environment delimiter`, `Missing number, treated as zero`, `seqsplit`, `pass^k 에러`, `통화 달러`, etc.
- **fix-mermaid: references/pandoc-pdf-pitfalls.md §6 & §7** — new sections "Unescaped Currency Dollar Sign" and "Unsafe LaTeX Characters in Inline Code" with risky-character table, safety proof for the auto-fix, three-layer collision diagram, and incident links to `claudedocs/debug_md_to_pdfs_20260429.md` (1) and (2)
- **README: fix-mermaid usage** — Skills table description gained mentions of currency-dollar auto-escape and unsafe-inline-code warnings; Workflow B rule table now lists `unescaped-currency-dollar` (error, ✅) and `unsafe-inline-code-escape` (warning, manual) alongside the existing rules; example output expanded; trigger phrases include `Bad math environment delimiter`, `통화 달러 이스케이프`, `Missing number treated as zero`, `seqsplit 충돌`, `pass^k 에러`; references count updated from 5 to 7 sections
- **tests: `tests/test_fix_pandoc_blanks.py`** — 22 new pytest cases across `TestCheckCurrencyDollar`, `TestFixCurrencyDollar`, `TestCheckUnsafeInlineCode`, `TestProcessFileCurrencyDollar` (TDD Red → Green). Covers digit-after-dollar detection, escape preservation, real-math preservation, fence/inline-code masking, multi-dollar lines, and the warning-not-modified guarantee. Full suite: **207 tests pass** (previous 185 + new 22)
- **Version bump**: 1.24.0 → 1.25.0

### v1.24.0 (2026-04-20)

- **fix-mermaid: opt-in Latin-1 Supplement romanization** — `fix_pandoc_blanks.py` gained a `--latin1-normalize` flag to handle diacritics (U+00C0–U+00FF subset: `á é í ó ú ñ ü ß Æ Ø …`, 62 entries) that CJK-only mainfonts like Apple SD Gothic Neo silently drop in lualatex PDF output. Symptom: `Román Orús` renders as `Rom□n Or□s` or `Rom Or`. The flag is **off by default** because romanization is lossy on proper nouns (`Román → Roman`); callers opt in when the trade-off is acceptable
- **fix-mermaid: `check_latin1_supplement` / `fix_latin1_supplement`** — new public functions mirroring the existing unicode-glyph API. Both skip fenced code blocks and math spans (`$…$`, `$$…$$`). Detection surfaces an `Issue(rule="latin1-supplement-glyph", severity="error")` listing every found codepoint (e.g. `U+00E1 á a-acute, U+00FA ú u-acute`). `process_file` takes a new `normalize_latin1: bool = False` parameter — passing False preserves 100% of pre-existing behavior
- **fix-mermaid: SKILL.md Step D4** — documents the opt-in workflow, symptom (CJK font glyph drop), trade-off rationale (lossy vs. preserving original), and the preferred manual alternative (Korean transliteration + ASCII romanization, e.g. `로만 오루스(Roman Orus)`)
- **tests: `tests/test_fix_pandoc_blanks.py`** — 23 new pytest cases across `TestCheckLatin1Supplement`, `TestFixLatin1Supplement`, and `TestProcessFileLatin1Supplement` (TDD Red → Green). Covers acute/tilde/diaeresis detection, uppercase/lowercase variants, `ß → ss`, `Æ → AE` ligature, math/fence preservation, and the off-by-default guarantee. Full suite: **183 tests pass** (previous 160 + new 23)
- **README: fix-mermaid usage** — Skills table description mentions `--latin1-normalize`; Workflow B block gained an "opt-in" subsection (symptom + CLI examples) and the rule table now lists `unicode-glyph-missing` (always-on) and `latin1-supplement-glyph` (opt-in) alongside the existing blank-line rules
- **Version bump**: 1.23.0 → 1.24.0

### v1.23.0 (2026-04-19)

- **fix-mermaid: mmdc feedback loop (Workflow A4)** — the Mermaid CLI is now ground truth. When invoked with `--with-mmdc`, `fix_mermaid.py` applies static rules, renders every ```` ```mermaid ```` block via `mmdc`, parses the `Parse error on line N:` / `Expecting …, got 'X'` output, and iterates targeted fixes until the file renders clean or no more automatic repairs are possible (max 3 iterations, early-exit when error set is unchanged between iterations). Exit code mirrors mmdc: static-only fixes no longer fail the run if the diagrams render
- **fix-mermaid: `scripts/validate_mermaid.py`** — new mmdc wrapper (Python 3.10+, Google-style docstrings, `logging` module, full type hints). Public surface: `extract_mermaid_blocks`, `run_mmdc`, `parse_mmdc_stderr`, `validate_file`, `find_mmdc_executable`. Dataclasses (`MermaidBlock`, `MmdcError`, `MmdcResult`, `ValidationError`) map mmdc's 1-based block-internal line numbers back to the host Markdown file line. Temp files cleaned up in a `finally` block; subprocess calls carry a 60 s timeout
- **fix-mermaid: mmdc error → fix rule mapping** — `suggest_fix_for_mmdc_error(err)` classifies parse errors into `reserved-word` (auto-fixed via existing `SAFE_RENAMES`), `unquoted-label` (flagged for manual quoting; the linter refuses to silently rewrite labels), or *unknown* (reported verbatim). The feedback loop exposes the suggestions in the summary so the user knows exactly what to do next
- **fix-mermaid: SKILL.md Workflow A4 + references update** — `SKILL.md` gained a step-by-step "mmdc Validation Loop" section with prerequisites, decision tree, and example output (success + stuck cases). `references/mermaid-v11-syntax.md` gained `§ 19 mmdc Error Catalog` documenting the stderr regex, three canonical error shapes (reserved-word / unquoted-label / unclosed-subgraph), and the 5-step procedure for adding a new pattern
- **tests: `tests/test_validate_mermaid.py`** — 18 pytest cases covering `extract_mermaid_blocks` (single block, multiple blocks, no-mermaid, non-mermaid fence), `parse_mmdc_stderr` (line / got / expected / context / clean stderr / flowchart variant), `run_mmdc` (success, parse-error, argv assertion, timeout), `find_mmdc_executable` (found / missing), and end-to-end `validate_file` (clean + broken). Subprocess fully mocked
- **tests: `tests/test_fix_mermaid.py`** — 7 pytest cases covering `suggest_fix_for_mmdc_error` (reserved-word, unquoted-label, unknown), `fix_with_mmdc_feedback` (clean single-pass exit, max-iterations cap, report shape), and a regression test confirming the existing static fixer still renames reserved participant IDs. Full suite: **160 tests pass** (previous 135 + new 25)
- **README: fix-mermaid usage** — Skills table description mentions the third script and `--with-mmdc`; fix-mermaid details block gained a "with mmdc feedback loop" subsection (prerequisite, example output for success and stuck paths, recognised error table, standalone `validate_mermaid.py` invocation)
- **Version bump**: 1.22.0 → 1.23.0

### v1.22.0 (2026-04-16)

- **apply-all-sc-save: fix Claude pane detection after Claude Code upgrade** — Recent Claude Code builds (v2.1.107+) report `pane_current_command` as a semver string (e.g. `2.1.107`, `2.1.108`) instead of the literal `claude`. The old strict equality check (`command != "claude"`) silently matched zero panes, so the broadcast became a no-op for anyone on a current Claude build. Replaced with a regex that accepts both legacy (`claude`) and modern (`\d+\.\d+\.\d+`) forms, restoring detection
- **apply-all-sc-save: `scripts/save_all_claude.py`** — new public helper `_is_claude_command(command)` encapsulates the classification rule; `find_claude_panes()` delegates to it. Future Claude Code process-name changes only require updating the pattern in one place
- **tests: `tests/test_save_all_claude.py`** — 23 pytest cases covering `_is_claude_command` (parametrized across 15 command strings including legacy/version/version-with-suffix/common-non-claude), `find_claude_panes` (mocked `_run_tmux` outputs for legacy commands, version commands, self-exclusion, non-Claude filtering, empty output, malformed lines), and `send_command` (dry-run, send with Enter). Full suite: 119 tests pass (96 + 23)
- **Version bump**: 1.21.0 → 1.22.0

### v1.21.0 (2026-04-15)

- **fix-mermaid: pandoc PDF rendering coverage** — skill expanded beyond Mermaid syntax to include pandoc Markdown pitfalls that silently corrupt `pandoc -d pdf-korean` (lualatex/xelatex) PDF output. New script `scripts/fix_pandoc_blanks.py` (Google-style docstrings, Python 3.10+ type hints, 120-char lines) detects:
  - **`missing-blank-before-list|table|fence`** (severity=error, **auto-fixable**) — block elements without a preceding blank line that pandoc silently merges into the previous paragraph, producing garbled lists/tables/code in the PDF. Korean writers frequently hit this because the `**라벨**:` → list pattern omits the blank line. Script inserts a single blank line before every offending block and never touches content inside fenced code
  - **`long-mixed-cell`** (severity=warning, **manual review**) — pipe-table cells ≥ 25 chars combining `**bold**` markup with risky symbols (`·`, `—`, `–`, `+`, `(`, `)`) that defeat `\sloppy` + `\emergencystretch` + `\seqsplit` and trigger LaTeX overfull hbox. Not auto-fixed because remediation (remove bold / shorten cell / restructure table) requires human judgment
- **fix-mermaid: 3-workflow SKILL.md** — decision tree now routes users by symptom: Workflow A (Mermaid syntax) → `fix_mermaid.py`, Workflow B (blank-line compliance) → `fix_pandoc_blanks.py --fix`, Workflow C (cell overflow) → `fix_pandoc_blanks.py` warnings + manual edits. Trigger keywords extended to cover pandoc PDF symptoms ("pandoc 테이블 깨짐", "md pdf 변환 문제", "테이블이 렌더링 안됨", "overfull hbox")
- **fix-mermaid: `references/pandoc-pdf-pitfalls.md`** — new English reference document in the style of `mermaid-v11-syntax.md` (Table of Contents + numbered sections + `%% WRONG` / `%% CORRECT` examples). Five sections: (1) Missing Blank Line Before Block Elements, (2) Long Table Cells Mixing Bold and Special Symbols, (3) Font Fallback for Korean and Emoji, (4) Pre-conversion Checklist, (5) External References
- **tests: `tests/test_fix_pandoc_blanks.py`** — 31 pytest cases (TDD Red-Green-Refactor) covering `check_lines`, `fix_lines`, `check_table_cells`, `process_file`, and `Issue` dataclass. Parametrized across 6 block patterns (bullet-no-blank, bullet-with-blank, numbered-no-blank, table-no-blank, fence-no-blank, list-after-heading). Full suite: 96 tests pass
- **Version bump**: 1.20.0 → 1.21.0

### v1.20.0 (2026-04-13)

- **hamilton-harness: ML/NLP/DL library type support** — `validate.py` (L6 type resolution) and `yaml_to_hamilton_stub.py` now recognize a comprehensive set of types from the Python data/ML ecosystem so DAG nodes can declare framework-specific return types without triggering "unresolved type" warnings:
  - **Data analysis**: pandas (full type set: DataFrame, Series, Index variants, Categorical, Timestamp, etc.), polars (DataFrame/LazyFrame/Series/Expr), pyarrow (Table, RecordBatch, Array, ChunkedArray), numpy (ndarray, matrix, recarray, MaskedArray + every dtype like `np.int64`, `np.float32`, `np.complex128`), scipy.sparse (csr_matrix, csc_matrix, coo_matrix, etc.)
  - **Classical ML**: sklearn (BaseEstimator, Pipeline, FeatureUnion, ColumnTransformer, scalers, encoders), xgboost (Booster, DMatrix, XGBClassifier/Regressor/Ranker), lightgbm (Booster, Dataset, LGBMClassifier/Regressor), catboost (CatBoost, Pool, CatBoostClassifier/Regressor)
  - **Deep learning**: tensorflow (Tensor, Variable, SparseTensor, RaggedTensor, tf.data.Dataset, tf.keras.Model/Sequential/layers/losses/optimizers/callbacks/metrics), keras (Model, Sequential, layers, losses, optimizers, callbacks), pytorch (Tensor, nn.Module, nn.Parameter, Dataset, DataLoader, Optimizer, LRScheduler, distributions, torchvision), jax (Array, jnp.ndarray, PRNGKey, PyTreeDef), onnx (ModelProto, GraphProto, TensorProto)
  - **NLP**: HuggingFace transformers (PreTrainedModel/Tokenizer, every Auto* class, Pipeline, BatchEncoding, Trainer/TrainingArguments), HuggingFace datasets (Dataset, DatasetDict, IterableDataset, Features, ClassLabel), sentence-transformers (SentenceTransformer, CrossEncoder), spacy (Language, Doc, Span, Token, Vocab, Lexeme), nltk (Text, FreqDist), gensim (KeyedVectors, Word2Vec, Doc2Vec, FastText, LdaModel, TfidfModel, Dictionary)
  - **RAG / vector stores**: langchain_core (Document, BaseMessage variants, BaseLanguageModel, BaseChatModel, Embeddings, BaseRetriever, VectorStore, BaseTool, Runnable, BaseOutputParser), modern langchain provider packages (Chroma, FAISS, Pinecone, Qdrant, Weaviate, Milvus, Redis, ElasticVectorSearch, InMemoryVectorStore)
  - **Image**: PIL (Image.Image), cv2 (Mat, UMat)
  - **Validation / serialization**: pydantic (BaseModel)
  - **stdlib**: extended pathlib (Path, PurePath + all 4 platform variants), datetime (timezone, tzinfo added), io (BytesIO, StringIO, TextIOWrapper, BufferedReader/Writer, FileIO)
- **hamilton-harness: conditional import emission in stub generator** — `yaml_to_hamilton_stub.py` now walks the spec to collect every type actually used (including types nested inside subscripts like `list[pd.DataFrame]`) and emits only the import statements those types require, instead of unconditionally importing pandas/numpy. Vector store imports default to provider-specific packages (`from langchain_qdrant import QdrantVectorStore`, `from langchain_chroma import Chroma`, etc.) — adjust the path if your project pins different versions
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
