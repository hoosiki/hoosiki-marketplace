---
name: workflow
description: "Turn a PRD or feature spec into an implementation plan"
license: MIT
metadata:
  author: "Junsang Park (adapted from SuperClaude Framework)"
  version: "1.0.0"
  upstream: "SuperClaude Framework 4.3.0"
  source: "src/superclaude/commands/workflow.md"
---

# /sc:workflow - Implementation Workflow Generator

## When to Use
- PRD and feature specification analysis for implementation planning
- Structured workflow generation for development projects
- Multi-persona coordination for complex implementation strategies
- Cross-session workflow management and dependency mapping

## Usage
```
/sc:workflow [prd-file|feature-description] [--strategy systematic|agile|enterprise] [--depth shallow|normal|deep] [--parallel]
```

## Behavioral Flow
1. **Analyze**: Parse PRD and feature specifications to understand implementation requirements
2. **Plan**: Generate comprehensive workflow structure with dependency mapping and task orchestration
3. **Coordinate**: Activate multiple personas for domain expertise and implementation strategy
4. **Execute**: Create structured step-by-step workflows with automated task coordination
5. **Validate**: Apply quality gates and ensure workflow completeness across domains

Key behaviors:
- Multi-persona orchestration across architecture, frontend, backend, security, and devops domains
- Advanced tool coordination with intelligent routing for specialized workflow analysis
- Systematic execution with progressive workflow enhancement and parallel processing
- Cross-session workflow management with comprehensive dependency tracking

## Tool Integration
- **Numbered reasoning (no tool needed)**: Complex multi-step workflow analysis and systematic implementation planning
- **Library docs (`mcp_context7_*`)**: Framework-specific workflow patterns and implementation best practices
- **UI code (written directly)**: UI/UX workflow generation and design system integration strategies
- **Browser (`browser_exec`, `mcp_chrome_devtools_*`)**: Testing workflow integration and quality assurance automation
- **Bulk edits (`patch`, `execute_code`)**: Large-scale workflow transformation and pattern-based optimization
- **Project memory (`/sc:save`, `/sc:load`, `session_search`)**: Cross-session workflow persistence, memory management, and project context
- **Availability**: `mcp_*` tools exist only when that server is connected in this profile. If one is missing, use `web_search` and `web_extract` for docs and native tools otherwise, and say so in your report.
- **Roles** (architect, analyzer, frontend, backend, security, devops, project-manager): Hermes has no preinstalled subagents for these. Take the role yourself, or name it in the `context` of a `delegate_task` task.

## Tool Coordination
- **`read_file`, `write_file`, `patch`**: PRD analysis and workflow documentation generation
- **`todo_list`**: Progress tracking for complex multi-phase workflow execution
- **`delegate_task`**: Advanced delegation for parallel workflow generation and multi-agent coordination
- **`web_search`**: Technology research, framework validation, and implementation strategy analysis
- **Numbered reasoning**: Structured reasoning for complex workflow dependency analysis

## Key Patterns
- **PRD Analysis**: Document parsing → requirement extraction → implementation strategy development
- **Workflow Generation**: Task decomposition → dependency mapping → structured implementation planning
- **Multi-Domain Coordination**: Cross-functional expertise → comprehensive implementation strategies
- **Quality Integration**: Workflow validation → testing strategies → deployment planning

## Examples

### Systematic PRD Workflow
```
/sc:workflow docs/PRD/feature-spec.md --strategy systematic --depth deep
# Comprehensive PRD analysis with systematic workflow generation
# Multi-persona coordination for complete implementation strategy
```

### Agile Feature Workflow
```
/sc:workflow "user authentication system" --strategy agile --parallel
# Agile workflow generation with parallel task coordination
# library docs and UI patterns for framework and UI workflow patterns
```

### Enterprise Implementation Planning
```
/sc:workflow enterprise-prd.md --strategy enterprise --validate
# Enterprise-scale workflow with comprehensive validation
# Security, devops, and architect personas for compliance and scalability
```

### Cross-Session Workflow Management
```
/sc:workflow project-brief.md --depth normal
# session checkpoints manages cross-session workflow context and persistence
# Progressive workflow enhancement with memory-driven insights
```

## Boundaries

**Will:**
- Generate comprehensive implementation workflows from PRD and feature specifications
- Coordinate multiple personas and tools for complete implementation strategies
- Provide cross-session workflow management and progressive enhancement capabilities

**Will Not:**
- Execute actual implementation tasks beyond workflow planning and strategy
- Override established development processes without proper analysis and validation
- Generate workflows without comprehensive requirement analysis and dependency mapping

## CRITICAL BOUNDARIES

**STOP AFTER PLAN CREATION**

This command produces an IMPLEMENTATION PLAN ONLY - no code execution.

**Explicitly Will NOT**:
- Execute any implementation tasks
- Write or modify code
- Create files (except the workflow plan document)
- Make architectural changes
- Run builds or tests

**Output**: Workflow plan document (`docs/workflows/workflow_*.md`) containing:
- Implementation phases
- Task dependencies
- Execution order
- Checkpoints and validation steps

**Next Step**: After workflow completes, use `/sc:implement` to execute the plan step by step.
