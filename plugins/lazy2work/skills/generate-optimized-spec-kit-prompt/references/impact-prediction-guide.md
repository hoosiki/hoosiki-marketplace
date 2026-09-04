# Impact Prediction and Conflict-Aware Waves

How the skill decides which features may run concurrently, and why the decision
is computed rather than judged.

## Why this exists

Waves used to be partitioned on the dependency DAG alone. Two features with no
dependency between them became siblings and ran concurrently — even when they
edited the same twenty files. The hotspot table was supposed to catch that, but
it was hand-authored: in one real project it recorded 2 of the 9 files two
sibling features actually shared, and the merge failed.

The literature is unambiguous about the shape of the problem:

- **Cassandra** (Kasi & Sarma, ICSE 2013) schedules tasks so that "dependent
  tasks *or tasks that share common files*" are not edited concurrently, by
  encoding both as constraints and solving them together.
- **Borba et al.** (IST 2020, 73,504 merge scenarios in Ruby/Python MVC
  projects) found conflict likelihood rises significantly when contributions
  "involve files from the same MVC slice (related model, view, and controller
  files)", and that more changed files raises it by 227%.
- **Leßenich et al.** (2018) found none of seven survey-derived indicators
  predicted conflict frequency — proxies do not work, you need the actual files.
- **Crystal** (Brun et al., FSE 2011) shows the only reliable check is to
  speculatively merge, build, and test, because a clean textual merge can still
  break behaviour.

So: predict the file sets, constrain the partition with them, and verify with a
real trial merge because prediction is never complete.

## The key asymmetry

**An overlap inside one wave is harmless.** A wave is a dependency chain that
runs sequentially in a single worktree; the second feature edits the first
feature's committed code. Overlap only matters between **sibling waves** — waves
running concurrently in the same stage, whose commits arrive at one barrier.

That gives a strong conflict two legal resolutions, not one:

| Fix | Cost |
|-----|------|
| Put both features in the **same wave** (sequential) | no extra merge barrier |
| Put them in **different stages** | one extra barrier |

`speckit_waves.py` tries both and keeps whichever has the shorter makespan,
preferring the merge on a tie. Pure graph colouring only ever considers the
second option, which is why this skill does not use it directly.

## Step 1 — per-issue impact prediction (subagents)

One subagent per issue, run in parallel, 5–8 at a time. Each writes exactly one
file: `.speckit-prompts/{prd-name}/.impact/{feature-id}.json`.

**Give every subagent:**

- the issue body in full;
- the repository tree (brownfield) **or** the constitution's directory, module
  and test-location conventions (greenfield) — without this, subagents invent
  different names for the same file and the overlap becomes invisible;
- the `creates[]` already declared by upstream features in the DAG, so a
  downstream feature does not re-create what an upstream one makes;
- the set names already declared by upstream features (see
  `completeness_claims` below), so the same set is not named two ways.

**Instruct explicitly:**

- **Recall beats precision.** If a file might be touched, include it with a low
  `confidence`. A missed file becomes a merge conflict; an extra file only costs
  a little parallelism. Strong models predict too few files by default — push
  against that.
- **Enumerate tests, docs, settings and migrations too.** These are
  systematically under-predicted, and in the real failure three of the nine
  shared files were tests.
- **Output JSON only**, matching the schema below. No prose.

### Output schema

```json
{
  "feature": "005-max-loan-quote",
  "status": "ok",
  "creates":       [{"path": "utils/loan/quote.py", "confidence": 0.9, "symbols": ["build_quote"]}],
  "modifies":      [{"path": "loan_app/services.py", "confidence": 0.8, "symbols": ["review_case"]}],
  "tests":         [{"path": "loan_app/tests/test_review_service.py", "confidence": 0.7}],
  "docs_configs":  [{"path": "docs/loan.md", "confidence": 0.4}],
  "registries":    [{"path": "loan_app/migrations/0007_quote.py", "confidence": 0.9}],
  "completeness_claims": [{"set": "verdict.consumers", "note": "FR-008 enumerates every reader"}],
  "extends_sets":  []
}
```

