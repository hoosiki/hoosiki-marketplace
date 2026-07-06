---
name: from-speckit-to-linear
description: Publish GitHub Spec Kit outputs (spec.md + plan.md + tasks.md from /speckit.specify, /speckit.plan, /speckit.tasks) into a Linear team as a Project→Milestone→Issue→Sub-issue hierarchy via the linear-server MCP. Takes a Linear team name, mirrors the tasks.md phase structure — Setup+Foundational becomes an "M0 Foundation" milestone, User Stories P1/P2/P3 become milestones, tasks become issues keyed by their T-ID for idempotent re-runs — keeps FRs as acceptance criteria instead of issues, blocks publication while [NEEDS CLARIFICATION] markers remain, and enforces dry-run approval + blocked-by DAG ordering. Triggers on "speckit을 linear에", "tasks.md를 linear로 발행", "spec을 linear에 정리", "speckit 결과물을 linear에 기록", "speckit to linear", "publish spec kit to Linear", "ingest tasks.md into Linear", or any request to convert Spec Kit artifacts into Linear projects/milestones/issues.
---

# From Spec Kit to Linear

Convert a Spec Kit feature directory (`specs/NNN-feature-name/` with `spec.md`,
`plan.md`, `tasks.md`) into a properly structured Linear hierarchy under a
user-specified team, using the **`linear-server` MCP tools** (`list_*`,
`save_project`, `save_milestone`, `save_issue`, `create_issue_label`).

**Mental model — mirror, don't re-slice.** SpecKit already finished the
slicing work: `specify` produced vertical slices (prioritized User Stories)
and `tasks` isolated the shared horizontal foundation (Foundational phase).
This skill's job is structure-preserving transfer:

```
Project   = the spec (1 feature dir)
Milestone = each User Story  (+ one "M0 Foundation" for Setup+Foundational)
Issue     = each task line   (T-ID preserved as the idempotency key)
Sub-issue = [P] splits / scaffold details, 1 level max
```

Sibling skill: `from-grill-me-to-linear` — same publish engine (gates,
idempotent upsert, MCP calls), different input parser and mapping rules.

Detailed conversion rules live in [references/mapping-rules.md](references/mapping-rules.md)
— read it before Step 2.

## Core invariants (never violate)

1. **Mirror the tasks.md phase structure — never re-slice by layer.**
   Decomposing into Backend/Frontend/DB issues destroys the vertical slices
   SpecKit built; the only legitimate horizontal piece is the Foundational
   phase, and it gets exactly one milestone: **M0 Foundation**.
2. **Functional Requirements (often 40–50 per spec) are NEVER issues** —
   they become acceptance-criteria checklists inside issue bodies.
3. **User Story narration never becomes an issue title** — stories are
   milestones; issue titles stay verb-first plain form.
4. **Dependencies are `blockedBy` relations (DAG)** published in topological
   order — milestone numbering must not fake a serial order for parallel
   stories.
5. **Every publish is an idempotent upsert keyed by T-ID** — query first,
   reuse, update by `id`; never blind-create.
6. **Two HITL gates** — no writes before the user approves the dry-run plan.

## Prerequisites

The `linear-server` MCP must be connected. Verify by calling `list_teams`.
If the tools are unavailable, stop and tell the user to enable the Linear MCP
integration — do not fall back to the REST API or `curl`.

## Inputs (collect before doing anything)

| Input | Required | How to get it |
|---|---|---|
| **Team name** | ✅ | From user args. Verify via `list_teams` (fuzzy-match; if no match, list available teams and ask) |
| **Spec directory** | ✅ | e.g. `specs/001-user-auth/` — needs at least `spec.md` + `tasks.md`. If only one exists, ask; `plan.md`/`constitution.md` are link-only extras |
| Milestone strategy | optional | Default: 1 User Story = 1 milestone + M0. Tiny specs (1–2 stories) may skip milestones → story labels (ask at Gate ②) |
| Multi-spec feature | optional | If the user points at several spec dirs, ask whether to group them under an Initiative (Project per spec) |

## Workflow

### Step 1 — Verify team & connection

```
list_teams → resolve the user-given team name to an exact team
```

If ambiguous or missing, show the available team names and ask.

### Step 2 — Parse the Spec Kit artifacts

Read `spec.md` and `tasks.md` (and `plan.md` if present) per
[references/mapping-rules.md](references/mapping-rules.md):

- **`spec.md`** → Project payload: `name` (outcome-style, from the feature
  title), `description` (Problem/Solution + story summaries + Out of Scope,
  Markdown), `summary` ≤255 chars. Extract the prioritized User Stories
  (P1/P2/P3) with their **Independent Test** criteria — those become
  milestone "done" definitions.
- **`tasks.md`** → phase-bucketed task list. Parse task lines loosely:

  ```
  - [ ] T001 [P] [US1] Description with file path
  ```

  `T001` = stable ID (idempotency key) · `[P]` = parallelizable (sub-issue
  candidate) · `[USn]` = story assignment · no story label = Setup /
  Foundational / Polish bucket. Phase headers vary across SpecKit versions —
  match on `Setup`, `Foundational`, `User Story N`, `Polish` keywords, not
  exact strings.
- **Link-only (never issues)**: `plan.md` tech decisions, `constitution.md`,
  FR lists (fold into AC), user-story narration (milestone descriptions).

