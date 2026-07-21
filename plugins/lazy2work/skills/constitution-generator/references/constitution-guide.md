# Constitution Best Practices Reference

## Core Principle: Minimal but Enforceable

A constitution is the set of **non-negotiable guardrails** that hold for the whole project — "how we work", never "what we build". Its prompt density should be the **lowest** of all Spec Kit commands: detail belongs downstream (`/speckit.specify` for What/Why, `/speckit.plan` for How).

The **#1 trap is over-constraint**, not under-constraint (Martin Fowler, den.dev):

- Dozens of rules → the agent follows them *too* eagerly, producing unnecessary artifacts ("illusion of work")
- Rule-compliance consumes the agent's attention budget → **context drift**, value delivery suffers
- Mitigation: **6–12 principles total** (hard cap 15) · require explicit justification before adding complexity · audit periodically and delete rules that stopped paying rent

## Rationale — Attach One to Every Principle

Agents comply better when they understand *why* a rule exists (den.dev, redreamality). Every principle gets a terse `(Rationale: …)`:

```
❌ Unit-test coverage must be at least 80%.
✅ MUST keep unit-test coverage ≥ 80% on business logic (Rationale: regression safety).

❌ Do not store secrets in settings.py.
✅ NO credentials in settings.py; MUST load secrets from .env (Rationale: leak prevention, 12-factor).
```

## Section Menu (not a quota)

Include a section **only when it carries a genuine non-negotiable**; omit empty sections — constitution.md is plain markdown, delete template boilerplate that doesn't apply.

| Section | When to include | What to include |
|---------|----------------|----------------|
| Project Identity | always | Name, one-line description |
| Tech Stack (Locked) | always | Language + framework + DB **with versions**, package manager |
| Prohibitions | always | ≥ 3 explicit NO items |
| Architecture Principles | if structure is non-negotiable | Project structure, layer separation |
| Coding Conventions | if tooling is fixed | Formatter, linter, naming, type hints |
| Testing Requirements | if a gate exists | Framework, **quantified** coverage threshold |
| Security Principles | if handling real data | Credential management, data protection |
| Deployment Target | **production stage only** | Hosting, containerization |

**Optional extras:** Performance Goals (production, quantified: P95 < 200ms) · Accessibility (WCAG) · i18n · Git Conventions · Existing Code Reference (brownfield — file paths).

## Prototype vs Production Stage

Production rules strangle experiments (a known failure mode — practitioners demonstrably *delete* these articles at prototype stage):

| Article type | Prototype | Production |
|--------------|-----------|------------|
| CI/CD, deployment | **omit** — say so explicitly in the prompt | include |
| Performance budgets (P95, throughput) | **omit** | include, quantified |
| Security gates | minimal (no-secrets-in-code only) | full (encryption, auth, compliance) |
| Coverage thresholds | optional, low | enforced (e.g. ≥ 80%) |

When a prototype graduates, revise the constitution — it is versioned, not immutable.

## Anti-Patterns

| Anti-Pattern | Why Bad | Fix |
|-------------|---------|-----|
| Over-constraint (dozens of rules) | Agent over-complies: unnecessary artifacts, context drift | 6–12 principles; justify additions; audit periodically |
| Principles without Rationale | Agent follows blindly, drops rule under pressure | Attach `(Rationale: …)` to every principle |
| Vague rules ("write quality code") | AI cannot verify | MUST/NO + quantified ("coverage ≥ 80%") |
| Production gates in a prototype | Perf/security gates block iteration | Strip CI/CD, deployment, perf budgets; state it in the prompt |
| No tech stack versions | AI picks arbitrary versions | Lock with "Django 4.2.x" |
| Missing Prohibitions | AI expands scope freely | List 3+ explicit NO items |
| Leftover template boilerplate | Agent treats filler as rules | Delete non-applicable sections — it's plain markdown |
| Too detailed implementation | AI over-interprets, creates duplicates | Keep principles only; details go in /plan |
| Feature requirements included | Constitution ≠ Spec | Move to /specify |
| Skipping constitution | Every spec re-litigates the same decisions | Always write constitution first |
| Never updating | Stack evolves, constitution drifts | Review periodically; spec/constitution first, code second |
| Copy-paste generic template | Ignores project specifics | Customize per project |

## Verifiable vs Non-Verifiable Rules

Write every rule in enforceable **MUST / NO** language with a quantified threshold — if it cannot be checked against code or a metric, it is not a constitution rule.

```
❌ "Write high-quality code"      → ✅ "MUST: type hints on all functions (Rationale: mypy gate)"
❌ "Be well-tested"                → ✅ "MUST: unit coverage ≥ 80% on business logic (Rationale: regression safety)"
❌ "Be secure"                     → ✅ "NO PII stored unencrypted, at rest or in transit (Rationale: compliance)"
❌ "Use latest Django"             → ✅ "MUST use Django 4.2.x (LTS) (Rationale: security-patch window)"
❌ "Good performance"              → ✅ "MUST: API responses P95 < 200ms (Rationale: UX budget)"  [production only]
```

