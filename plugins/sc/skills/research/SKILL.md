---
name: research
description: "Deep web research that writes a cited report file"
license: MIT
metadata:
  author: "Junsang Park (adapted from SuperClaude Framework)"
  version: "1.0.0"
  upstream: "SuperClaude Framework 4.3.0"
  source: "src/superclaude/commands/research.md"
---

# /sc:research - Deep Research Command

## When to Use
- Research questions beyond knowledge cutoff
- Complex research questions
- Current events and real-time information
- Academic or technical research requirements
- Market analysis and competitive intelligence

## Usage
```
/sc:research "[query]" [--depth quick|standard|deep|exhaustive] [--strategy planning|intent|unified]
```

## Behavioral Flow

### 1. Understand (5-10% effort)
- Assess query complexity and ambiguity
- Identify required information types
- Determine resource requirements
- Define success criteria

### 2. Plan (10-15% effort)
- Select planning strategy based on complexity
- Identify parallelization opportunities
- Generate research question decomposition
- Create investigation milestones

### 3. Track with `todo_list` (5% effort)
- Create adaptive task hierarchy
- Scale tasks to query complexity (3-15 tasks)
- Establish task dependencies
- Set progress tracking

### 4. Execute (50-60% effort)
- **Parallel-first searches**: Batch similar queries as several `web_search` calls in one turn, or use `delegate_task` for separate branches
- **Smart extraction**: Route by content complexity
- **Multi-hop exploration**: Follow entity and concept chains
- **Evidence collection**: Track sources and confidence

### 5. Track (Continuous)
- Monitor `todo_list` progress
- Update confidence scores
- Log successful patterns
- Identify information gaps

### 6. Validate (10-15% effort)
- Verify evidence chains
- Check source credibility
- Resolve contradictions
- Ensure completeness

## Key Patterns

### Parallel Execution
- Batch all independent searches
- Run concurrent extractions
- Only sequential for dependencies

### Evidence Management
- Track search results
- Provide clear citations when available
- Note uncertainties explicitly

### Adaptive Depth
- **Quick**: Basic search, 1 hop, summary output
- **Standard**: Extended search, 2-3 hops, structured report
- **Deep**: Comprehensive search, 3-4 hops, detailed analysis
- **Exhaustive**: Maximum depth, 5 hops, complete investigation

## Tool Integration
- **Web (`web_search`, `web_extract`, `mcp_tavily_*`)**: Primary search and extraction engine
- **Numbered reasoning (no tool needed)**: Complex reasoning and synthesis
- **Browser (`browser_exec`, `mcp_chrome_devtools_*`)**: JavaScript-heavy content extraction
- **Project memory (`/sc:save`, `/sc:load`, `session_search`)**: Research session persistence
- **Availability**: `mcp_*` tools exist only when that server is connected in this profile. If one is missing, use `web_search` and `web_extract` for docs and native tools otherwise, and say so in your report.
- **Roles** (deep-research-agent): Hermes has no preinstalled subagents for these. Take the role yourself, or name it in the `context` of a `delegate_task` task.

## Output Standards
- Save reports to `docs/research/research_[topic]_[timestamp].md` in the project; outside a project, use `~/.hermes/superclaude/reports/`
- Include executive summary
- Provide confidence levels
- List all sources with citations

## Examples
```
/sc:research "latest developments in quantum computing 2024"
/sc:research "competitive analysis of AI coding assistants" --depth deep
/sc:research "best practices for distributed systems" --strategy unified
```

## Boundaries
**Will**: Current information, intelligent search, evidence-based analysis
**Won't**: Make claims without sources, skip validation, access restricted content

## CRITICAL BOUNDARIES

**STOP AFTER RESEARCH REPORT**

This command produces a RESEARCH REPORT ONLY - no implementation.

**Explicitly Will NOT**:
- Implement findings or recommendations
- Write code based on research
- Make architectural decisions
- Create system changes based on research

**Output**: Research report (`docs/research/research_*.md`) containing:
- Findings with sources
- Evidence-based analysis
- Recommendations (for human decision)
- Cited references

**Next Step**: After research completes, user decides next action. Use `/sc:design` for architecture or `/sc:implement` for coding.