### Step 3 — Decide hierarchy

```
Project = spec
├─ M0 Foundation  = Phase Setup + Phase Foundational   (close first; blocks everything)
├─ M1..Mn         = User Story P1..Pn                  (P1 = MVP)
└─ Polish tasks   → last milestone, or fold into issue DoDs if few
```

Scale branches (confirm at Gate ② when borderline):
- **Tiny spec (1–2 stories)** → skip milestones; label issues `story:US1` etc.
- **Several spec dirs** → one Project per spec; offer an Initiative to group.
- Solo + single spec → no Initiative, no Cycles (overkill).

Dependency DAG: M0 blocks every story's first issue; cross-story `blockedBy`
only where tasks.md states it. Parallel stories stay parallel.

### Step 4 — Gate ① (clarification check)

Scan `spec.md`/`tasks.md` for `[NEEDS CLARIFICATION` markers and unresolved
TODO/TBD decisions. If any exist, **stop and tell the user to run
`/speckit.clarify` first** — publishing an unclarified spec produces issues
that get invalidated by the next clarify pass.

### Step 5 — Idempotency queries (read-only)

```
list_projects(team)       → project named after the spec (or NNN-slug in its
                            description)? reuse its id
list_milestones(project)  → existing milestones by name? reuse
list_issue_labels(team)   → existing taxonomy (area:*, type:*, story:*)
list_issues(project)      → match by T-ID kept in issue bodies → update, not create
```

**Always reuse existing labels.** Real workspaces accumulate duplicates
(e.g. `type:bug` and `Bug` coexisting) precisely because agents skip this
query. Only call `create_issue_label` for labels that truly don't exist.

### Step 6 — Gate ② (dry-run approval)

Print the full plan as a table **before any write**:

```
| Action        | Object    | Name/Title                       | Milestone | blockedBy | T-ID |
| create        | Project   | User authentication              | —         | —         | —    |
| create        | Milestone | M0 Foundation                    | ^project  | —         | —    |
| create        | Milestone | M1 Email signup & login (US1 🎯) | ^project  | —         | —    |
| create        | Issue     | Create User model + migration    | M0        | —         | T003 |
| update(TES-9) | Issue     | Wire session login view          | M1        | TES-7     | T012 |
```

Show which labels/milestones are **reused vs created**, and surface the
milestone-strategy choice here if the spec is tiny. Get explicit approval.

### Step 7 — Publish (topological order)

1. `save_project` — `name`, `addTeams: [team]`, `description` (Markdown,
   literal newlines — never escaped), `summary`, `lead: "me"`.
2. `save_milestone` — `project` (required), `name`, `description` = the
   story's Independent Test criteria (M0's = "shared foundation in place").
3. `save_issue` per task **in topological order** (M0 issues first, then
   story issues): `team`, `title` (verb-first), `project`, `milestone`,
   `description` (task detail + AC from the story's FRs + a `SpecKit: T001`
   footer line for future matching), `labels`, `blockedBy: [ids]`,
   `state: "Backlog"`.
4. Sub-issues last: `save_issue` with `parentId` for `[P]` splits or scaffold
   details that need independent tracking — otherwise keep them as body
   checkboxes.

After each successful write, record the returned ID in a running log
(e.g. `.linear-publish-log.json` next to the spec dir, or inline in your
reply) so an interrupted run resumes with updates instead of duplicates.

### Step 8 — Report

Summarize: created/updated/reused counts per object type, the project URL,
the dependency edges, the T-ID → Linear-ID mapping table, and everything the
noise filter redirected (FRs → which issue's AC, plan.md → link) so the user
can verify nothing was lost.

## Gotchas (observed, not theoretical)

- **`save_milestone` requires `project`** — publish order is forced:
  Project → Milestones → Issues.
- **`blockedBy`/`blocks`/`labels`/`links` are append-only** on `save_issue` —
  re-runs never remove stale relations; use `removeBlockedBy` to correct.
- **Label duplication is real**: a live team was observed carrying both
  `type:bug` and `Bug`. Step 5's label query is not optional.
- **`description` must use literal newlines** — escaped `\n` renders literally.
- **The T-ID footer is what makes re-runs cheap** — without `SpecKit: T001`
  in the body, Step 5 falls back to fuzzy title matching, which breaks the
  moment a title gets rephrased.
- **tasks.md task numbering ≠ execution order** — a P2 story can be scheduled
  before P1 ("MVP foundation" patterns); order comes from the DAG and
  milestone target dates, never from renumbering.
- **Milestone display order lies** for parallel stories — the `blockedBy`
  graph is the single source of truth for execution order; keep the 1 story =
  1 milestone mapping and let the DAG carry the real ordering.
- **`assignee` not `assigneeId`** on `save_issue`; accepts `"me"`.
- **One MCP call per object** (a 40–50-task spec ≈ that many calls) — mid-run
  failures are normal, which is why the Step 7 ID log exists.

## Out of scope

- GitHub↔Linear sync, including `/speckit.taskstoissues` (that path creates
  flat GitHub issues; native Issues Sync then drops milestones, sub-issue
  hierarchy, and blocked-by entirely — hierarchy needs this skill's
  direct-MCP path).
- Cycles and Initiatives by default — offer an Initiative only for
  multi-spec features; never map stories to Cycles (milestone = scope,
  cycle = time).
