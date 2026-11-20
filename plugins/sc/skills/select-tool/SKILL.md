---
name: select-tool
description: "Pick the best Hermes tool for an edit or search operation"
license: MIT
metadata:
  author: "Junsang Park (adapted from SuperClaude Framework)"
  version: "1.0.0"
  upstream: "SuperClaude Framework 4.3.0"
  source: "src/superclaude/commands/select-tool.md"
---

# /sc:select-tool - Tool Selection

Chooses the right Hermes tool for an edit or search, and explains why. The source chose between Serena and Morphllm. This keeps its scoring method and routes to the tools Hermes has.

## When to Use
- An operation could be done several ways and the choice affects accuracy or speed
- A change spans many files and the user asks for the safest approach
- The user asks which tool fits an operation

## Usage
```
/sc:select-tool [operation] [--analyze] [--explain]
```

## Behavioral Flow
1. **Parse**: Identify the operation type, file count, language, and whether meaning or only text matters.
2. **Score**: Rate complexity from 0 to 1 using the factors below.
3. **Match**: Compare the requirements with the routing table.
4. **Select**: Choose the tool. An explicit user preference always wins.
5. **Validate**: Say how the result will be verified. With `--explain`, give your reasoning. With `--analyze`, show the score.

## Complexity Score

| Factor | Adds |
|---|---|
| More than 5 files | 0.3 |
| Depends on meaning: symbols, types, call sites | 0.3 |
| Shared or public interface | 0.2 |
| No tests to catch mistakes | 0.2 |

- **Above 0.6**: Semantic path. Accuracy first: find every reference, edit, and verify.
- **Below 0.4**: Pattern path. Speed first: apply one edit or script.
- **0.4 to 0.6**: Decide by the most important feature of the operation.

## Routing

| Operation | Tool |
|---|---|
| Find files or text | `search_files` |
| Read known files | `read_file` |
| A few precise edits | `patch` |
| Coordinated edits across files | `patch` with `mode='patch'` |
| Same mechanical change across many files | A script through `execute_code`, then review the diff |
| Rename a symbol or change a signature (semantic path) | `mcp_serena_*` if connected; otherwise `search_files` for every reference, `patch`, then run tests and the type checker with `terminal` |
| Independent work that would flood the context | `delegate_task` |
| Build, test, or git | `terminal` |
| Library documentation | `mcp_context7_*` if connected; otherwise `web_extract` on official docs |
| Web facts | `web_search`, then `web_extract` |
| JavaScript-heavy pages or E2E | `browser_exec` or `mcp_chrome_devtools_*` |
| Short durable facts | `memory` |
| Project progress across sessions | `/sc:save` and `/sc:load` |
| Earlier conversations | `session_search` |
| A question only the user can answer | `clarify` |

Fall back from `mcp_*` tools to native tools, and say when you did.

## Examples

```
/sc:select-tool "rename function across 10 files" --analyze
# Score 0.6-0.8: many files and depends on meaning
# Semantic path: search_files for references, patch, run tests and type checker

/sc:select-tool "update console.log to logger.info across project" --explain
# Score 0.3: mechanical text change
# Pattern path: script through execute_code, then review the diff

/sc:select-tool "save project context and discoveries"
# Direct mapping: /sc:save for progress, memory for short durable facts
```

## Boundaries

**Will:**
- Recommend a tool with its reasoning and how to verify the result
- Respect an explicit user preference

**Will Not:**
- Perform the operation itself unless asked
- Recommend a tool that is not available in the session
