---
name: improve
description: "Refactor code for quality, performance, maintainability"
license: MIT
metadata:
  author: "Junsang Park (adapted from SuperClaude Framework)"
  version: "1.0.0"
  upstream: "SuperClaude Framework 4.3.0"
  source: "src/superclaude/commands/improve.md"
---

# /sc:improve - Code Improvement

## When to Use
- Code quality enhancement and refactoring requests
- Performance optimization and bottleneck resolution needs
- Maintainability improvements and technical debt reduction
- Best practices application and coding standards enforcement

## Usage
```
/sc:improve [target] [--type quality|performance|maintainability|style] [--safe] [--interactive]
```

## Behavioral Flow
1. **Analyze**: Examine codebase for improvement opportunities and quality issues
2. **Plan**: Choose improvement approach and activate relevant personas for expertise
3. **Execute**: Apply systematic improvements with domain-specific best practices
4. **Validate**: Ensure improvements preserve functionality and meet quality standards
5. **Document**: Generate improvement summary and recommendations for future work

Key behaviors:
- Multi-persona coordination (architect, performance, quality, security) based on improvement type
- Framework-specific optimization via library docs for best practices
- Systematic analysis via numbered reasoning for complex multi-component improvements
- Safe refactoring with comprehensive validation and rollback capabilities

## Tool Integration
- **Numbered reasoning (no tool needed)**: Auto-activated for complex multi-step improvement analysis and planning
- **Library docs (`mcp_context7_*`)**: Framework-specific best practices and optimization patterns
- **Persona Coordination**: Architect (structure), Performance (speed), Quality (maintainability), Security (safety)
- **Availability**: `mcp_*` tools exist only when that server is connected in this profile. If one is missing, use `web_search` and `web_extract` for docs and native tools otherwise, and say so in your report.
- **Roles** (architect, performance, quality, security): Hermes has no preinstalled subagents for these. Take the role yourself, or name it in the `context` of a `delegate_task` task.

## Tool Coordination
- **`read_file`, `search_files`**: Code analysis and improvement opportunity identification
- **`patch`**: Safe code modification and systematic refactoring
- **`todo_list`**: Progress tracking for complex multi-file improvement operations
- **`delegate_task`**: Delegation for large-scale improvement workflows requiring systematic coordination

## Key Patterns
- **Quality Improvement**: Code analysis → technical debt identification → refactoring application
- **Performance Optimization**: Profiling analysis → bottleneck identification → optimization implementation
- **Maintainability Enhancement**: Structure analysis → complexity reduction → documentation improvement
- **Security Hardening**: Vulnerability analysis → security pattern application → validation verification

## Examples

### Code Quality Enhancement
```
/sc:improve src/ --type quality --safe
# Systematic quality analysis with safe refactoring application
# Improves code structure, reduces technical debt, enhances readability
```

### Performance Optimization
```
/sc:improve api-endpoints --type performance --interactive
# Performance persona analyzes bottlenecks and optimization opportunities
# Interactive guidance for complex performance improvement decisions
```

### Maintainability Improvements
```
/sc:improve legacy-modules --type maintainability --preview
# Architect persona analyzes structure and suggests maintainability improvements
# Preview mode shows changes before application for review
```

### Security Hardening
```
/sc:improve auth-service --type security --validate
# Security persona identifies vulnerabilities and applies security patterns
# Comprehensive validation ensures security improvements are effective
```

## Boundaries

**Will:**
- Apply systematic improvements with domain-specific expertise and validation
- Provide comprehensive analysis with multi-persona coordination and best practices
- Execute safe refactoring with rollback capabilities and quality preservation

**Will Not:**
- Apply risky improvements without proper analysis and user confirmation
- Make architectural changes without understanding full system impact
- Override established coding standards or project-specific conventions

## AUTO-FIX VS APPROVAL-REQUIRED

**Auto-fix (applies automatically)**:
- Style fixes (formatting, naming conventions)
- Unused variable removal
- Import organization
- Simple type annotations

**Approval Required (prompts user first)**:
- Architectural changes
- Logic refactoring
- Function signature changes
- Removing code used by public APIs
- Changes affecting multiple files

**Explicitly Will NOT** (without `--force` flag):
- Make architectural decisions
- Refactor code structure without confirmation
- Remove functionality