## Greenfield vs Brownfield Constitution

| Aspect | Greenfield | Brownfield |
|--------|-----------|-----------|
| Tech stack | Free choice, lock after decision | Auto-detect from existing code, lock |
| Architecture | Design from scratch | Reverse-engineer from codebase |
| Conventions | Define new | Extract from existing code |
| Prohibitions | General (no over-engineering) | Specific (no new apps, no breaking changes) |
| Extra section | — | Existing Code Reference (file paths, patterns) |

## Example: Brownfield Django Project (production stage)

```
/speckit.constitution

Financial Automation Server — investment platform trade log extraction and withdrawal automation

Create the project constitution from the non-negotiable principles below.
- Attach a Rationale to every principle.
- Use enforceable MUST/NO language; keep every article objectively verifiable.
- Delete template sections that do not apply.

## Tech Stack (Locked)
- MUST use Python 3.11 + Django 4.2.9 + DRF 3.14.0 (Rationale: running production system, no migration budget)
- MUST use SQLite (db.database_fin); package manager: uv
- Selenium stays for existing flows; Playwright only for new flows (Rationale: rewrite risk outweighs benefit)

## Architecture Principles
- MUST preserve existing app structure: banking_app, withdrawal_app, web_control_app (Rationale: stable integration points)
- MUST keep /api/v1/ prefix; business logic lives in utils/ (Rationale: existing clients depend on it)

## Coding Conventions
- MUST format with Black (line-length 119) + isort (black profile) (Rationale: zero-diff reviews)
- MUST use type hints + Google-style docstrings (Rationale: mypy gate, onboarding)

## Testing Requirements
- MUST test with pytest + pytest-django; browser tests marked @pytest.mark.integration (Rationale: fast unit lane in CI)

## Security Principles
- NO credentials in code or settings.py; MUST load from .env (gitignored) (Rationale: financial credentials, leak prevention)

## Prohibitions
- NO new Django apps (Rationale: structure lock)
- NO breaking changes to existing APIs (Rationale: live clients)
- NO modifications to existing Selenium code (Rationale: fragile, verified flows)
- NO Docker/containerization (Rationale: bare-metal deployment target)

## Existing Code Reference
- View pattern: withdrawal_app/api/views.py
- Utility pattern: utils/withdrawal/
- Configuration: config/settings/base.py

## Deployment Target
- Development: runserver (local) / Production: Gunicorn + Nginx
```

## Example: Greenfield React App (production stage)

```
/speckit.constitution

Book Management SPA — personal reading log and search web app

Create the project constitution from the non-negotiable principles below.
- Attach a Rationale to every principle.
- Use enforceable MUST/NO language; delete template sections that do not apply.

## Tech Stack (Locked)
- MUST use React 18 + TypeScript 5.x + Vite 6.x (Rationale: team baseline, ecosystem support window)
- MUST use TailwindCSS 4.x + shadcn/ui; React Router v7; Axios (Rationale: one styling system, no CSS drift)

## Architecture Principles
- MUST use functional components + hooks only; API calls only via hooks/useApi.ts (Rationale: single seam for auth/errors/mocking)

## Coding Conventions
- MUST pass ESLint + Prettier (no semicolons, single quote, 2-space) (Rationale: zero-diff formatting)
- MUST use named exports only; components PascalCase.tsx, utils/hooks camelCase.ts (Rationale: grep-able imports)

## Testing Requirements
- MUST test with Vitest + React Testing Library; E2E with Playwright (Rationale: behavior-level regression safety)

## Security Principles
- NO API keys in source; MUST load via .env (Rationale: public repo)
- MUST sanitize user input with DOMPurify (Rationale: XSS)

## Prohibitions
- NO class components, NO Redux/MobX (Rationale: hooks + context suffice at this scale)
- NO `any` type (Rationale: defeats the TS gate)
- NO console.log in production builds (Rationale: log hygiene)

## Deployment Target
- GitHub Pages (static), CI/CD: GitHub Actions
```

## Example: CLI Tool (prototype stage)

```
/speckit.constitution

Markdown Metadata Analysis CLI Tool

Create the project constitution from the non-negotiable principles below.
- Attach a Rationale to every principle.
- Use enforceable MUST/NO language; delete template sections that do not apply.

## Tech Stack (Locked)
- MUST use Python 3.12 + Typer (Rationale: stdlib-adjacent, minimal deps)
- python-frontmatter + python-markdown; package manager: uv

## Architecture Principles
- MUST keep single package src/md_analyzer/ — entry cli.py, core logic core.py (Rationale: trivially navigable)

## Coding Conventions
- MUST format + lint with Ruff; type hints required (Rationale: one tool, one gate)

## Testing Requirements
- MUST test with pytest; fixtures under tests/fixtures/ (Rationale: reproducible sample docs)

## Prohibitions
- NO GUI (Rationale: CLI-only scope)
- NO external API calls (Rationale: offline tool)
- NO database usage (Rationale: stateless by design)

This project is at prototype stage — do NOT include CI/CD, deployment,
or performance-budget articles.
```
