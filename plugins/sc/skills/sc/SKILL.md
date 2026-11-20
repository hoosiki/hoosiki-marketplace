---
name: sc
description: "List the /sc:* workflow skills or route a request to one"
license: MIT
metadata:
  author: "Junsang Park (adapted from SuperClaude Framework)"
  version: "1.0.0"
  upstream: "SuperClaude Framework 4.3.0"
  source: "src/superclaude/commands/sc.md"
---

# /sc:sc - Workflow Skills for Hermes

Entry point to the `/sc:*` workflow skills. With no instruction, show the list below and stop. With an instruction, pick the best match, load it with `skill_view`, and follow it.

## When to Use
- The user types `/sc:sc` or asks which `/sc:*` skills exist
- The user wants one of these workflows but has not named one

## Usage
```
/sc:sc [request]
/sc:<name> [args and flags]
```

Each skill is `/sc:<name>`, the same name the command has in Claude Code. Anything typed after the name reaches the skill as its instruction, including flags.

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

## Going Further
- `/sc:help` lists every flag and what it maps to in Hermes
- `/sc:recommend "<goal>"` suggests a skill and flags for a goal

Adapted from SuperClaude Framework (MIT): https://github.com/SuperClaude-Org/SuperClaude_Framework. Not affiliated with or endorsed by the SuperClaude Framework project or Anthropic.
