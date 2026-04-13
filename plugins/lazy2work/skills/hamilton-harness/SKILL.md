---
name: hamilton-harness
description: |
  Build Hamilton data pipelines through a strict spec-driven workflow.
  Triggers on phrases like "파이프라인 만들어", "data pipeline", "DAG 설계",
  "Hamilton으로", "ETL 구현", "feature engineering", "RAG 인덱싱",
  "ML 학습 파이프라인", "DAG 시각화", "시각화해줘", "YAML 스펙 검증".
  Use this skill whenever the user asks to design, implement, validate, visualize,
  or modify a data/ML/RAG pipeline described by nodes and dependencies — even if
  they don't explicitly say "Hamilton". Supports 4 modes: F1 prompt→YAML,
  F2 validate YAML, F3 generate stub + optional viz, F4 modify existing YAML.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
model: opus
argument-hint: "[--viz] [--viz-format mermaid|graphviz|hamilton] [spec-name]"
---

# hamilton-harness

A self-contained skill that makes Claude Code build Hamilton pipelines through a structured spec-driven workflow. The skill bundles the YAML spec schema, validation, stub generation, and multi-format visualization.

## When to use

Activate this skill when the user asks to:

- **Design** a new data pipeline, ETL job, ML training flow, RAG ingestion, feature engineering chain, or any multi-step DAG-shaped computation.
- **Validate** an existing `dag_specs/*.yaml` against the Hamilton-harness schema.
- **Implement** Python Hamilton code from a YAML spec.
- **Visualize** a pipeline (Mermaid, Graphviz PNG/SVG, or Hamilton Driver rendering).
- **Modify** an existing YAML spec (add/remove/rewire nodes) safely.

If the user asks a small one-shot data task ("quickly aggregate this CSV"), check the complexity score in §1 before forcing the full workflow. This skill is meant to lift quality for pipelines, not to slow down simple scripting.

## Complexity score — when to enforce the 7-stage flow

Score the user's request against these signals:

| Signal | Points |
|--------|--------|
| User explicitly mentions "pipeline", "DAG", "workflow", "Hamilton" | +2 |
| Data transformation chain has ≥ 2 stages (input → A → B → output) | +2 |
| External systems involved (DB, API, file system, LLM) | +1 |
| Expected node count ≥ 3 | +1 |
| Domain is regulated (finance, healthcare, safety, compliance) | +2 |
| User requests "quick", "simple", "one-off", "just try" | -3 |

- **Score ≥ 3** → Enforce the 7-stage workflow (start at F1 unless the user provided a YAML).
- **Score < 3** → Offer the structured flow as an option but let Claude write code directly if the user prefers speed.

Record the final score in `build/metrics/session-<timestamp>.json` under `complexity_score` so the user can audit decisions later.

## The four modes (F1–F4)

Parse the user's request and dispatch to the correct mode. Usually only one mode runs per turn; only F1→F2→F3 is common as a chain.

| Signal | Mode | What Claude does |
|--------|------|-----------------|
| Natural-language request with no existing YAML | **F1** | Extract a YAML spec via the 6-step protocol (see §F1) |
| "Validate", "is this spec correct?", path to a YAML given | **F2** | Run `scripts/validate.py <path>` and interpret the report |
| "Implement", "generate stub", "render", "visualize" | **F3** | Run `scripts/viz.py <path>` with the appropriate flags |
| "Add/remove/modify a node", existing YAML present | **F4** | Follow the diff-first modification flow (see §F4) |

## 7-stage workflow (for high-complexity tasks)

```
Stage 1  SPEC          — F1 writes dag_specs/<name>.yaml
Stage 2  VALIDATE      — F2 must pass before moving on
Stage 3  STRUCTURE GATE — F3 render (optional but recommended when reviewing)
Stage 4  PBT SCAFFOLD  — generate tests/test_properties/ stubs (Hypothesis)
Stage 5  IMPLEMENT     — fill Hamilton function bodies one at a time
Stage 6  RUNTIME CHECK — run Driver, let @check_output verify contracts
Stage 7  LINEAGE DEBUG — on failure, use dr.what_is_upstream_of(node)
```

For low-complexity tasks, collapse to: F1 → F3 (with `--stub-only`) → implement.

## Visualization triggers

Visualization is **pull-based** — it only runs when the user asks for it. Automatic hooks are intentionally not wired up. Detect a viz request by looking for ANY of these keywords in the user's recent turns:

- Korean: 시각화, 그려, 보여줘, 다이어그램, DAG 그림, 렌더
- English: visualize, render, draw, diagram, show the DAG, graph

Three safety rules to avoid false triggers:

1. **Context window**: the keyword must appear in the same turn as a reference to a YAML/DAG/pipeline, or within the previous 3 turns of pipeline discussion.
2. **Negation filter**: phrases like "don't visualize", "시각화 하지 마", "skip the diagram" cancel the trigger.
3. **Ambiguous subject**: if no explicit target (no YAML path, no pipeline name), ask clarifying question instead of rendering.

Format selection when the user doesn't specify:

- Default → `mermaid` (inline-friendly, fast)
- If user says "PNG" / "SVG" / "image" → `graphviz`
- If user mentions "CI" / "공식" / "official rendering" → `hamilton`

## F1 — Prompt → YAML (6-step extraction protocol)

