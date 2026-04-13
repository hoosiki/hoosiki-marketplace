# Project rules for this pipeline repo

This project uses the `hamilton-harness` skill (bundled with the `lazy2work`
plugin) for spec-driven development.

## Core rules

- **`specs/*.yaml` is the single source of truth.** Modify specs first, then
  regenerate code from them. Do not hand-edit `src/pipelines/*.py` ahead of the
  spec.
- **Every pipeline follows the 7-stage flow** (SPEC → VALIDATE → STRUCTURE GATE
  → PBT → IMPLEMENT → RUNTIME CHECK → LINEAGE DEBUG). For low-complexity
  scripts (score < 3), collapse to SPEC → IMPLEMENT.
- **`build/` is throwaway.** Anything in `build/` must be regenerable from
  `specs/` and `src/`. Never commit it.
- **`runs/` is the audit trail.** Commit execution artifacts here so downstream
  consumers can trace lineage.

## How to invoke the skill

- Natural language: "Design a pipeline that …", "validate specs/churn.yaml",
  "render the DAG as mermaid", "add a node for X".
- Slash command: `/hamilton-harness [--viz] [--viz-format FMT] [spec-name]`.

## Expectations on Claude

- Propose spec changes as a YAML diff first; wait for confirmation before
  writing when the change is destructive (rename/remove/rewire/type-change).
- Prefer regenerating stubs through `scripts/viz.py` over hand-editing the
  generated `src/schemas.py`.
- On runtime failures, use Hamilton lineage (`dr.what_is_upstream_of(node)`)
  before rewriting upstream code blindly.

## Related docs in the skill

- `SPEC.md` — YAML schema reference
- `LAYOUT.md` — file structure
- `DEBUG.md` — failure decision tree
- `QUICKSTART.md` — 10-minute onboarding
