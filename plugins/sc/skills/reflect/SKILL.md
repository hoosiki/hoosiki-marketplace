---
name: reflect
description: "Check work against the goal and decide if it is really done"
license: MIT
metadata:
  author: "Junsang Park (adapted from SuperClaude Framework)"
  version: "1.0.0"
  upstream: "SuperClaude Framework 4.3.0"
  source: "src/superclaude/commands/reflect.md"
---

# /sc:reflect - Task Reflection and Validation

Checks work against what was actually asked and decides, from evidence, whether it is done. The source used Serena's reflection tools. In Hermes, answer the checklists below yourself and back each answer with evidence.

## When to Use
- A task looks finished and needs validating before you report it
- The session has drifted, or you want to review progress
- The user asks whether something is really done
- Insights from the session should be captured for later

## Usage
```
/sc:reflect [--type task|session|completion] [--analyze] [--validate]
```

## Behavioral Flow
1. **Analyze**: Reread the original request. Read the current state with `todo_list`, and the changes with `git status` and `git diff`.
2. **Validate**: Work through the checklist for the chosen `--type`. With `--type` omitted, use all three.
3. **Reflect**: Name what the evidence shows, including what you did not verify.
4. **Document**: With durable insights, append them to `learnings.md` as `/sc:save --type learnings` describes.
5. **Optimize**: Recommend the next action: continue, correct course, or finish.

## Checklists

### `--type task`: Is the approach still on target?
- What exactly did the user ask for, in their words?
- Does the current approach serve that, or something adjacent?
- Have you changed anything not requested? Should it be reverted or called out?
- Do project conventions in the context file and nearby code still hold?

### `--type session`: Is the information sufficient?
- What was learned, and which claims rest on assumptions rather than something you read or ran?
- What is still missing, and can you find it now with `search_files`, `read_file`, or `web_search`?
- Are there contradictions between sources? Which one is current?

### `--type completion`: Is it really done?
- Is every requirement met? List each one with its evidence.
- Were tests, builds, or real runs executed in this session? Quote the result.
- Are any steps skipped, stubbed, or failing? Are any items in `todo_list` still open?
- What would the user find first if they checked this now?

## Output Format

```
Reflection: <task|session|completion>
Verdict: on track | correct course | done | not done
Evidence:
- <claim>: <test output, file, or command that shows it>
Gaps:
- <what is unverified or missing>
Next: <single recommended action>
```

## Tool Coordination
- **`todo_list`**: Open and finished items
- **`terminal`**: `git status`, `git diff`, and rerunning tests
- **`read_file`, `search_files`**: Checking claims against the files
- **`session_search`**: Recovering the original request or earlier decisions

## Examples

```
/sc:reflect --type task --analyze
# Checks the current approach against the request and suggests a correction

/sc:reflect --type session --validate
# Reviews the session's work and information, and identifies gaps

/sc:reflect --type completion
# Checks completion criteria against evidence and lists remaining blockers
```

## Boundaries

**Will:**
- Report honest verdicts from evidence, including "not done"
- Separate what was verified from what was assumed

**Will Not:**
- Call work done when tests were not run or failed
- Change code; a correction waits for a decision or a follow-up task
