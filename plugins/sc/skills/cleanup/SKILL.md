---
name: cleanup
description: "Remove dead code and tidy project structure safely"
license: MIT
metadata:
  author: "Junsang Park (adapted from SuperClaude Framework)"
  version: "1.0.0"
  upstream: "SuperClaude Framework 4.3.0"
  source: "src/superclaude/commands/cleanup.md"
---

# /sc:cleanup - Code and Project Cleanup

## When to Use
- Code maintenance and technical debt reduction requests
- Dead code removal and import optimization needs
- Project structure improvement and organization requirements
- Codebase hygiene and quality improvement initiatives

## Usage
```
/sc:cleanup [target] [--type code|imports|files|all] [--safe|--aggressive] [--interactive]
```

## Behavioral Flow
1. **Analyze**: Assess cleanup opportunities and safety considerations across target scope
2. **Plan**: Choose cleanup approach and activate relevant personas for domain expertise
3. **Execute**: Apply systematic cleanup with intelligent dead code detection and removal
4. **Validate**: Ensure no functionality loss through testing and safety verification
5. **Report**: Generate cleanup summary with recommendations for ongoing maintenance

Key behaviors:
- Multi-persona coordination (architect, quality, security) based on cleanup type
- Framework-specific cleanup patterns via library docs integration
- Systematic analysis via numbered reasoning for complex cleanup operations
- Safety-first approach with backup and rollback capabilities

## Tool Integration
- **Numbered reasoning (no tool needed)**: Auto-activated for complex multi-step cleanup analysis and planning
- **Library docs (`mcp_context7_*`)**: Framework-specific cleanup patterns and best practices
- **Persona Coordination**: Architect (structure), Quality (debt), Security (credentials)
- **Availability**: `mcp_*` tools exist only when that server is connected in this profile. If one is missing, use `web_search` and `web_extract` for docs and native tools otherwise, and say so in your report.
- **Roles** (architect, quality, security): Hermes has no preinstalled subagents for these. Take the role yourself, or name it in the `context` of a `delegate_task` task.

## Tool Coordination
- **`read_file`, `search_files`**: Code analysis and pattern detection for cleanup opportunities
- **`patch`**: Safe code modification and structure optimization
- **`todo_list`**: Progress tracking for complex multi-file cleanup operations
- **`delegate_task`**: Delegation for large-scale cleanup workflows requiring systematic coordination

## Key Patterns
- **Dead Code Detection**: Usage analysis → safe removal with dependency validation
- **Import Optimization**: Dependency analysis → unused import removal and organization
- **Structure Cleanup**: Architectural analysis → file organization and modular improvements
- **Safety Validation**: Pre/during/post checks → preserve functionality throughout cleanup

## Examples

### Safe Code Cleanup
```
/sc:cleanup src/ --type code --safe
# Conservative cleanup with automatic safety validation
# Removes dead code while preserving all functionality
```

### Import Optimization
```
/sc:cleanup --type imports --preview
# Analyzes and shows unused import cleanup without execution
# Framework-aware optimization via library doc patterns
```

### Comprehensive Project Cleanup
```
/sc:cleanup --type all --interactive
# Multi-domain cleanup with user guidance for complex decisions
# Activates all personas for comprehensive analysis
```

### Framework-Specific Cleanup
```
/sc:cleanup components/ --aggressive
# Thorough cleanup with library doc patterns
# Numbered reasoning for complex dependency management
```

## Boundaries

**Will:**
- Systematically clean code, remove dead code, and optimize project structure
- Provide comprehensive safety validation with backup and rollback capabilities
- Apply intelligent cleanup algorithms with framework-specific pattern recognition

**Will Not:**
- Remove code without thorough safety analysis and validation
- Override project-specific cleanup exclusions or architectural constraints
- Apply cleanup operations that compromise functionality or introduce bugs

## AUTO-FIX VS APPROVAL-REQUIRED

**Auto-fix (applies automatically)**:
- Unused imports removal
- Dead code with zero references
- Empty blocks removal
- Redundant type annotations

**Approval Required (prompts user first)**:
- Code with indirect references
- Exports potentially used externally
- Test fixtures/utilities
- Configuration values

**Safety Threshold**:
- If code has ANY usage path, prompt user
- If code affects public API, prompt user
- If unsure, prompt user