When the user describes a pipeline in natural language, follow these six steps in order:

1. **Intent parsing** — summarize the pipeline's domain and purpose in one sentence. Use it as `description` in the YAML.
2. **Input identification** — list every external input (files, APIs, user params, config). Each becomes a node with `source: input`.
3. **Output identification** — list the final artifact(s) the user wants back. These are the leaf nodes.
4. **Intermediate decomposition** — break the middle into 3–7 nodes. Name them with verbs: `clean_orders`, `enrich_features`, `score_users`.
5. **Type inference** — for each node pick a Python type. Use `pd.DataFrame` / `pd.Series` for tabular, custom Pydantic models for structured objects, `dict` / `list` for collections, `object` only as a last resort.
6. **Invariant extraction** — scan the user's prompt for constraint hints and map them to `invariants` entries:
   - "between 0 and 1" → `range: [0, 1]`
   - "no missing values" / "required" → `no_nulls: true`
   - "one of A/B/C" → `values: [A, B, C]`
   - "must match pattern" / "email format" → `regex: "..."`

### Clarifying questions (ask when necessary)

Ask the user, do not guess, when:

- The **input source** is unclear (file path? DB query? API endpoint?)
- The **output form** is unclear (DataFrame? JSON file? DB insert?)
- There are **fewer than 3 intermediate steps** — confirm a Hamilton pipeline is actually warranted versus a single function.

## F2 — Validation

Always run `scripts/validate.py <spec_path>` (not manual inspection). Interpret the report and report to the user. On failure, cite the layer that failed (L1 schema, L2 name uniqueness, L3 cycle, L4 orphan, L5 dangling reference, L6 type resolution, L7 invariant syntax) and suggest a fix. Never proceed to F3 if F2 failed.

## F3 — Stub + (optional) visualization

Invoke:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/viz.py <spec_path> [--format FMT] [--stub-only] [--no-stub]
```

The script runs F2 internally, generates the Hamilton stub + Pydantic schemas, and renders the graph if `--format` is given. Report the produced file paths back to the user, and when the format is `mermaid` paste the generated `.mmd` contents into chat so they can see the graph inline.

## F4 — YAML modification flow (diff-first)

When the user wants to change an existing spec, do NOT write the updated YAML immediately. Instead:

1. Read `dag_specs/<name>.yaml`.
2. Draft the proposed change in memory.
3. Classify each change — check against the destructive-change table below.
4. Show the user a unified diff of the YAML, plus a summary of destructive impact.
5. If any change is destructive, ask for explicit confirmation before writing.
6. Run `scripts/validate.py` on the proposed YAML; only write if F2 passes.
7. Report what changed, and offer to regenerate stubs.

### Destructive changes (require confirmation)

| Change | Destructive? | Reason |
|--------|-------------|-------|
| New leaf node | No | No downstream impact |
| Rename node | **Yes** | All downstream references break |
| Modify `inputs` | **Yes** | Dependency rewiring |
| Delete node | **Yes** | Downstream orphans |
| Change `type` | **Yes** | Python signature must change |
| Tighten `invariants` (e.g., narrower range) | Warn | Past data may no longer pass |
| Loosen `invariants` | No | Safe |
| Edit `tags` or `description` | No | Metadata only |

Always include the expected downstream impact ("this will break 2 downstream nodes: X, Y") in your diff summary.

## Paths and conventions

- `${CLAUDE_SKILL_DIR}` → this skill's directory; use it for every internal script call.
- `${CLAUDE_PROJECT_DIR}` → the user's project root. **All pipeline assets live under `${CLAUDE_PROJECT_DIR}/hamilton_pipeline/`** (see `LAYOUT.md`). Reach `dag_specs/`, `src/`, `tests/`, `build/`, `runs/` through that prefix.
- CLI commands assume the CWD is `${CLAUDE_PROJECT_DIR}/hamilton_pipeline/` so the scripts' CWD-relative `build/` output lands inside the pipeline folder, not the repo root.
- Never reach into the plugin root. The skill is self-contained; all skill assets live under `${CLAUDE_SKILL_DIR}`.

## Supporting documents (read on demand)

- `SPEC.md` — full YAML schema reference. Read before writing or editing specs.
- `LAYOUT.md` — the target project layout the skill scaffolds into.
- `DEBUG.md` — decision tree for the three common failure modes.
- `QUICKSTART.md` — 10-minute onboarding; point new users here.
- `METRICS.md` — logging schema for session metrics.

## Related scripts (under `scripts/`)

- `viz.py` — F3 entry point, orchestrates validation → stub → render.
- `validate.py` — F2 standalone validator.
- `yaml_to_mermaid.py`, `yaml_to_graphviz.py`, `yaml_to_hamilton_stub.py` — format-specific renderers.
- `dump_impl_meta.py` — extract Hamilton Driver metadata for CI diffs.
- `row_validator.py` — Pydantic-based DataFrame sample validator for `@check_output_custom`.

## Examples (under `examples/`)

- `examples/etl/` — order log → daily aggregated Parquet.
- `examples/ml-training/` — churn prediction feature engineering + training.
- `examples/rag/` — documents → chunks → embeddings → vector index.

Read the example closest to the user's domain before writing the YAML; it saves a lot of clarification.
