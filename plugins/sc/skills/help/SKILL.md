---
name: help
description: "Show every /sc:* skill and flag, then stop"
license: MIT
metadata:
  author: "Junsang Park (adapted from SuperClaude Framework)"
  version: "1.0.0"
  upstream: "SuperClaude Framework 4.3.0"
  source: "src/superclaude/commands/help.md"
---

# /sc:help - Command Reference

## When to Use
- The user wants to discover skills or look up a flag
- The user asks what the `/sc:*` skills can do in Hermes

## Behavioral Flow
1. **Display**: Present the skill list and flags below
2. **Complete**: End the turn after displaying them

This is display only. Do not start any work, create files, or use `todo_list`.

## Skills

### Discover & plan
| Skill | What it does |
|---|---|
| `/sc:brainstorm` | Turn a vague idea into a requirements spec through questions |
| `/sc:brainstorm-mode` | Explore options in Socratic dialogue, then recommend one |
| `/sc:design` | Design system architecture, APIs, and component interfaces |
| `/sc:workflow` | Turn a PRD or feature spec into an implementation plan |
| `/sc:estimate` | Estimate time, effort, and complexity for dev work |
| `/sc:spec-panel` | Review a spec with a panel of software engineering experts |
| `/sc:business-panel` | Review a business document with a nine-expert panel |

### Build
| Skill | What it does |
|---|---|
| `/sc:implement` | Implement a feature with docs lookup, tests, and role focus |
| `/sc:build` | Build and package a project and diagnose build errors |
| `/sc:test` | Run tests and report coverage, failures, and quality |
| `/sc:improve` | Refactor code for quality, performance, maintainability |
| `/sc:cleanup` | Remove dead code and tidy project structure safely |
| `/sc:git` | Run git operations and write conventional commit messages |

### Investigate
| Skill | What it does |
|---|---|
| `/sc:analyze` | Audit code for quality, security, performance, architecture |
| `/sc:troubleshoot` | Diagnose bugs, build errors, and system failures |
| `/sc:troubleshoot-protocol` | Find the root cause before any retry when something fails |
| `/sc:explain` | Explain code, concepts, or system behavior step by step |
| `/sc:research` | Deep web research that writes a cited report file |
| `/sc:deep-research` | Investigate a question in chat with sources and confidence |

### Docs & session
| Skill | What it does |
|---|---|
| `/sc:document` | Write docs for a component, function, API, or feature |
| `/sc:index` | Generate project docs and a knowledge base for a codebase |
| `/sc:index-repo` | Write PROJECT_INDEX files to cut repo exploration tokens |
| `/sc:save` | Checkpoint session progress and learnings for later resume |
| `/sc:load` | Restore saved project context at the start of a session |
| `/sc:reflect` | Check work against the goal and decide if it is really done |

### Orchestrate
| Skill | What it does |
|---|---|
| `/sc:agent` | Own a task end to end: scope, confidence gate, build, review |
| `/sc:pm` | Run a project with PDCA cycles and role-based delegation |
| `/sc:pm-mode` | PDCA cycles with status reports and a confidence check |
| `/sc:task` | Run a complex multi-step task with tracked delegation |
| `/sc:spawn` | Split a large operation into epics and delegate the parts |
| `/sc:confidence-check` | Score readiness before coding; proceed only at 90% or above |
| `/sc:token-efficiency` | Compress output 30-50% when context is tight or on request |

### Meta
| Skill | What it does |
|---|---|
| `/sc:help` | Show every /sc:* skill and flag, then stop |
| `/sc:recommend` | Recommend the right /sc:* skill and flags for a request |
| `/sc:select-tool` | Pick the best Hermes tool for an edit or search operation |

## Flags

Flags are plain text after the skill name. The skill reads them as instructions, so they work with any `/sc:*` skill.

### Mode Activation Flags

| Flag | Trigger | Behavior |
|------|---------|----------|
| `--brainstorm` | Vague project requests, exploration keywords | Follow `/sc:brainstorm-mode`: ask probing questions |
| `--introspect` | Self-analysis requests, error recovery | Expose your reasoning with explicit markers |
| `--task-manage` | Multi-step operations (>3 steps) | Organize with `todo_list` and `delegate_task` |
| `--orchestrate` | Multi-tool operations, parallel execution | Choose tools with `/sc:select-tool`, run independent calls in parallel |
| `--token-efficient` | Context usage >75%, large-scale operations | Follow `/sc:token-efficiency` |