- `status` is `"ok"` or `"failed"`. On failure add `"error"`. **Never emit an
  empty prediction to represent a failure** — absent data and no overlap are
  different things, and conflating them reproduces the original bug.
- `symbols` feeds the reverse-reference sweep, so name the functions, classes,
  model fields and constants the feature introduces or changes.
- `registries` marks append-only files (settings lists, URL confs, migrations).

### completeness_claims and extends_sets

Some conflicts are invisible to file overlap. In the real failure, feature 005
shipped an acceptance criterion asserting that the consumers of a new verdict
value were *exactly four places*, plus a structural test enforcing it. Feature
006 added a consumer. Even with zero shared files, merging 006 breaks 005's test.

So each subagent declares:

- `completeness_claims` — sets this feature asserts it has enumerated completely;
- `extends_sets` — sets this feature adds members to.

The scheduler joins one against the other by set name and emits a **strong**
edge. Name sets by symbol path (`verdict.consumers`), never as free prose, and
reuse an upstream name when one exists.

## Step 2 — normalise, augment, grade

`speckit_waves.py` does this mechanically.

**Augment** (brownfield, skip with `--no-augment`):

- **Reverse references** — `git grep -l` each declared symbol; consumers join the
  feature's path set at confidence 0.5. This is what catches the files a subagent
  never thought to name.
- **Co-change coupling** — mine the last 400 commits; a file that historically
  moves with a predicted file in at least half of its commits joins at 0.4, up to
  five per seed. Files that changed together will change together again.

**Grade** each path `strong` / `conditional` / `additive`. The built-in table
wins; the subagent's opinion fills the gaps; ties resolve to the higher grade.
Projects override in `conflict-policy.toml`.

**Isolate hubs.** A non-additive path touched by three or more features is a hub.
Hubs are reported separately because burying one inside a wave only lengthens
that chain without reducing conflicts — move its ownership into the trunk, or
add it to the additive table with an idempotency rule.

## Step 3 — two graphs, kept separate

A shared file is **mutual exclusion**, not precedence. Conflating them loses
ordering information and the parallelism that survives ordering.

- **Precedence DAG** — declared blockers, hidden blockers from acceptance
  criteria, plus an inferred edge whenever one feature `creates` a path another
  `modifies`.
- **Conflict graph** — `strong` and `conditional` edges from shared paths, a
  `conditional` edge for same-directory overlap (the MVC-slice signal), and a
  `strong` edge for every completeness claim that another feature extends.
  `additive` paths produce no edge at all; they get an owner instead.

## Step 4 — schedule

Start from the existing spine decomposition, then repair: while any strong edge
joins two features in *different waves of the same stage*, either merge those
waves or split the stage, whichever yields the smaller makespan. Makespan is the
sum over stages of the longest wave in that stage, with every feature weighted 1.
Precedence is re-checked on every candidate, so a repair can never reorder a
blocker after its dependent.

A feature with no usable prediction gets a strong edge to everything, so it is
serialised wherever it legally sits. The run is refused outright unless
`--force-trunk` is passed, and the feature is then marked
`"placement": "unpredicted"` in `waves.json`.

## Step 5 — probe and feed back

Prediction is never complete, so the merge is verified for real.

- **Always**: `git merge-tree --write-tree` before each wave merge. A conflict
  reports the conflicting paths **by name** and skips that wave's merge.
- **When the wave's `probe` is `build-test`**: materialise the merged tree in a
  throwaway worktree and run the verification command against it. This is the
  only way to catch a conflict that merges cleanly and still breaks behaviour.
  It fires when the wave has conditional overlap with a sibling, when it extends
  a set another wave claims complete, or when it is the last wave of a stage.
- **Every probe appends one line** to `.speckit-logs/impact-recall.jsonl` with
  the predicted set, the actual conflicting files, and the resulting recall. The
  prediction sidecars are never overwritten — they are the baseline that makes
  recall measurable across runs.
