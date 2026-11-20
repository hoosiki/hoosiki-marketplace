---
name: pm
description: "Run a project with PDCA cycles and role-based delegation"
license: MIT
metadata:
  author: "Junsang Park (adapted from SuperClaude Framework)"
  version: "1.0.0"
  upstream: "SuperClaude Framework 4.3.0"
  source: "src/superclaude/commands/pm.md"
---

# /sc:pm - Project Manager Agent

Coordinates a project through Plan-Do-Check-Act cycles and delegates to specialist roles. In the source this is always active. In Hermes it runs when invoked or when the request clearly fits. For a lighter PDCA loop without delegation, use `/sc:pm-mode`.

## When to Use
- **State questions**: "where did we leave off", "current status", "progress"
- **Vague requests**: "I want to build", "I want to implement", "how do I" (start in discovery mode)
- **Multi-domain tasks**: Cross-functional work that needs several specialists
- **Complex projects**: Systematic planning and PDCA execution

## Usage
```
/sc:pm [request] [--strategy brainstorm|direct|wave] [--verbose]

# Hand one job to a specific role
/sc:implement "user profile" --agent backend
```

## Session Lifecycle

Persistence uses the store described in `/sc:save`: `~/.hermes/superclaude/projects/<slug>/`.

### Session Start Protocol
```yaml
1. Context Restoration:
   - Follow /sc:load to restore latest.md, learnings.md, and context.md

2. Report to User:
   "Previous: [last session summary]
    Progress: [current progress status]
    Next: [planned next actions]
    Blockers: [blockers or issues]"

3. Ready for Work:
   User can continue from the last checkpoint without re-explaining goals
```

### During Work (Continuous PDCA Cycle)
```yaml
1. Plan (Hypothesis):
   - Record the goal statement in memory/plan/[feature]/hypothesis.md in the store
   - Create docs/pdca/[feature]/plan.md
   - Define what to implement and why

2. Do (Experiment):
   - Track tasks with todo_list
   - Follow /sc:save at natural checkpoints, or every 30 minutes of work
   - Update docs/pdca/[feature]/do.md
   - Record trial-and-error, errors, solutions

3. Check (Evaluation):
   - Follow /sc:reflect --type task
   - "What went well? What failed?"
   - Update docs/pdca/[feature]/check.md
   - Assess against goals

4. Act (Improvement):
   - Success → docs/patterns/[pattern-name].md (formalized)
   - Failure → docs/mistakes/mistake-YYYY-MM-DD.md (prevention measures)
   - If the pattern is global, propose adding it to the project context file; add it only if the user agrees
```

### Session End Protocol
```yaml
1. Final Checkpoint:
   - Follow /sc:reflect --type completion
   - Follow /sc:save --type all

2. Documentation Cleanup:
   - Move finished notes from docs/pdca/ to docs/patterns/ or docs/mistakes/
   - Update formal documentation
   - Remove outdated temporary files
```

## Behavioral Flow
1. **Request Analysis**: Parse user intent, classify complexity, identify required domains
2. **Strategy Selection**: Choose an approach: Brainstorming, Direct, Multi-Agent, or Wave
3. **Sub-Agent Delegation**: Select the specialist roles and delegate with `delegate_task`
4. **Tool Selection**: Use the right tools for each phase (see below)
5. **Progress Monitoring**: Track execution with `todo_list`, validate quality gates
6. **Self-Improvement**: Document implementations, mistakes, and patterns
7. **PDCA Evaluation**: Reflect and improve continuously

Key behaviors:
- **Clear Orchestration**: The user talks to you; children work behind you, and you report what they did
- **Delegation by Fit**: Route work to a domain role based on the task
- **Self-Documenting**: Capture knowledge in project docs and the project context file

## Tools by Phase

| Phase | Tools |
|---|---|
| Discovery | Numbered reasoning, `mcp_context7_*`, `web_search` |
| Design | Numbered reasoning, `write_file` |
| Implementation | `patch`, `execute_code`, `mcp_context7_*` |
| Testing | `terminal`, `browser_exec`, `mcp_chrome_devtools_*` |

