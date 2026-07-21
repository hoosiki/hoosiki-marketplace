---
name: generate-optimized-spec-kit-prompt
description: Generate optimized GitHub Spec Kit prompts for the full 8-stage flow (/speckit.specify → clarify → plan → checklist → tasks → analyze → implement → converge) for all pre-sliced feature issues of a project. Use when user provides a PRD file plus an issues directory (vertically sliced features, one file per feature) via @ file paths and wants complete Spec Kit prompts generated. Triggers on "speckit prompts", "generate spec kit", "specify plan tasks implement", "SDD prompts", or when user provides a PRD + issues folder and wants full spec-driven development prompts. Assumes constitution already exists and features are already decomposed.
---

# Generate Optimized Spec Kit Prompts

Generate optimized prompts for the full **8-stage** GitHub Spec Kit flow — `/speckit.specify` → `/speckit.clarify` → `/speckit.plan` → `/speckit.checklist` → `/speckit.tasks` → `/speckit.analyze` → `/speckit.implement` → `/speckit.converge` — plus a final `/sc:git commit`, for each pre-sliced feature issue. Features arrive already decomposed (vertical slices in an issues directory); this skill does NOT re-split them. Each issue gets its own folder with 9 individual prompt files (8 stages + commit).

It also drops a headless runner script at `<project>/utilities/speckit_pipeline.sh` that executes those generated prompts end-to-end via `claude -p` (per-stage model/effort, resume, dry-run).

## Design Basis

This skill applies the exhaustive Spec Kit prompting research (`research_speckit_command_optimal_prompting_bestpractices_cautions_exhaustive_20260721`). Two research findings shape the biggest changes from earlier versions:

- **Tasks are generated, never hand-authored** (§6). `/speckit.tasks` scans `spec.md` + `plan.md` and produces `tasks.md` itself. The prompt must NOT enumerate `T001…` tasks — that hand-writes what the command should derive, and hand-editing `tasks.md` breaks downstream consistency. If tasks are wrong, fix `plan.md` and regenerate.
- **The refine/verify gates run non-interactively via auto-accept** (§3, §5, §7, §9). `/speckit.clarify`, `/speckit.checklist`, `/speckit.analyze`, and `/speckit.converge` each lead with `auto-accept all recommended options` so the pipeline resolves ambiguities, quality gaps, and convergence gaps without pausing for a human — with one guardrail: `/speckit.analyze` applies fixes at the correct layer (amend plan/spec and regenerate tasks, never hand-edit `tasks.md`, §7).

## Input

User provides two inputs via `@` file paths:

1. **PRD file** (e.g. `docs/prd-japanese-tutor.md`) — global context shared by every feature: problem statement, user stories, implementation/testing decisions, out of scope.
2. **Issues directory** (e.g. `docs/issues/`) — pre-sliced vertical features, **one file per feature**, named `NN-slug.md` (e.g. `00-env-compat-gate.md`, `01-sync-chat-http.md`). The first issue is typically the environment/prefactor setup slice. A `README.md` in this directory is an index (dependency order, blocked-by graph) — use it for ordering, never treat it as a feature.

**1 issue file = 1 feature.** Do not merge, split, or re-decompose issues.

## Workflow

### 1. Read and Analyze Inputs

Read the PRD and every issue file (use the issues `README.md` only for ordering/dependency info).

From the **PRD**, extract:
- Project name and purpose
- Tech stack and versions
- Architecture decisions and testing policy
- Existing code patterns (brownfield)
- Constraints and exclusions (Out of Scope)

From **each issue file**, extract:
- Feature name (from filename slug) and number (from filename prefix)
- What to build (scope of the slice)
- Acceptance criteria
- Blocked by (dependency on earlier issues)
- Referenced user story numbers (resolve against the PRD)

From either input, collect Mermaid diagrams — classify each diagram for stage placement:

**Mermaid Diagram Classification** (placement test: "Does this diagram remain valid if the tech stack changes?"):

| Diagram Type | Stage | Rationale |
|-------------|-------|-----------|
| User workflow (flowchart, no tech terms) | **specify** | WHAT — user behavior flow |
| User-system sequence (actor ↔ system) | **specify** | WHAT — user scenario visualization |
| Business process flow | **specify** | WHAT — business process |
| System architecture (components, layers) | **plan** | HOW — technical structure |
| API sequence (client ↔ server ↔ DB) | **plan** | HOW — API call chain |
| Function-level sequence (internal calls) | **plan** | HOW — internal function chain |
| ERD / data model (erDiagram) | **plan** | HOW — database schema |
| Data flow (service-to-service) | **plan** | HOW — data movement paths |
| State machine (stateDiagram) | **plan** | HOW — entity state transitions |
| Deployment structure (Docker, cloud) | **plan** | HOW — infrastructure |
| Task dependency (gantt) | **tasks** | ORDER — rarely used, text preferred |

### 2. Generate 8-Stage Prompts (+ commit) per Feature

For each issue file (in issue-number order), generate all 9 prompts following strict stage separation. Read [references/speckit-prompt-guide.md](references/speckit-prompt-guide.md) for the rules on what each stage MUST and MUST NOT include.

