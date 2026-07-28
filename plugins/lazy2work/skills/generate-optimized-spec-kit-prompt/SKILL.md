---
name: generate-optimized-spec-kit-prompt
description: Generate optimized GitHub Spec Kit prompts for the full 8-stage flow (/speckit.specify → clarify → plan → checklist → tasks → analyze → implement → converge) for all pre-sliced feature issues of a project, organized for maximum parallel execution — a dependency DAG with a Mermaid diagram, named waves, and a two-phase workmux runbook. Use when user provides a PRD file plus an issues directory (vertically sliced features, one file per feature) via @ file paths and wants complete Spec Kit prompts generated. Triggers on "speckit prompts", "generate spec kit", "specify plan tasks implement", "SDD prompts", "speckit 병렬", "wave 병렬 실행", "workmux speckit", or when user provides a PRD + issues folder and wants full spec-driven development prompts. Assumes constitution already exists and features are already decomposed.
---

# Generate Optimized Spec Kit Prompts

Generate optimized prompts for the full **8-stage** GitHub Spec Kit flow — `/speckit.specify` → `/speckit.clarify` → `/speckit.plan` → `/speckit.checklist` → `/speckit.tasks` → `/speckit.analyze` → `/speckit.implement` → `/speckit.converge` — plus a final `/sc:git commit`, for each pre-sliced feature issue. Features arrive already decomposed (vertical slices in an issues directory); this skill does NOT re-split them. Each issue gets its own folder with 9 individual prompt files (8 stages + commit).

It additionally plans the run for **maximum parallelism**: it derives a dependency DAG from the issues, groups them into named waves, and emits the documents and scripts needed to execute the whole project in **two phases** — all features in parallel through `specify`+`clarify`, then wave-by-wave through `plan`…`converge` — driven by `workmux` git worktrees.

## Design Basis

Two research bodies shape this skill.

**Prompting rules** (`research_speckit_command_optimal_prompting_bestpractices_cautions_exhaustive_20260721`):

- **Tasks are generated, never hand-authored** (§6). `/speckit.tasks` scans `spec.md` + `plan.md` and produces `tasks.md` itself. The prompt must NOT enumerate `T001…` tasks — that hand-writes what the command should derive, and hand-editing `tasks.md` breaks downstream consistency. If tasks are wrong, fix `plan.md` and regenerate.
- **The refine/verify gates run non-interactively via auto-accept** (§3, §5, §7, §9). `/speckit.clarify`, `/speckit.checklist`, `/speckit.analyze`, and `/speckit.converge` each lead with `auto-accept all recommended options` — with one guardrail: `/speckit.analyze` applies fixes at the correct layer (amend plan/spec and regenerate tasks, never hand-edit `tasks.md`, §7).

**Parallel safety boundary** (`research_speckit_pipeline_parallel_safety_boundary_by_command_exhaustive_20260728`):

- **The boundary is `/speckit.plan`**, because `plan` is the only stage that reads the codebase. `specify` and `clarify` are unconditionally parallel-safe; everything from `plan` onward must run in dependency waves with a merge barrier between them.
- **`/speckit.analyze` does not catch cross-feature contradictions** — it only reads its own feature's four artifacts. Global conventions must be pinned in `constitution.md` before Phase 1.
- **Two mechanical failures must be prevented up front**: feature-number auto-assignment collisions (`--number NNN`) and `.specify/feature.json` merge conflicts.

Read [references/parallel-execution-guide.md](references/parallel-execution-guide.md) for the full boundary table, wave algorithm, and workmux mechanics.

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
- **Declared** blocked-by (dependency on earlier issues)
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

### 2. Build the Dependency DAG and Plan the Waves

This step runs **before** prompt generation, because the wave plan feeds the prompts (upstream context, shared-file ownership).

Follow [references/parallel-execution-guide.md](references/parallel-execution-guide.md) §3–§4. In short:

1. **Effective dependencies** — for each issue, union of (a) the declared `Blocked by`, (b) **hidden dependencies extracted from the acceptance criteria**, and (c) dependencies implied by artifacts the issue references but another issue creates. Never trust the declared graph alone; an unreported hidden dependency produces a `plan.md` that references code that does not exist.
2. **Waves by longest-path depth** — `depth(f) = 0` if no blockers, else `1 + max(depth(blockers))`. Adjust for non-idempotent shared-file collisions.
3. **Name each wave** — `w{N}-{kebab-theme}` plus a human title and a one-sentence rationale (e.g. `w0-foundation` "Foundation", `w2-channels` "Delivery channels"). The theme comes from what the wave's features have in common.
4. **Collect the shared-infrastructure hotspots** — files more than one feature will touch, with an owner and an idempotency rule.
5. **Collect cross-feature convention candidates** — ambiguities that N concurrent `clarify` runs could resolve differently (timezone, recurrence semantics, error format, auth, logging, test strategy). These belong in `constitution.md`, not `clarify`.

