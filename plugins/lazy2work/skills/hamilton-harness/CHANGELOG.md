# Changelog — hamilton-harness

This changelog tracks the skill's own version independently from the `lazy2work` plugin that bundles it. Follow SemVer.

## [1.0.0] — 2026-04-13

### Added

- Initial release.
- Self-contained skill under `plugins/lazy2work/skills/hamilton-harness/`.
- Four operating modes: F1 (prompt→YAML), F2 (validate), F3 (stub+viz), F4 (modify YAML).
- 7-stage workflow with a complexity-score gate (≥ 3 enforces the flow, < 3 allows bypass).
- `SPEC.md` — YAML schema with four invariants (`range`, `no_nulls`, `values`, `regex`) plus Pydantic mapping for typed structures.
- `templates/spec-schema.json` — JSON Schema (Draft 2020-12) for automatic F2 validation.
- Scripts: `viz.py`, `validate.py`, `yaml_to_mermaid.py`, `yaml_to_graphviz.py`, `yaml_to_hamilton_stub.py`, `dump_impl_meta.py`, `row_validator.py`.
- CLI flags: `--viz`, `--viz-format {mermaid,graphviz,hamilton,all}`, `--stub-only`, `--no-stub`, `--orient`.
- Three example domains: `etl`, `ml-training`, `rag`.
- `DEBUG.md` decision tree for three common failure modes.
- `METRICS.md` session metrics schema.

### Design choices

- Visualization is **pull-based**: no automatic hooks. Trigger via natural language, `--viz` flag, or direct CLI.
- Plugin-level assets (`hooks/hooks.json`, `commands/`, `rules/`) are intentionally **untouched** — this skill is self-contained.
- DataFrame validation uses `RowModelValidator` (Pydantic, sample-based) rather than Pandera. Sample size defaults to 100.

### Known limitations

- Only Python 3.12+ is tested.
- No automatic migration scripts for future spec-schema bumps; manual migration guidance will ship with v2.0.
- `hamilton` format visualization requires `sf-hamilton[visualization]` extras plus the `graphviz` system binary.

## Upgrade notes

Future breaking changes to `SPEC.md` (new required fields, renamed keys, removed invariant kinds) will bump the MAJOR version and include a dedicated migration section here with `before/after` YAML snippets.
