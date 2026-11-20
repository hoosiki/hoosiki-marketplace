---
name: brainstorm
description: "Turn a vague idea into a requirements spec through questions"
license: MIT
metadata:
  author: "Junsang Park (adapted from SuperClaude Framework)"
  version: "1.0.0"
  upstream: "SuperClaude Framework 4.3.0"
  source: "src/superclaude/commands/brainstorm.md"
---

# /sc:brainstorm - Interactive Requirements Discovery

## When to Use
- Ambiguous project ideas requiring structured exploration
- Requirements discovery and specification development needs
- Concept validation and feasibility assessment requests
- Cross-session brainstorming and iterative refinement scenarios

## Usage
```
/sc:brainstorm [topic/idea] [--strategy systematic|agile|enterprise] [--depth shallow|normal|deep] [--parallel]
```

## Behavioral Flow
1. **Explore**: Transform ambiguous ideas through Socratic dialogue and systematic questioning
2. **Analyze**: Coordinate multiple personas for domain expertise and comprehensive analysis
3. **Validate**: Apply feasibility assessment and requirement validation across domains
4. **Specify**: Generate concrete specifications with cross-session persistence capabilities
5. **Handoff**: Create actionable briefs ready for implementation or further development

Key behaviors:
- Multi-persona orchestration across architecture, analysis, frontend, backend, security domains
- Advanced tool coordination with intelligent routing for specialized analysis
- Systematic execution with progressive dialogue enhancement and parallel exploration
- Cross-session persistence with comprehensive requirements discovery documentation

## Tool Integration
- **Numbered reasoning (no tool needed)**: Complex multi-step reasoning for systematic exploration and validation
- **Library docs (`mcp_context7_*`)**: Framework-specific feasibility assessment and pattern analysis
- **UI code (written directly)**: UI/UX feasibility and design system integration analysis
- **Browser (`browser_exec`, `mcp_chrome_devtools_*`)**: User experience validation and interaction pattern testing
- **Bulk edits (`patch`, `execute_code`)**: Large-scale content analysis and pattern-based transformation
- **Project memory (`/sc:save`, `/sc:load`, `session_search`)**: Cross-session persistence, memory management, and project context enhancement
- **Availability**: `mcp_*` tools exist only when that server is connected in this profile. If one is missing, use `web_search` and `web_extract` for docs and native tools otherwise, and say so in your report.
- **Roles** (architect, analyzer, frontend, backend, security, devops, project-manager): Hermes has no preinstalled subagents for these. Take the role yourself, or name it in the `context` of a `delegate_task` task.

## Tool Coordination
- **`read_file`, `write_file`, `patch`**: Requirements documentation and specification generation
- **`todo_list`**: Progress tracking for complex multi-phase exploration
- **`delegate_task`**: Advanced delegation for parallel exploration paths and multi-agent coordination
- **`web_search`**: Market research, competitive analysis, and technology validation
- **Numbered reasoning**: Structured reasoning for complex requirements analysis

## Key Patterns
- **Socratic Dialogue**: Question-driven exploration → systematic requirements discovery
- **Multi-Domain Analysis**: Cross-functional expertise → comprehensive feasibility assessment
- **Progressive Coordination**: Systematic exploration → iterative refinement and validation
- **Specification Generation**: Concrete requirements → actionable implementation briefs

## Examples

### Systematic Product Discovery
```
/sc:brainstorm "AI-powered project management tool" --strategy systematic --depth deep
# Multi-persona analysis: architect (system design), analyzer (feasibility), project-manager (requirements)
# numbered reasoning provides structured exploration framework
```

### Agile Feature Exploration
```
/sc:brainstorm "real-time collaboration features" --strategy agile --parallel
# Parallel exploration paths with frontend, backend, and security personas
# library docs and UI patterns for framework and UI pattern analysis
```

### Enterprise Solution Validation
```
/sc:brainstorm "enterprise data analytics platform" --strategy enterprise --validate
# Comprehensive validation with security, devops, and architect personas
# session checkpoints for cross-session persistence and enterprise requirements tracking
```

### Cross-Session Refinement
```
/sc:brainstorm "mobile app monetization strategy" --depth normal
# session checkpoints manages cross-session context and iterative refinement
# Progressive dialogue enhancement with memory-driven insights
```

## Boundaries

**Will:**
- Transform ambiguous ideas into concrete specifications through systematic exploration
- Coordinate multiple personas and tools for comprehensive analysis
- Provide cross-session persistence and progressive dialogue enhancement

**Will Not:**
- Make implementation decisions without proper requirements discovery
- Override user vision with prescriptive solutions during exploration phase
- Bypass systematic exploration for complex multi-domain projects

## CRITICAL BOUNDARIES

**STOP AFTER REQUIREMENTS DISCOVERY**

This command produces a REQUIREMENTS SPECIFICATION ONLY.

**Explicitly Will NOT**:
- Create architecture diagrams or system designs (use `/sc:design`)
- Generate implementation code (use `/sc:implement`)
- Make architectural decisions
- Design database schemas or API contracts
- Create technical specifications beyond requirements

**Output**: Requirements document with:
- Clarified user goals
- Functional requirements
- Non-functional requirements
- User stories / acceptance criteria
- Open questions for user

**Next Step**: After brainstorm completes, use `/sc:design` for architecture or `/sc:workflow` for implementation planning.
