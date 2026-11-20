---
name: confidence-check
description: "Score readiness before coding; proceed only at 90% or above"
license: MIT
metadata:
  author: "Junsang Park (adapted from SuperClaude Framework)"
  version: "1.0.0"
  upstream: "SuperClaude Framework 4.3.0"
  source: "src/superclaude/skills/confidence-check/SKILL.md"
---

# /sc:confidence-check - Confidence Check

## Purpose

Prevents wrong-direction execution by assessing confidence **BEFORE** starting implementation.

**Requirement**: ≥90% confidence to proceed with implementation.

## When to Use

Use this skill BEFORE implementing any task to ensure:
- No duplicate implementations exist
- Architecture compliance verified
- Official documentation reviewed
- Working OSS implementations found
- Root cause properly identified

## Confidence Assessment Criteria

Calculate confidence score (0.0 - 1.0) based on 5 checks:

### 1. No Duplicate Implementations? (25%)

**Check**: Search codebase for existing functionality

Use `search_files` to find similar functions, and `search_files` with `target='files'` to find related modules.

✅ Pass if no duplicates found
❌ Fail if similar implementation exists

### 2. Architecture Compliance? (25%)

**Check**: Verify tech stack alignment

- Read the project context file (`.hermes.md`, `AGENTS.md`, or `CLAUDE.md`) and `PLANNING.md` if present
- Confirm existing patterns used
- Avoid reinventing existing solutions

✅ Pass if uses existing tech stack (e.g., Supabase, UV, pytest)
❌ Fail if introduces new dependencies unnecessarily

### 3. Official Documentation Verified? (20%)

**Check**: Review official docs before implementation

- Use `mcp_context7_*` for official docs when connected
- Use `web_extract` for documentation URLs
- Verify API compatibility

✅ Pass if official docs reviewed
❌ Fail if relying on assumptions

### 4. Working OSS Implementations Referenced? (15%)

**Check**: Find proven implementations

- Use `web_search`, or `mcp_tavily_*` when connected
- Search GitHub for examples
- Verify working code samples

✅ Pass if OSS reference found
❌ Fail if no working examples

### 5. Root Cause Identified? (15%)

**Check**: Understand the actual problem

- Analyze error messages
- Check logs and stack traces
- Identify underlying issue

✅ Pass if root cause clear
❌ Fail if symptoms unclear

## Confidence Score Calculation

```
Total = Check1 (25%) + Check2 (25%) + Check3 (20%) + Check4 (15%) + Check5 (15%)

If Total >= 0.90:  ✅ Proceed with implementation
If Total >= 0.70:  ⚠️  Present alternatives, ask questions
If Total < 0.70:   ❌ STOP - Request more context
```

## Output Format

```
📋 Confidence Checks:
   ✅ No duplicate implementations found
   ✅ Uses existing tech stack
   ✅ Official documentation verified
   ✅ Working OSS implementation found
   ✅ Root cause identified

📊 Confidence: 1.00 (100%)
✅ High confidence - Proceeding to implementation
```

## ROI

**Token Savings**: Spend 100-200 tokens on confidence check to save 5,000-50,000 tokens on wrong-direction work.
