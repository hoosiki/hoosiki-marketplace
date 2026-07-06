---
name: generate-optimized-spec-kit-prompt
description: Generate optimized GitHub Spec Kit prompts (/speckit.specify, /speckit.plan, /speckit.tasks, /speckit.implement) for all pre-sliced feature issues of a project. Use when user provides a PRD file plus an issues directory (vertically sliced features, one file per feature) via @ file paths and wants complete Spec Kit prompts generated. Triggers on "speckit prompts", "generate spec kit", "specify plan tasks implement", "SDD prompts", or when user provides a PRD + issues folder and wants full spec-driven development prompts. Assumes constitution already exists and features are already decomposed.
---

# Generate Optimized Spec Kit Prompts

Generate optimized `/speckit.specify`, `/speckit.clarify`, `/speckit.plan`, `/speckit.tasks`, `/speckit.implement`, and `/sc:git commit` prompts for each pre-sliced feature issue. Features arrive already decomposed (vertical slices in an issues directory); this skill does NOT re-split them. Each issue gets its own folder with 6 individual prompt files.

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

### 2. Generate 6-Stage Prompts per Feature

For each issue file (in issue-number order), generate all 6 prompts following strict stage separation. Read [references/speckit-prompt-guide.md](references/speckit-prompt-guide.md) for the rules on what each stage MUST and MUST NOT include.

**Input → stage mapping:**
- `/speckit.specify` ← issue "What to build" + acceptance criteria + the PRD user stories the issue references. Strip tech terms from issue text (keep it tech-neutral).
- `/speckit.plan` ← PRD implementation/testing decisions + the issue's technical details.
- `/speckit.tasks` ← issue acceptance criteria as task acceptance; issue "Blocked by" as dependency context (assume blockers are already implemented).
- `/speckit.implement` ← rules only, as before.

**Critical rules:**
- `/speckit.specify` — WHAT + WHY only. Zero tech references. End with "What questions do you have?"
- `/speckit.clarify` — Auto-accept recommended options to resolve spec ambiguities before planning.
- `/speckit.plan` — HOW only. Tech stack, architecture, file paths. No feature requirements.
- `/speckit.tasks` — ORDER only. Sequence, deps, tags `[NEW]`/`[MODIFY]`/`[TEST]`. No tech decisions.
- `/speckit.implement` — RULES only. Scope `--tasks N-M`, commit strategy, failure behavior. No design changes.
- `/sc:git commit` — Commit after implementation completes.

**Mermaid diagram rules:**
- Include Mermaid diagrams in specify and plan where they add clarity. Always pair with 1-2 sentences of explanation text before the code block.
- `/speckit.specify` — User workflow flowcharts and user-system sequences only. No tech terms (Django, PostgreSQL, etc.) in any node or label.
- `/speckit.plan` — Architecture diagrams, API sequences, ERD, data flow, state machines, deployment diagrams. Use clear node names and edge labels.
- `/speckit.tasks` — Mermaid is optional. Task dependencies are typically expressed as text `[DEPENDS: T001]`.
- `/speckit.implement` — No Mermaid diagrams.
- One diagram = one concern. Do not combine architecture + sequence + ERD into a single Mermaid block.

### 3. Write Output Files

Create output directory and write files. See [references/api_reference.md](references/api_reference.md) for the exact output template.

**Directory**: `.speckit-prompts/` (project root)

**Structure**: All feature folders live under a single `feature/` parent. One folder per issue, each containing 6 stage files.

```
.speckit-prompts/
└── feature/
    ├── 000-env-compat-gate/
    │   ├── 01_specify.md
    │   ├── 02_clarify.md
    │   ├── 03_plan.md
    │   ├── 04_tasks.md
    │   ├── 05_implement.md
    │   └── 06_commit.md
    ├── 001-sync-chat-http/
    │   ├── 01_specify.md
    │   ├── 02_clarify.md
    │   ├── 03_plan.md
    │   ├── 04_tasks.md
    │   ├── 05_implement.md
    │   └── 06_commit.md
    └── 002-persistence-auth/
        ├── 01_specify.md
        ├── 02_clarify.md
        ├── 03_plan.md
        ├── 04_tasks.md
        ├── 05_implement.md
        └── 06_commit.md
```

**Folder naming**: `feature/{NNN}-{kebab-case-name}` — `{NNN}` is the source issue number zero-padded to 3 digits (`00` → `000`, `08` → `008`), `{kebab-case-name}` is the issue filename slug with the number prefix removed (e.g. `00-env-compat-gate.md` → `feature/000-env-compat-gate/`).

**File content**: Each file contains only the prompt for that stage. Do not include frontmatter (YAML `---` blocks). The first line of each file must start directly with the command (`/speckit.specify`, `/speckit.clarify`, `/speckit.plan`, `/speckit.tasks`, `/speckit.implement`, or `/sc:git`).

## Quality Checklist

After generating all prompts, verify each feature against:

| Check | Rule |
|-------|------|
| 1 issue file = 1 feature folder | No merging or re-splitting of issues |
| Folder number matches issue number | `00-env-compat-gate.md` → `feature/000-env-compat-gate/` |
| Issue acceptance criteria appear in tasks | Every criterion maps to a task or success criterion |
| /speckit.specify has no tech terms | Tech-neutral (survives stack change) |
| /speckit.specify ends with "What questions do you have?" | Always present |
| /speckit.specify has Out of Scope section | Prevents AI scope creep |
| /speckit.plan references specific file paths | Not vague "follow patterns" |
| /speckit.plan has explicit exclusions | Prevents AI adding Docker/CI/CD |
| /speckit.tasks uses `[NEW]`/`[MODIFY]`/`[TEST]` tags | Every task tagged |
| /speckit.tasks has 1 task = 1 commit size | Not too large |
| /speckit.implement uses `--tasks N-M` | Never all tasks at once |
| /speckit.implement has failure behavior | Stop and report on failure |
| Success criteria are measurable | "< 1s" not "fast" |
| /speckit.specify Mermaid has no tech terms | No Django, PostgreSQL, Redis in nodes |
| /speckit.plan has architecture + API sequence diagrams | Mermaid with explanation text |
| Each Mermaid block = one concern | No combined architecture + ERD blocks |

## References

- **Prompt rules**: [references/speckit-prompt-guide.md](references/speckit-prompt-guide.md) — what each stage must/must not include
- **Output format**: [references/api_reference.md](references/api_reference.md) — file naming and template