Emit this analysis as three artifacts (templates in [references/api_reference.md](references/api_reference.md)):

- `DEPENDENCIES.md` — the human-readable DAG document with a **Mermaid diagram** (wave subgraphs), declared-vs-effective table, hidden-dependency callouts, hotspot ownership, and constitution candidates
- `waves.json` — the machine-readable wave plan consumed by the runner scripts
- `PARALLEL_EXECUTION.md` — the wave-by-wave workmux runbook (see step 5)

### 3. Generate 8-Stage Prompts (+ commit) per Feature

For each issue file (in issue-number order), generate all 9 prompts following strict stage separation. Read [references/speckit-prompt-guide.md](references/speckit-prompt-guide.md) for the rules on what each stage MUST and MUST NOT include.

**Input → stage mapping:**

- `/speckit.specify` ← issue "What to build" + acceptance criteria + the PRD user stories the issue references. Strip tech terms from issue text (keep it tech-neutral).
- `/speckit.clarify` ← fixed auto-accept prompt (resolves spec ambiguities before planning).
- `/speckit.plan` ← PRD implementation/testing decisions + the issue's technical details + **the Upstream Context derived from the DAG**.
- `/speckit.checklist` ← fixed auto-accept prompt (requirements-quality gate on the spec, after plan).
- `/speckit.tasks` ← command only — no hand-authored tasks. `/speckit.tasks` derives them from spec + plan.
- `/speckit.analyze` ← fixed auto-accept prompt (constitution↔spec↔plan↔tasks consistency, before implement).
- `/speckit.implement` ← rules only + **shared-infrastructure rules from the hotspot table**.
- `/speckit.converge` ← fixed auto-accept loop prompt (verify + close gaps until converged).

**Critical rules:**

