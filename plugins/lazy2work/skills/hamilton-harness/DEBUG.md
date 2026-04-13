# Debug Decision Tree

Three failure modes are common with spec-driven Hamilton development. Walk through this tree when a run fails.

## Entry classification

Run the failing command and look at stderr / the test output. Categorize into one of:

- **A. Validation failure** — messages mention `jsonschema`, `L1`…`L7`, or `validate.py` exited non-zero.
- **B. Runtime contract violation** — messages mention `@check_output`, `DataValidationError`, or `ValidationError` from Pydantic.
- **C. Property-based test failure** — pytest output mentions `Falsifying example`, `Shrunken`, or `hypothesis.errors`.

Each entry points to a dedicated procedure below. Work each procedure sequentially; don't jump ahead.

## A. Validation failure (F2 layer)

1. Run `validate.py` with `--strict` and `-v` for full detail (from inside `hamilton_pipeline/`):
   ```bash
   cd "$CLAUDE_PROJECT_DIR/hamilton_pipeline"
   python "$CLAUDE_SKILL_DIR/scripts/validate.py" specs/<name>.yaml --strict
   ```
2. Copy the first reported error. The layer prefix tells you what to fix:
   - **L1 schema** — the YAML is missing a required field or has the wrong type. Open `SPEC.md` §1 and compare.
   - **L2 duplicate name** — search the YAML for the duplicated identifier, rename one side.
   - **L3 cycle** — read the cycle path the validator printed; decide which edge to drop or redirect.
   - **L4 orphan node** — the node has no `inputs` and no `source: input`. Either add an input source or delete the node.
   - **L5 dangling reference** — a name listed in `inputs` isn't a real node. Fix the typo or add the missing node.
   - **L6 type** — the `type` value isn't resolvable. Either add it to `schemas:` or correct the spelling.
   - **L7 invariant syntax** — `range` must be `[lo, hi]`, `values` must be a non-empty list, etc. Re-read `SPEC.md` §3.
3. Re-run `validate.py`. Repeat until it exits 0.

**Exit criterion**: `validate.py` returns 0 on the current YAML.

## B. Runtime contract violation (@check_output or Pydantic)

1. Note the failing node name from the traceback (it will appear as `<node>_raw_check_output_...`).
2. Open a Python shell or a small script (run from inside `hamilton_pipeline/`):
   ```python
   from hamilton import driver
   import src.pipelines.<module> as pipeline
   dr = driver.Builder().with_modules(pipeline).build()
   dr.display_upstream_of("<node>", "build/dags/debug/upstream.png")
   ```
3. Execute only the upstream nodes, checking the actual values:
   ```python
   intermediate = dr.execute(
       dr.what_is_upstream_of("<node>"),
       inputs={...},  # the same inputs that failed
   )
   for name, value in intermediate.items():
       print(name, type(value), getattr(value, "shape", len(value) if hasattr(value, "__len__") else "?"))
   ```
4. The first node that has an unexpected range / null count / type is the real culprit. Fix that node.
5. Re-run the original pipeline.

**Exit criterion**: the contract that failed now passes. If it still fails after the first upstream fix, there may be multiple violations — repeat from step 2 on the next failing node.

## C. Property-based test failure

1. Rerun the failing test with Hypothesis diagnostics:
   ```bash
   pytest -v tests/test_properties/test_<name>.py --hypothesis-show-statistics
   ```
2. Copy the **shrunken counter-example** — Hypothesis minimizes the failing input down to the smallest reproducer.
3. Two possibilities:
   - The implementation is wrong for that input. Trace through by hand with the counter-example in mind and fix the function.
   - The property itself is too strong (e.g., it requires commutativity that the real function doesn't guarantee). Re-read the docstring, weaken the property, and document why.
4. After a fix, re-run the full suite — not just the failing test — because Hypothesis may find a new counter-example.

**Exit criterion**: the property test passes; the fix doesn't break other properties.

## When the loop isn't converging

If you loop through any entry more than three times without progress, stop and escalate:

- Consult `DEBUG.md` examples from `examples/<domain>/` — similar failure modes may already be documented there.
- Re-read `SPEC.md` and the relevant upstream code.
- Invoke `/sc:troubleshoot` with the full transcript; that command is purpose-built for deeper forensics.

Loops of "fix → fail → revert → fix" usually mean a hidden assumption upstream. Step back and re-examine the spec with fresh eyes.
