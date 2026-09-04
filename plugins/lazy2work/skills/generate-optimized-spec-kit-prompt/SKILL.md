---
name: generate-optimized-spec-kit-prompt
description: Generate optimized GitHub Spec Kit prompts for the full 8-stage flow (/speckit.specify → clarify → plan → checklist → tasks → analyze → implement → converge) for all pre-sliced feature issues of a project, organized for maximum parallel execution — a dependency DAG with a Mermaid diagram, vertical waves (one wave = one dependency chain) computed from **predicted file overlap** so sibling waves cannot collide at merge time, and a two-phase runbook: Phase 1 runs every feature as background processes in one working tree, Phase 2 runs the trunk chain then the branch chains in parallel workmux worktrees. Use when user provides a PRD file plus an issues directory (vertically sliced features, one file per feature) via @ file paths and wants complete Spec Kit prompts generated. Triggers on "speckit prompts", "generate spec kit", "specify plan tasks implement", "SDD prompts", "speckit 병렬", "wave 병렬 실행", "수직 웨이브", "백그라운드 병렬 specify", "workmux speckit", "merge conflict 없는 wave", "파일 충돌 웨이브 분할", "impact prediction", "conflict-aware waves", or when user provides a PRD + issues folder and wants full spec-driven development prompts. Assumes constitution already exists and features are already decomposed.
---

# Generate Optimized Spec Kit Prompts

Generate optimized prompts for the full **8-stage** GitHub Spec Kit flow — `/speckit.specify` → `/speckit.clarify` → `/speckit.plan` → `/speckit.checklist` → `/speckit.tasks` → `/speckit.analyze` → `/speckit.implement` → `/speckit.converge` — plus a final `/sc:git commit`, for each pre-sliced feature issue. Features arrive already decomposed (vertical slices in an issues directory); this skill does NOT re-split them. Each issue gets its own folder with 9 individual prompt files (8 stages + commit).

It additionally plans the run for **maximum parallelism** and emits the documents and scripts to execute it in **two phases**:

- **Phase 1 — spec**: every feature at once as **background processes in one working tree**. No worktrees, no branches, no merges — `specify`/`clarify` only write to `specs/{NNN}-{slug}/`, and a per-process `SPECIFY_FEATURE_DIRECTORY` keeps those disjoint.
- **Phase 2 — build**: a dependency DAG grouped into **vertical waves** — one wave is one dependency *chain*, run sequentially in its own `workmux` git worktree, with waves running concurrently. The trunk chain runs first and auto-merges into `main`; the branch chains then run in parallel off that `main`.

## Design Basis

Two research bodies plus the Spec Kit source shape this skill.

**Prompting rules** (`research_speckit_command_optimal_prompting_bestpractices_cautions_exhaustive_20260721`):

- **Tasks are generated, never hand-authored** (§6). `/speckit.tasks` scans `spec.md` + `plan.md` and produces `tasks.md` itself. The prompt must NOT enumerate `T001…` tasks — that hand-writes what the command should derive, and hand-editing `tasks.md` breaks downstream consistency. If tasks are wrong, fix `plan.md` and regenerate.
- **The refine/verify gates run non-interactively via auto-accept** (§3, §5, §7, §9). `/speckit.clarify`, `/speckit.checklist`, `/speckit.analyze`, and `/speckit.converge` each lead with `auto-accept all recommended options` — with one guardrail: `/speckit.analyze` applies fixes at the correct layer (amend plan/spec and regenerate tasks, never hand-edit `tasks.md`, §7).

**Isolation boundary** (`research_speckit_pipeline_parallel_safety_boundary_by_command_exhaustive_20260728`, corrected against Spec Kit 0.12 source):

