# Parallel Execution Guide — Vertical Waves, DAG, workmux

How to turn a set of pre-sliced issues into a **maximally parallel** two-phase Spec Kit run.

Applies `research_speckit_pipeline_parallel_safety_boundary_by_command_exhaustive_20260728` (safety boundary per command) and `research_workmux_usage_and_speckit_parallel_pipeline_design_exhaustive_20260714` (workmux mechanics), corrected against Spec Kit **0.12.x** source (`core_pack/scripts/bash/common.sh`, `core_pack/commands/specify.md`) and **workmux 0.1.229**.

## 0. The two shapes of parallelism

| | Phase 1 — `spec` | Phase 2 — `build` |
|---|---|---|
| Stages | `01_specify` → `02_clarify` | `03_plan` → … → `08_converge` |
| Reads the codebase? | ❌ never | ✅ always (`plan` onward) |
| Isolation | **none needed** — one working tree | **git worktree per wave** |
| Unit of parallelism | **the feature** (all N at once) | **the wave** (one dependency chain) |
| Mechanism | background `claude -p` processes | `workmux` + tmux |
| Merge | none — writes land directly on `main` | sequential merge per stage |

Phase 1 needs no worktrees because `specify`/`clarify` write to exactly one place — `specs/{NNN}-{slug}/` — and those paths are disjoint across features. Phase 2 needs worktrees because `plan`…`implement` write source code.

## 1. The safety boundary — where isolation starts

**The line is `/speckit.plan`, because `plan` is the first stage that reads and writes the codebase.**

```
constitution ──▶ specify ──▶ clarify ──╬══▶ plan ──▶ checklist ──▶ tasks ──▶ analyze ──▶ implement ──▶ converge
   global 1×      ✅ N-parallel          ║   🔴 one worktree per wave, sequential inside the wave
                  (same working tree)    ║
                                    ★ BOUNDARY
                                (codebase access starts)
```

