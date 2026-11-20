# /sc:pm Examples

## Default Usage (No Command Needed)
```
# User simply describes what they want
User: "Need to add payment processing to the app"

# PM Agent automatically handles orchestration
PM Agent: Analyzing requirements...
  → Delegating to requirements-analyst for specification
  → Coordinating backend-architect + security-engineer
  → Engaging payment processing implementation
  → Quality validation with testing
  → Documentation update

Output: Complete payment system implementation
```

## Explicit Strategy Selection
```
/sc:pm "Improve application security" --strategy wave

# Wave mode for large-scale security audit
PM Agent: Initiating comprehensive security analysis...
  → Wave 1: Security engineer audits (authentication, authorization)
  → Wave 2: Backend architect reviews (API security, data validation)
  → Wave 3: Quality engineer tests (penetration testing, vulnerability scanning)
  → Wave 4: Documentation (security policies, incident response)

Output: Comprehensive security improvements with documentation
```

## Brainstorming Mode
```
User: "Maybe we could improve the user experience?"

PM Agent: Activating Brainstorming Mode...
  🤔 Discovery Questions:
     - What specific UX challenges are users facing?
     - Which workflows are most problematic?
     - Have you gathered user feedback or analytics?
     - What are your improvement priorities?

  📝 Brief: [Generate structured improvement plan]

Output: Clear UX improvement roadmap with priorities
```

## Manual Sub-Agent Override (Optional)
```
# User can still specify sub-agents directly if desired
/sc:implement "responsive navbar" --agent frontend

# PM Agent delegates to specified agent
PM Agent: Routing to frontend-architect...
  → Frontend specialist handles implementation
  → PM Agent monitors progress and quality gates

Output: Frontend-optimized implementation
```
