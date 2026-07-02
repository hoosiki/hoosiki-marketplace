---
name: from-grill-me-to-linear
description: Publish grill-me/grill-with-docs outputs (PRD + vertical-slice issues) into a Linear team as a Project→Milestone→Issue→Sub-issue hierarchy via the linear-server MCP. Takes a Linear team name, filters non-issue noise (user stories, decisions, glossary, open questions), preserves the dependency DAG with blocked-by relations, and enforces dry-run approval + idempotent upsert so re-runs never duplicate. Triggers on "linear에 발행", "linear로 정리", "PRD를 linear에", "이슈들을 linear에 등록", "linear에 기록", "grill-me to linear", "publish PRD to Linear", "ingest issues into Linear", or any request to convert a PRD + issue files into Linear projects/milestones/issues.
---

# From grill-me to Linear

Convert `grill-me` / `grill-with-docs` chain outputs (a PRD plus vertical-slice
issue files) into a properly structured Linear hierarchy under a user-specified
team, using the **`linear-server` MCP tools** (`list_*`, `save_project`,
`save_milestone`, `save_issue`, `create_issue_label`).

Also works with any generic `PRD.md` + `issues/*.md` pair that follows the same
shape (What to build / Acceptance criteria / Blocked by).

Detailed conversion rules live in [references/mapping-rules.md](references/mapping-rules.md)
— read it before Step 2.

## Core invariants (never violate)

1. **User stories, decisions, glossary entries, and open questions are NEVER
   created as Issues** — they go to the project brief, linked docs, or comments.
2. **Dependencies are expressed only as `blockedBy` relations (DAG)** — never
   force a linear milestone ordering onto parallel slices.
3. **Every publish is an idempotent upsert** — query existing objects first,
   reuse them, update by `id`; never blind-create.
4. **Two HITL gates** — no writes before the user approves the dry-run plan.

## Prerequisites

The `linear-server` MCP must be connected. Verify by calling `list_teams`.
If the tools are unavailable, stop and tell the user to enable the Linear MCP
integration — do not fall back to the REST API or `curl`.

## Inputs (collect before doing anything)

| Input | Required | How to get it |
|---|---|---|
| **Team name** | ✅ | From user args. Verify it exists via `list_teams` (fuzzy-match; if no match, list available teams and ask) |
| **PRD** | ✅ | File path (e.g. `PRD.md`) or pasted text |
| **Issues** | ✅ | Directory (e.g. `issues/*.md`), file list, or pasted text |
| Milestone strategy | optional | Default: promote each big slice to a Milestone; small flat sets skip milestones (ask at Gate ②) |
| AFK delegation | optional | If issues carry `mode:afk`, ask whether to set `delegate: "Linear"` |

## Workflow

### Step 1 — Verify team & connection

```
list_teams → resolve the user-given team name to an exact team
```

If ambiguous or missing, show the available team names and ask.

### Step 2 — Parse & filter

Read the PRD and every issue file. Classify each fragment using the mapping
table in [references/mapping-rules.md](references/mapping-rules.md):

- PRD → one **Project** payload (`name` = outcome-style, `description` = full
  PRD Markdown, `summary` ≤255 chars incl. Out of Scope one-liner).
- Each issue file → `{title, body, mode, blocked_by[], is_scaffold}`.
- **Drop from the issue list**: user-story narration, implementation/testing
  decisions, glossary, open questions, out-of-scope items. These are absorbed
  into the brief or left as repo links. *Filtering these out is half the value
  of this skill.*
- Rewrite titles to **verb-first plain form** (`Add Stripe webhook`) — never
  `"As a user…"`. Fold "tests pass" clauses into the issue body as a
  DoD checklist, never as separate issues.

### Step 3 — Decide hierarchy

```
Project   = the PRD (always exactly one)
Milestone = a large vertical slice (one slice file ≈ one milestone) — optional layer
Issue     = one end-to-end unit of work inside a slice (verb-first, ≤2 days)
Sub-issue = scaffold/boilerplate splits only, 1 level deep max
```

Build the dependency DAG from `Blocked by` references and topologically sort.
Do **not** serialize parallel branches (`01→02→{03,04,05,06}` stays a fan-out).

