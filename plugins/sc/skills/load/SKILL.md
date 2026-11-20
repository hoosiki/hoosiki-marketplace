---
name: load
description: "Restore saved project context at the start of a session"
license: MIT
metadata:
  author: "Junsang Park (adapted from SuperClaude Framework)"
  version: "1.0.0"
  upstream: "SuperClaude Framework 4.3.0"
  source: "src/superclaude/commands/load.md"
---

# /sc:load - Project Context Loading

Restores what `/sc:save` stored and reports where the work stands, so the session can continue without re-explaining anything.

## When to Use
- A session is starting on a project with earlier work
- The user asks where things were left off, or to resume or restore context
- The user wants project, config, or dependency context loaded before starting

## Usage
```
/sc:load [target] [--type project|config|deps|checkpoint] [--refresh] [--analyze] [--checkpoint <timestamp>]
```

`target` is a project path and defaults to the current directory. `--type` defaults to `checkpoint`, plus a short `project` pass.

## Behavioral Flow
1. **Locate**: Find the store with `terminal`, running this in the target directory. The layout is described in `/sc:save`.
   ```bash
   (git rev-parse --show-toplevel 2>/dev/null || pwd) | tr '/' '-'
   ```
   The store is `~/.hermes/superclaude/projects/<slug>/`.
2. **Load** with `read_file`, by `--type`:
   - `checkpoint`: `latest.md` and `learnings.md`. With `--checkpoint <timestamp>`, read `checkpoints/<timestamp>.md` instead of `latest.md`.
   - `project`: `context.md`, the project context file (`.hermes.md`, `AGENTS.md`, or `CLAUDE.md`), `README`, and `PROJECT_INDEX.md` if present.
   - `config`: Configuration files found with `search_files` and `target='files'`.
   - `deps`: The dependency manifest and lockfile.
3. **Fill the gaps**:
   - No store yet, or `--refresh`: use `session_search` to find recent sessions about this project.
   - `.serena/memories/*.md` in the project: these come from Claude Code `/sc:save` runs. Read them as extra context and never edit them.
4. **Validate**: Saved context can be stale. Compare it with the current state from `git status` and `git branch`. Flag a different branch, files that no longer exist, or a checkpoint that looks old. Current files win over saved claims.
5. **Activate**: Put open items back with `todo_list`. With `--analyze`, also review the project structure and report what you learned.
6. **Report**, then wait for the user:
   ```
   Previous: [last session summary]
   Progress: [current status]
   Next: [planned next actions]
   Blockers: [blockers or issues]
   ```
   If nothing was found, say so plainly and suggest `/sc:index-repo`.

## Tool Coordination
- **`terminal`**: Slug, branch, and working tree state
- **`read_file`, `search_files`**: Checkpoints and project files
- **`session_search`**: Earlier sessions when there is no checkpoint
- **`todo_list`**: Restoring open items

## Examples

```
/sc:load
# Restores the latest checkpoint for the current project and reports status

/sc:load /path/to/project --type project --analyze
# Loads project context for another path and reviews its structure

/sc:load --type checkpoint --checkpoint 20261105-143000
# Restores one specific earlier checkpoint

/sc:load --type deps --refresh
# Loads dependency context and searches earlier sessions again
```

## Boundaries

**Will:**
- Restore saved context and report it with its age
- Flag saved claims that no longer match the project

**Will Not:**
- Change project files or configuration without explicit permission
- Replace `latest.md` or any other stored context; only `/sc:save` writes the store
- Start the next action before the user confirms