- **The boundary is `/speckit.plan`**, because `plan` is the first stage that reads and writes the codebase. Before it, isolation is a single environment variable; after it, isolation costs a worktree.
- **Spec Kit 0.12+ resolves the active feature from `SPECIFY_FEATURE_DIRECTORY` → `.specify/feature.json`, not from the git branch**, and core `/speckit.specify` creates no branch at all (that moved to the optional git extension). This is what makes the Phase 1 fan-out safe in one working tree.
- **`/speckit.analyze` does not catch cross-feature contradictions** — it only reads its own feature's four artifacts. Global conventions must be pinned in `constitution.md` before Phase 1.
- **Waves are constrained by predicted file overlap, not by dependencies alone.** Two features with no dependency between them can still edit the same twenty files. An overlap *inside* a wave is harmless — the wave is sequential in one worktree — so a strong conflict only forbids the two features from being **siblings**. That is satisfied either by putting them in one wave or by separating stages, and the scheduler picks whichever costs less. See [references/impact-prediction-guide.md](references/impact-prediction-guide.md).
- **Vertical waves remove the "plan is blind" problem.** Every effective blocker's code is physically on disk when `plan` runs: earlier stages are merged into `main`, and earlier features in the same wave are already committed in the same worktree.

Read [references/parallel-execution-guide.md](references/parallel-execution-guide.md) for the full boundary table, the spine-decomposition wave algorithm, and workmux mechanics.

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

### 2. Build the Dependency DAG and Plan the Vertical Waves

This step runs **before** prompt generation, because the wave plan feeds the prompts (upstream context, shared-file ownership).

Follow [references/parallel-execution-guide.md](references/parallel-execution-guide.md) §3–§4. In short:

1. **Effective dependencies** — for each issue, union of (a) the declared `Blocked by`, (b) **hidden dependencies extracted from the acceptance criteria**, and (c) dependencies implied by artifacts the issue references but another issue creates. Never trust the declared graph alone; a missed dependency can place two features in sibling waves that cannot actually run concurrently.
2. **Predict each feature's file impact — one subagent per issue, run in parallel.** Follow [references/impact-prediction-guide.md](references/impact-prediction-guide.md) for the prompt contract and the output schema. Launch them 5–8 at a time; each writes exactly one file, `.speckit-prompts/{prd-name}/.impact/{feature-id}.json`, and returns nothing else. Give every subagent the repository tree (brownfield) or the constitution's directory conventions (greenfield), plus the `creates[]` and set names already declared upstream. Instruct for **recall over precision** — a missed file becomes a merge conflict, an extra file costs only a little parallelism — and require tests, docs, settings and migrations to be enumerated. A subagent that fails must write `"status": "failed"`, never an empty prediction: absent data and no overlap are different things.
3. **Write `waves.json` with `features[]` only** — `id`, `number`, `slug`, `spec_dir`, `declared_blocked_by`, `hidden_blocked_by`, `effective_blocked_by`, `hidden_reason`. Do **not** hand-author `waves[]`, `stages[]`, or `hotspots[]`; the scheduler computes them. Hand-authoring is what produced a hotspot table covering 2 of 9 genuinely shared files.
4. **Run the scheduler** — it builds the conflict graph, isolates hubs, and partitions the DAG under both precedence and file-overlap constraints:

   ```bash
   python3 <project>/utilities/{prd-name}/speckit_waves.py .speckit-prompts/{prd-name} --status provisional
   ```

   It rewrites `waves[]`, `stages[]` and `hotspots[]` in place, writes `conflict-graph.json`, and prints the repair log (which waves were merged or split, and the makespan before and after). Read that output: it is the evidence that the plan is conflict-free. The waves it emits are **provisional** — they are finalized after Phase 1 (step 6).
5. **Collect cross-feature convention candidates** — ambiguities that N concurrent `clarify` runs could resolve differently (timezone, recurrence semantics, error format, auth, logging, test strategy). These belong in `constitution.md`, not `clarify`.

Emit this analysis as three artifacts (templates in [references/api_reference.md](references/api_reference.md)):