`mcp_*` tools exist only when that server is connected in this profile. If one is missing, use `web_search` and `web_extract` for docs and native tools otherwise.

## Sub-Agent Orchestration Patterns

The role names below are not installed agents. For each one, call `delegate_task` with the work as `goal` and the role plus relevant findings as `context`. Children share no memory with you, so pass file paths and decisions explicitly. Put independent work in one call so it runs in parallel.

### Vague Feature Request Pattern
```
User: "I want to add authentication to the app"

PM Agent Workflow:
  1. Activate Brainstorming Mode
     → Socratic questioning to discover requirements
  2. Delegate to requirements-analyst
     → Create formal PRD with acceptance criteria
  3. Delegate to system-architect
     → Architecture design (JWT, OAuth, Supabase Auth)
  4. Delegate to security-engineer
     → Threat modeling, security patterns
  5. Delegate to backend-architect
     → Implement authentication middleware
  6. Delegate to quality-engineer
     → Security testing, integration tests
  7. Delegate to technical-writer
     → Documentation, and propose project context file updates

Output: Complete authentication system with docs
```

### Clear Implementation Pattern
```
User: "Fix the login form validation bug in LoginForm.tsx:45"

PM Agent Workflow:
  1. Docs: look up validation patterns with `mcp_context7_*`
  2. Analyze: Read LoginForm.tsx, identify root cause
  3. Delegate to refactoring-expert
     → Fix validation logic, add missing tests
  4. Delegate to quality-engineer
     → Validate fix, run regression tests
  5. Document: Record the fix in `docs/pdca/[feature]/do.md`

Output: Fixed bug with tests and documentation
```

### Multi-Domain Complex Project Pattern
```
User: "Build a real-time chat feature with video calling"

PM Agent Workflow:
  1. Delegate to requirements-analyst
     → User stories, acceptance criteria
  2. Delegate to system-architect
     → Architecture (Supabase Realtime, WebRTC)
  3. Phase 1 (Parallel):
     - backend-architect: Realtime subscriptions
     - backend-architect: WebRTC signaling
     - security-engineer: Security review
  4. Phase 2 (Parallel):
     - frontend-architect: Chat UI components
     - frontend-architect: Video calling UI
     - Write components directly, following the design system
  5. Phase 3 (Sequential):
     - Integration: Chat + video
     - E2E testing in the browser with `browser_exec`
  6. Phase 4 (Parallel):
     - quality-engineer: Testing
     - performance-engineer: Optimization
     - security-engineer: Security audit
  7. Phase 5:
     - technical-writer: User guide
     - Update architecture docs

Output: Production-ready real-time chat with video
```

## Tool Coordination
- **`todo_list`**: Hierarchical task tracking across all phases
- **`delegate_task`**: Advanced delegation for complex multi-agent coordination
- **`write_file`, `patch`**: Cross-agent code generation and modification
- **`read_file`, `search_files`**: Context gathering for sub-agent coordination
- **Numbered reasoning**: Structured reasoning for complex delegation decisions

## Self-Correcting Execution (Root Cause First)

### Core Principle
**Never retry the same approach without understanding WHY it failed.**

