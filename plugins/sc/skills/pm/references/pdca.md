# /sc:pm PDCA Reference

## Memory Key Schema (Standardized)

**Pattern: `[category]/[subcategory]/[identifier]`**, stored as a file under `~/.hermes/superclaude/projects/<slug>/memory/`. `/sc:save` documents `<slug>`.

Inspired by: Kubernetes namespaces, Git refs, Prometheus metrics

```yaml
session/:
  session/context        # Complete PM state snapshot
  session/last           # Previous session summary
  session/checkpoint     # Progress snapshots (30-min intervals)

plan/:
  plan/[feature]/hypothesis     # Plan phase: hypothesis and design
  plan/[feature]/architecture   # Architecture decisions
  plan/[feature]/rationale      # Why this approach chosen

execution/:
  execution/[feature]/do        # Do phase: experimentation and trial-and-error
  execution/[feature]/errors    # Error log with timestamps
  execution/[feature]/solutions # Solution attempts log

evaluation/:
  evaluation/[feature]/check    # Check phase: evaluation and analysis
  evaluation/[feature]/metrics  # Quality metrics (coverage, performance)
  evaluation/[feature]/lessons  # What worked, what failed

learning/:
  learning/patterns/[name]      # Reusable success patterns
  learning/solutions/[error]    # Error solution database
  learning/mistakes/[timestamp] # Failure analysis with prevention

project/:
  project/context               # Project understanding
  project/architecture          # System architecture
  project/conventions           # Code style, naming patterns

Example Writes:
  save current_state to `memory/session/checkpoint.md`
  save hypothesis_doc to `memory/plan/auth/hypothesis.md`
  save experiment_log to `memory/execution/auth/do.md`
  save analysis to `memory/evaluation/auth/check.md`
  save success_pattern to `memory/learning/patterns/supabase-auth.md`
  save solution to `memory/learning/solutions/jwt-config-error.md`
```

## PDCA Document Structure (Normalized)

**Location: `docs/pdca/[feature-name]/`**

```yaml
Structure (clear and intuitive):
  docs/pdca/[feature-name]/
    ├── plan.md           # Plan: hypothesis and design
    ├── do.md             # Do: experimentation and trial-and-error
    ├── check.md          # Check: evaluation and analysis
    └── act.md            # Act: improvement and next actions

Template - plan.md:
  # Plan: [Feature Name]

  ## Hypothesis
  [What to implement and why this approach]

  ## Expected Outcomes (quantitative)
  - Test Coverage: 45% → 85%
  - Implementation Time: ~4 hours
  - Security: OWASP compliance

  ## Risks & Mitigation
  - [Risk 1] → [mitigation]
  - [Risk 2] → [mitigation]

Template - do.md:
  # Do: [Feature Name]

  ## Implementation Log (chronological)
  - 10:00 Started auth middleware implementation
  - 10:30 Error: JWTError - SUPABASE_JWT_SECRET undefined
    → Investigation: `mcp_context7_*` "Supabase JWT configuration"
    → Root Cause: Missing environment variable
    → Solution: Add to .env + startup validation
  - 11:00 Tests passing, coverage 87%

  ## Learnings During Implementation
  - Environment variables need startup validation
  - Supabase Auth requires JWT secret for token validation

Template - check.md:
  # Check: [Feature Name]

  ## Results vs Expectations
  | Metric | Expected | Actual | Status |
  |--------|----------|--------|--------|
  | Test Coverage | 80% | 87% | ✅ Exceeded |
  | Time | 4h | 3.5h | ✅ Under |
  | Security | OWASP | Pass | ✅ Compliant |

  ## What Worked Well
  - Root cause analysis prevented repeat errors
  - Official docs from `mcp_context7_*` were accurate

  ## What Failed / Challenges
  - Initial assumption about JWT config was wrong
  - Needed 2 investigation cycles to find root cause

Template - act.md:
  # Act: [Feature Name]

  ## Success Pattern → Formalization
  Created: docs/patterns/supabase-auth-integration.md

  ## Learnings → Global Rules
  Proposed for the project context file:
    - Always validate environment variables at startup
    - Use `mcp_context7_*` for official configuration patterns

  ## Checklist Updates
  docs/checklists/new-feature-checklist.md:
    - [ ] Environment variables documented
    - [ ] Startup validation implemented
    - [ ] Security scan passed

Lifecycle:
  1. Start: Create docs/pdca/[feature]/plan.md
  2. Work: Continuously update docs/pdca/[feature]/do.md
  3. Complete: Create docs/pdca/[feature]/check.md
  4. Success → Formalize:
     - Move to docs/patterns/[feature].md
     - Create docs/pdca/[feature]/act.md
     - Propose a project context file update if globally applicable
  5. Failure → Learn:
     - Create docs/mistakes/[feature]-YYYY-MM-DD.md
     - Create docs/pdca/[feature]/act.md with prevention
     - Update checklists with new validation steps
```

## Self-Improvement Integration

### Implementation Documentation
```yaml
After each successful implementation:
  - Create docs/patterns/[feature-name].md (formalized)
  - Document architecture decisions in ADR format
  - Propose new best practices for the project context file
  - save reusable_pattern to `memory/learning/patterns/[name].md`
```

### Mistake Recording
```yaml
When errors occur:
  - Create docs/mistakes/[feature]-YYYY-MM-DD.md
  - Document root cause analysis (WHY did it fail)
  - Create prevention checklist
  - save failure_analysis to `memory/learning/mistakes/[timestamp].md`
  - Update anti-patterns documentation
```

### Monthly Maintenance
```yaml
Regular documentation health:
  - Remove outdated patterns and deprecated approaches
  - Merge duplicate documentation
  - Update version numbers and dependencies
  - Prune noise, keep essential knowledge
  - Review docs/pdca/ → Archive completed cycles
```
