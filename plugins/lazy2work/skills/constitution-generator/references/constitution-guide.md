# Constitution Best Practices Reference

## Required Sections (8)

| # | Section | What to include |
|---|---------|----------------|
| 1 | Project Identity | Name, one-line description, purpose |
| 2 | Tech Stack (Locked) | Language + framework + DB + runtime **with versions** |
| 3 | Architecture Principles | Project structure, layer separation, API patterns |
| 4 | Coding Conventions | Formatter, linter, naming, docstring style |
| 5 | Testing Requirements | Framework, coverage target, test types |
| 6 | Security Principles | Auth, data protection, credential management |
| 7 | Prohibitions | Explicit list of what AI must NOT do |
| 8 | Deployment Target | Hosting, CDN, containerization |

## Optional Sections

- Performance Goals — when response time / throughput matters
- Accessibility — WCAG compliance needed
- Internationalization (i18n) — multi-language support
- Dependency Management — package manager rules
- Git Conventions — branch strategy, commit message format
- Existing Code Reference — brownfield: existing pattern file paths

## Anti-Patterns

| Anti-Pattern | Why Bad | Fix |
|-------------|---------|-----|
| Vague rules ("write quality code") | AI cannot verify | Make verifiable ("type hints required") |
| No tech stack versions | AI picks arbitrary versions | Lock with "Django 4.2.x" |
| Missing Prohibitions | AI expands scope freely | List 3+ explicit prohibitions |
| Too detailed implementation | AI over-interprets, creates duplicates | Keep principles only; details go in /plan |
| Feature requirements included | Constitution ≠ Spec | Move to /specify |
| Skipping constitution | All downstream decisions baseless | Always write constitution first |
| Never updating | Stack evolves, constitution drifts | Review periodically |
| Copy-paste generic template | Ignores project specifics | Customize per project |

## Verifiable vs Non-Verifiable Rules

```
❌ "Write high-quality code"           → cannot check
✅ "All functions must have type hints" → can check

❌ "Use latest Django"                  → ambiguous version
✅ "Django 4.2.x (LTS)"               → specific

❌ "Good performance"                   → unmeasurable
✅ "API responses follow JSON:API spec" → checkable
```

## Greenfield vs Brownfield Constitution

| Aspect | Greenfield | Brownfield |
|--------|-----------|-----------|
| Tech stack | Free choice, lock after decision | Auto-detect from existing code, lock |
| Architecture | Design from scratch | Reverse-engineer from codebase |
| Conventions | Define new | Extract from existing code |
| Prohibitions | General (no over-engineering) | Specific (no new apps, no breaking changes) |
| Extra section | — | Existing Code Reference (file paths, patterns) |

## Example: Brownfield Django Project

```
/speckit.constitution

Financial Automation Server — investment platform trade log extraction and withdrawal automation

## Tech Stack (Do Not Change)
- Python 3.11
- Django 4.2.9 + DRF 3.14.0
- SQLite (db.database_fin)
- Selenium (existing) + Playwright (new)
- Package manager: uv

## Architecture Principles
- Preserve existing app structure: banking_app, withdrawal_app, web_control_app
- API routes: maintain /api/v1/ prefix
- Business logic: separate into utils/ directory

## Coding Conventions
- Black (line-length 119)
- isort (black profile)
- Google style docstring
- Type hints required

## Testing Requirements
- pytest + pytest-django
- Browser tests: mark with @pytest.mark.integration

## Security Principles
- Manage credentials via environment variables (.env)
- Include .env in .gitignore
- Never hardcode secrets

## Prohibitions
- Do not create new Django apps
- No breaking changes to existing APIs
- Do not modify existing Selenium code
- No Docker/containerization
- No credentials in settings.py

## Existing Code Reference
- View pattern: withdrawal_app/api/views.py
- Utility pattern: utils/withdrawal/
- Configuration: config/settings/base.py

## Deployment Target
- Development: runserver (local)
- Production: Gunicorn + Nginx
```

## Example: Greenfield React App

```
/speckit.constitution

Book Management SPA — personal reading log and search web app

## Tech Stack
- React 18 + TypeScript 5.x
- Vite 6.x
- TailwindCSS 4.x + shadcn/ui
- React Router v7
- Axios (HTTP)

## Architecture Principles
- Atomic Design (atoms/molecules/organisms/templates/pages)
- Functional components + hooks only
- API calls: abstract via hooks/useApi.ts custom hook

## Coding Conventions
- ESLint + Prettier (no semicolons, single quote, 2-space)
- Components: PascalCase.tsx
- Utils/hooks: camelCase.ts
- Named exports only (no export default)

## Testing Requirements
- Vitest + React Testing Library
- E2E: Playwright

## Security Principles
- Manage API keys via .env
- User input: sanitize with DOMPurify

## Prohibitions
- No class components
- No Redux/MobX
- No `any` type
- No export default
- No console.log in production

## Deployment Target
- GitHub Pages (static)
- CI/CD: GitHub Actions
```

## Example: CLI Tool

```
/speckit.constitution

Markdown Metadata Analysis CLI Tool

## Tech Stack
- Python 3.12
- Typer (CLI)
- python-frontmatter + python-markdown
- Package manager: uv

## Architecture Principles
- Single package: src/md_analyzer/
- Entry: cli.py, Core: core.py
- Output formats: JSON, CSV, Table (rich)

## Coding Conventions
- Ruff (format + lint)
- Type hints required
- Google style docstring

## Testing Requirements
- pytest
- Test data: tests/fixtures/

## Prohibitions
- No GUI (CLI only)
- No external API calls
- No database usage

## Deployment Target
- PyPI distribution (uv publish)
```
