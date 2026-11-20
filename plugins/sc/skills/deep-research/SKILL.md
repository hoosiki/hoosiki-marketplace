---
name: deep-research
description: "Investigate a question in chat with sources and confidence"
license: MIT
metadata:
  author: "Junsang Park (adapted from SuperClaude Framework)"
  version: "1.0.0"
  upstream: "SuperClaude Framework 4.3.0"
  source: "plugins/superclaude/skills/deep-research/SKILL.md"
---

# Deep Research Mode

## When to Use
- The user asks to research or investigate something
- The answer needs current information with citations in chat, not a report file

This answers in chat. For a report saved to a file, use `/sc:research`.

Follow this systematic investigation process:

## Research Protocol

1. **Scope Definition**: Clarify the research question and boundaries
2. **Source Gathering**: Use `web_search`, `web_extract`, and `mcp_tavily_*` when connected to collect evidence
3. **Evidence Evaluation**: Assess source credibility and relevance
4. **Synthesis**: Combine findings into a coherent analysis
5. **Citation**: Always cite sources with URLs

## Requirements

- Every claim must have a source
- Present multiple perspectives when they exist
- Distinguish between facts, consensus, and speculation
- Use tables for comparisons
- Provide a confidence level for conclusions (high/medium/low)
- Include a "Sources" section at the end

## Output Format

```
## Research: [Topic]

### Key Findings
- Finding 1 (Source: [URL])
- Finding 2 (Source: [URL])

### Analysis
[Synthesized analysis with inline citations]

### Confidence: [High/Medium/Low]
[Reasoning for confidence level]

### Sources
1. [Title](URL) - [Brief description]
2. [Title](URL) - [Brief description]
```

Apply this to the instruction given with the skill, or to the current task if there is none.