### Tool Flags

`mcp_*` tools exist only when that server is connected in this profile. When one is missing, use the fallback and say so.

| Flag | Trigger | Behavior in Hermes |
|------|---------|----------|
| `--c7` / `--context7` | Library imports, framework questions | Use `mcp_context7_*`; fall back to `web_extract` on official docs |
| `--seq` / `--sequential` | Complex debugging, system design | Write numbered reasoning steps before acting |
| `--magic` | UI component requests | Write the components directly, following the project's design system |
| `--morph` / `--morphllm` | Bulk code transformations | Use `patch`, or a script through `execute_code` |
| `--serena` | Symbol operations, project memory | Use `mcp_serena_*` if connected; otherwise `search_files` with `patch`, and `/sc:save` with `/sc:load` for memory |
| `--play` / `--playwright` | Browser testing, E2E scenarios | Use `browser_exec` or `mcp_chrome_devtools_*` |
| `--all-mcp` | Maximum complexity scenarios | Use every connected `mcp_*` tool that helps |
| `--no-mcp` | Native-only execution needs | Do not use `mcp_*` tools |

### Role Flags

| Flag | Behavior |
|------|----------|
| `--persona-<role>` / `--agent <role>` | Take that role (architect, frontend, backend, security, qa, performance, mentor, and so on), or name it in the `context` of a `delegate_task` task |

### Analysis Depth Flags

| Flag | Trigger | Behavior |
|------|---------|----------|
| `--think` | Multi-component analysis needs | Standard structured analysis (~4K tokens) with numbered reasoning |
| `--think-hard` | Architectural analysis, system-wide dependencies | Deep analysis (~10K tokens), adding library docs |
| `--ultrathink` | Critical system redesign, legacy modernization | Maximum depth analysis (~32K tokens) with every connected tool that helps |

### Execution Control Flags

| Flag | Trigger | Behavior |
|------|---------|----------|
| `--delegate [auto\|files\|folders]` | >7 directories OR >50 files | Split the work across `delegate_task` children |
| `--concurrency [n]` | Resource optimization needs | Limit parallel work to n; Hermes also caps it at `delegation.max_concurrent_children` |
| `--loop` | Improvement keywords (polish, refine, enhance) | Iterate with a validation gate after each cycle |
| `--iterations [n]` | Specific improvement cycle requirements | Set the improvement cycle count (1-10) |
| `--validate` | Risk score >0.7, resource usage >75% | Assess risk before executing, and stop at validation gates |
| `--safe-mode` | Resource usage >85%, production environment | Maximum validation, conservative execution |

### Output Optimization Flags

| Flag | Trigger | Behavior |
|------|---------|----------|
| `--uc` / `--ultracompressed` | Context pressure, efficiency requirements | Follow `/sc:token-efficiency` |
| `--scope [file\|module\|project\|system]` | Analysis boundary needs | Define operational scope and analysis depth |
| `--focus [performance\|security\|quality\|architecture\|accessibility\|testing]` | Domain-specific optimization | Target one analysis domain |

### Flag Priority Rules

- **Safety First**: `--safe-mode` > `--validate` > optimization flags
- **Explicit Override**: User flags > auto-detection
- **Depth Hierarchy**: `--ultrathink` > `--think-hard` > `--think`
- **Tool Control**: `--no-mcp` overrides all individual tool flags
- **Scope Precedence**: system > project > module > file

### Usage Examples

```bash
# Deep analysis with library docs
/sc:analyze --think-hard --context7 src/

# Token-efficient task management
/sc:task --token-efficient --delegate auto "Refactor authentication system"

# Safe production build
/sc:build --safe-mode --validate --focus security
```

## Boundaries

**Will:**
- Display the skill list and flags
- Explain what each flag does in Hermes

**Will Not:**
- Execute any skill or create any file
- Start implementation or a project
