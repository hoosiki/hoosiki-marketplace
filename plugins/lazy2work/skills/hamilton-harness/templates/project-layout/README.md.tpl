# {{ project_name }}

Hamilton-based data pipeline project scaffolded with `hamilton-harness`. All
pipeline assets live under the `hamilton_pipeline/` directory — see the skill's
`LAYOUT.md` for the full structure.

## Quick commands

```bash
# All commands run from inside hamilton_pipeline/
cd hamilton_pipeline

# Validate a spec
python "$CLAUDE_SKILL_DIR/scripts/validate.py" dag_specs/<name>.yaml

# Generate stubs + render mermaid
python "$CLAUDE_SKILL_DIR/scripts/viz.py" dag_specs/<name>.yaml --format mermaid

# Run the pipeline
python -c "
from hamilton import driver
import src.pipelines.<name> as pipeline
dr = driver.Builder().with_modules(pipeline).build()
result = dr.execute(final_vars=['<final_node>'], inputs={...})
print(result)
"

# Tests
pytest tests/ -v
```

## Layout

See the skill's `LAYOUT.md` for the full expected structure. Key directories
(all under `hamilton_pipeline/`):

- `dag_specs/`: YAML specs (the source of truth)
- `src/pipelines/`: Hamilton modules
- `src/schemas.py`: generated Pydantic models
- `tests/`: pytest + Hypothesis property tests
- `build/`: throwaway; regenerable (gitignored)
- `runs/`: committed; execution artifacts

## Development loop

1. Describe your pipeline in plain language — Claude writes `hamilton_pipeline/dag_specs/<name>.yaml`.
2. `cd hamilton_pipeline` and validate: `python "$CLAUDE_SKILL_DIR/scripts/validate.py" dag_specs/<name>.yaml`.
3. Generate stubs + diagram: `python "$CLAUDE_SKILL_DIR/scripts/viz.py" dag_specs/<name>.yaml --format all`.
4. Review the diagram; if the structure looks right, copy the stub into `src/pipelines/`.
5. Fill in function bodies one at a time. Run tests after each function.
6. On failure, consult the skill's `DEBUG.md`.