- `DEPENDENCIES.md` — the human-readable DAG document with a **Mermaid diagram** (one subgraph per wave, chains drawn left to right), the stage/wave table, declared-vs-effective table, hidden-dependency callouts, hotspot ownership, and constitution candidates
- `waves.json` — the machine-readable stage/wave plan consumed by the runner scripts (`waves[].features` order **is** the execution order). You write `features[]`; `speckit_waves.py` computes the rest and stamps `status`
- `conflict-graph.json` + `.impact/*.json` — the computed edges and the per-feature predictions behind them (audit trail and the baseline for recall measurement)
- `PARALLEL_EXECUTION.md` — the two-phase runbook (see step 5)

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
- `/speckit.plan` — HOW only. Tech stack, architecture, file paths. No feature requirements. **MUST carry an `## Upstream Context` section** listing, per effective blocker, the concrete artifacts it provides (module paths, signatures, endpoints, model fields), where it now lives (merged into `main` from an earlier stage, or committed earlier in this wave), and an instruction to **read those files** rather than guess. Add: if a listed file is genuinely absent, STOP and report — that means the wave plan is wrong, so never build a replacement. End with a stop-guard: generate `plan.md` only, do not start tasks or code (research trap #1011).
- `/speckit.checklist` — Lead with `auto-accept all recommended options`. Unit-tests the requirements (completeness / clarity / consistency) after plan, before tasks.
- `/speckit.tasks` — Command only. Do NOT enumerate `T001…` tasks in the prompt; `/speckit.tasks` generates `tasks.md` from spec + plan. Never hand-edit `tasks.md`; fix `plan.md` and regenerate.
- `/speckit.analyze` — Lead with `auto-accept all recommended options`, but apply every fix at the correct layer: amend plan/spec and regenerate tasks — never hand-edit `tasks.md`. Runs before implement so gaps are caught while plan/tasks are still adjustable.
- `/speckit.implement` — RULES only. Run **all tasks in one pass**, per-task verify + commit, stop-and-report on failure. No design changes. **MUST carry a `## Shared Infrastructure` section** for every hotspot the feature touches: the owner, the owner's wave, and the idempotent form of the edit — plus "do not reorder or restructure" for non-owners, since sibling waves merge whole chains into the same file.
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
    ├── DEPENDENCIES.md          ← DAG (Mermaid) + stages/waves + hidden deps + hotspots
    ├── PARALLEL_EXECUTION.md    ← two-phase runbook (background fan-out + wave worktrees)
    ├── waves.json               ← machine-readable stage/wave plan (read by the scripts)
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
| 9 | `09_commit.md` | `/sc:git commit` | end of a build feature (Phase 1 commits once, from the driver) |

**Folder naming**: `{prd-name}/{NNN}-{kebab-case-name}`

- `{prd-name}` — a short kebab-case project name you derive from the PRD (title/product name, 2-4 words; strip generic words like "PRD"). Example: PRD titled "일본어 학습 튜터 챗봇" → `japanese-tutor`.
- `{NNN}` — source issue number zero-padded to 3 digits (`00` → `000`, `08` → `008`).
- `{kebab-case-name}` — issue filename slug with the number prefix removed (e.g. `00-env-compat-gate.md` → `{prd-name}/000-env-compat-gate/`).

The folder name is the feature `id` used throughout `waves.json`, branch names, and status files — keep them identical.

**File content**: Each stage file contains only the prompt for that stage. Do not include frontmatter (YAML `---` blocks). The first line of each file must start directly with the command (`/speckit.specify`, `/speckit.clarify`, `/speckit.plan`, `/speckit.checklist`, `/speckit.tasks`, `/speckit.analyze`, `/speckit.implement`, `/speckit.converge`, or `/sc:git`).

### 5. Install the Runner Scripts and workmux Config

After writing the prompts, install the bundled execution assets so the user can run the pipeline sequentially or in parallel.

**Copy verbatim** (do NOT hand-retype these — copy the asset files so they stay byte-for-byte correct), then `chmod +x` each:

**Scripts go in a per-project folder: `utilities/{prd-name}/`, never directly in `utilities/`.**
Each script derives its project from its own directory name, so
`utilities/loan-review/wm_pre_merge_gate.sh` knows it belongs to `.speckit-prompts/loan-review`.
That is what makes a repo with several Spec Kit projects unambiguous — see **Why a per-project folder** below.

| Asset | Destination | Role |
|-------|-------------|------|
| `assets/speckit_pipeline.sh` | `<project>/utilities/{prd-name}/speckit_pipeline.sh` | headless stage runner (phase/wave aware) — single source of stage/model/effort logic and of the feature-directory pin |
| `assets/speckit_parallel.sh` | `<project>/utilities/{prd-name}/speckit_parallel.sh` | driver — Phase 1 background fan-out, Phase 2 stage-by-stage workmux waves |
| `assets/wm_stage_runner.sh` | `<project>/utilities/{prd-name}/wm_stage_runner.sh` | in-worktree pane script — derives the wave from the branch name |
| `assets/wm_pre_merge_gate.sh` | `<project>/utilities/{prd-name}/wm_pre_merge_gate.sh` | quality gate — `pre_merge` hook for build, direct call for the Phase 1 spec gate |
| `assets/speckit_waves.py` | `<project>/utilities/{prd-name}/speckit_waves.py` | wave scheduler — conflict graph, hub isolation, precedence + overlap partition |
| `assets/conflict-policy.toml` | `<project>/.speckit-prompts/{prd-name}/conflict-policy.toml` | per-project grade overrides and hub threshold (optional; defaults apply if absent) |

### Why a per-project folder

A repo accumulates Spec Kit projects — a finished one and the one you are building now. The scripts
resolve `waves.json` by scanning `.speckit-prompts/`, and **scanning is ambiguous the moment there are two.**
An earlier version picked `sort | head -1`, so the alphabetically-first project always won and every wave of
every other project failed the merge gate with "no such wave in waves.json". The gate is invoked by the
`pre_merge` hook **with no arguments**, so there was no way to correct it from configuration — every wave of
the second project was permanently unmergeable.

Putting the scripts under `utilities/{prd-name}/` makes the answer structural: the folder name *is* the
project. Resolution order is now `--prompts` → `SPECKIT_PROMPTS_DIR` → **folder name** → scan for the file
that actually contains the requested wave (never "the first file found"). The scripts still work from a bare
`utilities/` for backward compatibility, falling back to the corrected scan.

It also keeps a finished project's scripts pinned to the version that ran it, instead of being overwritten
by the next project's install.

**Fill in and write** `assets/workmux.yaml.template` → `<project>/.workmux.yaml`, replacing:

- `{{ MAIN_BRANCH }}` — resolve from the repo (`git symbolic-ref --short HEAD` on a clean main, or the repo's default branch)
- `{{ SCRIPTS_PATH }}` — `utilities/{prd-name}` (the folder you just installed the four scripts into)
- `{{ PROMPTS_PATH }}` — `.speckit-prompts/{prd-name}`
- `{{ FILES_COPY }}` / `{{ POST_CREATE }}` — derive from the PRD's tech stack (e.g. `- .env` and `- 'uv sync --frozen'` for a uv-based Python project; `- 'npm ci'` for Node). If nothing applies, write `[]` for `files.copy` and drop the `post_create` key.
- `{{ VERIFY_CMD }}` — the project's own verification command for the build gate. **Measure the baseline before writing it**: run the project's test command once and look at the *exit code*, not just the summary. A brownfield repo very often exits non-zero on a clean tree (integration tests that need a live server, known xfails, environment-gated suites), and the gate treats any non-zero exit as a merge failure — so an unmeasured value blocks every wave forever while the driver reports only "conflict or gate". Narrow the command until it is green on the untouched baseline (`--deselect`/`--ignore` the known-failing paths, `-m 'not integration'`, and so on) and say in the file which paths you excluded and why. Do **not** chain lint or type checks with `&&`: those carry their own baselines and fail for the same reason. If the project genuinely has no runnable check, write `skip` and tell the user the gate is disabled.

If any destination already exists, do not clobber it silently — diff and ask the user before overwriting. For an existing `.workmux.yaml`, merge in `layouts.speckit` and `pre_merge` rather than replacing the file.

**Then report the two pre-flight actions the user must take** (these are mechanical failures, not suggestions):

```bash
git rm --cached .specify/feature.json 2>/dev/null; echo '.specify/feature.json' >> .gitignore
echo '.speckit-logs/' >> .gitignore
```

**Usage summary to give the user:**

```bash
# Phase 1 → finalize → Phase 2. Finalizing is mandatory: `build` refuses
# to run while the wave plan is still provisional.
./utilities/{prd-name}/speckit_parallel.sh spec              # Phase 1
#   … re-predict impact for any feature whose spec.md changed, then:
python3 ./utilities/{prd-name}/speckit_waves.py .speckit-prompts/{prd-name} --status final
./utilities/{prd-name}/speckit_parallel.sh build             # Phase 2

# Sequential (single process, no worktrees) — unchanged from before
./utilities/{prd-name}/speckit_pipeline.sh .speckit-prompts/{prd-name}
./utilities/{prd-name}/speckit_pipeline.sh .speckit-prompts/{prd-name} --phase build --wave w1-scheduling

# Parallel
./utilities/{prd-name}/speckit_parallel.sh waves            # show the stage/wave plan
./utilities/{prd-name}/speckit_parallel.sh spec --dry-run   # Phase 1 preview
./utilities/{prd-name}/speckit_parallel.sh spec             # Phase 1 — all features, background, one working tree
./utilities/{prd-name}/speckit_parallel.sh build            # Phase 2 — trunk stage, merge, then branch waves in parallel
./utilities/{prd-name}/speckit_parallel.sh build --from-stage 1   # resume after fixing a stage
```

Because the scripts live under `utilities/{prd-name}/`, they default to `.speckit-prompts/{prd-name}`
and need no `--prompts` even when the repo holds several Spec Kit projects.

Phase 1 needs neither workmux nor tmux — only Phase 2 does.

Per-stage model/effort defaults are Opus for the reasoning stages (specify, clarify, plan, checklist, analyze, converge) and Sonnet for the execution stages (tasks, implement), overridable via env vars. `MAX_TURNS` defaults to 2000.

**Models are never pinned to a version.** At run start the pipeline resolves "the newest Opus / Sonnet available right now" once and holds it for the whole run — `SPECKIT_OPUS_MODEL`/`SPECKIT_SONNET_MODEL` if pinned, else the Models API (`GET /v1/models`, newest by `created_at`, needs `ANTHROPIC_API_KEY`), else the CLI aliases `opus`/`sonnet` which `claude --model` resolves to the latest on its own. Resolving once rather than per call keeps a model released mid-run from splitting a project across two models; the resolved IDs are logged. Do not write a concrete model ID into the generated prompts or scripts.

> Note: the pipeline's headless preamble tells Claude to use `uv run` for Python commands. If the target project does not use `uv`, tell the user to adjust that line (or set it via the project's `CLAUDE.md`).

### 6. Finalize the Waves After Phase 1

The waves emitted at generation time are **provisional**. They were computed from
issue text, before `/speckit.clarify` resolved the `[NEEDS CLARIFICATION]` markers
that can move a feature's scope — and therefore its file set.

Phase 1 does not use waves at all: `specify` and `clarify` fan out across every
feature in one working tree. So finalizing costs nothing and happens where the
information is best — after `spec.md` exists for every feature.

Tell the user to run this between the phases:

1. Re-run the impact prediction **only for features whose `spec.md` changed** during
   Phase 1, overwriting their `.impact/{feature-id}.json`.
2. Re-run the scheduler with `--status final`.
3. Read the printed repair log. If a wave split or merged, the parallel plan the user
   approved has changed, and they should see why before Phase 2 starts.

`speckit_parallel.sh build` hard-fails while `status` is `provisional` and names the
command to run. That gate exists because running Phase 2 on a stale plan fails later,
at a merge barrier, where the cause is no longer visible.

If a prediction is missing or failed, the scheduler refuses outright. Re-run that one
prediction; use `--force-trunk` only when a serialized placement is acceptable, and it
is recorded as `"placement": "unpredicted"` in `waves.json`.

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
| `DEPENDENCIES.md` exists with a Mermaid DAG | One subgraph per wave, chains drawn left to right, edges = effective dependencies |
| **Every feature has an impact prediction** | `.impact/{id}.json` exists with `status: ok`; a failure is recorded as `failed`, never as an empty file set |
| **Predictions enumerate tests, docs and migrations** | These are systematically under-predicted; in the real failure 3 of 9 shared files were tests |
| **`waves[]`/`stages[]`/`hotspots[]` are computed, not hand-written** | `speckit_waves.py` derives them from `features[]` + `.impact/*.json` |
| **No strong file overlap between sibling waves** | The scheduler guarantees it; its repair log names every wave it merged or split |
| **Completeness claims are declared and joined** | A feature asserting a set is complete may not be a sibling of one extending it — invisible to file overlap |
| `conflict-graph.json` exists next to `waves.json` | Audit trail: edges, grades, hubs, augmentation counts, repair log |
| `waves.json` carries `status` | `provisional` at generation, `final` after Phase 1; `build` refuses provisional |
| Hidden dependencies extracted from ACs | Declared-vs-effective differences called out explicitly |
| **Waves are chains, not depth levels** | Spine → trunk wave; each gap component → one branch wave; features ordered topologically inside |
| **No edge crosses sibling waves** | A blocker is earlier in the same wave or in an earlier stage — otherwise merge the two waves |
| Stages alternate trunk and branch groups | `stages[]` ordered; a trunk stage holds exactly one wave |
| Every wave has a name, title, kind, and rationale | `w{N}-{kebab-theme}` + human title + `trunk`/`branch` + what the chain delivers |
| `waves.json` matches the folder names | `features[].id`, `waves[].features`, and `specs/` directory names are all identical |
| `waves[].features` is in execution order | The runner follows the array, not the folder numbering |
| Hotspot table has owner + owner wave + idempotency rule | Ownership pushed into the trunk where possible |
| Constitution candidates listed | Cross-feature conventions that `clarify` must not decide independently |
| `PARALLEL_EXECUTION.md` exists | Pre-flight, both phase commands, monitoring, failure recovery, merge-conflict guidance |
| 5 scripts installed + `chmod +x` | pipeline, parallel, stage runner, pre-merge gate, wave scheduler |
| Scripts live in `utilities/{prd-name}/`, **not** bare `utilities/` | The folder name is how each script resolves its project; a bare install is ambiguous once a second project exists |
| `.workmux.yaml` references scripts via `{{ SCRIPTS_PATH }}` | Both the pane command and the `pre_merge` hook — a bare `utilities/…` path breaks per-project resolution |
| No script resolves `waves.json` with `head -1` | Resolution must pick the file **containing the requested wave**, never "the first file found" |
| No hardcoded model version anywhere | Prompts and scripts name no concrete model ID; the runner resolves the latest Opus/Sonnet at run start |
| `.workmux.yaml` has a **single-pane** `speckit` layout | Two panes deadlock `-W`/`--max-concurrent` |
| `pre_merge` passes an explicit `SPECKIT_VERIFY_CMD` | Verified green against the untouched baseline; no `&&`-chained lint/type checks |
| That env var is passed via `env VAR=...`, not `VAR=...` | `VAR=value cmd` is shell syntax and dies if the hook is exec'd without a shell |
| The pane command **ends with `; exit`** | The command runs in a shell; without it the shell survives the script and the window never closes |
| `.workmux.yaml` uses `merge_strategy: merge` | A wave carries a chain of commits; rebase replays each through the same conflict |
| Pre-flight actions reported to the user | `.specify/feature.json` untracked + `.speckit-logs/` ignored + no `before_specify` git hook |

## References

- **Prompt rules**: [references/speckit-prompt-guide.md](references/speckit-prompt-guide.md) — what each stage must/must not include
- **Parallel execution**: [references/parallel-execution-guide.md](references/parallel-execution-guide.md) — safety boundary, wave algorithm, workmux mechanics
- **Impact prediction and waves**: [references/impact-prediction-guide.md](references/impact-prediction-guide.md) — subagent contract, grading, conflict graph, scheduler, probes
- **Output format**: [references/api_reference.md](references/api_reference.md) — file naming and templates
- **Assets**: [assets/](assets/) — `speckit_pipeline.sh`, `speckit_parallel.sh`, `wm_stage_runner.sh`, `wm_pre_merge_gate.sh`, `speckit_waves.py`, `conflict-policy.toml`, `workmux.yaml.template`
