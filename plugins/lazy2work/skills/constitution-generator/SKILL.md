---
name: constitution-generator
description: Generate an optimized GitHub Spec Kit constitution prompt from project information. Use when user says "generate constitution", "constitution prompt", "speckit constitution", or provides project details (tech stack, architecture) and wants a `/speckit.constitution` prompt. Triggers on constitution creation, SDD setup, or spec-kit project initialization requests.
---

# Constitution Generator

Generate a best-practice `/speckit.constitution` prompt from user-provided project information.

**Guiding principle: minimal but enforceable.** A constitution holds only non-negotiable guardrails — "how we work", never "what we build". The #1 failure mode is over-constraint, not under-constraint: dozens of rules make the agent over-comply (unnecessary artifacts, context drift). Keep the prompt density LOW; save the detail for `/speckit.specify` and `/speckit.plan`.

## Workflow

### 1. Gather Project Info

Ask the user for the following. Skip items the user already provided.

**Required (must ask if missing):**
- Project name + one-line purpose
- Tech stack (language, framework, DB — with versions)
- Project type: greenfield or brownfield
- Project stage: **prototype/experiment** or **production** — this decides whether CI/CD, deployment, and performance-budget articles belong at all

**Ask only if relevant:**
- Deployment target (cloud, NAS, local) — production stage only
- Package manager (uv, npm, pip)
- Existing code patterns to preserve (brownfield only)

### 2. Detect Brownfield

If brownfield, analyze the codebase:
- Read project structure (`ls`, key config files)
- Identify existing conventions (formatter, linter, test framework)
- Note existing app/module structure to lock in constitution

### 3. Generate Constitution Prompt

Output a complete `/speckit.constitution` prompt text following this structure. Every principle must be **verifiable and enforceable** — written in MUST/NO language with quantified thresholds; if a rule cannot be checked against code, rewrite it. Attach a `(Rationale: …)` to every principle — agents follow rules better when they understand why.

Sections below are a **menu, not a quota**: include a section only when it carries a genuine non-negotiable; omit empty sections. Target **6–12 principles total** (hard cap 15).

```
/speckit.constitution

[Project one-line description]

Create the project constitution from the non-negotiable principles below.
- Attach a Rationale to every principle.
- Use enforceable MUST/NO language; keep every article objectively verifiable.
- Delete template sections that do not apply — constitution.md is plain markdown, do not pad.

## Tech Stack (Locked)
- MUST use [Language + version] (Rationale: [why locked])
- MUST use [Framework + version] (Rationale: ...)
- [Database + version] / [Package manager]

## Architecture Principles
- MUST [structure / layer-separation rule] (Rationale: ...)

## Coding Conventions
- MUST [formatter + config] (Rationale: zero-diff formatting debates)
- MUST [linter / type-hints rule] (Rationale: ...)

## Testing Requirements
- MUST [test framework + quantified gate, e.g. "unit coverage ≥ 80% on business logic"] (Rationale: regression safety)

## Security Principles
- NO [credential anti-pattern, e.g. "secrets in code"]; MUST [credential management] (Rationale: ...)

## Prohibitions
- NO [explicit thing AI must not do] (Rationale: ...)
- NO [...]
- NO [...]

## Deployment Target            ← production stage only
- [Hosting / infrastructure]

This project is at prototype stage — do NOT include CI/CD, deployment,
or performance-budget articles.   ← prototype stage only (replaces Deployment Target)
```

### 4. Validation Checklist

After generating, verify against these anti-patterns:

| Check | Pass? |
|-------|-------|
| All rules verifiable, in MUST/NO language (no "write good code") | |
| Every principle carries a `(Rationale: …)` | |
| Thresholds quantified (≥ 80%, P95 < 200ms — not "fast", "well-tested") | |
| Total principles ≤ 12, all non-negotiable (over-constraint → agent over-compliance) | |
| Stage match: prototype has no CI/CD / deployment / performance-budget articles | |
| Tech stack has specific versions | |
| Prohibitions section exists and has ≥ 3 items | |
| No feature requirements (belongs in /specify) | |
| No implementation details (belongs in /plan) | |
| Empty template sections dropped, not padded | |
| Brownfield: existing patterns referenced | |

## Rules

- Output prompt text only — do not create files
- Each principle: one imperative sentence in MUST/NO form + `(Rationale: …)`
- Only non-negotiables — if the team could reasonably revisit it per-feature, it belongs in /specify or /plan, not here
- Quantify every threshold; versions always included (e.g., "Django 4.2.x" not "Django")
- Prohibitions: minimum 3 items, be explicit
- Prototype stage: strip production gates (CI/CD, deployment, performance budgets) and say so in the prompt
- Brownfield: always include "Existing Code Reference" section with file paths
- Instruct the agent to delete non-applicable template sections instead of filling them

## References

For detailed best practices, anti-patterns, and examples, read [references/constitution-guide.md](references/constitution-guide.md).
