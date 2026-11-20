# sc

36 workflow skills for [Hermes Agent](https://github.com/NousResearch/hermes-agent), invoked as `/sc:<name>`. They are adapted from the 30 commands and 6 skills of [SuperClaude Framework](https://github.com/SuperClaude-Org/SuperClaude_Framework) 4.3.0 and rewritten for Hermes tools.

This is a Hermes plugin only. It is not listed in this repository's Claude Code marketplace (see [Not for Claude Code](#not-for-claude-code)).

## Install

```bash
hermes plugins install hoosiki/hoosiki-marketplace#plugins/sc --enable

# Plugins are per profile. Install into a named profile with -p:
hermes -p engineer plugins install hoosiki/hoosiki-marketplace#plugins/sc --enable
```

Update with `hermes plugins update sc` and remove with `hermes plugins remove sc`. Without `--enable`, Hermes asks whether to enable the plugin; you can turn it on later with `hermes plugins enable sc`.

## Use

```
/sc:sc                                    # list the skills
/sc:sc "review this API design"           # route a request to the best skill
/sc:analyze src/ --focus security         # run one skill; the rest of the line is its instruction
```

- Slash commands for plugin skills work in the Hermes CLI, TUI and desktop app. Messaging gateways do not offer them as commands.
- `/sc:save` and `/sc:load` keep session context as files in `~/.hermes/superclaude/projects/<slug>/`, where `<slug>` is the git root path with `/` replaced by `-`.
- Skills that mention `mcp_context7_*` or `mcp_chrome_devtools_*` use those MCP servers when the profile has them connected, and fall back to `web_search`, `web_extract` and the native tools otherwise.

## Skills

The dispatcher, `/sc:sc`, lists the other 35 skills or routes a request to one.

**Discover & plan**

| Skill | What it does |
|---|---|
| `/sc:brainstorm` | Turn a vague idea into a requirements spec through questions |
| `/sc:brainstorm-mode` | Explore options in Socratic dialogue, then recommend one |
| `/sc:design` | Design system architecture, APIs, and component interfaces |
| `/sc:workflow` | Turn a PRD or feature spec into an implementation plan |
| `/sc:estimate` | Estimate time, effort, and complexity for dev work |
| `/sc:spec-panel` | Review a spec with a panel of software engineering experts |
| `/sc:business-panel` | Review a business document with a nine-expert panel |

**Build**

| Skill | What it does |
|---|---|
| `/sc:implement` | Implement a feature with docs lookup, tests, and role focus |
| `/sc:build` | Build and package a project and diagnose build errors |
| `/sc:test` | Run tests and report coverage, failures, and quality |
| `/sc:improve` | Refactor code for quality, performance, maintainability |
| `/sc:cleanup` | Remove dead code and tidy project structure safely |
| `/sc:git` | Run git operations and write conventional commit messages |

**Investigate**

| Skill | What it does |
|---|---|
| `/sc:analyze` | Audit code for quality, security, performance, architecture |
| `/sc:troubleshoot` | Diagnose bugs, build errors, and system failures |
| `/sc:troubleshoot-protocol` | Find the root cause before any retry when something fails |
| `/sc:explain` | Explain code, concepts, or system behavior step by step |
| `/sc:research` | Deep web research that writes a cited report file |
| `/sc:deep-research` | Investigate a question in chat with sources and confidence |

**Docs & session**

| Skill | What it does |
|---|---|
| `/sc:document` | Write docs for a component, function, API, or feature |
| `/sc:index` | Generate project docs and a knowledge base for a codebase |
| `/sc:index-repo` | Write PROJECT_INDEX files to cut repo exploration tokens |
| `/sc:save` | Checkpoint session progress and learnings for later resume |
| `/sc:load` | Restore saved project context at the start of a session |
| `/sc:reflect` | Check work against the goal and decide if it is really done |

**Orchestrate**

| Skill | What it does |
|---|---|
| `/sc:agent` | Own a task end to end: scope, confidence gate, build, review |
| `/sc:pm` | Run a project with PDCA cycles and role-based delegation |
| `/sc:pm-mode` | PDCA cycles with status reports and a confidence check |
| `/sc:task` | Run a complex multi-step task with tracked delegation |
| `/sc:spawn` | Split a large operation into epics and delegate the parts |
| `/sc:confidence-check` | Score readiness before coding; proceed only at 90% or above |
| `/sc:token-efficiency` | Compress output 30-50% when context is tight or on request |

**Meta**

| Skill | What it does |
|---|---|
| `/sc:help` | Show every /sc:* skill and flag, then stop |
| `/sc:recommend` | Recommend the right /sc:* skill and flags for a request |
| `/sc:select-tool` | Pick the best Hermes tool for an edit or search operation |

## Changes from the source

- **Tools:** Claude Code tools are mapped to Hermes tools, for example Read to `read_file`, Edit to `patch`, Bash to `terminal`, Task to `delegate_task` and TodoWrite to `todo_list`. Serena memory is replaced by the file store above.
- **Scope:** only the commands and skills were ported. The source's agents, behavioral modes and core rules were not.
- **Behavior:** `/sc:pm` proposes changes to the agent's context file and applies them only if the user agrees; the source edits it on its own. Usage statistics in `/sc:recommend` that had no data behind them were removed, and references to commands that no longer exist were remapped or dropped.
- **Panels:** `/sc:spec-panel` and `/sc:business-panel` simulate the viewpoints of real authors. Each now states that its quotes and dialogue are invented examples, not statements by those people, and asks the agent to say once in its output that the panel is simulated.

## Not for Claude Code

Claude Code already gets `/sc:*` from SuperClaude itself, in `~/.claude/commands/sc/`. A Claude Code plugin named `sc` would use the same names. In a test on Claude Code 2.1.318, a plugin skill named `sc:load` was hidden by the existing command, while a plugin skill with a new name was added. Listing this plugin in `.claude-plugin/marketplace.json` would therefore mix the two sets, and the added skills would name Hermes tools that Claude Code does not have.

## License

MIT. See [LICENSE](LICENSE), which keeps the upstream notice and adds one for this port:

- Copyright (c) 2024 SuperClaude Framework Contributors
- Copyright (c) 2026 Junsang Park (Hermes port and modifications)

Not affiliated with or endorsed by the SuperClaude Framework project or Anthropic. Claude is a trademark of Anthropic.
