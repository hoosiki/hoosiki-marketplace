# Spec Kit Prompt Guide — Quick Reference

Applies the exhaustive Spec Kit prompting research (`research_speckit_command_optimal_prompting_bestpractices_cautions_exhaustive_20260721`). Prompt density differs per stage: **think in detail up front (specify/plan), act briefly at the back (tasks/analyze/implement/converge).**

## 8-Stage Role Separation (+ commit)

| # | Stage | Role | Prompt Focus | MUST NOT Include |
|---|-------|------|-------------|-----------------|
| 1 | `/speckit.specify` | **What + Why** | Features, users, scenarios, constraints | Tech stack, architecture, code |
| 2 | `/speckit.clarify` | **Refine** | `auto-accept all recommended options` — resolve spec ambiguities | Manual intervention |
| 3 | `/speckit.plan` | **How** | Upstream context, tech stack, architecture, file paths, stop-guard | Feature requirements; starting tasks/code |
| 4 | `/speckit.checklist` | **Requirements QA** | `auto-accept all recommended options` — completeness/clarity/consistency | Implementation detail |
| 5 | `/speckit.tasks` | **Order (generated)** | Command only — derive tasks from spec+plan | Hand-authored `T001…`; tech decisions |
| 6 | `/speckit.analyze` | **Cross-check** | `auto-accept all recommended options` — 4-way consistency, fix at correct layer | Hand-editing tasks.md |
| 7 | `/speckit.implement` | **Rules** | Shared-file ownership, scope (all tasks, one pass), commit, failure behavior | Design changes |
| 8 | `/speckit.converge` | **Close gaps** | `auto-accept` loop — converge → implement → converge until done | Manual gap triage |
| — | `/sc:git commit` | **Commit** | Final commit after convergence | Design changes, new features |

## Cross-Stage Principles (research §0)

1. **EARS-style acceptance criteria** — every requirement is a testable "shall/MUST" statement (Given/When/Then in the spec).
2. **Atomic + testable** — "it should work well" is not a requirement; use measurable triggers/responses.
3. **Explicit Out of Scope** — what you are NOT building matters as much as what you are.
4. **Typed blocks, not a blob** — separate role/objective/constraints/criteria visually so the model processes each.
5. **Human review at stage boundaries** — the auto-accept gates automate the *inner* decisions; the user still reviews between features.

## /speckit.specify — Required Fields

Aligned with the official spec-template mandatory sections:

1. Feature name + one-line description
2. Purpose (Why)
3. User stories — prioritized (P1, P2, P3...), each independently testable with an **Independent Test** statement
4. Acceptance scenarios — **Given/When/Then** format per user story
5. Edge cases — boundary conditions and error scenarios
6. Functional requirements — numbered `FR-NNN` ("System MUST ..."); mark unknowns as `[NEEDS CLARIFICATION: ...]`
7. Success criteria — numbered `SC-NNN`, measurable and technology-agnostic
8. Constraints — business/regulatory
9. Out of Scope — explicit

**Rules**: WHAT & WHY only. No HOW. Tech-neutral (spec survives stack change). Do NOT append trailing questions ("What questions do you have?") — the official flow resolves ambiguity via `/speckit.clarify`, and open unknowns are marked inline with `[NEEDS CLARIFICATION]`. Keep it 1-3 pages; one feature = one spec (never a whole-app spec).

## /speckit.clarify — Auto-Accept Mode (research §3)

1. Scans spec for ambiguities across the official 10-category taxonomy (Functional Scope & Behavior, Domain & Data Model, Interaction & UX Flow, Non-Functional Quality Attributes, Integration & External Dependencies, Edge Cases & Failure Handling, Constraints & Tradeoffs, Terminology & Consistency, Completion Signals, Misc/Placeholders)
2. Generates up to 5 clarification questions (one at a time)
3. Automatically selects the recommended/suggested option for each (no user input)
4. Integrates answers into the spec's `## Clarifications` section

**Rules**: Lead with `auto-accept all recommended options`. Runs **before plan** — ambiguity resolved after planning would already have propagated into a wrong plan/tasks.

## /speckit.plan — Required Fields (research §4)

