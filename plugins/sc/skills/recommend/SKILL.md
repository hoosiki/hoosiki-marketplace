---
name: recommend
description: "Recommend the right /sc:* skill and flags for a request"
license: MIT
metadata:
  author: "Junsang Park (adapted from SuperClaude Framework)"
  version: "1.0.0"
  upstream: "SuperClaude Framework 4.3.0"
  source: "src/superclaude/commands/recommend.md"
---

# /sc:recommend - Command Recommender

Recommends the most suitable `/sc:*` skills and flags for any request. It only recommends; it does not run them.

## When to Use
- The user asks which `/sc:*` skill or flags fit a request
- The user describes a goal without knowing where to start
- The user asks for alternatives, an estimate, or the next step

## Usage

```bash
/sc:recommend [user request] --options [flags]
```

## Language

Detect the request's language and answer in it. Match keywords by meaning, in any language. Skill names and flags stay as written.

```bash
/sc:recommend "I want to build ML algorithm"
/sc:recommend "my website is slow, help me optimize"
/sc:recommend "사이트가 느려요, 어떻게 해야 하나요?"
/sc:recommend "새 기능을 추가해야 해요"
```

## Reading Recommendations

Flags such as `--seq`, `--c7`, and `--persona-frontend` are explained in `/sc:help`. Only recommend skills that `/sc:sc` lists.

## Recommendation Engine

### 1. Keyword Extraction and Persona Matching
```yaml
keyword_extraction:
  pattern_matching:
    # Machine Learning
    - "machine learning|ml|ai|artificial intelligence" → ml_category + --persona-analyzer
    - "data|database|sql" → data_category + --persona-backend
    - "model|algorithm|prediction|classify" → ml_category + --persona-architect

    # Web Development
    - "website|frontend|ui/ux" → web_category + --persona-frontend
    - "react|vue|angular|component" → web_category + --persona-frontend
    - "api|backend|server|microservice" → api_category + --persona-backend

    # Debugging & Performance
    - "error|bug|issue|not working" → debug_category + --persona-analyzer
    - "slow|performance|optimization" → performance_category + --persona-performance
    - "security|auth|vulnerability" → security_category + --persona-security

    # Development
    - "new|create|build|develop|feature" → create_category + --persona-frontend|backend
    - "design|architecture" → design_category + --persona-architect
    - "test|qa|quality|validation" → test_category + --persona-qa

    # Learning
    - "how|learn|explain|tutorial" → learning_category + --persona-mentor
    - "refactor|cleanup|improve|quality" → improve_category + --persona-refactorer

  context_analysis:
    - "beginner|starter|just started" → beginner_level + --persona-mentor
    - "expert|senior|experienced" → expert_level + --persona-architect
    - "continue|resume" → continuity_mode + --seq
    - "next step|what now" → next_step_mode + --think
```

