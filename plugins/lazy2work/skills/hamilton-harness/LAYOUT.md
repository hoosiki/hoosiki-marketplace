# Target Project Layout

When you use `hamilton-harness` in a project, it expects (and scaffolds) the following layout. Stick to it — several scripts assume these paths.

```
your-project/
├── CLAUDE.md                            # Project rules; mentions hamilton-harness
├── specs/                               # Single source of truth (human-edited)
│   └── *.yaml
├── src/
│   ├── pipelines/                       # Hamilton modules (one file per pipeline)
│   │   └── *.py
│   └── schemas.py                       # Generated Pydantic models
├── tests/
│   ├── test_dag_matches_spec.py         # L1 structural equivalence (auto-generated)
│   └── test_properties/                 # L3 Hypothesis property tests
│       └── test_*.py
├── build/                               # gitignored; always regenerable
│   ├── stubs/                           # YAML → Python stubs produced by F3
│   ├── dags/
│   │   ├── spec/                        # Images rendered from the YAML
│   │   ├── impl/                        # Images rendered from the code
│   │   └── diff/                        # Spec vs impl visual diffs (CI)
│   ├── reports/                         # pytest + hypothesis reports
│   └── metrics/                         # session-*.json — see METRICS.md
└── runs/                                # Committed; execution artifacts
    └── {YYYYMMDD}/{feature}/
        ├── input_snapshot.parquet
        ├── output.parquet
        └── hamilton_tracker.json
```

## Guardrails

1. **`specs/` is human-only** — Claude may propose changes through F4 but writes only after the user confirms the diff.
2. **`build/` is throwaway** — add it to `.gitignore`. A clean run must be able to regenerate everything in here.
3. **`runs/` is committed** — execution artifacts are the ground truth for audits. They're reproducibility anchors, not transient files.
4. **`src/schemas.py` is generated** — prefer regenerating through F3 over hand-editing. If a hand edit is needed, delete the generated header comment so we know.

## Initial scaffolding

`templates/project-layout/` in this skill holds seed files you can copy into a fresh project:

- `CLAUDE.md.tpl` — a starter CLAUDE.md that enables hamilton-harness
- `.gitignore.tpl` — covers `build/` and typical Python noise
- `README.md.tpl` — a short project README with instructions to run the stack

The skill does NOT auto-scaffold. When a user asks, read these templates and write them (or offer them as suggestions first).

## CI integration

Two templates live in `templates/`:

- `pre-commit-config.yaml` — runs `validate.py` on staged specs before each commit.
- `github-workflow-dag-gate.yml` — on PR, re-runs validation + checks that the impl module's Driver metadata matches the spec.

Copy them into the target project's `.pre-commit-config.yaml` and `.github/workflows/dag-gate.yml` respectively.
