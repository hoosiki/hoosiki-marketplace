---
name: token-efficiency
description: "Compress output 30-50% when context is tight or on request"
license: MIT
metadata:
  author: "Junsang Park (adapted from SuperClaude Framework)"
  version: "1.0.0"
  upstream: "SuperClaude Framework 4.3.0"
  source: "plugins/superclaude/skills/token-efficiency/SKILL.md"
---

# Token Efficiency Mode

## When to Use
- Context is running low
- The user asks for brevity
- A large-scale operation would otherwise produce long output

Minimize token usage while preserving information quality (>=95%).

## Rules

- Use bullet points and tables, never verbose paragraphs
- Abbreviate common terms (fn=function, impl=implementation, cfg=config)
- Use symbols for status: OK, FAIL, WARN, SKIP
- One sentence per concept
- Code blocks only — no prose explanations of code
- Skip preamble, greetings, and transitions
- Target: 30-50% token reduction vs normal output
