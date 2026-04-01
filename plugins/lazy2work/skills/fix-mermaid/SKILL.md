---
name: fix-mermaid
description: >
  Fix Mermaid diagram syntax errors in Markdown files. Use this skill whenever the user reports
  Mermaid rendering failures ("Syntax error in text mermaid version ..."), broken diagrams,
  or asks to validate/fix/debug Mermaid code blocks. Also use when the user pastes Mermaid code
  that won't render, mentions mermaid syntax issues, or wants to check mermaid code before publishing.
  Triggers on: "mermaid error", "mermaid fix", "mermaid 수정", "mermaid 오류", "다이어그램 깨짐",
  "mermaid syntax", "mermaid 렌더링", "diagram broken", "mermaid validation".
---

# Fix Mermaid — Mermaid Diagram Syntax Fixer

Scan Markdown files for ` ```mermaid ` code blocks, diagnose syntax errors against
Mermaid v11.x rules, and apply corrections in place.

## When to Use

- User reports "Syntax error in text mermaid version X.X.X"
- Mermaid diagrams fail to render in GitHub, Obsidian, MkDocs, or any Markdown viewer
- User wants to validate Mermaid code before committing
- User pastes Mermaid code and asks why it doesn't work

## Workflow

### Step 1 — Locate Mermaid Blocks

Read the target Markdown file and extract every fenced code block tagged as `mermaid`:

````
```mermaid
<diagram code>
```
````

Report how many blocks were found and their line numbers.

### Step 2 — Diagnose Each Block

For each block, check the issues listed below **in order** (earlier rules catch more errors).
Read `references/mermaid-v11-syntax.md` for the full rule set and examples.

**Critical checks (cause immediate parse failure):**

1. **Diagram type declaration** — First non-comment line must be a valid type
   (`flowchart`, `sequenceDiagram`, `classDiagram`, `stateDiagram-v2`,
   `erDiagram`, `gantt`, `pie`, `gitgraph`, `mindmap`, `timeline`, `block-beta`, etc.)
2. **Direction keyword** — `flowchart` requires a direction (`TD`, `TB`, `LR`, `RL`, `BT`).
   `graph` also requires one.
3. **Special characters in node labels** — Characters like `(`, `)`, `[`, `]`, `{`, `}`,
   `<`, `>`, `|`, `:`, `;`, `#`, `&`, `"`, `'` inside labels must be wrapped in double quotes.
   Korean and other Unicode text in labels should also be quoted.
4. **Arrow syntax** — Validate per diagram type:
   - Flowchart: `-->`, `---`, `-.->`, `==>`, `--text-->`, `-->|text|`
   - Sequence: `->>`, `-->>`, `-)`, `--)`, `-x`, `--x`
   - Class: `<|--`, `*--`, `o--`, `..>`, `..|>`
   - ER: `||--o{`, `}|..|{`, etc.
   - State: `-->`
5. **Subgraph / end conflicts** — If a node ID or label contains the word `end`,
   Mermaid may misinterpret it as closing a subgraph. Wrap in quotes or rename.
6. **Unclosed subgraph/block** — Every `subgraph` needs a matching `end`.
7. **Empty nodes or edges** — Nodes with no ID or edges with missing endpoints.
8. **Unicode / invisible characters (Langium parser)** — The v11 Langium parser
   cannot handle many Unicode symbols. Scan every line for:
   - **Invisible chars**: zero-width space (U+200B), BOM (U+FEFF), non-breaking space (U+00A0),
     zero-width joiner/non-joiner (U+200D/U+200C) → **delete or replace with ASCII space**.
   - **Smart quotes**: `"` `"` `'` `'` → replace with `"` `'`.
   - **Typographic dashes**: em dash `—`, en dash `–` → replace with `--` or `-`.
   - **Unicode arrows/symbols**: `→` `←` `⇒` `↔` → replace with Mermaid arrow syntax or text.
   - **Fullwidth CJK punctuation**: `（` `）` `【` `】` `：` `；` → replace with ASCII equivalents.
   - **Ellipsis**: `…` (U+2026) → replace with `...`.
   - **Mathematical symbols**: `×` `÷` `±` `≤` `≥` `≠` → spell out or use entity (`#215;` etc.).
   See `references/mermaid-v11-syntax.md` section 16 for the full replacement table.
9. **Special characters in sequence diagram messages** — Characters `{`, `}`, `[`, `]`, `"`
   in message text (after `:` in arrows) and Note text cause parser failures.
   Replace with Mermaid entity syntax: `#123;` `#125;` `#91;` `#93;` `#34;`.

**Warning checks (may cause rendering issues):**

10. **Deprecated `graph` keyword** — `graph` works but `flowchart` is recommended
    for new diagrams (better feature support).
11. **HTML in labels** — Use `<br/>` not `<br>` for line breaks inside labels.
12. **Semicolons at line end** — Remove trailing `;` (unnecessary and sometimes problematic).
13. **Indentation inside subgraphs** — Not required but improves readability.
14. **Duplicate node IDs** — Same ID with different label shapes causes conflicts.

### Step 3 — Fix and Report

For each issue found:

1. Apply the fix directly in the Mermaid code block
2. Record what was changed (line number, before → after, rule number)

After all fixes, write the corrected file and present a summary table:

```
| Block # | Line | Rule | Before | After |
|---------|------|------|--------|-------|
| 1       | 15   | 3    | A[입력(값)] | A["입력(값)"] |
| 1       | 18   | 5    | end_node --> B | end_node["end_node"] --> B |
```

If no issues are found, confirm the Mermaid code is valid.

### Step 4 — Validate (optional)

If the user wants extra confidence, suggest testing the fixed code at:
- Mermaid Live Editor (mermaid.live)
- Or rendering locally with `npx @mermaid-js/mermaid-cli mmdc -i file.md`

## Key Principles

- **Fix conservatively**: Only change what's broken. Don't rewrite working diagrams.
- **Preserve intent**: The diagram's meaning and structure must not change.
- **Quote liberally**: When in doubt, wrap labels in double quotes — it never hurts.
- **Report clearly**: The user should understand exactly what changed and why.

## Edge Cases

- **Multiple diagram types in one file**: Check each block independently.
- **Nested quotes**: Use single quotes inside double-quoted labels, or use HTML entities (`&quot;`).
- **Very long labels**: Keep them quoted; don't split into multiple nodes unless asked.
- **Code blocks inside labels**: Not supported by Mermaid; suggest alternatives.

## Reference

For the complete syntax rule set with examples for each diagram type,
read `references/mermaid-v11-syntax.md`.
