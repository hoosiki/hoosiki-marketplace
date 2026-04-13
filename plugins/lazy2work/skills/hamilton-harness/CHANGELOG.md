# Changelog — hamilton-harness

This changelog tracks the skill's own version independently from the `lazy2work` plugin that bundles it. Follow SemVer.

## [1.2.0] — 2026-04-13

### Changed

- **Renamed the spec directory: `specs/` → `dag_specs/`.** The new name makes it immediately clear that the YAML files describe a DAG (as opposed to test specs, OpenAPI specs, or other "spec" folders that can appear elsewhere in the repo). The directory's contents and schema are unchanged.
- **Docs updated** — `LAYOUT.md`, `SKILL.md` (Paths and conventions + trigger phrase "YAML 스펙 검증"), `QUICKSTART.md`, `DEBUG.md`, `METRICS.md`, `SPEC.md` all reference `hamilton_pipeline/dag_specs/` instead of `specs/`.
- **Templates updated** — `CLAUDE.md.tpl` rules, `README.md.tpl` development loop, `pre-commit-config.yaml` regex (`^hamilton_pipeline/dag_specs/.*\.yaml$`), `github-workflow-dag-gate.yml` trigger paths and for-loops now target `dag_specs/`.
- **Examples renamed on disk** — `examples/{etl,ml-training,rag}/specs/` renamed to `examples/{etl,ml-training,rag}/dag_specs/` via `git mv` (history preserved).
- **Scripts** — docstring examples in `viz.py` and `validate.py` updated to `dag_specs/<name>.yaml`. No behavioral changes; the scripts still accept any spec path as the first positional argument.

### Migration

For projects using the 1.1.0 layout:

```bash
cd hamilton_pipeline
git mv specs dag_specs
# Update .pre-commit-config.yaml and .github/workflows/dag-gate.yml
# paths: hamilton_pipeline/specs/ → hamilton_pipeline/dag_specs/
```

No code changes are required — Hamilton modules in `src/pipelines/*.py` never imported from `specs/` in the first place; only the CLI invocations and CI configs reference the directory.

## [1.1.0] — 2026-04-13

### Changed

- **Top-level `hamilton_pipeline/` folder wrapper.** All pipeline assets (`specs/`, `src/`, `tests/`, `build/`, `runs/`) now live under a single `hamilton_pipeline/` directory at the project root, keeping them isolated from other parts of the repo (Django apps, notebooks, web UI).
- **`LAYOUT.md`** — tree re-rooted under `hamilton_pipeline/`; added "Why a dedicated folder" rationale, "Working directory convention" (`cd hamilton_pipeline/` before running CLI), and a concrete bootstrap command.
- **`SKILL.md` Paths and conventions** — `${CLAUDE_PROJECT_DIR}` now points to the repo root; pipeline assets resolved through the `${CLAUDE_PROJECT_DIR}/hamilton_pipeline/` prefix.
- **`QUICKSTART.md`** — all `cd` and relative-path examples updated to run inside `hamilton_pipeline/`.
- **`DEBUG.md`** — validation and `display_upstream_of` commands now instruct `cd hamilton_pipeline/` first.
- **`METRICS.md`** — session metrics path changed from `build/metrics/` to `hamilton_pipeline/build/metrics/`.
- **`templates/project-layout/CLAUDE.md.tpl`** — rules reference `hamilton_pipeline/specs/*.yaml`, `hamilton_pipeline/build/`, `hamilton_pipeline/runs/`.
- **`templates/project-layout/README.md.tpl`** — `cd hamilton_pipeline` pattern used consistently; key directories listed with prefix.
- **`templates/project-layout/.gitignore.tpl`** — `build/` entry replaced with `hamilton_pipeline/build/`.
- **`templates/pre-commit-config.yaml`** — `files:` regex now `^hamilton_pipeline/specs/.*\.yaml$`.
- **`templates/github-workflow-dag-gate.yml`** — trigger paths, CI steps, and `upload-artifact` paths all prefixed with `hamilton_pipeline/`; `defaults.run.working-directory: hamilton_pipeline` so subsequent `specs/*.yaml` globs resolve correctly.
- **`examples/*/README.md`** — show `cp -r "$CLAUDE_SKILL_DIR/examples/<domain>/"* hamilton_pipeline/` + `cd hamilton_pipeline` as the recommended path; in-place experimentation (`cd $CLAUDE_SKILL_DIR/examples/<domain>`) still documented for sandbox use.

### Unchanged

- **Scripts** (`viz.py`, `validate.py`, `yaml_to_*.py`, `dump_impl_meta.py`, `row_validator.py`) — unchanged. They still use CWD-relative paths for reads (`specs/`) and writes (`build/`). The new convention is that the user's CWD is `hamilton_pipeline/` when invoking them.
- **Spec schema** (`SPEC.md`, `templates/spec-schema.json`) — unchanged.
- **Example YAMLs** (`examples/*/specs/*.yaml`) — unchanged.

### Migration

For projects already using the 1.0.0 flat layout:

```bash
mkdir -p hamilton_pipeline
git mv specs src tests build runs hamilton_pipeline/
# Update .gitignore: build/ → hamilton_pipeline/build/
# Update CI: paths in .pre-commit-config.yaml and .github/workflows/dag-gate.yml
```

No code changes are required — Hamilton modules still import from `src.pipelines.<name>` when invoked with `hamilton_pipeline/` as the CWD.

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