| Stage | Depends on other features? | Verdict |
|-------|---------------------------|---------|
| `specify` | ❌ none (WHAT/WHY only) | ✅ **all features at once, one working tree** |
| `clarify` | 🟡 almost none (own spec's `[NEEDS CLARIFICATION]`) | ✅ **all features at once, one working tree** |
| `plan` | 🔴 high — scans codebase, maps integration points | 🔴 **worktree-isolated, wave-ordered** |
| `checklist` | ❌ own spec + plan | 🟡 inherits the wave |
| `tasks` | 🟡 own plan artifacts | 🟡 inherits the wave |
| `analyze` | ❌ own 4-way + constitution (read-only) | 🟡 inherits the wave |
| `implement` | 🔴 absolute — shared source hotspots | 🔴 **worktree-isolated + sequential merge** |
| `converge` | 🔴 implement's output | 🔴 one body with implement |

`/speckit.analyze` does **not** rescue cross-feature contradictions: it only reads its own feature's constitution↔spec↔plan↔tasks. Two features that adopted opposite conventions both pass. The only place a cross-feature convention can be enforced is **`constitution.md`** — see §9.

## 2. Phase 1 — background fan-out in one working tree

### Why no worktrees

Spec Kit 0.12 resolves the active feature from **explicit state**, not from the git branch (`common.sh::get_feature_paths`):

```
1. SPECIFY_FEATURE_DIRECTORY   (environment variable — wins)
2. .specify/feature.json        ("feature_directory" key)
3. error
```

and `/speckit.specify` uses whatever `SPECIFY_FEATURE_DIRECTORY` it is given **as-is**, only auto-numbering when the variable is absent (`commands/specify.md` §3). Core `create-new-feature.sh` creates **no git branch at all** — branch creation moved to the optional git extension (`/speckit.git.feature`).

So a per-process environment variable is a complete isolation channel:

```bash
SPECIFY_FEATURE_DIRECTORY="specs/003-ws-streaming" \
SPECIFY_FEATURE="003-ws-streaming" \
  claude -p "$(cat 003-ws-streaming/01_specify.md)" ... &
```

N of those in the same directory write to N disjoint `specs/` subdirectories. No branch, no worktree, no merge.

### The four shared-state risks and how each is closed

| # | Shared thing | Failure without a fix | Fix |
|---|--------------|----------------------|-----|
| 1 | Feature numbering | Every process scans `specs/` and computes the same `max+1` → **all N features collide on one number** | `SPECIFY_FEATURE_DIRECTORY` pins both number and slug. (Legacy ≤0.11 fallback: `create-new-feature.sh --number NNN --short-name {slug}`.) |
| 2 | `.specify/feature.json` | N writers truncate-and-rewrite one file | Benign **only because** every process sets `SPECIFY_FEATURE_DIRECTORY`, which is read *before* the file and never falls through to it. Also `git rm --cached` + `.gitignore` it. |
| 3 | The git index | N agents running `git add`/`git commit` corrupt each other's staging | Agents run with **`--no-commit`**. The driver makes **one** commit after the fan-out joins. |
| 4 | The current branch | An agent that creates or switches a branch yanks the working tree out from under the other N−1 | The preamble forbids branch operations outright. Core Spec Kit no longer creates one. |

### Gate, then commit

After all N processes exit, the driver runs the spec gate over every feature — `spec.md` exists and zero `[NEEDS CLARIFICATION]` markers remain — and only then commits `specs/`. A failed feature is reported and leaves its directory in place for a targeted re-run; it does not block the others.

### Concurrency

The default is **all N at once** — that is the whole point of Phase 1, and these stages are short (`01_specify` caps at 30 turns, `02_clarify` at 50). Throttle with `--max-concurrent` when the account hits 429s; see §10.

## 3. Building the dependency DAG

**Do not trust the declared `Blocked by` alone.** Issues routinely declare one blocker while their acceptance criteria require two more.

For every issue, derive `effective_blocked_by` as the union of:

1. **Declared** — the issue's own `Blocked by:` line (and the issues `README.md` index, if present).
2. **Hidden (from acceptance criteria)** — read every AC and ask "which other issue must already exist for this criterion to be verifiable?" An AC that says "the reminder arrives in Telegram" depends on the Telegram channel issue even if only the scheduler issue is declared.
3. **Hidden (from artifact references)** — the issue names a module, endpoint, model, or CLI that another issue creates.

Record declared vs effective separately in the DAG document, and call out each difference explicitly. In the vertical-wave model a missed dependency does not merely weaken a prompt — it **puts two features in sibling waves that cannot actually run concurrently**, and the second one's `plan` will find nothing to build on.

Then reduce transitively: if A→B and B→C, drop a redundant A→C edge from the diagram (keep it in the data if it was declared).

## 4. Computing waves — vertical, not horizontal

### The change and why it matters

The obvious partition is **horizontal**: group by longest-path depth, run each depth level in parallel, merge, repeat. It is wrong for this pipeline in two ways.

- **Every level is a barrier.** A 4-deep graph pays 4 merge barriers, and each barrier waits for the slowest feature in that level.
- **Every feature plans blind.** A feature at depth 2 branches from a `main` that has depth-0 and depth-1 code, but its *own* level's siblings are invisible — and so is anything the prompt failed to describe. This is what forced the hardcoded `Upstream Context` crutch.

The **vertical** partition groups a *dependency chain* into one wave: sequential inside the wave, parallel across waves.

```
declared graph                        vertical waves

000 → 001 → 003 ┬→ 004 → 005 → 006    w0-foundation : 000 → 001 → 003   (trunk,  runs first, merges)
                ├→ 007 → 008 → 009    w1-…          : 004 → 005 → 006   ┐
                └→ 010 → 011 → 012    w2-…          : 007 → 008 → 009   ├ parallel
                                      w3-…          : 010 → 011 → 012   ┘
```

What this buys:

- **Two barriers instead of four.** Trunk merges once; the three branch waves merge once at the end.
- **Wall-clock = the longest chain**, not the sum of per-level maxima.
- **Nothing plans blind.** Trunk code is on `main` before any branch wave starts, and inside a wave each feature's blocker was implemented by the previous step *in the same worktree*. Every effective blocker's code is physically on disk when `plan` runs.

That last point is the real prize: vertical waves dissolve the problem that the safety boundary created. `Upstream Context` stops being a crutch that substitutes for missing code and becomes a pointer to code that is actually there (§8).

### The algorithm — spine decomposition

Work on the transitively-reduced effective DAG.

1. **Find the spine.** A feature is on the spine if it is comparable to *every* other feature — that is, every other feature is either its ancestor or its descendant. Spine features cannot be parallelized with anything; they are the serial backbone.

   ```
   spine = { f : ancestors(f) ∪ {f} ∪ descendants(f) == all_features }
   ```

2. **Group consecutive spine features into a trunk wave.** In topological order, a maximal run of adjacent spine features becomes one wave with `kind: "trunk"`. It runs sequentially, alone.

3. **Split the gaps into branch waves.** Every non-spine feature sits in exactly one *gap* between two consecutive spine features (or before the first / after the last). Within a gap, take the **weakly-connected components** of the induced subgraph; each component becomes one wave with `kind: "branch"`. Order its features topologically — that order is the execution order.

4. **Assemble stages.** Walking topologically, trunk waves and gap groups alternate. Each is a **stage**. Stages run in order with a merge barrier between them; all waves inside one branch stage run concurrently.

Two properties this guarantees, both load-bearing:

- **No edges cross between sibling waves.** Two connected features land in the same component by construction. If an edge you discover later would cross waves, the two waves must be merged into one — do not "just run them anyway".
- **Every blocker is already merged or already local.** A blocker is either on the spine (merged in an earlier stage), in the same wave earlier in the chain (same worktree), or in an earlier gap (merged in an earlier stage).

### Spine decomposition is only the starting point — the repair pass

Spine decomposition reads the dependency DAG and nothing else. That is exactly its blind spot: two features with no edge between them are perfectly free to be siblings *in the DAG* and still rewrite the same `models.py`. Waves are therefore no longer computed by eye from the graph — `speckit_waves.py` computes them from the DAG **plus predicted file overlap** (§5), taking the spine partition as the seed and then running a **repair pass** over it.

The asymmetry that makes the repair cheap:

- **A wave is a sequential chain in one worktree.** Two features in the same wave touch the same file one after the other, in the same tree, and the second one sees the first one's edit. A file overlap *inside* a wave is harmless — it is an ordinary sequential edit, not a merge.
- **Overlap only matters between sibling waves** — waves that run concurrently, in different worktrees, inside the same stage, and land at the same barrier.

So a `strong` conflict edge asserts exactly one thing: **these two may not be siblings.** That leaves exactly two fixes, and both of them are legal:

| Fix | Cost | What the overlap becomes |
|-----|------|--------------------------|
| **Same wave** — fuse the two waves into one chain | no extra barrier; that chain gets longer | a sequential in-worktree edit |
| **Different stages** — push one wave into a later stage | one extra merge barrier | a merged-then-branched-from edit |

The scheduler tries **both** candidates for every violated edge and keeps whichever gives the smaller **makespan** — the sum over stages of the longest wave in that stage, every feature weighted 1. On a tie it prefers the same-wave merge, because a barrier costs more than a step. **Precedence is re-checked on every candidate**: a repair that would place a blocker after its dependent is rejected outright, so no repair can ever break the DAG.

This is **not plain graph colouring**, and the difference is not cosmetic. A colouring assigns conflicting features to different colours — different rounds — which is only ever the second fix. It cannot express "put them in the same wave", so it pays a barrier for conflicts that a fused chain resolves for free, and it is strictly less parallel here.

### Adjustments

- **Hotspot ownership beats hotspot avoidance.** Two sibling waves that both extend `settings.py` will conflict at merge no matter what wave they are in. Do not split waves to avoid it — assign the file an owner (§9) and make the edits idempotent. Such a file is graded `additive`, and the repair pass leaves it alone (§5).
- **Balance, don't reorder.** If one branch wave is 8 features and its siblings are 2, wall-clock is the 8-chain. That is a signal to re-check whether those 8 dependencies are all real — never to fake a partition the DAG does not support.
- **A component that is internally wide** (a small DAG, not a chain) still runs sequentially in topological order. Splitting it further would need another barrier; only do that if it dominates wall-clock.
- **No spine at all** (multiple independent roots) is fine: stage 0 is a branch stage with several waves. **All spine** (one long chain) is also fine: a single trunk wave, no parallelism to be had.

### Wave naming

Each wave gets a machine-safe name **and** a human title:

- name: `w{N}-{kebab-theme}` — lowercase, git-branch-safe, e.g. `w0-foundation`, `w1-scheduling`, `w2-channels`
- title: a short human phrase, e.g. "Foundation", "Scheduling chain"
- rationale: one sentence stating what the wave delivers end to end and why it is independent of its siblings

The theme comes from what the *chain* accomplishes, not from a counter. `w0-foundation` is nearly always the trunk containing the environment/prefactor slice.

## 5. Conflict constraints

The repair pass is only as good as the edges handed to it. Not every shared file is a conflict, so overlap is **graded** — a blanket "same file ⇒ separate them" would serialize the whole run over `settings.py`.

### The three grades

| Grade | Meaning | Siblings? | Example |
|-------|---------|-----------|---------|
| `strong` | Both features rewrite the same structured region of the same file. | ❌ **may not be siblings** — the repair pass must fuse or re-stage them | two features adding fields to the same app's `models.py` |
| `conditional` | Overlap is plausible but usually mergeable. | 🟡 siblings allowed, but the merge gets a **build+test probe** (§6) | two features in the same MVC slice with no shared file |
| `additive` | Append-only structure with one owner and an idempotency rule. | ✅ siblings allowed | `INSTALLED_APPS` in `settings.py` |

**Additive** covers the usual registry files: settings app lists, URL confs, migrations, i18n catalogs, lockfiles. These are hotspots, not conflicts — they get an owner and an idempotent edit rule (§9), never a wave split.

**Strong** covers same-app `models.py` / `views.py` / `services.py` / `forms.py` — the MVC quartet of one app — and shared test files.

### The same-directory signal

Two features working the same **MVC slice** get a `conditional` edge **even when they share no file at all**. Structural proximity predicts conflict on its own: Borba et al. (IST 2020) analysed **73,504 merge scenarios** in Ruby and Python MVC projects and found conflict likelihood rises significantly when the two contributions involve files from the same MVC slice, and that a higher number of changed files raises it by **227%**. A shared *directory* is therefore evidence, and the probe is the cheap way to act on it.

### Hub isolation

A non-additive path touched by **3 or more features** is a **hub**. Burying a hub inside one wave does not reduce conflicts — the other features still reach it from their own waves; it only lengthens that chain. Two ways out, in order:

1. Move its ownership into the **trunk**, so every branch wave branches from a version that already has the extension point.
2. Or declare it `additive` and write down the idempotency rule.

Never "solve" a hub by growing the wave that happens to contain it.

### Completeness claims

A feature whose acceptance criteria assert that a set is **exhaustively enumerated** may not be a sibling of a feature that **adds members to that set**. This constraint is invisible to file overlap — the two features can touch entirely disjoint files and still break each other.

The concrete case: one feature added a verdict value and shipped a structural test asserting that its consumers were *exactly four places*. A sibling feature added a fifth consumer. The textual merge was clean; the merge broke the first feature's own test. Read acceptance criteria for "all", "exactly N", "every", and "no other" and emit the edge by hand — nothing derives it from the diff.

## 6. workmux mapping

### One worktree per wave

```
Phase 1  (no branch)          → runs on main, N background processes
Phase 2  build/{wave-name}    → one worktree, runs the wave's features 03…08 in order
```

The pane script recovers everything it needs from `git rev-parse --abbrev-ref HEAD`:

```bash
BRANCH=$(git rev-parse --abbrev-ref HEAD)   # build/w1-scheduling
PHASE=${BRANCH%%/*}                          # build
WAVE=${BRANCH#*/}                            # w1-scheduling
```

There is no reliable channel to tell a tmux pane which work to do — tmux windows do not inherit the driver's environment. **The branch name is the channel.** Handles slugify to `build-w1-scheduling`, so `workmux list` and the dashboard read cleanly.

### Four design decisions that are not optional

The driver blocks on `-W/--wait`, which returns only when the window closes, and a window closes only when every pane's process has exited. Three of these four exist to guarantee that actually happens.

| # | Decision | Why |
|---|----------|-----|
| 1 | **Script pane, not agent pane** — a single-pane named layout running a script | An interactive `claude` never exits, so `-W/--wait` never returns and `--max-concurrent` deadlocks. A script exits → the window/session closes → the driver advances. It also enables per-stage `--model`/`--effort`/`--max-turns`. |
| 2 | **Exactly one pane** | The window closes only when *all* panes exit. A default two-pane layout (agent + shell) hangs forever because the shell never dies. |
| 3 | **The pane command must end with `; exit`** | A pane `command:` is a line handed to a **shell**, not the pane's process. When the script finishes, the shell returns to its prompt and sits there — the wave completes, writes `OK`, and the driver still blocks forever. `'bash utilities/{prd-name}/wm_stage_runner.sh …; exit'` closes the shell with the script. This one is invisible in `--dry-run`; it only shows up in a real run. |
| 4 | **`--foreach` + `--max-concurrent`, not a bash `&` loop** | Concurrent `git worktree add` races on `.git/worktrees/` metadata. workmux serializes creation internally and throttles concurrency. |

Verified against **workmux 0.1.229**:

- `--branch-template` exposes `--foreach` variables **by bare name** — use `{{ wave }}`, not `{{ foreach_vars.wave }}` (the latter errors). Available: `agent`, `base_name`, each foreach var, `foreach_vars`, `index`, `num`.
- `--foreach "var:a,b;var2:x,y"` zips by index; it is **not** a cartesian product.
- Branch names containing `/` work; the worktree directory and tmux target slugify the slashes.
- `-W/--wait` blocks until the window/session closes but **does not propagate the exit code** — success must be reported through a status file written to the *main* repo (worktrees may be removed).
- `mode: session` avoids the "driver must run inside tmux" constraint of window mode.

### Merging

- Merge **sequentially**, never in parallel — concurrent `workmux merge` races on main's index. Merge in `waves.json` order so conflicts are reproducible.
- Use **`merge_strategy: merge`** (not `rebase`). A vertical wave carries a whole chain of commits; rebasing replays every one of them through the same hotspot and can demand the same conflict resolution repeatedly. One merge commit resolves it once. Keep `--rebase` only for waves that are a single feature.
- Gate every merge with `pre_merge`; a failing gate aborts the merge and preserves the worktree. **`pre_merge` is no longer the only check before a merge** — the driver runs a speculative probe first (below).
- **Probe before you merge.** Before every wave merge the driver runs `git merge-tree --write-tree` against the target. It computes the merged tree without touching the index or the working tree, so it costs nothing and cannot leave a half-merged `main`; if it reports conflicts, the driver names the conflicting paths and **skips that merge**. Then, when the wave's `probe` field is `build-test` (§5), it materializes the merged tree in a throwaway worktree and runs the verification command against it — that is what catches the conflicts that merge cleanly but break behaviour, which no textual merge can see (the Crystal approach, Brun et al., FSE 2011).
- Set `merge_keep: true` so evidence survives a bad automated run. Clean up with `workmux rm --all` after review.

## 7. Mandatory pre-conditions (mechanical — skip these and it breaks deterministically)

These are not quality concerns. They are guaranteed failures.

| # | Problem | Fix |
|---|---------|-----|
| 1 | Feature numbering collides across concurrent `specify` runs. | Export `SPECIFY_FEATURE_DIRECTORY=specs/{NNN}-{slug}` per process — the runner does this for every stage. |
| 2 | `.specify/feature.json` holds "the current feature" as a single global file that every process rewrites. | `git rm --cached .specify/feature.json` + `.gitignore`. The env var makes the content irrelevant; tracking it makes every wave merge conflict. |
| 3 | Agents committing concurrently in one working tree corrupt the index. | Phase 1 runs with `--no-commit`; the driver commits once after the join. |
| 4 | Every worktree needs a unique branch name. | The `build/{wave}` template guarantees it. |
| 5 | `workmux add --base` defaults to the *current* branch, not `main`. | Set `base_branch` in `.workmux.yaml` **and** pass `--base` explicitly. |
| 6 | `.speckit-logs/` committed into feature branches makes every merge conflict. | `.gitignore` it. |
| 7 | The `pre_merge` gate falls back to `uv run pytest -q` / `npm test` when `SPECKIT_VERIFY_CMD` is unset, and reads any non-zero exit as failure. A repo whose baseline already exits non-zero therefore fails **every** wave merge, and the driver only reports "conflict or gate". | Set it explicitly in `.workmux.yaml`, narrowed until it is green on the untouched baseline. Never `&&` lint/type checks onto it — they carry their own baselines. |
| 8 | `VAR=value cmd` in a hook is **shell syntax**. If workmux exec's the hook without a shell, `VAR=...` is taken as the program name and the hook dies before the gate runs — which looks identical to a gate rejection. | Write `env VAR=value cmd`. `env` is a real binary, so it works whether or not a shell is involved. |
| 9 | Sibling waves edit the same files, so every wave in the stage lands its conflicts at one barrier. | Waves are computed by `speckit_waves.py` from predicted file overlap, not from the dependency DAG alone. Never hand-author `waves[]`. |
| 10 | Phase 2 runs on a provisional wave plan computed before `clarify` changed feature scope. | `speckit_parallel.sh build` refuses while `waves.json` has `status: provisional`. Finalize with `speckit_waves.py --status final` after Phase 1. |

## 8. What the generated prompts must carry

Vertical waves put every blocker's code on disk before `plan` runs, so the prompts stop compensating for absent code and start pointing at present code.

**`03_plan.md` MUST include an Upstream Context section** listing, per effective blocker, the concrete artifacts it provides — module paths, function signatures, endpoints, model fields — and where they now live:

```markdown
## Upstream Context (already implemented — read it, do NOT rebuild)

- **001-sync-chat-http** (`w0-foundation`, merged into main): `chat/gateway.py::CommandGateway`
  — idempotency, seq issuance, `undo()`. Spec: `specs/001-sync-chat-http/`.
- **004-reminder-core** (`w1-scheduling`, earlier in this wave — already committed in this worktree):
  `reminders/scheduler.py::schedule(job, when)`.

Read these files before planning. If one is genuinely absent, STOP and report — do not
create a replacement, it means the wave plan is wrong.
```

The "STOP and report" clause matters: a missing file is now **evidence of a wave-plan error**, not an expected condition. That converts a silent design drift into a loud failure.

**`07_implement.md` MUST include shared-infrastructure rules** for every hotspot the feature touches: who owns the file, and the idempotent form of the edit ("append to `LOCAL_APPS` only if absent — `w2-channels` makes the same change and both waves merge into `main`").

**`01_specify.md`** stays tech-neutral as always; the runner injects the feature-directory pin, so the prompt must not hardcode a number.

## 9. Shared infrastructure ownership

A vertical wave accumulates a whole chain of commits before it merges, so cross-wave hotspot collisions are **larger** than in a horizontal run, and they all arrive at the same barrier. Three rules, in priority order:

1. **Push ownership into the trunk.** If the trunk wave creates the shared file *with its extension point already in place* (an empty `INSTALLED_APPS` tail, a router that auto-discovers, a `pyproject` optional-dependency group), branch waves only append and never restructure.
2. **Prefer per-feature files with auto-discovery** over one shared registry — `apps/{feature}/urls.py` collected by a glob beats every wave editing `urls.py`. State this in `plan`, not `implement`; it is a design decision.
3. **Idempotent appends plus sequential merge.** Neither works without the other.

Record every file more than one feature touches, with the owning feature, the owning wave, and the idempotency rule. Typical hotspots:

| File | Touched by |
|------|-----------|
| settings / installed-apps module | every feature that adds an app |
| API router / URL conf | every feature that adds an endpoint |
| dependency manifest + lockfile | every feature that adds a dependency |

## 10. Cost and rate limits

Concurrent `claude -p` sessions multiply input tokens (CLAUDE.md + constitution + prompt) by the concurrency factor. Headless `claude -p` bills against Agent SDK credits separately from the interactive subscription pool, and falls back to API rates when exhausted.

- **Phase 1** is cheap and short — run all N. Throttle only after seeing 429s.
- **Phase 2** concurrency is bounded by the wave count, which the DAG fixes; `--max-concurrent` caps it further. Each wave is long-running, so a 429 mid-wave is expensive — start at 4..6 concurrent waves.

## 11. Notes on adjacent stages

- **`/speckit.taskstoissues`** (not part of this skill's 8-stage flow): if used, run it **sequentially**, only on `analyze`-passed tasks, and preview with `--dry-run`. It writes to external shared state (GitHub Issues); its duplicate-check is check-then-create and races under concurrency, and mis-created issues cannot be `git reset`.
- **`/speckit.converge` exit codes** report execution success, not convergence. Detect convergence with a sentinel in the output, and guard against phantom completion (`[X]` marked but unimplemented) with real build/test gates — the `pre_merge` gate enforces this by rejecting any unchecked `- [ ] T…` line.
- **The git extension** (`/speckit.git.feature`) creates numbered feature branches. It is incompatible with this pipeline's branch scheme — leave it out of `.specify/extensions.yml`, or the `before_specify` hook will create N branches inside one working tree during Phase 1.