**Input → stage mapping:**
- `/speckit.specify` ← issue "What to build" + acceptance criteria + the PRD user stories the issue references. Strip tech terms from issue text (keep it tech-neutral).
- `/speckit.clarify` ← fixed auto-accept prompt (resolves spec ambiguities before planning).
- `/speckit.plan` ← PRD implementation/testing decisions + the issue's technical details.
- `/speckit.checklist` ← fixed auto-accept prompt (requirements-quality gate on the spec, after plan).
- `/speckit.tasks` ← command only — no hand-authored tasks. `/speckit.tasks` derives them from spec + plan.
- `/speckit.analyze` ← fixed auto-accept prompt (constitution↔spec↔plan↔tasks consistency, before implement).
- `/speckit.implement` ← rules only.
- `/speckit.converge` ← fixed auto-accept loop prompt (verify + close gaps until converged).

**Critical rules:**
- `/speckit.specify` — WHAT + WHY only. Zero tech references. Official spec-template structure (prioritized user stories with Independent Test, Given/When/Then scenarios, `FR-NNN`/`SC-NNN`); mark unknowns `[NEEDS CLARIFICATION]` — no trailing questions.
- `/speckit.clarify` — Lead with `auto-accept all recommended options`. Resolves spec ambiguities non-interactively before planning.
- `/speckit.plan` — HOW only. Tech stack, architecture, file paths. No feature requirements. End with a stop-guard: generate `plan.md` only, do not start tasks or code (research trap #1011).
- `/speckit.checklist` — Lead with `auto-accept all recommended options`. Unit-tests the requirements (completeness / clarity / consistency) after plan, before tasks.
- `/speckit.tasks` — Command only. Do NOT enumerate `T001…` tasks in the prompt; `/speckit.tasks` generates `tasks.md` from spec + plan. Never hand-edit `tasks.md`; fix `plan.md` and regenerate.
- `/speckit.analyze` — Lead with `auto-accept all recommended options`, but apply every fix at the correct layer: amend plan/spec and regenerate tasks — never hand-edit `tasks.md`. Runs before implement so gaps are caught while plan/tasks are still adjustable.
- `/speckit.implement` — RULES only. Run **all tasks in one pass**, per-task verify + commit, stop-and-report on failure. No design changes.
- `/speckit.converge` — Lead with `auto-accept all recommended options`. Verify planned work is complete; if gaps surface as new tasks, run implement then converge again, looping until it reports "converged".
- `/sc:git commit` — Final commit after convergence completes.

**Mermaid diagram rules:**
- Include Mermaid diagrams in specify and plan where they add clarity. Always pair with 1-2 sentences of explanation text before the code block.
- `/speckit.specify` — User workflow flowcharts and user-system sequences only. No tech terms (Django, PostgreSQL, etc.) in any node or label.
- `/speckit.plan` — Architecture diagrams, API sequences, ERD, data flow, state machines, deployment diagrams. Use clear node names and edge labels.
- `/speckit.checklist`, `/speckit.tasks`, `/speckit.analyze`, `/speckit.implement`, `/speckit.converge` — No Mermaid diagrams (task dependencies, if any, are text `[DEPENDS: T001]`).
- One diagram = one concern. Do not combine architecture + sequence + ERD into a single Mermaid block.

### 3. Write Output Files

Create output directory and write files. See [references/api_reference.md](references/api_reference.md) for the exact output template.

**Directory**: `.speckit-prompts/` (project root)

**Structure**: All per-issue folders live under a single parent folder **named after the PRD** — read the PRD and derive a short, fitting kebab-case project name yourself (do NOT use a literal `feature/`). One folder per issue, each containing the 9 stage files in execution order.

```
.speckit-prompts/
└── japanese-tutor/              ← parent name derived from the PRD
    ├── 000-env-compat-gate/
    │   ├── 01_specify.md
    │   ├── 02_clarify.md
    │   ├── 03_plan.md
    │   ├── 04_checklist.md
    │   ├── 05_tasks.md
    │   ├── 06_analyze.md
    │   ├── 07_implement.md
    │   ├── 08_converge.md
    │   └── 09_commit.md
    ├── 001-sync-chat-http/
    │   └── … (same 9 files)
    └── 002-persistence-auth/
        └── … (same 9 files)
```

**Stage file order** (filenames encode the sequential run order):

| # | File | Command |
|---|------|---------|
| 1 | `01_specify.md` | `/speckit.specify` |
| 2 | `02_clarify.md` | `/speckit.clarify` (auto-accept) |
| 3 | `03_plan.md` | `/speckit.plan` |
| 4 | `04_checklist.md` | `/speckit.checklist` (auto-accept) |
| 5 | `05_tasks.md` | `/speckit.tasks` (command only) |
| 6 | `06_analyze.md` | `/speckit.analyze` (auto-accept) |
| 7 | `07_implement.md` | `/speckit.implement` |
| 8 | `08_converge.md` | `/speckit.converge` (auto-accept loop) |
| 9 | `09_commit.md` | `/sc:git commit` |

**Folder naming**: `{prd-name}/{NNN}-{kebab-case-name}`
- `{prd-name}` — a short kebab-case project name you derive from the PRD (title/product name, 2-4 words; strip generic words like "PRD"). Example: PRD titled "일본어 학습 튜터 챗봇" → `japanese-tutor`.
- `{NNN}` — source issue number zero-padded to 3 digits (`00` → `000`, `08` → `008`).
- `{kebab-case-name}` — issue filename slug with the number prefix removed (e.g. `00-env-compat-gate.md` → `{prd-name}/000-env-compat-gate/`).

**File content**: Each file contains only the prompt for that stage. Do not include frontmatter (YAML `---` blocks). The first line of each file must start directly with the command (`/speckit.specify`, `/speckit.clarify`, `/speckit.plan`, `/speckit.checklist`, `/speckit.tasks`, `/speckit.analyze`, `/speckit.implement`, `/speckit.converge`, or `/sc:git`).

### 4. Drop the Headless Runner Script

After writing the prompts, install the bundled pipeline runner so the user can execute all generated prompts headlessly.

- **Copy** this skill's `assets/speckit_pipeline.sh` verbatim to `<project-root>/utilities/speckit_pipeline.sh` (create `utilities/` if missing). Do NOT hand-retype the ~700-line script — copy the asset file so it stays byte-for-byte correct.
- **`chmod +x`** the destination so it is runnable.
- If a `utilities/speckit_pipeline.sh` already exists, do not clobber it silently — diff and ask the user before overwriting.

The script reads the `NNN-<slug>` feature folders under `.speckit-prompts/{prd-name}/` (the exact layout this skill just wrote) and runs each feature through `01_specify → … → 08_converge → commit` via `claude -p`. Usage: `./utilities/speckit_pipeline.sh .speckit-prompts/{prd-name}` (plus `--only`/`--from`/`--dry-run`/`--resume`/`--skip-clarify`). Per-stage model/effort defaults are Opus for the reasoning stages (specify, clarify, plan, checklist, analyze, converge) and Sonnet for the execution stages (tasks, implement), overridable via env vars. `MAX_TURNS` defaults to 1000.

> Note: the script's headless prompt tells Claude to use `uv run` for Python commands. If the target project does not use `uv`, tell the user to adjust that line (or set it via the project's `CLAUDE.md`).

