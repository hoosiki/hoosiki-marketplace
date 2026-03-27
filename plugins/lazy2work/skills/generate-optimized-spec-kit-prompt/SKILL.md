---
name: generate-optimized-spec-kit-prompt
description: Generate optimized GitHub Spec Kit prompts (/speckit.specify, /speckit.plan, /speckit.tasks, /speckit.implement) for all features of a project. Use when user provides project information via @ file path and wants complete Spec Kit prompts generated. Triggers on "speckit prompts", "generate spec kit", "feature breakdown", "specify plan tasks implement", "SDD prompts", or when user provides a constitution/project file and wants full spec-driven development prompts. Assumes constitution already exists.
---

# Generate Optimized Spec Kit Prompts

Split a project into features and generate optimized `/speckit.specify`, `/speckit.plan`, `/speckit.tasks`, `/speckit.implement` prompts for each feature. Each feature gets its own folder with 4 individual prompt files.

## Input

User provides project information via `@` file path. This can be:
- A constitution file (`speckit.constitution`)
- A project description / PRD document
- Any file describing the project's scope, tech stack, and goals

## Workflow

### 1. Read and Analyze Project Info

Read the provided file(s). Extract:
- Project name and purpose
- Tech stack and versions
- Architecture decisions
- Existing code patterns (brownfield)
- Constraints and exclusions
- Mermaid diagrams — classify each diagram for stage placement:

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

### 2. Decompose into Features

Split the project into features following these rules:
- Each feature: 1 person, 1-5 days to complete
- Each feature: independently testable and deployable
- Name format: short imperative phrase (e.g., "User Authentication", "Markdown Rendering")
- Order: foundation features first, then dependent features

Output a numbered feature list for confirmation awareness before proceeding.

### 3. Generate 4-Stage Prompts per Feature

For each feature, generate all 4 prompts following strict stage separation. Read [references/speckit-prompt-guide.md](references/speckit-prompt-guide.md) for the rules on what each stage MUST and MUST NOT include.

**Critical rules:**
- `/speckit.specify` — WHAT + WHY only. Zero tech references. End with "What questions do you have?"
- `/speckit.plan` — HOW only. Tech stack, architecture, file paths. No feature requirements.
- `/speckit.tasks` — ORDER only. Sequence, deps, tags `[NEW]`/`[MODIFY]`/`[TEST]`. No tech decisions.
- `/speckit.implement` — RULES only. Scope `--tasks N-M`, commit strategy, failure behavior. No design changes.

**Mermaid diagram rules:**
- Include Mermaid diagrams in specify and plan where they add clarity. Always pair with 1-2 sentences of explanation text before the code block.
- `/speckit.specify` — User workflow flowcharts and user-system sequences only. No tech terms (Django, PostgreSQL, etc.) in any node or label.
- `/speckit.plan` — Architecture diagrams, API sequences, ERD, data flow, state machines, deployment diagrams. Use clear node names and edge labels.
- `/speckit.tasks` — Mermaid is optional. Task dependencies are typically expressed as text `[DEPENDS: T001]`.
- `/speckit.implement` — No Mermaid diagrams.
- One diagram = one concern. Do not combine architecture + sequence + ERD into a single Mermaid block.

### 4. Write Output Files

Create output directory and write files. See [references/api_reference.md](references/api_reference.md) for the exact output template.

**Directory**: `.speckit-prompts/` (project root)

**Structure**: One folder per feature, each containing 4 stage files.

```
.speckit-prompts/
├── feature-001-user-authentication/
│   ├── 01_specify.md
│   ├── 02_plan.md
│   ├── 03_tasks.md
│   └── 04_implement.md
├── feature-002-dashboard/
│   ├── 01_specify.md
│   ├── 02_plan.md
│   ├── 03_tasks.md
│   └── 04_implement.md
└── feature-003-api-endpoints/
    ├── 01_specify.md
    ├── 02_plan.md
    ├── 03_tasks.md
    └── 04_implement.md
```

**Folder naming**: `feature-{NNN}-{kebab-case-name}` (e.g., `feature-001-user-authentication`)

**File content**: Each file contains only the prompt for that stage. Do not include frontmatter (YAML `---` blocks). The first line of each file must start directly with the `/speckit.specify`, `/speckit.plan`, `/speckit.tasks`, or `/speckit.implement` command.

## Quality Checklist

After generating all prompts, verify each feature against:

| Check | Rule |
|-------|------|
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
