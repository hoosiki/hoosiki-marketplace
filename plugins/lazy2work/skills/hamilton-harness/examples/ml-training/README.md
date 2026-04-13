# Example — churn_training (ML)

Customer-churn prediction training pipeline. Highlights:

- Feature engineering chain (`user_tenure_days`, `user_avg_order_value` → `features`).
- Train/val split as sibling nodes branching from `labelled_features`.
- Structured output: `ModelMetrics` is a Pydantic model declared in `schemas:`
  and attached to the `metrics` node — runtime validation ensures ROC AUC is
  in [0, 1].

## Try it

```bash
cd examples/ml-training
python $CLAUDE_SKILL_DIR/scripts/viz.py specs/churn_training.yaml --format all
```

Open `build/dags/spec/churn_training.png` to see the DAG. Notice how
`train_set` and `val_set` both depend on `labelled_features` — the tool places
them side-by-side automatically.

## Teaching points

- **Typed outputs for ML metrics** — avoids the "what does `result['auc']` return?"
  confusion. The Pydantic model doubles as documentation.
- **Branch then merge** — `metrics` only depends on `trained_model` and
  `val_set`; the split is explicit in the YAML.
- **Importance tags** — `trained_model` and `metrics` are `critical`; CI can
  gate merges on these passing their invariants.