## Quality Checklist

After generating all prompts, verify each feature against:

| Check | Rule |
|-------|------|
| 1 issue file = 1 feature folder | No merging or re-splitting of issues |
| Parent folder named from the PRD | Short kebab-case project name (e.g. `japanese-tutor`), never a literal `feature` |
| `utilities/speckit_pipeline.sh` installed | Bundled runner copied verbatim + `chmod +x` |
| 9 stage files per folder in order | `01_specify … 09_commit` — filenames encode run order |
| Folder number matches issue number | `00-env-compat-gate.md` → `{prd-name}/000-env-compat-gate/` |
| Issue acceptance criteria appear in spec | Every criterion maps to a `FR-NNN` or `SC-NNN` |
| /speckit.specify has no tech terms | Tech-neutral (survives stack change) |
| /speckit.specify uses official spec-template structure | Prioritized user stories + Given/When/Then + FR-NNN/SC-NNN; no trailing questions |
| /speckit.specify has Out of Scope section | Prevents AI scope creep |
| /speckit.clarify leads with auto-accept | `auto-accept all recommended options` |
| /speckit.plan references specific file paths | Not vague "follow patterns" |
| /speckit.plan has explicit exclusions + stop-guard | Prevents Docker/CI/CD creep; "generate plan.md only, no tasks/code" |
| /speckit.checklist leads with auto-accept | Requirements-quality gate, non-interactive |
| /speckit.tasks is command-only | No hand-authored `T001…`; tasks derived from spec+plan, never hand-edited |
| /speckit.analyze leads with auto-accept + layer guard | Fixes applied to plan/spec then regenerate tasks — never edit tasks.md directly |
| /speckit.implement runs all tasks in one pass | Execute the whole task list at once, per-task verify+commit |
| /speckit.implement has failure behavior | Stop and report on failure |
| /speckit.converge leads with auto-accept loop | converge → implement → converge until "converged" |
| Success criteria are measurable | "< 1s" not "fast" |
| /speckit.specify Mermaid has no tech terms | No Django, PostgreSQL, Redis in nodes |
| /speckit.plan has architecture + API sequence diagrams | Mermaid with explanation text |
| Each Mermaid block = one concern | No combined architecture + ERD blocks |

## References

- **Prompt rules**: [references/speckit-prompt-guide.md](references/speckit-prompt-guide.md) — what each stage must/must not include
- **Output format**: [references/api_reference.md](references/api_reference.md) — file naming and template
- **Headless runner**: [assets/speckit_pipeline.sh](assets/speckit_pipeline.sh) — copy to `<project>/utilities/speckit_pipeline.sh` to execute the generated prompts via `claude -p`
