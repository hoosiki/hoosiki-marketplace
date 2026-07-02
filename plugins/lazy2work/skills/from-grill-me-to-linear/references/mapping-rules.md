# Mapping rules — grill-me outputs → Linear objects

Full conversion table, filter rules, and anti-pattern guardrails.
Source: Linear-ingestion research series (2026-06-22 → 2026-07-02), verified
against the live `linear-server` MCP schemas.

## 1. Conversion table

| grill-me artifact | → Linear object | Rule |
|---|---|---|
| PRD (whole) | **Project** (PRD as project description/document, single owner) | Always 1 PRD = 1 Project |
| User Stories (narrative) | ❌ never an Issue → absorb into **project brief/summary** | Linear officially calls user-story issues an anti-pattern |
| tracer-bullet vertical slice | **Issue** (verb-first, end-to-end) | Default |
| ↳ slice too big (bundle of end-to-end tasks) | Promote to **Milestone**, decompose inside into Issues | When one story bundles several through-cutting tasks |
| Scaffold/boilerplate-only work | **Sub-issue** (`parentId`) — **1 level max** | No deep trees |
| Implementation/Testing Decisions | ❌ → link to ADR / project document | Decisions are not issues |
| CONTEXT.md glossary | ❌ → stays in repo, link only | "Zero implementation detail" in Linear |
| Out of Scope | ❌ → one line in project summary | Prevents scope creep |
| Open questions | ❌ → Triage or issue comment | Only resolved items deserve issues |
| HITL/AFK markers | **Label** `mode:hitl` / `mode:afk` | Enables agent-delegation pipelines |
| Inter-slice dependencies | **blocked-by relations** (DAG) | Never encode as milestone sequence |
| Acceptance criteria / "pytest passes" clauses | ❌ not separate issues → **AC/DoD checklist inside the issue body** | TDD: the test is part of the issue's DoD |
| Weekly timebox | **Cycle** (optional, orthogonal to milestones) | Milestone = scope, Cycle = time — never conflate |

Title rule: issue titles are **verb-first plain statements** (`Add Stripe
webhook`). The `"As a user…"` format is banned at the issue level; if the
narrative matters, it lives in the milestone name/description.

## 2. Hierarchy shape

```
Project      = 1 PRD                          (save_project)
 └ Milestone = large vertical slice / story    (save_milestone; project required)
    └ Issue  = executable end-to-end task      (save_issue; project + milestone)
       └ Sub = scaffold split, 1 level only    (save_issue; parentId)
```

- Milestones are an **optional layer** — a small flat slice set can hang
  Issues directly off the Project. Don't manufacture milestones.
- Rough sizing: an Issue should be closable in ≤2 days; several per week.

## 3. Dependency (DAG) rules

- Parse `Blocked by <ID>` lines → `save_issue.blockedBy` arrays.
- **No linearization**: a fan-out like `01→02→{03,04,05,06}` must stay
  parallel. Milestone numbering must not imply a false serial order.
- Publish in **topological order** so every `blockedBy` reference already
  exists.
- `blockedBy`/`blocks` are **append-only**; corrections need
  `removeBlockedBy`/`removeBlocks`.

## 4. Idempotency contract

Query → reuse → create-only-if-missing, in this order:

1. `list_teams` — resolve team.
2. `list_projects` — same-name project ⇒ update via `save_project(id=…)`.
3. `list_issue_labels(team)` — reuse `area:*` / `type:*` / `mode:*` taxonomy.
4. `list_milestones(project)` — reuse same-name milestones.
5. `list_issues` — match by stable key (title or slice ID kept in the body);
   found ⇒ `save_issue(id=…)` update, else create.

Log every created/updated ID so interrupted runs resume as updates.

## 5. Anti-pattern guardrails (reject or warn)

| Anti-pattern | Skill response |
|---|---|
| Publishing a first-draft, un-grilled PRD | Gate ① blocks until user confirms decisions are resolved |
| Transcribing user stories as Issues | Route narrative to brief; exclude from issue candidates |
| Making issues out of FRs/decisions/glossary/open questions | Filtered by §1 ❌ rows |
| Defining new triage labels misaligned with the team's existing taxonomy | Compare against `list_issue_labels` first; reuse |
| Flat publishing with no Project/Milestone structure | Enforce PRD=Project, slice-bundle=Milestone |
| Re-publishing without idempotency | §4 upsert contract is mandatory |
| Encoding parallel slices as serial milestone order | blocked-by only |
| Splitting one slice back into layer issues (model/view/template) | Keep vertical cohesion — decompose by task, not by layer |
| Sub-issue nesting ≥2 levels | 1 level max |
| "Write tests" as a standalone issue | Fold into the related issue's DoD |

## 6. MCP parameter notes (live schema, 2026-07)

- `save_project`: `name` + `addTeams` required on create; `description` is
  Markdown with **literal newlines**; `summary` ≤255 chars; `lead: "me"` works.
- `save_milestone`: `project` **always required**; `id` accepts name or ID.
- `save_issue`: `team`+`title` required on create; `id` (e.g. `TES-12`) for
  updates; `assignee` (not `assigneeId`) accepts `"me"`; `parentId` makes it a
  sub-issue; `milestone` accepts name or ID; `state` accepts state name
  (`"Backlog"`); `delegate: "Linear"` hands the issue to the Linear agent.
- `create_issue_label`: `teamId` is a **UUID** (from `list_teams`), omit for a
  workspace-level label.
