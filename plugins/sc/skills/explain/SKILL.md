---
name: explain
description: "Explain code, concepts, or system behavior step by step"
license: MIT
metadata:
  author: "Junsang Park (adapted from SuperClaude Framework)"
  version: "1.0.0"
  upstream: "SuperClaude Framework 4.3.0"
  source: "src/superclaude/commands/explain.md"
---

# /sc:explain - Code and Concept Explanation

## When to Use
- Code understanding and documentation requests for complex functionality
- System behavior explanation needs for architectural components
- Educational content generation for knowledge transfer
- Framework-specific concept clarification requirements

## Usage
```
/sc:explain [target] [--level basic|intermediate|advanced] [--format text|examples|interactive] [--context domain]
```

## Behavioral Flow
1. **Analyze**: Examine target code, concept, or system for comprehensive understanding
2. **Assess**: Determine audience level and appropriate explanation depth and format
3. **Structure**: Plan explanation sequence with progressive complexity and logical flow
4. **Generate**: Create clear explanations with examples, diagrams, and interactive elements
5. **Validate**: Verify explanation accuracy and educational effectiveness

Key behaviors:
- Multi-persona coordination for domain expertise (educator, architect, security)
- Framework-specific explanations via library docs
- Systematic analysis via numbered reasoning for complex concept breakdown
- Adaptive explanation depth based on audience and complexity

## Tool Integration
- **Numbered reasoning (no tool needed)**: Auto-activated for complex multi-component analysis and structured reasoning
- **Library docs (`mcp_context7_*`)**: Framework documentation and official pattern explanations
- **Persona Coordination**: Educator (learning), Architect (systems), Security (practices)
- **Availability**: `mcp_*` tools exist only when that server is connected in this profile. If one is missing, use `web_search` and `web_extract` for docs and native tools otherwise, and say so in your report.
- **Roles** (educator, architect, security): Hermes has no preinstalled subagents for these. Take the role yourself, or name it in the `context` of a `delegate_task` task.

## Tool Coordination
- **`read_file`, `search_files`**: Code analysis and pattern identification for explanation content
- **`todo_list`**: Progress tracking for complex multi-part explanations
- **`delegate_task`**: Delegation for comprehensive explanation workflows requiring systematic breakdown

## Key Patterns
- **Progressive Learning**: Basic concepts → intermediate details → advanced implementation
- **Framework Integration**: Library documentation → accurate official patterns and practices
- **Multi-Domain Analysis**: Technical accuracy + educational clarity + security awareness
- **Interactive Explanation**: Static content → examples → interactive exploration

## Examples

### Basic Code Explanation
```
/sc:explain authentication.js --level basic
# Clear explanation with practical examples for beginners
# Educator persona provides learning-optimized structure
```

### Framework Concept Explanation
```
/sc:explain react-hooks --level intermediate --context react
# library docs for official React documentation patterns
# Structured explanation with progressive complexity
```

### System Architecture Explanation
```
/sc:explain microservices-system --level advanced --format interactive
# Architect persona explains system design and patterns
# Interactive exploration with a numbered analysis breakdown
```

### Security Concept Explanation
```
/sc:explain jwt-authentication --context security --level basic
# Security persona explains authentication concepts and best practices
# Framework-agnostic security principles with practical examples
```

## Boundaries

**Will:**
- Provide clear, comprehensive explanations with educational clarity
- Auto-activate relevant personas for domain expertise and accurate analysis
- Generate framework-specific explanations with official documentation integration

**Will Not:**
- Generate explanations without thorough analysis and accuracy verification
- Override project-specific documentation standards or reveal sensitive details
- Bypass established explanation validation or educational quality requirements
