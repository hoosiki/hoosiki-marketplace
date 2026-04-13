# Example — orders_etl (ETL)

A minimal spec that turns a CSV of order events into a daily-aggregated Parquet
report. Shows:

- An external-input chain (`order_csv_path`, `report_parquet_path` as params).
- Row-level Pydantic validation on the raw table (`OrderRow`).
- Range + no-nulls invariants on the final `daily_totals`.
- Tag-based ownership and importance.

## Try it

The example's contents are laid out as a mini `hamilton_pipeline/` directory —
copy them into your project's `hamilton_pipeline/` and run from there:

```bash
# From your project root:
mkdir -p hamilton_pipeline && cp -r "$CLAUDE_SKILL_DIR/examples/etl/"* hamilton_pipeline/
cd hamilton_pipeline

# 1. Validate
python "$CLAUDE_SKILL_DIR/scripts/validate.py" specs/orders_etl.yaml

# 2. Render + generate stubs
python "$CLAUDE_SKILL_DIR/scripts/viz.py" specs/orders_etl.yaml --format all

# 3. Copy the generated stub into src/pipelines/ and fill in the bodies:
#    cp build/stubs/orders_etl_stub.py src/pipelines/orders_etl.py
#    cp build/stubs/schemas.py src/schemas.py
```

Or stay inside the skill's example directory (`cd $CLAUDE_SKILL_DIR/examples/etl`)
to play with it without touching your project layout.

## Key teaching points

- `raw_orders` has `type: OrderRow` where `OrderRow` is a Pydantic model from
  the `schemas:` section. The generator emits:

  ```python
  @check_output_custom(RowModelValidator(OrderRow, sample_size=100))
  def raw_orders(order_csv_path: str) -> pd.DataFrame: ...
  ```

- `daily_totals` has `range: [0, 1e9]` + `no_nulls: true`. Both stack into two
  `@check_output` decorators.

- `written_report_path` depends on two inputs (one is the target path itself)
  — pattern for side-effect nodes.
