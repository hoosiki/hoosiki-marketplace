# Mapping rules — Spec Kit outputs → Linear objects

Full conversion table, parsing rules, and anti-pattern guardrails.
Source: Linear-ingestion research series (2026-06-22 → 2026-07-02: SpecKit
vertical/horizontal slicing mapping, PRD→4-layer worked example, grill-me
conversion study), verified against the live `linear-server` MCP schemas.

## 1. Input artifacts (what the parser must know)

`specs/NNN-feature-name/` per feature:

| File | Produced by | Structure | Role here |
|---|---|---|---|
| `spec.md` | `/speckit.specify` | 3–5 prioritized User Stories (P1/P2/P3), each with an **Independent Test** criterion and its own MVP scope; ~10 FRs per story, 40–50 per spec | Source of Project name/brief and Milestone definitions |
| `tasks.md` | `/speckit.tasks` | Phase structure + task lines (below) | Direct source of Issues |
| `plan.md` | `/speckit.plan` | Tech stack / architecture decisions | ❌ link-only, never issues |
| `constitution.md` | `/speckit.constitution` | Project principles | ❌ link-only |

### 1.1 tasks.md phase structure

```
Phase 1: Setup            — init, dependencies              (no story label)
Phase 2: Foundational     — blocking prerequisites, shared  (★ the only legal
                            models/base                        horizontal slice)
Phase 3: User Story 1 (P1)— 🎯 MVP, independently testable   [US1]
Phase 4: User Story 2 (P2)                                   [US2]
Phase 5: User Story 3 (P3)                                   [US3]
Phase N: Polish           — errors/accessibility/perf        (no story label)
```

MVP = Phases 1–3 (Setup + Foundational + first story). Phase headers vary
across SpecKit versions — **match keywords loosely** (`Setup`, `Foundational`,
`User Story \d`, `Polish`), not exact strings.

### 1.2 Task line tokens

```
- [ ] T001 [P] [US1] Description with file path
```

| Token | Meaning | Linear mapping |
|---|---|---|
| `T001` | Stable task ID | **Idempotency key** — keep as a `SpecKit: T001` footer in the issue body |
| `[P]` | Parallelizable (different files) | Sub-issue candidate (only when it needs independent tracking) |
| `[USn]` | Story assignment | Which milestone the issue lands in |
| (no label) | Setup/Foundational/Polish bucket | M0 Foundation or Polish handling |

## 2. Conversion table

| Spec Kit artifact | → Linear object | Rule |
|---|---|---|
| Feature/spec (1 dir) | **Project** (single owner, outcome-style name, spec/plan linked) | Always 1 spec = 1 Project |
| User Story P1 (MVP) | **Milestone "M1"** | Independent Test = the milestone's "done" definition |
| User Story P2, P3… | **Milestones M2, M3…** | Priority = target-date order, not execution order |
| **Phase Setup + Phase Foundational** | **Milestone "M0 Foundation"** | The only legal horizontal piece (walking skeleton); blocks every story; close first |
| Phase Polish | Last milestone, or fold into issue DoDs | Judge by size |
| One task line | **Issue** (verb-first title, ≤2 days) | `T001` preserved in body |
| `[P]` splits / scaffold detail | **Sub-issue** (`parentId`) — 1 level max | Only when independently tracked; else body checkboxes |
| Functional Requirements (40–50) | ❌ never issues → **AC checklists in issue bodies** | The core over-granulation filter |
| User-story narration ("As a user…") | ❌ never an issue title → milestone name/description + project brief | Linear's official anti-pattern |
| plan.md / constitution.md | ❌ → project document links | Re-entry causes drift; files stay SSOT |
| Out of Scope | ❌ → one line in the project description (brief) | Keeps the ≤255-char `summary` free for the actual summary |
| Story dependencies | **blocked-by relations (DAG)** | Never milestone sequence |
| Sprint timebox | **Cycle** (optional, orthogonal) | Milestone = scope, Cycle = time |

## 3. Hierarchy & scale branches

