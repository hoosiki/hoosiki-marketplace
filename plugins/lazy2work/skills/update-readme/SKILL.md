---
name: update-readme
description: Audit and update a project's README.md against README best practices, reconciling it with the current code and docs. Reads the existing README, discovers current state from the codebase/git, and fills each best-practice gap — resolving facts from the code directly and grilling the user one question at a time (with a recommended answer) only for gaps that need a human decision. If the user says a section has no info or isn't needed, it is omitted. Triggers on "README 갱신", "readme 업데이트", "README 최신화", "README best practice", "리드미 개선", "update README", "improve the README", "audit my README", "bring the README up to date", or any request to refresh/upgrade a README.
---

# update-readme

Bring a project's `README.md` up to best-practice standard **and** in sync with
the current code — through an interview-driven audit, not a blind rewrite.

The rubric is [references/readme-checklist.md](references/readme-checklist.md).
**Read it fully before Step 2.** It defines the required backbone, the
recommended sections, the anti-patterns, the security "never include" list, and
the split signals.

## Golden rules (never violate)

1. **One question at a time.** Ask, wait for the answer, then ask the next.
   Batching questions is bewildering. Walk the checklist top-to-bottom.
2. **Facts vs decisions.** If something can be found by exploring the codebase,
   git history, manifests, or existing docs — **look it up, don't ask.** Only
   *decisions* (positioning, the "why", what to emphasize, whether a section is
   worth keeping) go to the user.
3. **Always recommend an answer.** For every question, give your recommended
   answer and reasoning, so the user can just confirm.
4. **Omit on request.** If the user says a section has no info or isn't needed,
   drop it from the README — do not invent filler.
5. **No blind rewrite.** Preserve the README's existing voice, structure, and
   working content. You are auditing and patching, not starting over.
6. **Never enact before shared understanding.** Do not write the final README
   until the user has confirmed the plan of changes.

## Step 1 — Discover the current state (silent, no questions yet)

Gather facts before asking anything. In parallel where possible:

- **Read the existing `README.md`** (or note its absence).
- **Manifests & config**: `package.json`, `pyproject.toml`, `go.mod`,
  `Cargo.toml`, `plugin.json`, `Dockerfile`, `Makefile`, `.github/workflows/`.
  → real name, version, deps, min runtime, install/build/test commands.
- **Git reality**: recent commits, changed files, current version/tags — what
  changed since the README was last touched (`git log`, `git diff` against the
  README's last edit if useful).
- **Structure**: top-level layout, entry points, examples, `docs/`,
  `CONTRIBUTING.md`, `SECURITY.md`, `CHANGELOG.md`, `AGENTS.md`/`CLAUDE.md`,
  `LICENSE`.
- **Project type** (library / application / internal tool / dataset) — this
  sets which sections matter (see checklist §A ordering and the type notes).

## Step 2 — Audit against the checklist → build a findings list

Walk [references/readme-checklist.md](references/readme-checklist.md) section by
section (A required → B recommended → C anti-patterns → D AGENTS split → E
staleness). For each item classify it as:

- **✅ present & correct** — leave it.
- **🔧 resolvable from code** — you already have the fact (Step 1). Draft the
  fix; no question needed.
- **❓ needs a decision** — queue a single question with a recommended answer.
- **⚠️ security / anti-pattern** — flag loudly (esp. checklist §C2 secrets:
  recommend removal + rotation, never silently keep).

Then present a **short plan**: the ordered list of findings you'll walk
through — which you'll fix from the code, and which you need to ask about.

## Step 3 — Grill, one question at a time

For each ❓ finding, in checklist order:

> **[Section]** — <what's missing/weak>.
> **Recommended:** <your proposed content/answer + why>.
> Keep it, adjust it, or skip this section?

Wait for the answer. Fold it in. Move to the next. If the user says "skip" /
"no info" / "not needed" → omit that section and note it. If they give raw
info, **rewrite it into clean, scannable README prose** (headings, bullets,
short paragraphs, verified code blocks) — never paste their words verbatim.

## Step 4 — Reconcile & write

Once all findings are resolved and the user confirms shared understanding:

- Apply every 🔧 code-derived fix (correct stale versions, commands, paths,
  feature lists to match the code).
- Insert/adjust the ❓ sections with the user's confirmed content.
- Enforce best-practice form: one `<h1>`, scannable headings, badge alt text,
  `.env.example` placeholders only, links out to `docs/`/`CONTRIBUTING.md`/
  `CHANGELOG.md`/`AGENTS.md` instead of inlining them, split if it blows past
  ~800–1200 words.
- **Show a diff / summary of changes**, not just "done."

## What this skill does NOT do

- It does **not** move dev/build/CHANGELOG/full-API content *into* the README —
  it routes them out (checklist §C1).
- It does **not** touch secrets except to flag and recommend removal.
- It does **not** write AGENTS.md/CLAUDE.md content — it recommends the split.
- It is human docs only; agent instructions stay in AGENTS.md/CLAUDE.md.