### 2. Command Map
```yaml
category_mapping:
  ml_category:
    primary_commands: ["/sc:analyze --seq --c7", "/sc:design --seq --ultrathink"]
    secondary_commands: ["/sc:build --feature --tdd", "/sc:improve --performance"]
    tool_flags: ["--c7", "--seq"]
    personas: ["--persona-analyzer", "--persona-architect"]
    flags: ["--think-hard", "--evidence", "--profile"]

  web_category:
    primary_commands: ["/sc:build --feature", "/sc:design --api --seq"]
    secondary_commands: ["/sc:test --coverage --e2e --play", "/sc:analyze --code"]
    tool_flags: ["--c7", "--play"]
    personas: ["--persona-frontend", "--persona-qa"]
    flags: ["--react", "--tdd", "--validate"]

  api_category:
    primary_commands: ["/sc:design --api --ddd --seq", "/sc:build --feature --tdd"]
    secondary_commands: ["/sc:analyze --focus security --owasp", "/sc:analyze --performance --play"]
    tool_flags: ["--seq", "--c7", "--play"]
    personas: ["--persona-backend", "--persona-security"]
    flags: ["--microservices", "--ultrathink", "--security"]

  debug_category:
    primary_commands: ["/sc:troubleshoot --investigate --seq", "/sc:analyze --code --seq"]
    secondary_commands: ["/sc:analyze --focus security", "/sc:improve --quality"]
    tool_flags: ["--seq", "--all-mcp"]
    personas: ["--persona-analyzer", "--persona-security"]
    flags: ["--evidence", "--think-hard", "--profile"]

  performance_category:
    primary_commands: ["/sc:analyze --performance --play --profile", "/sc:troubleshoot --seq"]
    secondary_commands: ["/sc:improve --performance --iterate", "/sc:build --optimize"]
    tool_flags: ["--play", "--seq"]
    personas: ["--persona-performance", "--persona-analyzer"]
    flags: ["--profile", "--monitoring", "--benchmark"]

  security_category:
    primary_commands: ["/sc:analyze --focus security --owasp --deps", "/sc:analyze --security --seq"]
    secondary_commands: ["/sc:improve --security --harden", "/sc:troubleshoot --investigate"]
    tool_flags: ["--seq"]
    personas: ["--persona-security", "--persona-analyzer"]
    flags: ["--strict", "--validate", "--owasp"]

  create_category:
    primary_commands: ["/sc:build --feature --tdd", "/sc:design --seq --ultrathink"]
    secondary_commands: ["/sc:analyze --code --c7", "/sc:test --coverage --e2e"]
    tool_flags: ["--c7", "--play"]
    personas: ["--persona-frontend", "--persona-backend", "--persona-architect"]
    flags: ["--interactive", "--plan", "--think"]

  test_category:
    primary_commands: ["/sc:test --coverage --e2e --play", "/sc:analyze --validate"]
    secondary_commands: ["/sc:improve --quality", "/sc:troubleshoot --investigate"]
    tool_flags: ["--play"]
    personas: ["--persona-qa", "--persona-performance"]
    flags: ["--validate", "--coverage", "--monitoring"]

  improve_category:
    primary_commands: ["/sc:improve --quality --iterate", "/sc:cleanup --code --all"]
    secondary_commands: ["/sc:analyze --code --seq", "/sc:improve --quality"]
    tool_flags: ["--seq"]
    personas: ["--persona-refactorer", "--persona-mentor"]
    flags: ["--threshold", "--iterate", "--profile"]

  learning_category:
    primary_commands: ["/sc:document --user --examples", "/sc:analyze --code --c7"]
    secondary_commands: ["/sc:brainstorm --interactive", "/sc:help --specific"]
    tool_flags: ["--c7"]
    personas: ["--persona-mentor", "--persona-analyzer"]
    flags: ["--examples", "--visual", "--interactive"]
```

### 3. Expertise Level Detection and Customization
```yaml
expertise_levels:
  beginner:
    style: "detailed, step-by-step, explanatory"
    recommended_commands: ["/sc:brainstorm --educational", "/sc:help --interactive"]
    extra_explanations: true
    step_by_step: true

  intermediate:
    style: "balanced, technical but understandable"
    recommended_commands: ["/sc:implement --guided", "/sc:design --template"]
    some_explanations: true

  expert:
    style: "fast, technical, direct"
    recommended_commands: ["/sc:implement --advanced", "/sc:analyze --deep"]
    minimal_explanations: true
```

## Intelligent Recommendation Format

```yaml
standard_response_format:
  header:
    - 🎯 Project analysis
    - 🌍 Request language
    - 📊 Level determination

  main_recommendations:
    - ✅ Main recommendations (3 commands)
    - 💡 Additional recommendations (optional)
    - 🚀 Quick start (if available)

  enhanced_features:
    - 🔧 Smart flag recommendations
    - 📊 Time/Budget estimation
    - 🎯 Success metrics
    - 📚 Learning resources
```

## 🚀 HOW TO USE?

```bash
/sc:recommend "I want to do something"
/sc:recommend "new React project" --estimate --alternatives
/sc:recommend --stream "I'm developing my e-commerce site"
/sc:recommend "I want to learn React" --expertise beginner
/sc:recommend "blog site" --community
```

## References

Load these with `skill_view` only when needed:

- `references/examples.md`: worked recommendations for each kind of request
- `references/modes.md`: project detection, `--stream`, `--alternatives`, `--estimate`, smart flags, and `--community` workflow patterns
