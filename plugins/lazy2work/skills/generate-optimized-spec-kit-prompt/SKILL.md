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

### 4. Write Output Files

Create output directory and write files. See [references/api_reference.md](references/api_reference.md) for the exact output template.

**Directory**: `.speckit-prompts/` (프로젝트 루트)

**구조**: feature별 폴더, 각 폴더에 4개 스테이지 파일.

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

**폴더 네이밍**: `feature-{NNN}-{kebab-case-name}` (예: `feature-001-user-authentication`)

**파일별 내용**: 각 파일은 해당 스테이지의 프롬프트만 포함한다. 파일 상단에 feature 이름과 생성일을 frontmatter로 기록한다.

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

## References

- **Prompt rules**: [references/speckit-prompt-guide.md](references/speckit-prompt-guide.md) — what each stage must/must not include
- **Output format**: [references/api_reference.md](references/api_reference.md) — file naming and template