- `/speckit.specify` — WHAT + WHY only. Zero tech references. Official spec-template structure (prioritized user stories with Independent Test, Given/When/Then scenarios, `FR-NNN`/`SC-NNN`); mark unknowns `[NEEDS CLARIFICATION]` — no trailing questions.
- `/speckit.clarify` — Lead with `auto-accept all recommended options`. Resolves spec ambiguities non-interactively before planning.
- `/speckit.plan` — HOW only. Tech stack, architecture, file paths. No feature requirements. **MUST carry an `## Upstream Context` section** listing, per effective blocker, the concrete artifacts it provides (module paths, signatures, endpoints, model fields) with "do NOT rebuild" — a parallel plan cannot read that code, so the prompt has to supply it. End with a stop-guard: generate `plan.md` only, do not start tasks or code (research trap #1011).
- `/speckit.checklist` — Lead with `auto-accept all recommended options`. Unit-tests the requirements (completeness / clarity / consistency) after plan, before tasks.
- `/speckit.tasks` — Command only. Do NOT enumerate `T001…` tasks in the prompt; `/speckit.tasks` generates `tasks.md` from spec + plan. Never hand-edit `tasks.md`; fix `plan.md` and regenerate.
- `/speckit.analyze` — Lead with `auto-accept all recommended options`, but apply every fix at the correct layer: amend plan/spec and regenerate tasks — never hand-edit `tasks.md`. Runs before implement so gaps are caught while plan/tasks are still adjustable.
- `/speckit.implement` — RULES only. Run **all tasks in one pass**, per-task verify + commit, stop-and-report on failure. No design changes. **MUST carry a `## Shared Infrastructure` section** for every hotspot the feature touches: the owner and the idempotent form of the edit.
- `/speckit.converge` — Lead with `auto-accept all recommended options`. Verify planned work is complete; if gaps surface as new tasks, run implement then converge again, looping until it reports "converged".
- `/sc:git commit` — Final commit after convergence completes.

**Mermaid diagram rules:**

- Include Mermaid diagrams in specify and plan where they add clarity. Always pair with 1-2 sentences of explanation text before the code block.
- `/speckit.specify` — User workflow flowcharts and user-system sequences only. No tech terms (Django, PostgreSQL, etc.) in any node or label.
- `/speckit.plan` — Architecture diagrams, API sequences, ERD, data flow, state machines, deployment diagrams. Use clear node names and edge labels.
- `/speckit.checklist`, `/speckit.tasks`, `/speckit.analyze`, `/speckit.implement`, `/speckit.converge` — No Mermaid diagrams (task dependencies, if any, are text `[DEPENDS: T001]`).
- One diagram = one concern. Do not combine architecture + sequence + ERD into a single Mermaid block.
- The dependency DAG belongs in `DEPENDENCIES.md`, never inside a stage prompt.

### 4. Write Output Files

Create output directory and write files. See [references/api_reference.md](references/api_reference.md) for the exact output templates.

**Directory**: `.speckit-prompts/` (project root)

**Structure**: All per-issue folders live under a single parent folder **named after the PRD** — read the PRD and derive a short, fitting kebab-case project name yourself (do NOT use a literal `feature/`). The three planning artifacts sit at the top of that parent folder; one folder per issue holds the 9 stage files in execution order.

```
.speckit-prompts/
└── japanese-tutor/              ← parent name derived from the PRD
    ├── DEPENDENCIES.md          ← DAG (Mermaid) + waves + hidden deps + hotspots
    ├── PARALLEL_EXECUTION.md    ← two-phase workmux runbook
    ├── waves.json               ← machine-readable wave plan (read by the scripts)
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

| # | File | Command | Phase |
|---|------|---------|-------|
| 1 | `01_specify.md` | `/speckit.specify` | 1 (spec) |
| 2 | `02_clarify.md` | `/speckit.clarify` (auto-accept) | 1 (spec) |
| 3 | `03_plan.md` | `/speckit.plan` | 2 (build) |
| 4 | `04_checklist.md` | `/speckit.checklist` (auto-accept) | 2 (build) |
| 5 | `05_tasks.md` | `/speckit.tasks` (command only) | 2 (build) |
| 6 | `06_analyze.md` | `/speckit.analyze` (auto-accept) | 2 (build) |
| 7 | `07_implement.md` | `/speckit.implement` | 2 (build) |
| 8 | `08_converge.md` | `/speckit.converge` (auto-accept loop) | 2 (build) |
| 9 | `09_commit.md` | `/sc:git commit` | both (end of phase) |

**Folder naming**: `{prd-name}/{NNN}-{kebab-case-name}`

- `{prd-name}` — a short kebab-case project name you derive from the PRD (title/product name, 2-4 words; strip generic words like "PRD"). Example: PRD titled "일본어 학습 튜터 챗봇" → `japanese-tutor`.
- `{NNN}` — source issue number zero-padded to 3 digits (`00` → `000`, `08` → `008`).
- `{kebab-case-name}` — issue filename slug with the number prefix removed (e.g. `00-env-compat-gate.md` → `{prd-name}/000-env-compat-gate/`).

The folder name is the feature `id` used throughout `waves.json`, branch names, and status files — keep them identical.

**File content**: Each stage file contains only the prompt for that stage. Do not include frontmatter (YAML `---` blocks). The first line of each file must start directly with the command (`/speckit.specify`, `/speckit.clarify`, `/speckit.plan`, `/speckit.checklist`, `/speckit.tasks`, `/speckit.analyze`, `/speckit.implement`, `/speckit.converge`, or `/sc:git`).

### 5. Install the Runner Scripts and workmux Config

After writing the prompts, install the bundled execution assets so the user can run the pipeline sequentially or in parallel.

**Copy verbatim** (do NOT hand-retype these — copy the asset files so they stay byte-for-byte correct), then `chmod +x` each:

| Asset | Destination | Role |
|-------|-------------|------|
| `assets/speckit_pipeline.sh` | `<project>/utilities/speckit_pipeline.sh` | headless stage runner (phase/wave aware) — single source of stage/model/effort logic |
| `assets/speckit_parallel.sh` | `<project>/utilities/speckit_parallel.sh` | workmux driver — two-phase, wave-by-wave, sequential merge |
| `assets/wm_stage_runner.sh` | `<project>/utilities/wm_stage_runner.sh` | in-worktree pane script — derives phase/wave/feature from the branch name |
| `assets/wm_pre_merge_gate.sh` | `<project>/utilities/wm_pre_merge_gate.sh` | `pre_merge` quality gate |

**Fill in and write** `assets/workmux.yaml.template` → `<project>/.workmux.yaml`, replacing:

- `{{ MAIN_BRANCH }}` — resolve from the repo (`git symbolic-ref --short HEAD` on a clean main, or the repo's default branch)
- `{{ PROMPTS_PATH }}` — `.speckit-prompts/{prd-name}`
- `{{ FILES_COPY }}` / `{{ POST_CREATE }}` — derive from the PRD's tech stack (e.g. `- .env` and `- 'uv sync --frozen'` for a uv-based Python project; `- 'npm ci'` for Node). If nothing applies, write `[]` for `files.copy` and drop the `post_create` key.

If any destination already exists, do not clobber it silently — diff and ask the user before overwriting. For an existing `.workmux.yaml`, merge in `layouts.speckit` and `pre_merge` rather than replacing the file.

**Then report the two pre-flight actions the user must take** (these are mechanical failures, not suggestions):

```bash
git rm --cached .specify/feature.json 2>/dev/null; echo '.specify/feature.json' >> .gitignore
echo '.speckit-logs/' >> .gitignore
```

**Usage summary to give the user:**

```bash
# Sequential (single process, no worktrees) — unchanged from before
./utilities/speckit_pipeline.sh .speckit-prompts/{prd-name}
./utilities/speckit_pipeline.sh .speckit-prompts/{prd-name} --phase build --wave w1-core-domain

# Parallel (workmux)
./utilities/speckit_parallel.sh waves            # show the wave plan
./utilities/speckit_parallel.sh spec --dry-run   # Phase 1 preview
./utilities/speckit_parallel.sh spec             # Phase 1 — all features in parallel
./utilities/speckit_parallel.sh build            # Phase 2 — wave by wave
```

Per-stage model/effort defaults are Opus for the reasoning stages (specify, clarify, plan, checklist, analyze, converge) and Sonnet for the execution stages (tasks, implement), overridable via env vars. `MAX_TURNS` defaults to 1000.

> Note: the pipeline's headless preamble tells Claude to use `uv run` for Python commands. If the target project does not use `uv`, tell the user to adjust that line (or set it via the project's `CLAUDE.md`).

## Quality Checklist

After generating everything, verify against:

### Prompts

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
| /speckit.clarify leads with auto-accept | `auto-accept all recommended options` |
| /speckit.plan references specific file paths | Not vague "follow patterns" |
| **/speckit.plan has Upstream Context** | One entry per effective blocker with concrete artifacts + "do NOT rebuild" |
| /speckit.plan has explicit exclusions + stop-guard | Prevents Docker/CI/CD creep; "generate plan.md only, no tasks/code" |
| /speckit.checklist leads with auto-accept | Requirements-quality gate, non-interactive |
| /speckit.tasks is command-only | No hand-authored `T001…`; tasks derived from spec+plan, never hand-edited |
| /speckit.analyze leads with auto-accept + layer guard | Fixes applied to plan/spec then regenerate tasks — never edit tasks.md directly |
| /speckit.implement runs all tasks in one pass | Execute the whole task list at once, per-task verify+commit |
| **/speckit.implement has Shared Infrastructure rules** | Owner + idempotent form for every hotspot the feature touches |
| /speckit.implement has failure behavior | Stop and report on failure |
| /speckit.converge leads with auto-accept loop | converge → implement → converge until "converged" |
| Success criteria are measurable | "< 1s" not "fast" |
| /speckit.specify Mermaid has no tech terms | No Django, PostgreSQL, Redis in nodes |
| /speckit.plan has architecture + API sequence diagrams | Mermaid with explanation text |
| Each Mermaid block = one concern | No combined architecture + ERD blocks |

### Parallel plan

| Check | Rule |
|-------|------|
| `DEPENDENCIES.md` exists with a Mermaid DAG | Wave subgraphs, edges = effective dependencies |
| Hidden dependencies extracted from ACs | Declared-vs-effective differences called out explicitly |
| Waves computed by longest-path depth | Every blocker sits in a strictly earlier wave |
| Every wave has a name, title, and rationale | `w{N}-{kebab-theme}` + human title + why-these-together |
| `waves.json` matches the folder names | `features[].id` and `waves[].features` are exactly the feature folder names |
| Hotspot table has an owner + idempotency rule | Per shared file touched by more than one feature |
| Constitution candidates listed | Cross-feature conventions that `clarify` must not decide independently |
| `PARALLEL_EXECUTION.md` exists | Pre-flight, phase commands per wave, monitoring, failure recovery |
| 4 scripts installed + `chmod +x` | pipeline, parallel, stage runner, pre-merge gate |
| `.workmux.yaml` has a **single-pane** `speckit` layout | Two panes deadlock `-W`/`--max-concurrent` |
| Pre-flight actions reported to the user | `.specify/feature.json` untracked + `.speckit-logs/` ignored |

## References

- **Prompt rules**: [references/speckit-prompt-guide.md](references/speckit-prompt-guide.md) — what each stage must/must not include
- **Parallel execution**: [references/parallel-execution-guide.md](references/parallel-execution-guide.md) — safety boundary, wave algorithm, workmux mechanics
- **Output format**: [references/api_reference.md](references/api_reference.md) — file naming and templates
- **Assets**: [assets/](assets/) — `speckit_pipeline.sh`, `speckit_parallel.sh`, `wm_stage_runner.sh`, `wm_pre_merge_gate.sh`, `workmux.yaml.template`
