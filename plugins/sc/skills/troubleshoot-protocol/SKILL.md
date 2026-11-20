---
name: troubleshoot-protocol
description: "Find the root cause before any retry when something fails"
license: MIT
metadata:
  author: "Junsang Park (adapted from SuperClaude Framework)"
  version: "1.0.0"
  upstream: "SuperClaude Framework 4.3.0"
  source: "plugins/superclaude/skills/troubleshoot/SKILL.md"
---

# Troubleshooting Protocol

## When to Use
- The user reports an error, bug, or unexpected behavior
- A command or test you ran has just failed

For a full diagnosis report, use `/sc:troubleshoot`.

Follow this systematic root cause analysis process. NEVER retry the same approach without understanding WHY it failed.

## Protocol

1. **STOP**: Do not re-execute the same command
2. **Observe**: What exactly happened? What was expected?
3. **Hypothesize**: What could cause this? (list 2-3 possibilities)
4. **Investigate**: Check official docs, logs, stack traces, config
5. **Root Cause**: Identify the fundamental cause (not symptoms)
6. **Fix**: Implement a solution that addresses the root cause
7. **Verify**: Confirm the fix works
8. **Learn**: Document the solution for future reference

## Anti-Patterns (strictly prohibited)

- "Got an error. Let's just try again"
- "Retry: attempt 1... attempt 2... attempt 3..."
- "It timed out, so let's increase the wait time" (ignoring root cause)
- "There are warnings but it works, so it's fine" (future technical debt)

## Required Format

```
## Root Cause Analysis

**Error**: [Exact error message]
**Expected**: [What should have happened]
**Cause**: [Root cause with evidence]
**Fix**: [Solution addressing root cause]
**Prevention**: [How to prevent recurrence]
```

Apply this to the instruction given with the skill, or to the current task if there is none.
