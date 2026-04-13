# Target Project Layout

When you use `hamilton-harness` in a project, it expects (and scaffolds) the following layout. All pipeline assets live under a single top-level `hamilton_pipeline/` directory so they stay isolated from the rest of your repo (Django app, services, notebooks, etc.). Stick to it — several scripts and CI templates assume these paths.

```
your-project/
├── CLAUDE.md                                   # Project rules; mentions hamilton-harness
└── hamilton_pipeline/                          # All pipeline assets live here
    ├── dag_specs/                                  # Single source of truth (human-edited)
    │   └── *.yaml
    ├── src/
    │   ├── pipelines/                          # Hamilton modules (one file per pipeline)
    │   │   └── *.py
    │   └── schemas.py                          # Generated Pydantic models
    ├── tests/
    │   ├── test_dag_matches_spec.py            # L1 structural equivalence (auto-generated)
    │   └── test_properties/                    # L3 Hypothesis property tests
    │       └── test_*.py
    ├── build/                                  # gitignored; always regenerable
    │   ├── stubs/                              # YAML → Python stubs produced by F3
    │   ├── dags/
    │   │   ├── spec/                           # Images rendered from the YAML
    │   │   ├── impl/                           # Images rendered from the code
    │   │   └── diff/                           # Spec vs impl visual diffs (CI)
    │   ├── reports/                            # pytest + hypothesis reports
    │   └── metrics/                            # session-*.json — see METRICS.md
    └── runs/                                   # Committed; execution artifacts
        └── {YYYYMMDD}/{feature}/
            ├── input_snapshot.parquet
            ├── output.parquet
            └── hamilton_tracker.json
```

## Why a dedicated `hamilton_pipeline/` folder

- **Clear ownership.** Other parts of your repo (Django apps, web UI, notebooks) never collide with pipeline assets.
- **Single CWD for commands.** Every CLI invocation (`validate.py`, `viz.py`) runs from inside `hamilton_pipeline/`, so the scripts' CWD-relative `build/` and `dag_specs/` paths resolve predictably.
- **CI-friendly.** `.github/workflows/dag-gate.yml` and `.pre-commit-config.yaml` filter on `hamilton_pipeline/dag_specs/**.yaml` and `hamilton_pipeline/src/pipelines/**.py` — no cross-contamination with unrelated code.
- **Easy deletion / extraction.** The whole pipeline stack can be moved to a sibling repo by copying `hamilton_pipeline/` alone.

## Guardrails

1. **`hamilton_pipeline/dag_specs/` is human-only** — Claude may propose changes through F4 but writes only after the user confirms the diff.
2. **`hamilton_pipeline/build/` is throwaway** — add `hamilton_pipeline/build/` to `.gitignore`. A clean run must be able to regenerate everything in here.
3. **`hamilton_pipeline/runs/` is committed** — execution artifacts are the ground truth for audits. They're reproducibility anchors, not transient files.
4. **`hamilton_pipeline/src/schemas.py` is generated** — prefer regenerating through F3 over hand-editing. If a hand edit is needed, delete the generated header comment so we know.

## Working directory convention

All CLI commands assume you are inside `hamilton_pipeline/`:

```bash
cd hamilton_pipeline
python "$CLAUDE_SKILL_DIR/scripts/validate.py" dag_specs/<name>.yaml
python "$CLAUDE_SKILL_DIR/scripts/viz.py"       dag_specs/<name>.yaml --format all
```

Running from the repo root requires the `hamilton_pipeline/` prefix on every path and still writes `build/` into the repo root — prefer the `cd` approach.

## Initial scaffolding

`templates/project-layout/` in this skill holds seed files you can copy into a fresh project:

- `CLAUDE.md.tpl` — a starter CLAUDE.md at the **repo root** that enables hamilton-harness and points to `hamilton_pipeline/`
- `.gitignore.tpl` — covers `hamilton_pipeline/build/` and typical Python noise
- `README.md.tpl` — a short project README with instructions to run the stack

Typical bootstrap:

```bash
mkdir -p hamilton_pipeline/{dag_specs,src/pipelines,tests/test_properties,runs}
touch hamilton_pipeline/src/__init__.py hamilton_pipeline/src/pipelines/__init__.py

cp "$CLAUDE_SKILL_DIR/templates/project-layout/CLAUDE.md.tpl"   CLAUDE.md
cp "$CLAUDE_SKILL_DIR/templates/project-layout/.gitignore.tpl"  .gitignore
cp "$CLAUDE_SKILL_DIR/templates/project-layout/README.md.tpl"   README.md
```

The skill does NOT auto-scaffold. When a user asks, read these templates and write them (or offer them as suggestions first).

## CI integration

Two templates live in `templates/`:

- `pre-commit-config.yaml` — runs `validate.py` on staged specs under `hamilton_pipeline/dag_specs/` before each commit.
- `github-workflow-dag-gate.yml` — on PR, re-runs validation + checks that the impl module's Driver metadata matches the spec.

Copy them into the target project's `.pre-commit-config.yaml` and `.github/workflows/dag-gate.yml` respectively.
