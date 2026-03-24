# Spec Kit Prompt Guide — Quick Reference

## 4-Stage Role Separation

| Stage | Role | Prompt Focus | MUST NOT Include |
|-------|------|-------------|-----------------|
| `/speckit.specify` | **What + Why** | Features, users, scenarios, constraints | Tech stack, architecture, code |
| `/speckit.plan` | **How** | Tech stack, architecture, existing code refs | Feature requirements (in spec) |
| `/speckit.tasks` | **Order** | Impl sequence, deps, TDD, task size | Tech decisions (in plan) |
| `/speckit.implement` | **Rules** | Scope, commit strategy, code style | Design changes (go back to plan) |

## /speckit.specify — Required Fields

1. Feature name + one-line description
2. Purpose (Why)
3. Users (Who) — persona + goal
4. Core features (What) — numbered list
5. User scenarios — happy path + error paths
6. Success criteria — measurable
7. Constraints — business/regulatory
8. Out of Scope — explicit
9. "What questions do you have?" — always end with this

**Rules**: WHAT & WHY only. No HOW. Tech-neutral (spec survives stack change).

## /speckit.plan — Required Fields

1. Tech stack — language, framework, DB with versions
2. Architecture pattern — structural decisions
3. Existing code references — brownfield: specific file paths
4. Non-functional requirements — performance, security, deployment
5. Explicit exclusions — things NOT to do
6. Test strategy — framework, scope

**Rules**: No feature requirements (already in spec). Reference specific file paths, not vague "follow existing patterns."

## /speckit.tasks — Required Fields

1. Implementation order — foundation → core → integration
2. Task size — 1 task = 1 commit
3. Dependencies — predecessor tasks
4. Parallel hints — `[P]` marker for independent tasks
5. TDD flag — test-first or test-after
6. Tags — `[MODIFY]` existing file, `[NEW]` new file, `[TEST]` test
7. Acceptance criteria per task

**Rules**: No tech decisions (already in plan). Keep tasks small.

## /speckit.implement — Required Fields

1. Scope — `--tasks N-M` for partial impl
2. Commit strategy — per-task commit
3. Code style — formatter, docstring, type hints
4. Verification — test after each task
5. Failure behavior — stop and report on test failure

**Rules**: Never implement all tasks at once. Go back to /speckit.plan if design change needed.

## Feature Sizing

- 1 person, 1-5 days to complete
- If larger, split into sub-features
- Each feature should be independently deployable

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|-------------|-----------------|
| Tech stack in /speckit.specify | Tech decisions only in /speckit.plan |
| All tasks at once in /speckit.implement | `--tasks 1-3` partial impl |
| Spec change without re-plan | spec change → re-plan → re-tasks |
| Skip output review | Manual review after each stage |
| Vague success criteria ("fast") | Measurable ("< 1 second") |
| Missing Out of Scope | Always specify to prevent AI scope creep |
| Feature too large | Split to 1-5 day units |