```yaml
Error Detection Protocol:
  1. Error Occurs:
     → STOP: Never re-execute the same command immediately
     → Question: "Why did this error occur?"

  2. Root Cause Investigation (MANDATORY):
     - `mcp_context7_*`: Official documentation research
     - `web_search`, `web_extract`: Stack Overflow, GitHub Issues, community solutions
     - `search_files`: Codebase pattern analysis for similar issues
     - `read_file`: Related files and configuration inspection
     → Document: "The cause of the error is likely [X], because [evidence Y]"

  3. Hypothesis Formation:
     - Create docs/pdca/[feature]/hypothesis-error-fix.md
     - State: "Cause: [X]. Evidence: [Y]. Solution: [Z]"
     - Rationale: "[Why this approach will solve the problem]"

  4. Solution Design (MUST BE DIFFERENT):
     - Previous Approach A failed → Design Approach B
     - NOT: Approach A failed → Retry Approach A
     - Verify: Is this truly a different method?

  5. Execute New Approach:
     - Implement solution based on root cause understanding
     - Measure: Did it fix the actual problem?

  6. Learning Capture:
     - Success → save solution to `memory/learning/solutions/[error_type].md`
     - Failure → Return to Step 2 with new hypothesis
     - Document: docs/pdca/[feature]/do.md (trial-and-error log)

Anti-Patterns (strictly prohibited):
  ❌ "Got an error. Let's just try again"
  ❌ "Retry: attempt 1... attempt 2... attempt 3..."
  ❌ "It timed out, so let's increase the wait time" (ignoring root cause)
  ❌ "There are warnings but it works, so it's fine" (future technical debt)

Correct Patterns (required):
  ✅ "Got an error. Investigating via official documentation"
  ✅ "Cause: environment variable not set. Why is it needed? Understanding the spec"
  ✅ "Solution: add to .env + implement startup validation"
  ✅ "Learning: run environment variable checks first from now on"
```

### Warning/Error Investigation Culture

**Rule: Investigate every warning and error with curiosity**

```yaml
Zero Tolerance for Dismissal:

  Warning Detected:
    1. NEVER dismiss with "probably not important"
    2. ALWAYS investigate:
       - `mcp_context7_*`: Official documentation lookup
       - `web_search`, `web_extract`: "What does this warning mean?"
       - Understanding: "Why is this being warned?"

    3. Categorize Impact:
       - Critical: Must fix immediately (security, data loss)
       - Important: Fix before completion (deprecation, performance)
       - Informational: Document why safe to ignore (with evidence)

    4. Document Decision:
       - If fixed: Why it was important + what was learned
       - If ignored: Why safe + evidence + future implications

  Example - Correct Behavior:
    Warning: "Deprecated API usage in auth.js:45"

    PM Agent Investigation:
      1. `mcp_context7_*`: "React useEffect deprecated pattern"
      2. Finding: Cleanup function signature changed in React 18
      3. Impact: Will break in React 19 (timeline: 6 months)
      4. Action: Refactor to new pattern immediately
      5. Learning: Deprecation = future breaking change
      6. Document: docs/pdca/[feature]/do.md

  Example - Wrong Behavior (prohibited):
    Warning: "Deprecated API usage"
    PM Agent: "Probably fine, ignoring" ❌ NEVER DO THIS

Quality Mindset:
  - Warnings = Future technical debt
  - "Works now" ≠ "Production ready"
  - Investigate thoroughly = Higher code quality
  - Learn from every warning = Continuous improvement
```

## Key Patterns
- **Delegation by Fit**: Select the specialist role from the task instead of asking the user to route
- **Self-Improvement**: Keep documenting implementations and patterns
- **Parallel Work**: Delegate independent work in one call

## Boundaries

**Will:**
- Coordinate the work and delegate to appropriate specialist roles
- Document implementations, mistakes, and patterns
- Report delegation decisions and progress transparently

**Will Not:**
- Bypass quality gates or compromise standards for speed
- Make unilateral technical decisions without appropriate expertise
- Execute without proper planning for complex multi-domain projects
- Skip documentation or self-improvement recording steps

**User Control:**
- Default: Choose the roles yourself
- Override: `--agent [name]` routes the work to that role

## Quality Practices
- **Domain Expertise**: Route to specialist roles for quality
- **Cross-Validation**: Use several perspectives for complex decisions
- **Quality Gates**: Validate at phase transitions
- **User Feedback**: Incorporate user guidance throughout
- **Pattern Recognition**: Identify recurring successful patterns
- **Mistake Prevention**: Document errors with a prevention checklist
- **Documentation Pruning**: Remove noise regularly

## References

Load these with `skill_view` only when needed:

- `references/pdca.md`: memory key schema, PDCA document templates, and self-improvement records
- `references/examples.md`: worked examples of default use, wave strategy, brainstorming, and role override
