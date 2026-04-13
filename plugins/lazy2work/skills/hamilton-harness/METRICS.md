# Session Metrics Schema

Each hamilton-harness session (a chain of F1–F4 operations on one project) writes a JSON file to `build/metrics/session-<timestamp>.json`. This lets you audit Claude's decisions later and spot drift or bypass patterns.

## File location

```
<project-root>/build/metrics/session-2026-04-13T14-23-05Z.json
```

The timestamp is the session start, ISO 8601, with colons replaced by `-` for filename safety.

## Schema

```json
{
  "session_id": "a3f1c2b0-6c12-4f4a-8f3d-1b2e5d9c7a11",
  "started_at": "2026-04-13T14:23:05.321Z",
  "ended_at":   "2026-04-13T14:41:18.902Z",
  "skill_version": "1.0.0",
  "complexity_score": 5,
  "entered_mode": "F1",
  "bypass_invoked": false,
  "events": [
    {
      "timestamp": "2026-04-13T14:23:10.113Z",
      "event": "spec_created",
      "stage": 1,
      "outcome": "success",
      "spec_name": "churn",
      "node_count": 9
    },
    {
      "timestamp": "2026-04-13T14:24:02.443Z",
      "event": "validation",
      "stage": 2,
      "outcome": "fail",
      "errors": ["L3 cycle detected: churn_features -> scored -> churn_features"]
    },
    {
      "timestamp": "2026-04-13T14:25:47.118Z",
      "event": "validation",
      "stage": 2,
      "outcome": "success",
      "retry_count": 1
    },
    {
      "timestamp": "2026-04-13T14:27:33.904Z",
      "event": "viz_rendered",
      "stage": 3,
      "outcome": "success",
      "format": "mermaid",
      "trigger": "natural_language"
    }
  ],
  "summary": {
    "stages_passed": [1, 2, 3, 5, 6],
    "stages_failed": [],
    "total_retries": 1,
    "total_viz_renders": 2,
    "total_validations": 3,
    "drift_events": 0,
    "claude_bypass_attempts": 0
  }
}
```

## Event enum

| `event` | Stage | When fired |
|---------|-------|-----------|
| `spec_created` | 1 | F1 wrote `specs/<name>.yaml` |
| `validation` | 2 | F2 ran (`outcome`: `success` / `fail`) |
| `stub_generated` | 3 | `yaml_to_hamilton_stub.py` finished |
| `viz_rendered` | 3 | A Mermaid/Graphviz/Hamilton render succeeded |
| `pbt_scaffolded` | 4 | Property-test stubs emitted |
| `impl_written` | 5 | Claude filled at least one function body |
| `check_output_triggered` | 6 | A runtime `@check_output` decorator fired (with outcome `success`/`fail`) |
| `lineage_debug` | 7 | Stage-7 upstream inspection was used |
| `destructive_change_confirmed` | any | F4 accepted a destructive change |
| `bypass_requested` | any | Claude skipped the 7-stage flow for a low-complexity request |

## Aggregate fields

| Field | Description |
|-------|-------------|
| `complexity_score` | The score computed in `SKILL.md` §Complexity |
| `entered_mode` | The first mode dispatched (`F1`/`F2`/`F3`/`F4`) |
| `bypass_invoked` | True if the 7-stage flow was skipped |
| `total_retries` | Number of `validation: fail` → `validation: success` transitions |
| `drift_events` | `test_dag_matches_spec` failures observed in this session |
| `claude_bypass_attempts` | Times Claude tried to write to `src/` without a passing spec |

## Writing metrics

The skill scripts themselves only append events. They never overwrite or delete existing metrics files. A session ends when the user closes Claude Code or moves to a different project; the `ended_at` field is updated as each event is appended.

## Reading metrics

Recommended follow-up: run `/sc:analyze build/metrics/` periodically to spot trends — e.g., if `total_retries` is consistently high on specific specs, that YAML likely has structural issues worth revisiting.
