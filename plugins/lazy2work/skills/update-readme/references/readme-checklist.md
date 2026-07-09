# README.md Best-Practice Audit Checklist

Distilled from an exhaustive research report (primary sources: Standard Readme
spec, GitHub Docs *About READMEs*, Tom Preston-Werner's *Readme Driven
Development*, Keep a Changelog, AGENTS.md spec, Checkmarx security). Use this as
the rubric when auditing and updating a project's `README.md`.

> **North star**: The README is the project's *front door* and *elevator
> pitch* — not the full documentation. A visitor must be able to tell **within
> 10 seconds** whether the project fits their needs. If a section makes the file
> longer without helping that judgment, it belongs in another file.

---

## A. Required backbone (audit these first)

Every README should carry these. Missing one is a finding.

| # | Section | What it must answer | Where the fact lives |
|---|---------|---------------------|----------------------|
| A1 | **Title** | Matches repo/package name | manifest / dir name → **look up** |
| A2 | **One-line pitch** | *What* it does + *who* for. `With X, you can [verb] [noun]`. Describe what, not how. | needs **decision** if unclear |
| A3 | **Why / description** | What problem it solves; why this over alternatives | often **decision** |
| A4 | **Requirements** | Runtime, min versions, OS, system deps | manifest / CI / Dockerfile → **look up** |
| A5 | **Install** | Copy-pasteable, *verified* commands (package-manager one-liner first) | scripts / manifest → **look up + verify** |
| A6 | **Usage / Quick Start** | Minimal working example with real code & real output | examples / tests → **look up** |
| A7 | **License** | Name + link to LICENSE (no full text, no essay) | LICENSE file → **look up** |
| A8 | **Contributing** (OSS only) | Link to CONTRIBUTING.md, not the body | repo → **look up** |

**Ordering**: for a project new visitors are still evaluating, put
**Usage/demo before Install** (they decide *what it does* before *whether to
install*). For established/returning-user tools, Install-first is fine.

---

## B. Recommended when they add value (offer, don't force)

- **Badges** (shields.io): build / version / license / coverage. Every badge
  needs `alt` text; don't build a badge wall; don't put badges inside `<h1>`.
- **Screenshot / GIF / demo** — a short clip near related text, with a caption
  and alt text; support dark/light (transparent or theme-paired images).
- **Features / Highlights** — selling-point bullets near the top.
- **Table of Contents** — effectively required once the file passes ~100 lines.
- **Configuration** — env vars via `.env.example` **placeholders** (never real
  values).
- **Architecture diagram** — inline Mermaid to seed a mental model.
- **Roadmap / Status**, **FAQ / Troubleshooting** (link out if long),
  **Acknowledgements**, **Contact / Support**, **Related projects**.

---

## C. Anti-patterns — findings to fix

### C1. Belongs in another file (bloats the README)
- **Full API reference** → `docs/` or a docs site.
- **Dev/build instructions up top** → bottom or `CONTRIBUTING.md`.
- **CHANGELOG / release history** → `CHANGELOG.md` (Keep a Changelog).
- **Long tutorials, step-by-step guides, deep config matrices** → `docs/`.
- **Contributing guide body** → `CONTRIBUTING.md` (README keeps only the link).

> **Split signals** (archbee): file exceeds ~800–1200 words / hard to scan /
> user-vs-developer-vs-contributor needs diverge / per-platform install matrix /
> deep architecture-security-compliance / frequently-changing sections.

### C2. NEVER include (security — highest priority)
Secrets belong in **no** source file, config, or doc:
- API keys, tokens, passwords, credentials, encryption keys, certificates.
- Internal URLs / hostnames / infra details → externalize to env / secret
  manager.
- PII (names, emails, addresses).
- Real `.env` values → README shows **`.env.example` placeholders only**.

> Why fatal: git history is **permanent** (survives deletion via commits,
> branches, forks). "It's an internal repo" is a trap. If you spot a secret in
> the README during audit, **flag it loudly** and recommend rotation + history
> scrub — don't just delete the line.

### C3. Style anti-patterns
- Manifesto / wall of text; writing for yourself; skipping *Why*; long code
  blocks with no explanation; **stale/broken commands**; undefined jargon;
  install that starts at `npm install` with no context; over-complex install.

---

## D. README ≠ AGENTS.md (2026 axis)

Keep **human** docs and **agent** docs separate:
- **README.md** = human developers (overview / install / usage).
- **CONTRIBUTING.md** = human contributors.
- **AGENTS.md / CLAUDE.md** = AI coding agents (build commands, test runner,
  conventions, constraints) — write **only what an agent can't discover on its
  own** (standard tools like npm/pytest are already known).

> Finding: if the README has stuffed AI/build/test instructions into itself,
> recommend moving them to AGENTS.md/CLAUDE.md and linking.

---

## E. Keep it current (the whole point of this skill)

- Cross-check every command, version number, and file path against the **actual
  codebase and git state**. Stale = a finding.
- If the code changed (new features, renamed commands, moved files, bumped
  deps), the README must reflect it. Reconcile README claims with reality.
- Prefer verified copy-paste commands. An AI-updated README must be
  human-reviewed before it's trusted.

---

## F. Final pass

- [ ] 10-second test: pitch conveys *what/who* (not a tech list)
- [ ] *Why* present
- [ ] demo/screenshot (alt + caption, dark mode) where useful
- [ ] Requirements (versions/OS) stated
- [ ] **verified** copy-paste Install
- [ ] minimal Usage with real output
- [ ] Configuration = `.env.example` placeholders only
- [ ] License (name + link)
- [ ] Contributing = link (OSS)
- [ ] ❌ no secrets / tokens / internal URLs / PII
- [ ] ❌ no full API / dev instructions / CHANGELOG inline (link out)
- [ ] split if > ~800–1200 words
- [ ] no badge wall · one `<h1>` · alt text
- [ ] no stale commands (reconciled with code)
- [ ] AI/build instructions moved to AGENTS.md/CLAUDE.md if present
