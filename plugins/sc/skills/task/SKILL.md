---
name: task
description: "Run a complex multi-step task with tracked delegation"
license: MIT
metadata:
  author: "Junsang Park (adapted from SuperClaude Framework)"
  version: "1.0.0"
  upstream: "SuperClaude Framework 4.3.0"
  source: "src/superclaude/commands/task.md"
---

# /sc:task - Enhanced Task Management

## When to Use
- Complex tasks requiring multi-agent coordination and delegation
- Projects needing structured workflow management and cross-session persistence
- Operations requiring intelligent tool routing and domain expertise
- Tasks benefiting from systematic execution and progressive enhancement

## Usage
```
/sc:task [action] [target] [--strategy systematic|agile|enterprise] [--parallel] [--delegate]
```

## Behavioral Flow
1. **Analyze**: Parse task requirements and determine optimal execution strategy
2. **Delegate**: Route to appropriate tools and activate relevant personas
3. **Coordinate**: Execute tasks with intelligent workflow management and parallel processing
4. **Validate**: Apply quality gates and comprehensive task completion verification
5. **Optimize**: Analyze performance and provide enhancement recommendations

Key behaviors:
- Multi-persona coordination across architect, frontend, backend, security, devops domains
- Intelligent tool routing (see Tool Integration)
- Systematic execution with progressive task enhancement and cross-session persistence
- Advanced task delegation with hierarchical breakdown and dependency management

## Tool Integration
- **Numbered reasoning (no tool needed)**: Complex multi-step task analysis and systematic execution planning
- **Library docs (`mcp_context7_*`)**: Framework-specific patterns and implementation best practices
- **UI code (written directly)**: UI/UX task coordination and design system integration
- **Browser (`browser_exec`, `mcp_chrome_devtools_*`)**: Testing workflow integration and validation automation
- **Bulk edits (`patch`, `execute_code`)**: Large-scale task transformation and pattern-based optimization
- **Project memory (`/sc:save`, `/sc:load`, `session_search`)**: Cross-session task persistence and project memory management
- **Availability**: `mcp_*` tools exist only when that server is connected in this profile. If one is missing, use `web_search` and `web_extract` for docs and native tools otherwise, and say so in your report.
- **Roles** (architect, analyzer, frontend, backend, security, devops, project-manager): Hermes has no preinstalled subagents for these. Take the role yourself, or name it in the `context` of a `delegate_task` task.

## Tool Coordination
- **`todo_list`**: Hierarchical task breakdown and progress tracking across Epic → Story → Task levels
- **`delegate_task`**: Advanced delegation for complex multi-agent coordination and sub-task management
- **`read_file`, `write_file`, `patch`**: Task documentation and implementation coordination
- **Numbered reasoning**: Structured reasoning for complex task dependency analysis

## Key Patterns
- **Task Hierarchy**: Epic-level objectives → Story coordination → Task execution → Subtask granularity
- **Strategy Selection**: Systematic (comprehensive) → Agile (iterative) → Enterprise (governance)
- **Multi-Agent Coordination**: Role selection → tool routing → parallel execution → result integration
- **Cross-Session Management**: Task persistence → context continuity → progressive enhancement

## Examples

### Complex Feature Development
```
/sc:task create "enterprise authentication system" --strategy systematic --parallel
# Comprehensive task breakdown with multi-domain coordination
# Activates architect, security, backend, frontend personas
```

### Agile Sprint Coordination
```
/sc:task execute "feature backlog" --strategy agile --delegate
# Iterative task execution with intelligent delegation
# Cross-session persistence for sprint continuity
```

### Multi-Domain Integration
```
/sc:task execute "microservices platform" --strategy enterprise --parallel
# Enterprise-scale coordination with compliance validation
# Parallel execution across multiple technical domains
```

## Boundaries

**Will:**
- Execute complex tasks with multi-agent coordination and intelligent delegation
- Provide hierarchical task breakdown with cross-session persistence
- Coordinate multiple tools and personas for optimal task outcomes

**Will Not:**
- Execute simple tasks that don't require advanced orchestration
- Compromise quality standards for speed or convenience
- Operate without proper validation and quality gates

## CRITICAL BOUNDARIES

**USER-INVOKED DISCRETE TASK EXECUTION**

This command executes specific tasks when explicitly invoked by user.

**Difference from /sc:pm**:
- `/sc:pm` = session-level orchestration (background monitoring, continuous)
- `/sc:task` = user-invoked discrete execution (explicit start/end)

**Behavior**:
- User invokes `/sc:task [description]`
- Execute the specific task using multi-agent coordination
- **STOP when task is complete** - do not continue to next tasks without user input

**Completion Criteria**:
- Task objective achieved
- All sub-tasks marked completed in `todo_list`
- Validation passed

**Output**: Task completion report with:
- What was accomplished
- Files modified
- Tests status (if applicable)

**Next Step**: User decides next action. May invoke another `/sc:task` or use specific commands.
