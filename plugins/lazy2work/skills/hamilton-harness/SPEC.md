# YAML Spec Reference — hamilton-harness v1.0

The ground-truth schema for pipeline specs consumed by this skill. Every YAML under `specs/` must conform to this document.

## Top-level structure

```yaml
name: customer_churn          # required, snake_case
description: >-               # optional
  One-sentence summary of the pipeline's purpose.
version: 1.0.0                # optional, semver; defaults to 1.0.0

schemas:                      # optional, list of Pydantic model definitions
  - name: ModelMetrics
    fields:
      roc_auc: { type: float, ge: 0.0, le: 1.0 }

nodes:                        # required, ≥ 1 item
  - name: raw_orders
    type: pd.DataFrame
    source: input

metadata:                     # optional, free-form
  owner: analytics-team
  project: churn-2026
```

| Field | Required | Type | Notes |
|-------|----------|------|-------|
| `name` | ✓ | string | snake_case, `^[a-z][a-z0-9_]*$` |
| `description` | – | string | Free-form, prose |
| `version` | – | string | SemVer. Defaults to `1.0.0` |
| `schemas` | – | list | Pydantic model declarations (see §2) |
| `nodes` | ✓ | list | Must contain ≥ 1 entry |
| `metadata` | – | map | Free-form metadata passed through to Hamilton `@tag` where possible |

## 1. Nodes

Every element in `nodes` is either an **external input** (has `source: input`) or a **computed node** (has `inputs`). A node never has both.

```yaml
- name: churn_prediction
  type: pd.Series
  inputs: [churn_features, trained_model]
  description: Probability of churn, 0-1.
  invariants:
    - range: [0.0, 1.0]
    - no_nulls: true
  tags:
    owner: ml-team
    importance: critical
```

### Node fields

| Field | Required | Type | Constraint |
|-------|----------|------|------------|
| `name` | ✓ | string | snake_case, unique across the spec |
| `type` | ✓ | string | Python built-in, pandas/numpy type, or name of a schema in the `schemas:` section |
| `source` | — | enum | Only `input` is valid. Mutually exclusive with `inputs` |
| `inputs` | — | list[string] | Each item must match another node's `name`. Mutually exclusive with `source` |
| `description` | – | string | Used verbatim as the Hamilton docstring |
| `invariants` | – | list | Runtime checks. See §3 |
| `tags` | – | map | Copied into `@tag(...)` on the generated stub |

### Type resolution order

`validate.py` walks these namespaces in order:

1. Python built-ins (`int`, `float`, `str`, `bool`, `bytes`, `list`, `dict`, `object`, `None`)
2. pandas (`pd.DataFrame`, `pd.Series`)
3. numpy (`np.ndarray`, `np.int32`, `np.int64`, `np.float64`, ...)
4. datetime (`datetime`, `date`, `timedelta`)
5. `schemas[].name` declared in the same spec
6. Unknown → warning (strict mode: error)

## 2. Schemas — Pydantic model declarations

Use `schemas:` to declare the Pydantic models that appear as node `type` values. This keeps strongly-typed structures in the spec without scattering `class` definitions.

```yaml
schemas:
  - name: UserScore
    fields:
      user_id: { type: int }
      score:   { type: float, ge: 0.0, le: 1.0 }
      tier:    { values: [A, B, C] }
      note:    { type: str, nullable: true, max_length: 200 }
```

### Field options

| Option | Applies to | Effect |
|--------|-----------|--------|
| `type` | any | Python type name |
| `ge`, `le`, `gt`, `lt` | numeric | `Field(ge=..., le=...)` |
| `min_length`, `max_length` | string / list | `Field(min_length=..., max_length=...)` |
| `pattern` | string | `Field(pattern="...")` |
| `nullable` | any | Wraps type in `Optional[T]` and sets default `None` |
| `values` | any | Emits `Literal[...]`; overrides `type` |
| `description` | any | `Field(description="...")` |

### Emitted Python

```python
from typing import Literal, Optional
from pydantic import BaseModel, Field

class UserScore(BaseModel):
    user_id: int
    score: float = Field(ge=0.0, le=1.0)
    tier: Literal["A", "B", "C"]
    note: Optional[str] = Field(default=None, max_length=200)
```

## 3. Invariants — runtime data quality checks

`invariants` is a list. Each entry is a single-key dict. Four kinds are supported in v1.0:

| Key | Value | Emits (Hamilton) |
|-----|-------|------------------|
| `range` | `[lo, hi]` | `@check_output(range=(lo, hi), importance="fail")` |
| `no_nulls` | `true` / `false` | `@check_output(allow_nans=False, importance="fail")` |
| `values` | list of literals | `@check_output_custom(ValuesInValidator(values))` |
| `regex` | string | `@check_output_custom(RegexValidator(pattern))` |

Multiple entries stack into multiple decorators on the same function.

### DataFrame invariants

For a node whose `type` resolves to `pd.DataFrame` **and** whose `type` also matches a schema in the `schemas:` list, the stub generator emits:

```python
@check_output_custom(
    RowModelValidator(model=OrderRow, sample_size=100, importance="fail")
)
def raw_orders(...) -> pd.DataFrame: ...
```

`RowModelValidator` is bundled in `scripts/row_validator.py`. It samples N rows (default 100) and validates each against the Pydantic model. This trades full correctness for practical speed on large frames.

## 4. Tags

Free-form `tags` are copied directly to `@tag(...)`. Two conventions are recommended but not enforced:

- `owner`: a team or individual identifier.
- `importance`: one of `low`, `medium`, `high`, `critical`. CI gates can filter on these.

## 5. Full minimal example

```yaml
name: daily_orders_etl
description: Aggregate daily order logs into a reporting table.
schemas:
  - name: OrderRow
    fields:
      order_id: { type: int }
      user_id:  { type: int }
      amount:   { type: float, ge: 0.0 }
      ts:       { type: datetime }

nodes:
  - name: order_csv_path
    type: str
    source: input

  - name: raw_orders
    type: OrderRow
    inputs: [order_csv_path]
    description: Raw order log, validated row-by-row.

  - name: daily_totals
    type: pd.DataFrame
    inputs: [raw_orders]
    description: Sum of amount per day.
    invariants:
      - range: [0.0, 1_000_000_000.0]
      - no_nulls: true
    tags:
      owner: data-eng
      importance: high
```

## 6. Version policy

The `version` field refers to the spec schema version (this document). If a future `SPEC.md` is released as v1.1, it will only add optional fields — existing v1.0 specs will continue to validate. Breaking changes go into v2.0 and include a migration guide in `CHANGELOG.md`.
