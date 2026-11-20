---
name: brainstorm-mode
description: "Explore options in Socratic dialogue, then recommend one"
license: MIT
metadata:
  author: "Junsang Park (adapted from SuperClaude Framework)"
  version: "1.0.0"
  upstream: "SuperClaude Framework 4.3.0"
  source: "plugins/superclaude/skills/brainstorm/SKILL.md"
---

# Brainstorming Mode

## When to Use
- The request is vague or exploratory
- The user wants options compared before choosing

Use Socratic dialogue to explore ideas.

## Approach

1. **Ask, Don't Assume**: Use probing questions to uncover requirements
2. **Diverge First**: Generate multiple options before narrowing
3. **Build on Ideas**: Use "Yes, and..." thinking
4. **Visualize**: Use tables, lists, and comparisons
5. **Converge**: Help the user pick the best approach

## Socratic Questions

- "What problem are you trying to solve?"
- "Who are the users? What do they need?"
- "What constraints do we have? (time, budget, tech stack)"
- "What does success look like?"
- "What are the risks if we don't do this?"

## Output Format

Present ideas as structured options:

```
## Option A: [Name]
- Pros: [...]
- Cons: [...]
- Effort: [Low/Medium/High]
- Risk: [Low/Medium/High]

## Option B: [Name]
...

## Recommendation
[Which option and why]
```

Apply this to the instruction given with the skill, or to the current task if there is none.
