# {{ project_name }}

Hamilton-based data pipeline project scaffolded with `hamilton-harness`.

## Quick commands

```bash
# Validate a spec
python $CLAUDE_SKILL_DIR/scripts/validate.py specs/<name>.yaml

# Generate stubs + render mermaid
python $CLAUDE_SKILL_DIR/scripts/viz.py specs/<name>.yaml --format mermaid

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

See the skill's `LAYOUT.md` for the full expected structure. Key directories:

- `specs/`: YAML specs (the source of truth)
- `src/pipelines/`: Hamilton modules
- `src/schemas.py`: generated Pydantic models
- `tests/`: pytest + Hypothesis property tests
- `build/`: throwaway; regenerable
- `runs/`: committed; execution artifacts

## Development loop

1. Describe your pipeline in plain language — Claude writes `specs/<name>.yaml`.
2. Validate: `python $CLAUDE_SKILL_DIR/scripts/validate.py specs/<name>.yaml`.
3. Generate stubs + diagram: `python $CLAUDE_SKILL_DIR/scripts/viz.py specs/<name>.yaml --format all`.
4. Review the diagram; if the structure looks right, copy the stub into `src/pipelines/`.
5. Fill in function bodies one at a time. Run tests after each function.
6. On failure, consult the skill's `DEBUG.md`.
