"""Row-level Pydantic validator for pandas DataFrames.

Plug into Hamilton functions with `@check_output_custom`. The validator samples
N rows at random and validates each against a Pydantic model; on any failure it
reports which rows failed and a small sample of errors.

Example:
    from pydantic import BaseModel, Field
    from hamilton.function_modifiers import check_output_custom
    from scripts.row_validator import RowModelValidator

    class OrderRow(BaseModel):
        order_id: int
        amount: float = Field(ge=0)
        user_id: int

    @check_output_custom(RowModelValidator(OrderRow, sample_size=100, importance="fail"))
    def raw_orders(...) -> pd.DataFrame: ...
"""
from __future__ import annotations

import random
from typing import Any, Type

try:
    import pandas as pd
    from pydantic import BaseModel, ValidationError
    from hamilton.data_quality import base
    from hamilton.data_quality.base import ValidationResult
except ImportError as e:
    raise ImportError(
        f"row_validator requires pandas, pydantic>=2, and sf-hamilton. "
        f"Missing: {e.name}"
    )


class RowModelValidator(base.BaseDefaultValidator):
    """Validate a DataFrame by sampling rows and checking each against a Pydantic model."""

    def __init__(
        self,
        model: Type[BaseModel],
        sample_size: int = 100,
        importance: str = "fail",
        random_seed: int | None = None,
    ):
        super().__init__(importance=importance)
        self.model = model
        self.sample_size = sample_size
        self.random_seed = random_seed

    @classmethod
    def applies_to(cls, datatype: type) -> bool:
        return issubclass(datatype, pd.DataFrame)

    @classmethod
    def description(cls) -> str:
        return ("Samples rows from a DataFrame and validates each against a "
                "Pydantic model; reports failures and the first few error details.")

    @classmethod
    def name(cls) -> str:
        return "row_model_validator"

    def validate(self, data: pd.DataFrame) -> ValidationResult:
        rows_total = len(data)
        if rows_total == 0:
            return ValidationResult(
                passes=True,
                message="DataFrame is empty; skipping row validation.",
                diagnostics={"rows_total": 0, "rows_checked": 0},
            )

        n = min(self.sample_size, rows_total)
        if self.random_seed is not None:
            rng = random.Random(self.random_seed)
            indices = rng.sample(range(rows_total), n)
        else:
            indices = random.sample(range(rows_total), n)

        failed_indices: list[int] = []
        error_samples: list[dict[str, Any]] = []

        for idx in indices:
            row = data.iloc[idx].to_dict()
            try:
                self.model.model_validate(row)
            except ValidationError as exc:
                failed_indices.append(int(data.index[idx]) if hasattr(data.index[idx], "__int__") else idx)
                if len(error_samples) < 10:
                    # compact the error list
                    first_err = exc.errors()[0]
                    error_samples.append({
                        "index": int(data.index[idx]) if hasattr(data.index[idx], "__int__") else idx,
                        "field": ".".join(str(p) for p in first_err["loc"]),
                        "error": first_err["msg"],
                    })

        passed = not failed_indices
        coverage_pct = n / rows_total
        message = (
            f"OK: {n}/{rows_total} rows validated against {self.model.__name__}"
            if passed
            else f"{len(failed_indices)} of {n} sampled rows failed {self.model.__name__} validation"
        )
        return ValidationResult(
            passes=passed,
            message=message,
            diagnostics={
                "rows_total": rows_total,
                "rows_checked": n,
                "failed_rows": len(failed_indices),
                "first_failure_indices": failed_indices[:10],
                "error_samples": error_samples,
                "coverage_pct": round(coverage_pct, 4),
                "model": self.model.__name__,
            },
        )
