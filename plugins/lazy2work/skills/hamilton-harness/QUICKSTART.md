# Quickstart — 10 minutes to your first pipeline

This walkthrough uses the `etl` example to get you from zero to a rendered DAG. All pipeline assets live under a single `hamilton_pipeline/` directory at your project root — see `LAYOUT.md` for details.

## Prerequisites (one-time)

```bash
# Python packages
uv pip install "sf-hamilton[visualization,pandera]" pydantic hypothesis pyyaml jsonschema networkx

# System binary (macOS example)
brew install graphviz
# Ubuntu: sudo apt-get install -y graphviz
```

Verify: `python -c "import hamilton, pydantic, hypothesis; print('ok')"` and `dot -V`.

## Step 1 — Invoke the skill with an example

In Claude Code, type:

```
/hamilton-harness
```

Then say:

> Walk me through the ETL example. Explain the spec and render it as a Mermaid diagram.

Claude should read `examples/etl/dag_specs/orders_etl.yaml` and produce a Mermaid diagram in the chat.

## Step 2 — Copy the example into a fresh project

```bash
mkdir -p ~/my-first-pipeline/hamilton_pipeline && cd ~/my-first-pipeline/hamilton_pipeline
cp -r $(python -c "import os; print(os.path.expanduser('~/.claude/plugins/cache/lazy2work@*/plugins/lazy2work/skills/hamilton-harness/examples/etl/'))")* .
```

You now have `dag_specs/`, `src/`, `tests/` under `my-first-pipeline/hamilton_pipeline/`. All subsequent commands run from inside `hamilton_pipeline/`.

## Step 3 — Validate the spec

```bash
cd ~/my-first-pipeline/hamilton_pipeline   # if not already there
python "$CLAUDE_SKILL_DIR/scripts/validate.py" dag_specs/orders_etl.yaml
```

Expected output ends with `PASSED`.

## Step 4 — Render + generate stubs

```bash
python "$CLAUDE_SKILL_DIR/scripts/viz.py" dag_specs/orders_etl.yaml --format all
```

This writes (all inside `hamilton_pipeline/`):

- `build/stubs/orders_etl_stub.py`
- `build/dags/spec/orders_etl.mmd`
- `build/dags/spec/orders_etl.png`
- `build/dags/spec/orders_etl.meta.json`

Open the PNG to confirm the structure matches the Mermaid.

## Step 5 — Fill in the stubs and run

Edit `build/stubs/orders_etl_stub.py` — replace each `raise NotImplementedError` with real logic. Copy the result into `src/pipelines/orders_etl.py` once you're happy with the first function.

Run a minimal execution (from inside `hamilton_pipeline/`):

```python
from hamilton import driver
import src.pipelines.orders_etl as pipeline

dr = driver.Builder().with_modules(pipeline).build()
result = dr.execute(
    final_vars=["daily_totals"],
    inputs={"order_csv_path": "data/orders.csv"},
)
print(result["daily_totals"].head())
```

If `@check_output` decorators flag a violation, use `DEBUG.md` Entry B.

## Step 6 — Ask Claude to generate the PBT scaffolding

> Generate Hypothesis-based property tests for orders_etl.yaml. Focus on the `daily_totals` node.

Claude should produce files under `tests/test_properties/` derived from the `invariants` in the spec.

## What next?

- Follow the same steps with `examples/ml-training/` or `examples/rag/`.
- Read `SPEC.md` to understand every field before writing your own spec.
- Read `LAYOUT.md` for the full project layout this skill expects.
- When you hit failures, jump to `DEBUG.md`.