### Step 4 — Gate ① (input sanity)

Block publication and tell the user why, if:
- The PRD looks like an un-grilled first draft (unresolved decisions, open
  questions marked TODO/TBD inline).
- Issue files have no acceptance criteria at all.

Ask the user to confirm the inputs are final before proceeding.

### Step 5 — Idempotency queries (read-only)

```
list_projects(team)          → existing project with same name? reuse its id
list_milestones(project)     → existing milestones by name? reuse
list_issue_labels(team)      → existing label taxonomy (area:*, type:*, mode:*)
list_issues(project/team)    → existing issues by stable key (title or slice ID in body)
```

**Always reuse existing labels.** Real workspaces accumulate duplicates
(e.g. `type:bug` and `Bug` coexisting) precisely because agents skip this
query. Only call `create_issue_label` for labels that truly don't exist.

### Step 6 — Gate ② (dry-run approval)

Print the full plan as a table **before any write**:

```
| Action        | Object    | Name/Title                  | Parent/Milestone | blockedBy | Labels |
| create        | Project   | 영어 회화 튜터 MVP           | —                | —         | —      |
| create        | Milestone | M1 Walking Skeleton         | ^project         | —         | —      |
| create        | Issue     | Scaffold apps + settings    | M1               | —         | type:feature |
| update(TES-4) | Issue     | Wire streaming protocol     | M1               | TES-3     | …      |
```

Include which labels/milestones are being **reused vs created**. Get explicit
user approval. Offer the milestone-strategy choice here if the slice set is
small (≤3 slices → consider flat, no milestones).

### Step 7 — Publish (topological order)

1. `save_project` — `name`, `addTeams: [team]`, `description` (PRD Markdown,
   literal newlines — never escaped), `summary`, `lead: "me"`.
2. `save_milestone` per slice group — `project` (required), `name`,
   `description` (= the slice's "done" definition / independent test).
3. `save_issue` per issue **in topological order** (prerequisites first, so
   `blockedBy` targets exist): `team`, `title`, `project`, `milestone`,
   `description` (body + AC/DoD checklist), `labels`, `blockedBy: [ids]`,
   `state: "Backlog"`.
4. Sub-issues last: `save_issue` with `parentId` = parent's identifier.
5. `mode:afk` issues: if approved at input stage, add `delegate: "Linear"`.

After each successful write, record the returned ID in a running log
(e.g. `.linear-publish-log.json` next to the PRD, or inline in your reply) so
an interrupted run can resume with updates instead of duplicate creates.

### Step 8 — Report

Summarize: created/updated/reused counts per object type, the project URL,
and the dependency edges established. Note anything skipped by the noise
filter and where it went (brief, docs link, comment) so the user can verify
nothing was lost.

## Gotchas (observed, not theoretical)

- **`save_milestone` requires `project`** — milestones cannot exist outside a
  project. Publish order is forced: Project → Milestones → Issues.
- **`blockedBy`/`blocks`/`labels`/`links` are append-only** on `save_issue` —
  re-running an update never removes stale relations. Use `removeBlockedBy` /
  `removeBlocks` to correct mistakes.
- **Label duplication is real**: a live team was observed carrying both
  `type:bug` and `Bug`. Step 5's label query is not optional.
- **`description` must use literal newlines** — the MCP schema explicitly
  rejects escaped `\n` sequences (they render literally).
- **Milestone order lies**: Linear displays milestones in sequence, which
  falsely implies serial execution for parallel slices. The `blockedBy` graph
  is the single source of truth for ordering; consider grouping parallel
  slices into one milestone if the roadmap must look honest.
- **`assignee` not `assigneeId`** on `save_issue`; accepts `"me"`.
- **One MCP call per object** (~40 calls for a real PRD) — a mid-run failure
  is normal, which is why the Step 7 ID log exists.

## Out of scope

- GitHub↔Linear sync (native Issues Sync moves only 6 fields and drops
  milestones/sub-issue hierarchy/blocked-by entirely — hierarchy needs this
  skill's direct-MCP path).
- Cycles and Initiatives — mention them only if the user asks; solo/single-PRD
  runs don't need either.
