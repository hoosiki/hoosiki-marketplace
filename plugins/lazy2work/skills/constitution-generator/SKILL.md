---
name: constitution-generator
description: Generate an optimized GitHub Spec Kit constitution prompt from project information. Use when user says "generate constitution", "constitution prompt", "speckit constitution", or provides project details (tech stack, architecture) and wants a `/speckit.constitution` prompt. Triggers on constitution creation, SDD setup, or spec-kit project initialization requests.
---

# Constitution Generator

Generate a best-practice `/speckit.constitution` prompt from user-provided project information.

## Workflow

### 1. Gather Project Info

Ask the user for the following. Skip items the user already provided.

**Required (must ask if missing):**
- Project name + one-line purpose
- Tech stack (language, framework, DB — with versions)
- Project type: greenfield or brownfield

**Ask only if relevant:**
- Deployment target (cloud, NAS, local)
- Package manager (uv, npm, pip)
- Existing code patterns to preserve (brownfield only)

### 2. Detect Brownfield

If brownfield, analyze the codebase:
- Read project structure (`ls`, key config files)
- Identify existing conventions (formatter, linter, test framework)
- Note existing app/module structure to lock in constitution

### 3. Generate Constitution Prompt

Output a complete `/speckit.constitution` prompt text following this structure. Every rule must be **verifiable** — if a rule cannot be checked against code, rewrite it.

```
/speckit.constitution

[Project one-line description]

## Tech Stack
- [Language + version]
- [Framework + version]
- [Database]
- [Other key dependencies with versions]

## Architecture Principles
- [Project structure rules]
- [Layer separation / API pattern]
- [Module organization]

## Coding Conventions
- [Formatter + config]
- [Linter + config]
- [Naming convention]
- [Docstring style]
- [Type hints rule]

## Testing Requirements
- [Test framework]
- [Coverage target]
- [Test classification]

## Security Principles
- [Credential management]
- [Auth method]

## Prohibitions
- [Explicit list of things AI must NOT do]

## Deployment Target
- [Hosting / infrastructure]
```

### 4. Validation Checklist

After generating, verify against these anti-patterns:

| Check | Pass? |
|-------|-------|
| All rules are verifiable (no "write good code") | |
| Tech stack has specific versions | |
| Prohibitions section exists and is non-empty | |
| No feature requirements (belongs in /specify) | |
| No implementation details (belongs in /plan) | |
| Each section has 3-7 rules | |
| Brownfield: existing patterns referenced | |

## Rules

- Output prompt text only — do not create files
- Each rule: one sentence, imperative form
- Versions: always include (e.g., "Django 4.2.x" not "Django")
- Prohibitions: minimum 3 items, be explicit
- Brownfield: always include "Existing Code Reference" section with file paths

## References

For detailed best practices, anti-patterns, and examples, read [references/constitution-guide.md](references/constitution-guide.md).
