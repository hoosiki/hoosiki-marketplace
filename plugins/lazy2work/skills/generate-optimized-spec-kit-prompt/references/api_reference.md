# Output Format Reference

## File Naming Convention

```
claudedocs/speckit/{YYYYMMDD}/features_{batch_start}-{batch_end}_{YYYYMMDD}.md
```

Examples:
- `claudedocs/speckit/20260324/features_01-05_20260324.md`
- `claudedocs/speckit/20260324/features_06-10_20260324.md`
- `claudedocs/speckit/20260324/features_11-12_20260324.md`

## Single Feature Output Template

```markdown
---

## Feature {N}: {Feature Name}

### /specify

/specify {Feature Name}: {one-line description}

#### Purpose (Why)
{2-3 sentences}

#### Users (Who)
- {Persona}: {goal}

#### Core Features (What)
1. {Feature 1}
2. {Feature 2}
...

#### User Scenarios
##### Happy Path
1. {step}

##### Error: {error name}
1. {step}

#### Success Criteria
- {measurable criterion}

#### Constraints
- {constraint}

#### Out of Scope
- {exclusion}

What questions do you have?

---

### /plan

/plan

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

---

### /tasks

/tasks

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

---

### /implement

/implement --tasks 1-{N}

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
