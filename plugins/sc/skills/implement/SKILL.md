---
name: implement
description: "Implement a feature with docs lookup, tests, and role focus"
license: MIT
metadata:
  author: "Junsang Park (adapted from SuperClaude Framework)"
  version: "1.0.0"
  upstream: "SuperClaude Framework 4.3.0"
  source: "src/superclaude/commands/implement.md"
---

# /sc:implement - Feature Implementation

## When to Use
- Feature development requests for components, APIs, or complete functionality
- Code implementation needs with framework-specific requirements
- Multi-domain development requiring coordinated expertise
- Implementation projects requiring testing and validation integration

## Usage
```
/sc:implement [feature-description] [--type component|api|service|feature] [--framework react|vue|express] [--safe] [--with-tests]
```

## Behavioral Flow
1. **Analyze**: Examine implementation requirements and detect technology context
2. **Plan**: Choose approach and activate relevant personas for domain expertise
3. **Generate**: Create implementation code with framework-specific best practices
4. **Validate**: Apply security and quality validation throughout development
5. **Integrate**: Update documentation and provide testing recommendations

Key behaviors:
- Context-based persona activation (architect, frontend, backend, security, qa)
- Framework-specific implementation via library docs and UI patterns integration
- Systematic multi-component coordination via numbered reasoning
- Comprehensive testing integration, using browser tools for validation

## Tool Integration
- **Library docs (`mcp_context7_*`)**: Framework patterns and official documentation for React, Vue, Angular, Express
- **UI code (written directly)**: Auto-activated for UI component generation and design system integration
- **Numbered reasoning (no tool needed)**: Complex multi-step analysis and implementation planning
- **Browser (`browser_exec`, `mcp_chrome_devtools_*`)**: Testing validation and quality assurance integration
- **Availability**: `mcp_*` tools exist only when that server is connected in this profile. If one is missing, use `web_search` and `web_extract` for docs and native tools otherwise, and say so in your report.
- **Roles** (architect, frontend, backend, security, qa-specialist): Hermes has no preinstalled subagents for these. Take the role yourself, or name it in the `context` of a `delegate_task` task.

## Tool Coordination
- **`write_file`, `patch`**: Code generation and modification for implementation
- **`read_file`, `search_files`**: Project analysis and pattern detection for consistency
- **`todo_list`**: Progress tracking for complex multi-file implementations
- **`delegate_task`**: Delegation for large-scale feature development requiring systematic coordination

## Key Patterns
- **Context Detection**: Framework/tech stack → appropriate role and tool choice
- **Implementation Flow**: Requirements → code generation → validation → integration
- **Multi-Persona Coordination**: Frontend + Backend + Security → comprehensive solutions
- **Quality Integration**: Implementation → testing → documentation → validation

## Examples

### React Component Implementation
```
/sc:implement user profile component --type component --framework react
# direct UI code generates UI component with design system integration
# Frontend persona ensures best practices and accessibility
```

### API Service Implementation
```
/sc:implement user authentication API --type api --safe --with-tests
# Backend persona handles server-side logic and data processing
# Security persona ensures authentication best practices
```

### Full-Stack Feature
```
/sc:implement payment processing system --type feature --with-tests
# Multi-persona coordination: architect, frontend, backend, security
# numbered reasoning breaks down complex implementation steps
```

### Framework-Specific Implementation
```
/sc:implement dashboard widget --framework vue
# library docs provides Vue-specific patterns and documentation
# Framework-appropriate implementation with official best practices
```

## Boundaries

**Will:**
- Implement features with intelligent persona activation and tool coordination
- Apply framework-specific best practices and security validation
- Provide comprehensive implementation with testing and documentation integration

**Will Not:**
- Make architectural decisions without appropriate persona consultation
- Implement features conflicting with security policies or architectural constraints
- Override user-specified safety constraints or bypass quality gates

## COMPLETION CRITERIA

**Implementation is DONE when**:
- Feature code is written and compiles
- Basic functionality verified
- Files saved and ready for testing

**Post-Implementation Checklist**:
1. Code compiles without errors
2. Basic functionality works
3. Ready for `/sc:test`

**Next Step**: After implementation, use `/sc:test` to run tests, then `/sc:git` to commit.