1. **Upstream Context** — per effective blocker, the concrete artifacts it provides (module path, symbol, signature, endpoint, model fields), where it now lives (merged into `main` from an earlier stage, or committed earlier in this wave), an instruction to **read those files**, and "do NOT rebuild". Required whenever the feature has blockers.
2. Tech stack — language, framework, DB with versions
3. Architecture pattern — structural decisions
4. Existing code references — brownfield: **exact file paths + function signatures + API contracts** (ambiguity here causes the "duplicate-file" disaster where the agent creates new files instead of editing existing ones)
5. Non-functional requirements — performance (quantified), security, deployment
6. Explicit exclusions — things NOT to do
7. Test strategy — framework, scope
8. **Stop-guard** — "generate `plan.md` only; do not start tasks or write code" (research trap #1011: some agents auto-start coding at plan)

**Rules**: No feature requirements (already in spec). Reference specific file paths, not vague "follow existing patterns." Distinguish existing vs new code explicitly.

**Why Upstream Context is mandatory**: `plan` is the first stage that reads the codebase, which is why it is the isolation boundary. With **vertical waves** the blocker's code *is* on disk when `plan` runs — merged into `main` from an earlier stage, or committed earlier in the same wave's worktree — so this section is not a substitute for missing code. Its job is to point `plan` at the right files so it reads them instead of inventing a parallel implementation, and to make absence *loud*: a listed file that genuinely does not exist means the wave partition is wrong, so the prompt must say **STOP and report**, never "create it". See [parallel-execution-guide.md](parallel-execution-guide.md) §1, §4, §7.

## /speckit.checklist — Requirements-Quality Gate (research §5)

Runs **after plan, before tasks**. Think of it as "unit tests for the requirements (the English)."

1. Lead with `auto-accept all recommended options` (auto-select focus areas, run non-interactively)
2. Validate the spec for completeness, clarity, and consistency
3. Report items tagged `[Completeness]` / `[Edge case]` / `[Consistency]` / `[Clarity]` (e.g. "Is fallback defined when the list is empty? [Edge case]")
4. Auto-resolve fixable gaps by accepting the recommended resolution

**Rules**: Treat as an always-on gate, not optional. Requirements QA only — no implementation detail.

## /speckit.tasks — Command Only, Generated (research §6)

**Do NOT hand-author tasks.** `/speckit.tasks` scans `spec.md` + `plan.md` and generates `tasks.md` itself. The prompt is essentially just the command.

- Official generated format: `- [ ] T001 [P] [US1] Description with exact file path` — `[P]` = parallelizable (different files, no deps), `[USn]` = user-story tag.
- TDD tasks precede their implementation tasks; one task ≈ one commit.
- **Never hand-edit `tasks.md`.** If tasks are wrong, fix `plan.md` (or `spec.md`) and regenerate — hand-editing breaks constitution↔spec↔plan↔tasks consistency.

**Rules**: No enumerated `T001…` in the prompt (that hand-writes what the command derives). No tech decisions (already in plan).

## /speckit.analyze — Cross-Check, Correct-Layer Fixes (research §7)

Runs **after tasks, before implement**. Cross-checks `constitution ↔ spec ↔ plan ↔ tasks` for consistency, coverage, duplicate logic, uncovered requirements, and hygiene (lint/security markers).

1. Lead with `auto-accept all recommended options`
2. **CRITICAL layer guard**: apply each fix at the correct layer. A finding that implies a task change means amend `plan.md` (or `spec.md`) and **regenerate** tasks via `/speckit.tasks` — never hand-edit `tasks.md` directly (research §7, the rule beginners most often break).
3. First analyze must run **before** implement, so gaps are caught while plan/tasks are still adjustable.

**Rules**: For higher confidence, analyze can be re-run with a second model until findings converge.

## /speckit.implement — Required Fields (research §8)

1. **Shared Infrastructure** — per hotspot file the feature touches: the owning feature and the idempotent form of the edit. Required whenever another feature also writes that file.
2. Scope — implement all tasks in one pass (no `--tasks N-M` slicing)
3. Commit strategy — per-task commit (Commit Regularly)
4. Code style — formatter, docstring, type hints
5. Verification — test after each task (Verify Frequently)
6. Failure behavior — stop and report on test failure

**Rules**: Implement the entire task list at once. Go back to `/speckit.plan` if a design change is needed — never redesign inside implement.

**Why Shared Infrastructure is mandatory**: settings/installed-apps modules, API routers, and dependency manifests are written by nearly every feature. A vertical wave lands a whole chain of commits at one merge barrier, so sibling waves' hotspot edits all collide at once. Idempotent edits are what let waves merge cleanly — and they only hold if merges are sequential. State the owner, the owner's wave, and the idempotent form; "append if absent" is a rule, "add the app" is not. Non-owners must also be told not to reorder or restructure the file.

## /speckit.converge — Close Gaps in a Loop (research §9)

Runs **after implement**. Verifies planned work is complete and closes remaining gaps.

1. Lead with `auto-accept all recommended options`
2. If converge surfaces remaining gaps as new tasks → run `/speckit.implement` on them → run `/speckit.converge` again
3. Repeat the converge → implement → converge loop until it reports **"converged"** (no new tasks)
4. Verify with the project's build/test/lint gates each round; stop and report on failure

**Rules**: Non-interactive — the loop auto-accepts recommended options each round rather than asking.

## /sc:git commit

Final commit after convergence completes. Fixed prompt — no per-feature customization.

**Rules**: Only commit after successful convergence. Commit message auto-generated from changes; do not push.

## Feature Source (pre-sliced issues)

- Features arrive as issue files (`NN-slug.md`), one vertical slice each — do NOT re-split or merge them
- The first issue (e.g. `00-env-*`) is the environment/prefactor setup slice; treat it as a normal feature
- Use each issue's "Blocked by" for implementation order and task dependency context — but **the declared graph is not the real graph**. Extract hidden dependencies from the acceptance criteria too, and record declared vs effective separately (see [parallel-execution-guide.md](parallel-execution-guide.md) §3)
- Map issue acceptance criteria → measurable success criteria (specify); tasks are then generated, not transcribed

## Cross-Feature Conventions Belong in the Constitution

`/speckit.clarify` runs per feature. Whether features run in parallel or stage-major, N features resolve the same ambiguity independently — and `/speckit.analyze` only checks a feature against *its own* constitution↔spec↔plan↔tasks, so two features that adopted opposite conventions **both pass every gate**. The contradiction surfaces at implement.

Pin these globally before any `specify` runs: timezone handling, recurrence semantics, error format / failure policy, auth and authorization, logging and observability, test strategy. `analyze` reads the constitution, so anything pinned there *is* caught.

## Mermaid Diagram Placement

**Placement test**: "Does the diagram remain valid if the tech stack changes?" — Yes → specify, No → plan.

### In /speckit.specify (tech-neutral only)
- User workflow flowcharts (no tech terms in nodes/labels)
- User ↔ system sequence diagrams (actor + generic "System" participant)
- Always pair with explanation text before the code block

### In /speckit.plan (all technical diagrams)
- System architecture (graph TB with subgraphs for layers)
- API sequence diagrams (Client → View → Service → DB)
- ERD (erDiagram with entities, attributes, relationships)
- Data flow (flowchart LR showing service-to-service data movement)
- State machines (stateDiagram-v2 for entity state transitions)
- Deployment structure (Docker, cloud infrastructure)
- Always pair with explanation text before the code block

### In checklist / tasks / analyze / implement / converge (none)
- No Mermaid. Task dependencies, if any, are text `[DEPENDS: T001]`.

### Mermaid Anti-Patterns
| Anti-Pattern | Correct Approach |
|-------------|-----------------|
| Tech terms in specify Mermaid | Move to plan |
| Mermaid code without explanation text | Always add 1-2 sentences before the block |
| Multiple concerns in one Mermaid block | Split: 1 diagram = 1 concern |
| User workflow in plan | Move to specify |

## Anti-Patterns (research §10)

| Anti-Pattern | Correct Approach |
|-------------|-----------------|
| Tech stack in /speckit.specify | Tech decisions only in /speckit.plan |
| Under-specification ("works fine") | Measurable EARS acceptance criteria |
| Over-specification in spec ("use a Map") | Implementation detail belongs in plan |
| Hand-authoring or hand-editing tasks.md | Let /speckit.tasks generate; fix upstream + regenerate |
| analyze finding → edit tasks.md directly | Fix plan/spec, then regenerate tasks |
| plan agent starts coding (#1011) | Stop-guard: "generate plan.md only" |
| Brownfield vague instructions | Exact file paths, function signatures, API contracts |
| Spec change without re-plan | spec change → re-plan → re-tasks |
| Skip clarify/checklist/analyze gates | Treat them as always-on (non-interactive) |
| Prompt → merged PR with no human review | Review at feature boundaries |
| Vague success criteria ("fast") | Measurable ("< 1 second") |
| Missing Out of Scope | Always specify to prevent AI scope creep |
| Re-slicing pre-sliced issues | Keep 1 issue file = 1 feature |
| plan prompt with no Upstream Context | List every effective blocker's artifacts, where they live, and "read them, do NOT rebuild" |
| "If the file is missing, create it" in a plan prompt | STOP and report — a missing upstream file means the wave partition is wrong |
| Trusting the declared `Blocked by` graph | Extract hidden dependencies from the acceptance criteria |
| Grouping waves by depth level | Group by dependency *chain* — sequential inside a wave, parallel across waves |
| A dependency edge between sibling waves | Merge those two waves into one; never run them concurrently anyway |
| Leaving a global convention to `clarify` | Pin it in `constitution.md` — `analyze` cannot see sibling features |
| implement prompt with no shared-file ownership | Name the owner, the owner's wave, and the idempotent form of each hotspot edit |
| Writing a feature number or `create-new-feature.sh` into a prompt | The runner pins `SPECIFY_FEATURE_DIRECTORY`; a hardcoded number fights it |
