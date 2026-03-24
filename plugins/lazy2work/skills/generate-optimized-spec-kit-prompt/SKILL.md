---
name: generate-optimized-spec-kit-prompt
description: Generate optimized GitHub Spec Kit prompts (specify/plan/tasks/implement) for all features of a project. Use when user provides project information via @ file path and wants complete Spec Kit prompts generated. Triggers on "speckit prompts", "generate spec kit", "feature breakdown", "specify plan tasks implement", "SDD prompts", or when user provides a constitution/project file and wants full spec-driven development prompts. Assumes constitution already exists.
---

# Generate Optimized Spec Kit Prompts

Split a project into features and generate optimized `/specify`, `/plan`, `/tasks`, `/implement` prompts for each feature. Output grouped into files of 5 features each.

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
- `/specify` — WHAT + WHY only. Zero tech references. End with "What questions do you have?"
- `/plan` — HOW only. Tech stack, architecture, file paths. No feature requirements.
- `/tasks` — ORDER only. Sequence, deps, tags `[NEW]`/`[MODIFY]`/`[TEST]`. No tech decisions.
- `/implement` — RULES only. Scope `--tasks N-M`, commit strategy, failure behavior. No design changes.

### 4. Write Output Files

Create output directory and write files. See [references/api_reference.md](references/api_reference.md) for the exact output template.

**Directory**: `claudedocs/speckit/{YYYYMMDD}/`

**File grouping**: 5 features per file.

```
claudedocs/speckit/20260324/
├── features_01-05_20260324.md
├── features_06-10_20260324.md
└── features_11-12_20260324.md   (remainder)
```

**File structure per batch:**

```markdown
# Spec Kit Prompts: {Project Name}

> Generated: {YYYY-MM-DD} | Features {N}-{M} of {Total}

## Feature Index
1. {Feature 1 name}
2. {Feature 2 name}
...

---

## Feature 1: {Name}

### /specify
{full specify prompt}

---

### /plan
{full plan prompt}

---

### /tasks
{full tasks prompt}

---

### /implement
{full implement prompt}

---

## Feature 2: {Name}
...
```

If total features <= 4, write a single file: `features_all_{YYYYMMDD}.md`.

## Quality Checklist

After generating all prompts, verify each feature against:

| Check | Rule |
|-------|------|
| /specify has no tech terms | Tech-neutral (survives stack change) |
| /specify ends with "What questions do you have?" | Always present |
| /specify has Out of Scope section | Prevents AI scope creep |
| /plan references specific file paths | Not vague "follow patterns" |
| /plan has explicit exclusions | Prevents AI adding Docker/CI/CD |
| /tasks uses `[NEW]`/`[MODIFY]`/`[TEST]` tags | Every task tagged |
| /tasks has 1 task = 1 commit size | Not too large |
| /implement uses `--tasks N-M` | Never all tasks at once |
| /implement has failure behavior | Stop and report on failure |
| Success criteria are measurable | "< 1s" not "fast" |

## References

- **Prompt rules**: [references/speckit-prompt-guide.md](references/speckit-prompt-guide.md) — what each stage must/must not include
- **Output format**: [references/api_reference.md](references/api_reference.md) — file naming and template
