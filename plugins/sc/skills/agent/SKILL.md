---
name: agent
description: "Own a task end to end: scope, confidence gate, build, review"
license: MIT
metadata:
  author: "Junsang Park (adapted from SuperClaude Framework)"
  version: "1.0.0"
  upstream: "SuperClaude Framework 4.3.0"
  source: "src/superclaude/commands/agent.md"
---

# /sc:agent - Session Controller

Owns a task from scope to validated result: orchestrate the helpers, keep the user out of busywork, and report only what matters. Hermes starts this when invoked, not at every session start.

## When to Use
- The user wants one agent to own investigation, implementation, and review of a task
- The user invokes `/sc:agent` with a task or a helper name

## Usage
```
/sc:agent [task]
/sc:agent deep-research|repo-index|self-review [args]
```

A helper name runs that helper directly (see Tooling Guidance).

## Startup Checklist (keep output terse)
1. Run `git status --porcelain` with `terminal` and announce `📊 Git: clean|X files|not a repo`.
2. Remind the user: `💡 Use /context to confirm token budget.`
3. Report core services: confidence check, deep research, repository index.

With no task given, stop here until the user describes one.

---

## Task Protocol

When the user assigns a task, own the entire workflow:

1. **Clarify scope**
   - Confirm success criteria, blockers, and constraints. Use `clarify` when the answer changes the plan.
   - Capture any acceptance tests that matter.

2. **Plan investigation**
   - Use parallel tool calls where possible.
   - Reach for the helpers below instead of inventing bespoke commands.

3. **Iterate until confident**
   - Track confidence from `/sc:confidence-check`. Do not implement below 0.90.
   - Escalate to the user if confidence stalls or new context is required.

4. **Implementation wave**
   - Prepare edits as a single checkpoint summary.
   - Prefer grouped `patch` edits over many tiny actions.
   - Run the agreed test commands with `terminal` after edits.

5. **Self-review and reflexion**
   - Run the self-review helper to double-check outcomes.
   - Share residual risks or follow-up tasks.

Deliver concise updates at the end of each major phase. Avoid repeating facts already established in the session.

---

## Tooling Guidance

Load a helper skill with `skill_view`. To keep its work out of your context, run it through `delegate_task`, naming the skill in the task `goal` and passing the facts it needs in `context`.

| Helper | Use | When |
|---|---|---|
| Confidence check | `/sc:confidence-check` | Before implementing. A score of 0.90 or above is required |
| Deep research | `/sc:deep-research`, or `/sc:research` for a report file | Open questions or external lookups, before speculating |
| Repo index | `/sc:index-repo` | First task per session, or whenever the codebase drifts |
| Self-review | `/sc:reflect --type completion`, or an independent `delegate_task` review given the diff and acceptance criteria | After implementing |

Log the latest confidence score whenever it changes so the user can see progress.

If a tool or `mcp_*` server is unavailable, note the failure, fall back to native Hermes tools, and flag the gap for follow-up.

---

## Token Discipline

- Use short status messages (`🔄 Investigating…`, `📊 Confidence: 0.82`).
- Collapse redundant summaries; refer back to prior answers.
- Persist long briefs with `/sc:save` only if the user requests it.
