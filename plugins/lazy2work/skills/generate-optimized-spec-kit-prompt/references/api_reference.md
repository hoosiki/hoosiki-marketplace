# Output Format Reference

## Directory Structure

```
.speckit-prompts/
├── feature-{NNN}-{kebab-case-name}/
│   ├── 01_specify.md
│   ├── 02_plan.md
│   ├── 03_tasks.md
│   └── 04_implement.md
```

## Folder Naming Convention

- Format: `feature-{NNN}-{kebab-case-name}`
- `{NNN}`: 3자리 zero-padded 번호 (001, 002, ...)
- `{kebab-case-name}`: feature 이름을 kebab-case로 변환
- Examples:
  - `feature-001-user-authentication`
  - `feature-002-markdown-rendering`
  - `feature-003-api-endpoints`

## 01_specify.md Template

```markdown
---
feature: "{Feature Name}"
stage: specify
generated: {YYYY-MM-DD}
---

/speckit.specify {Feature Name}: {one-line description}

## Purpose (Why)
{2-3 sentences}

## Users (Who)
- {Persona}: {goal}

## Core Features (What)
1. {Feature 1}
2. {Feature 2}
...

## User Scenarios

### Happy Path
1. {step}

### Error: {error name}
1. {step}

## Success Criteria
- {measurable criterion}

## Constraints
- {constraint}

## Out of Scope
- {exclusion}

What questions do you have?
```

## 02_plan.md Template

```markdown
---
feature: "{Feature Name}"
stage: plan
generated: {YYYY-MM-DD}
---

/speckit.plan

Tech Stack:
- {language + version}
- {framework + version}

Architecture:
- {structural decision}

Existing Code Reference:
- {file path}: {pattern}

Test Strategy:
- {framework + scope}

Explicit Exclusions:
- {exclusion}
```

## 03_tasks.md Template

```markdown
---
feature: "{Feature Name}"
stage: tasks
generated: {YYYY-MM-DD}
---

/speckit.tasks

Task Classification:
- Each task = 1 git commit
- [MODIFY] existing file, [NEW] new file, [TEST] test

Phase 1 (Foundation):
  Task 1 [{tag}]: {file} — {description}
  Task 2 [{tag}]: {file} — {description}

Phase 2 (Integration):
  Task 3 [{tag}]: {file} — {description}

Phase 3 (Testing):
  Task 4 [{tag}]: {description}

Dependencies:
- {dependency info}
```

## 04_implement.md Template

```markdown
---
feature: "{Feature Name}"
stage: implement
generated: {YYYY-MM-DD}
---

/speckit.implement --tasks 1-{N}

Implementation Rules:
- Run tests after each task
- Stop on test failure
- Commit per task: "feat: [Task N] {description}"

Code Style:
- {formatter + rules}

Failure Handling:
- Test failure → stop and report
- Regression → rollback and report
```
