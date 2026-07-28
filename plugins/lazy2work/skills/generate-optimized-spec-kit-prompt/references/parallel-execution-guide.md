# Parallel Execution Guide — Waves, DAG, workmux

How to turn a set of pre-sliced issues into a **maximally parallel** two-phase Spec Kit run.

Applies `research_speckit_pipeline_parallel_safety_boundary_by_command_exhaustive_20260728` (safety boundary per command) and `research_workmux_usage_and_speckit_parallel_pipeline_design_exhaustive_20260714` (workmux mechanics).

## 1. The Safety Boundary — where parallelism stops

**The line is drawn at `/speckit.plan`, because `plan` is the only stage that reads the codebase.**

```
constitution ──▶ specify ──▶ clarify ──╬══▶ plan ──▶ checklist ──▶ tasks ──▶ analyze ──▶ implement ──▶ converge
   global 1×      ✅ all-parallel        ║   🔴 wave-only  🟡 inherits  🟡 inherits  🟡 inherits   🔴 wave-only   🔴 tied to implement
                                        ║
                                  ★ BOUNDARY
                              (codebase reading starts)
```

| Stage | Depends on other features? | Verdict |
|-------|---------------------------|---------|
| `specify` | ❌ none (WHAT/WHY only) | ✅ **all features in parallel** |
| `clarify` | 🟡 almost none (own spec's `[NEEDS CLARIFICATION]`) | ✅ **all features in parallel** |
| `plan` | 🔴 high — scans codebase, maps integration points | 🔴 **wave-only** |
| `checklist` | ❌ own spec + plan | 🟡 inherits plan's wave |
| `tasks` | 🟡 own plan artifacts | 🟡 inherits plan's wave |
| `analyze` | ❌ own 4-way + constitution (read-only) | 🟡 inherits plan's wave |
| `implement` | 🔴 absolute — shared source hotspots | 🔴 **wave-only + sequential merge** |
| `converge` | 🔴 implement's output | 🔴 one body with implement |

Two consequences that shape everything below:

- **Parallelism is not the culprit.** Running sequentially but *stage-major* (all specify → all plan → …) loses exactly the same thing. The cause is "the prior feature's code does not exist yet at plan time."
- **What is lost at parallel `plan` is verification, not design intent.** The generated prompts hardcode upstream context, so the design stays right — but if the prompt is wrong, nothing detects it. This is why `03_plan.md` MUST carry an explicit **Upstream Context** section (§6).

`/speckit.analyze` does **not** rescue cross-feature contradictions: it only reads its own feature's constitution↔spec↔plan↔tasks. Two features that adopted opposite conventions both pass. The only place a cross-feature convention can be enforced is **`constitution.md`** — see §7.

## 2. Mandatory pre-conditions (mechanical — skip these and it breaks deterministically)

These are not quality concerns. They are guaranteed failures.

| # | Problem | Fix |
|---|---------|-----|
| 1 | `create-new-feature.sh` derives the number as `max(specs/*) + 1`. Every parallel worktree branches from the same base → **every feature gets the same number**. | Pass `--number NNN` explicitly. The runner injects this into the `01_specify` prompt. Side benefit: kills the `+1` offset that misaligns prompt numbers vs `specs/` numbers even in sequential runs. |
| 2 | `.specify/feature.json` holds "the current feature" as a single global file. N worktrees each overwrite it → **100% merge conflict**. | `git rm --cached .specify/feature.json` + `.gitignore`, or `.gitattributes` `merge=ours`, or drive via `SPECIFY_FEATURE`. |
| 3 | Every worktree needs a unique branch name. | Branch templates in §5 guarantee this. |
| 4 | `workmux add --base` defaults to the *current* branch, not `main`. | Set `base_branch` in `.workmux.yaml` **and** pass `--base` explicitly. |

## 3. Building the dependency DAG

**Do not trust the declared `Blocked by` alone.** Issues routinely declare one blocker while their acceptance criteria require two more.

For every issue, derive `effective_blocked_by` as the union of:

1. **Declared** — the issue's own `Blocked by:` line (and the issues `README.md` index, if present).
2. **Hidden (from acceptance criteria)** — read every AC and ask "which other issue must already exist for this criterion to be verifiable?" An AC that says "the reminder arrives in Telegram" depends on the Telegram channel issue even if only the scheduler issue is declared.
3. **Hidden (from artifact references)** — the issue names a module, endpoint, model, or CLI that another issue creates.

Record declared vs effective separately in the DAG document, and call out each difference explicitly — an unreported hidden dependency produces a `plan.md` that references code that does not exist.

Then reduce transitively: if A→B and B→C, drop a redundant A→C edge from the diagram (keep it in the data if it was declared).

## 4. Computing waves

Wave = **longest-path depth** in the effective DAG, not breadth-first level. Using longest path guarantees every blocker lands in a strictly earlier wave.

```
depth(f) = 0                                   if effective_blocked_by(f) is empty
depth(f) = 1 + max(depth(b) for b in blockers) otherwise
wave_k   = { f : depth(f) == k }
```

Then apply two adjustments:

- **Hotspot split** — if two features in the same wave both rewrite the same shared file (settings, router, dependency manifest) in a *non-idempotent* way, push the later one down a wave. Idempotent edits may stay together, but record the ownership rule (§8).
- **Width cap** — a wave wider than `MAX_CONCURRENT` is fine (workmux throttles), but a wave of 1 sitting between two wide waves is a scheduling stall; consider whether its blocker is real.

Never reorder to make waves prettier. A wrong wave produces a plan that references non-existent code.

### Wave naming

Each wave gets a machine-safe name **and** a human title:

- name: `w{N}-{kebab-theme}` — lowercase, git-branch-safe, e.g. `w0-foundation`, `w1-core-domain`, `w2-channels`, `w3-automation`, `w4-delivery`
- title: a short human phrase, e.g. "Foundation", "Core domain", "Delivery channels"
- rationale: one sentence stating *why* these features can run together and what the previous wave unlocked for them

The theme is derived from what the wave's features have in common, not from a counter. `w0-foundation` is nearly always the environment/prefactor slice.

## 5. workmux mapping

### Branch naming encodes phase and wave

There is no reliable channel to tell a tmux pane which stage to run — tmux windows do not inherit the driver's environment. **The branch name is the channel.**

```
spec/{NNN}-{slug}                   → Phase 1: 01_specify + 02_clarify + commit
build/{wave-name}/{NNN}-{slug}      → Phase 2: 03_plan … 08_converge + commit
```

The pane script recovers everything with `git rev-parse --abbrev-ref HEAD`:

```bash
BRANCH=$(git rev-parse --abbrev-ref HEAD)   # build/w1-core-domain/003-time-views
PHASE=${BRANCH%%/*}                          # build
REST=${BRANCH#*/}                            # w1-core-domain/003-time-views
WAVE=${REST%%/*}                             # w1-core-domain  (empty-safe for spec/)
FEATURE=${REST#*/}                           # 003-time-views
```

Handles slugify to `spec-003-time-views` / `build-w1-core-domain-003-time-views`, so `workmux list` and the dashboard read cleanly and wave membership is visible at a glance.

### Three design decisions that are not optional

| # | Decision | Why |
|---|----------|-----|
| 1 | **Script pane, not agent pane** — a single-pane named layout running a script | An interactive `claude` never exits, so `-W/--wait` never returns and `--max-concurrent` deadlocks. A script exits → the window/session closes → the driver advances. It also enables per-stage `--model`/`--effort`/`--max-turns` and exit-code success detection. |
| 2 | **Exactly one pane** | The window closes only when *all* panes exit. A default two-pane layout (agent + shell) hangs forever because the shell never dies. |
| 3 | **`--foreach` + `--max-concurrent`, not a bash `&` loop** | Concurrent `git worktree add` races on `.git/worktrees/` metadata. workmux serializes creation internally and throttles concurrency. |

Verified against workmux 0.1.224:

- `--branch-template` exposes `--foreach` variables **by bare name** — use `{{ feature }}`, not `{{ foreach_vars.feature }}` (the latter errors). Available: `agent`, `base_name`, `feature` (each foreach var), `foreach_vars`, `index`, `num`.
- `--foreach "var:a,b;var2:x,y"` zips by index; it is **not** a cartesian product.
- `-W/--wait` blocks until the window/session closes but **does not propagate the exit code** — success must be reported through a status file written to the *main* repo (worktrees may be removed).
- `mode: session` avoids the "driver must run inside tmux" constraint of window mode.

### Merging

- Merge **sequentially**, never in parallel — concurrent `workmux merge` races on main's index.
- Use `--rebase` for linear history.
- Gate every merge with `pre_merge`; a failing gate aborts the merge and preserves the worktree.
- Set `merge_keep: true` so evidence survives a bad automated run. Clean up with `workmux rm --all` after review.

## 6. What the generated prompts must carry for parallel safety

Because a parallel `plan` cannot see the prior feature's code, the prompt has to supply what the code would have told it.

**`03_plan.md` MUST include an Upstream Context section** listing, per effective blocker, the concrete artifacts it provides — module paths, function signatures, endpoints, model fields — with an explicit instruction not to rebuild them:

```markdown
## Upstream Context (already provided by prior issues — do NOT rebuild)

- **Issue 001** (`w0-foundation`): `todo/gateway.py::CommandGateway` — idempotency, seq issuance, undo()
- **Issue 002** (`w1-core-domain`): `todo/parser/` — `parse(text, now, tz, lang) -> ParseResult`
```

**`07_implement.md` MUST include shared-infrastructure rules** for every hotspot the feature touches: who owns the file, and the idempotent form of the edit ("if the mount is not `api/v1/`, change it — issue 001 makes the same change, so make it idempotent").

**`01_specify.md`** stays tech-neutral as always; parallel safety adds nothing to it beyond the number pin, which the runner injects.

## 7. Cross-feature conventions belong in the constitution

Running N `clarify` stages concurrently means N independent resolutions of the same ambiguity — and `analyze` will pass both contradictory answers. Pin these globally **before** Phase 1:

- timezone handling
- recurrence semantics
- error format / failure policy
- auth and authorization
- logging and observability
- test strategy (e.g. full TDD)

The DAG document lists candidates it detected; the user decides what goes into `constitution.md`.

## 8. Shared infrastructure ownership

List every file that more than one feature will touch, assign an owner, and state the idempotency rule. Typical hotspots:

| File | Touched by |
|------|-----------|
| settings / installed-apps module | every feature that adds an app |
| API router / URL conf | every feature that adds an endpoint |
| dependency manifest + lockfile | every feature that adds a dependency |

Idempotent handling plus **sequential merge** is what keeps these from colliding. Neither works without the other.

## 9. Cost and rate limits

Concurrent `claude -p` sessions multiply input tokens (CLAUDE.md + constitution + prompt) by the concurrency factor. Headless `claude -p` bills against Agent SDK credits separately from the interactive subscription pool, and falls back to API rates when exhausted.

Start at `MAX_CONCURRENT=4..6` and watch for 429s. There is no benefit to launching every feature at once.

## 10. Notes on adjacent stages

- **`/speckit.taskstoissues`** (not part of this skill's 8-stage flow): if used, run it **sequentially**, only on `analyze`-passed tasks, and preview with `--dry-run`. It writes to external shared state (GitHub Issues); its duplicate-check is check-then-create and races under concurrency, and mis-created issues cannot be `git reset`.
- **`/speckit.converge` exit codes** report execution success, not convergence. Detect convergence with a sentinel in the output, and guard against phantom completion (`[X]` marked but unimplemented) with real build/test gates.