```
Project      = spec.md                       (save_project)
 ├ M0        = Setup + Foundational          (save_milestone; close first)
 ├ M1..Mn    = User Stories                  (save_milestone)
 │   └ Issue = task (T-ID)                   (save_issue; project+milestone)
 │      └ Sub= [P]/scaffold, 1 level         (save_issue; parentId)
 └ Polish    = last milestone or DoD lines
```

| Scale | Structure |
|---|---|
| 1 spec = 1 cohesive feature (typical) | Spec=Project · Story=Milestone · Task=Issue |
| Huge feature (multiple specs) | **Initiative**=feature · Project per spec · Milestone per story |
| Tiny spec (1–2 stories) | Skip milestones → `story:USn` labels · Task=Issue directly |
| Solo, single project | No Initiative, no Cycles (overkill) |

## 4. Dependency (DAG) rules

- M0 Foundation blocks the first issue of every story milestone.
- Typical shape: `Foundation → US1(MVP)`, then `US2/US3…` depend only on
  Foundation (or a specific story) and run **in parallel** — never serialize
  them via milestone numbering.
- Story priority (P1/P2/P3) ≠ execution order — a P2 "MVP foundation" story
  can legitimately precede P1. Express order via the DAG + milestone target
  dates only.
- Publish in **topological order** so `blockedBy` targets exist.
- `blockedBy`/`blocks` are **append-only**; corrections need
  `removeBlockedBy`/`removeBlocks`.

## 5. Idempotency contract

Query → reuse → create-only-if-missing, in this order:

1. `list_teams` — resolve team.
2. `list_projects` — project matching the spec name (or `NNN-slug` in its
   description) ⇒ update via `save_project(id=…)`.
3. `list_issue_labels(team)` — reuse `area:*` / `type:*` / `story:*` taxonomy.
4. `list_milestones(project)` — reuse same-name milestones.
5. `list_issues(project)` — **match by the `SpecKit: Tnnn` footer** in issue
   bodies (SpecKit's natural stable key — sturdier than title matching);
   found ⇒ `save_issue(id=…)` update, else create.

Log every created/updated ID so interrupted runs resume as updates.

## 6. Anti-pattern guardrails (reject or warn)

| Anti-pattern | Skill response |
|---|---|
| Re-slicing tasks by layer (Backend/Frontend/DB issues) | Blocked — mirror the phase structure; vertical cohesion is SpecKit's output, preserve it |
| Making 40–50 FRs into 40–50 issues | FRs are AC checklists only |
| `"As a user…"` issue titles | Story → milestone; issues verb-first plain |
| Pasting spec.md/plan.md wholesale into Linear | Hierarchy + links only; files remain SSOT (drift prevention) |
| Mapping stories to Cycles | Story → Milestone; Cycle is the orthogonal time axis |
| Folding Foundational into one story's milestone | Isolate as M0 Foundation |
| Serializing parallel stories via milestone numbers | blocked-by DAG only |
| "Write tests" as standalone issues | Fold into the related issue's DoD |
| Sub-issue nesting ≥2 levels | 1 level max |
| Publishing with `[NEEDS CLARIFICATION]` markers present | Gate ① blocks; route to `/speckit.clarify` |
| Re-publishing without T-ID matching | §5 upsert contract is mandatory |

## 7. MCP parameter notes (live schema, 2026-07)

- `save_project`: `name` + `addTeams` required on create; `description` is
  Markdown with **literal newlines**; `summary` ≤255 chars; `lead: "me"` works.
- `save_milestone`: `project` **always required**; `id` accepts name or ID.
- `save_issue`: `team`+`title` required on create; `id` (e.g. `TES-12`) for
  updates; `assignee` (not `assigneeId`) accepts `"me"`; `parentId` makes it a
  sub-issue; `milestone` accepts name or ID; `state` accepts state name
  (`"Backlog"`); `blockedBy`/`blocks`/`labels`/`links` are append-only.
- `create_issue_label`: `teamId` is a **UUID** (from `list_teams`), omit for a
  workspace-level label.
