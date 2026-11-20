---
name: save
description: "Checkpoint session progress and learnings for later resume"
license: MIT
metadata:
  author: "Junsang Park (adapted from SuperClaude Framework)"
  version: "1.0.0"
  upstream: "SuperClaude Framework 4.3.0"
  source: "src/superclaude/commands/save.md"
---

# /sc:save - Session Context Persistence

Saves session progress so a later session can resume with `/sc:load`. Hermes has no Serena memory here, so checkpoints are plain files in a store outside the repository.

## When to Use
- The session is ending and its progress should survive
- The user asks to checkpoint, save context, or record learnings
- A long or risky stretch of work has just finished

## Usage
```
/sc:save [--type session|learnings|context|all] [--summarize] [--checkpoint]
```

## Checkpoint Store

Each project has one folder, shared by every session and profile:

```
~/.hermes/superclaude/projects/<slug>/
├── latest.md                 # current state, replaced on every save
├── learnings.md              # patterns and solutions, appended
├── context.md                # project understanding, updated in place
└── checkpoints/<timestamp>.md  # earlier versions of latest.md
```

Get `<slug>` and the timestamp with `terminal`:

```bash
(git rev-parse --show-toplevel 2>/dev/null || pwd) | tr '/' '-'
date +%Y%m%d-%H%M%S
```

## Behavioral Flow
1. **Analyze**: Review the session for the goal, finished work, decisions, and open items. Read the current list with `todo_list`.
2. **Checkpoint**: If `latest.md` exists, copy it to `checkpoints/<timestamp>.md` before replacing it, so nothing is lost.
3. **Persist**: Write the files for the chosen `--type` with `write_file`:
   - `session` (default): `latest.md`
   - `learnings`: append dated entries to `learnings.md`
   - `context`: update `context.md`
   - `all`: all three
4. **Keep durable facts**: Use the `memory` tool only for short facts useful in every future session, such as a user preference or a lasting project constraint. It has a small limit, so progress and logs belong in the store.
5. **Validate**: Read `latest.md` back with `read_file` and confirm every section is filled in. Then give its full path.

With `--summarize`, also show the session summary in your reply. With `--checkpoint`, also keep a copy of the new `latest.md` under `checkpoints/`.

## latest.md Format

```markdown
# Checkpoint: <project name>
Saved: <ISO timestamp>
Session: ${HERMES_SESSION_ID}
Branch: <git branch>

## Goal
## Done
<finished work, with file paths>
## In Progress
## Next Actions
<ordered list, first item ready to start>
## Blockers
## Key Decisions
<decision and why>
```

## Tool Coordination
- **`terminal`**: Slug, timestamp, branch, and copying the previous checkpoint
- **`todo_list`**: Open and finished items
- **`write_file`, `read_file`**: Writing and verifying checkpoint files
- **`memory`**: Short durable facts only

## Examples

```
/sc:save
# Replaces latest.md and keeps the previous version under checkpoints/

/sc:save --type all --checkpoint
# Saves state, learnings, and context, and keeps a recovery copy

/sc:save --summarize
# Saves state and shows the session summary

/sc:save --type learnings
# Appends new patterns and solutions only
```

## Boundaries

**Will:**
- Save session context so a later session can resume it
- Keep the previous checkpoint before replacing it
- Report the path of what was saved

**Will Not:**
- Write secrets, tokens, or credentials into a checkpoint, even if they appeared in the session
- Commit anything or add files to the repository
- Overwrite `latest.md` without keeping the previous version
