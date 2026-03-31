---
name: fix-mermaid
description: >
  Fix Mermaid diagram syntax errors in Markdown files. Use this skill whenever the user reports
  Mermaid rendering failures ("Syntax error in text mermaid version ..."), broken diagrams,
  or asks to validate/fix/debug Mermaid code blocks. Also use when the user pastes Mermaid code
  that won't render, mentions mermaid syntax issues, or wants to check mermaid code before publishing.
  Covers: reserved word conflicts, Unicode/Langium parser issues, message escaping, and general syntax.
  Includes a bundled Python script for automated detection and fixing.
  Triggers on: "mermaid error", "mermaid fix", "mermaid 수정", "mermaid 오류", "다이어그램 깨짐",
  "mermaid syntax", "mermaid 렌더링", "diagram broken", "mermaid validation", "mermaid lint",
  "mermaid 예약어", "mermaid reserved word".
---

# Fix Mermaid — Mermaid Diagram Linter & Auto-Fixer

Scan Markdown files for ` ```mermaid ` code blocks, diagnose syntax errors against
Mermaid v11.x Langium parser rules, and apply corrections in place.

## When to Use

- User reports "Syntax error in text mermaid version X.X.X"
- Mermaid diagrams fail to render in GitHub, Obsidian, MkDocs, or any Markdown viewer
- User wants to validate Mermaid code before committing
- User pastes Mermaid code and asks why it doesn't work

## Quick Fix (Bundled Script)

For automated detection and fixing, run the bundled script:

```bash
# Lint only (report issues without changing the file)
python scripts/fix_mermaid.py <file_or_dir>

# Auto-fix in place
python scripts/fix_mermaid.py <file_or_dir> --fix

# JSON output for programmatic use
python scripts/fix_mermaid.py <file_or_dir> --json
```

The script handles reserved words, Unicode, and message escaping automatically.
Use this for bulk processing or CI integration. For nuanced issues (diagram type
errors, arrow syntax, structural problems), follow the manual workflow below.

## Manual Workflow

### Step 1 — Locate Mermaid Blocks

Read the target Markdown file and extract every fenced code block tagged as `mermaid`.
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
8. **Sequence diagram reserved words** — Participant IDs that collide with Mermaid
   keywords cause silent rendering failures. The parser interprets the ID as a
   syntax keyword instead of a participant reference.

   | Reserved Word | Mermaid Meaning | Safe Rename |
   |---------------|-----------------|-------------|
   | `opt` | optional fragment | `OPTA` |
   | `alt` | alternative paths | `ALTR` |
   | `par` | parallel execution | `PRSR` |
   | `loop` | loop block | `LOOPN` |
   | `rect` | highlight region | `RCTL` |
   | `note` | note annotation | `NOTEB` |
   | `end` | block terminator | `ENDP` |
   | `and` | parallel separator | `ANDN` |
   | `else` | alt separator | `ELSN` |
   | `break` | break block | `BRKN` |
   | `critical` | critical section | `CRIT` |
   | `activate` | activation bar | `ACTV` |
   | `deactivate` | deactivation bar | `DEACTV` |

   Common dangerous abbreviations: `OPT` (Optuna/Optimizer), `ALT` (Alternative),
   `PAR` (Parser), `END` (Endpoint). Comparison is **case-insensitive**.

   **Fix**: Rename the participant ID and update all references in the block.
   The `participant ... as ...` alias (display name) can stay unchanged.

   ```
   %% WRONG — OPT is a reserved word
   participant OPT as Optuna
   CEL->>OPT: create_study

   %% CORRECT
   participant OPTA as Optuna
   CEL->>OPTA: create_study
   ```

9. **Unicode / invisible characters (Langium parser)** — The v11 Langium parser
   cannot handle many Unicode symbols. Scan every line for:
   - **Invisible chars**: zero-width space (U+200B), BOM (U+FEFF), non-breaking space (U+00A0) → **delete or replace with ASCII space**.
   - **Smart quotes**: `"` `"` `'` `'` → replace with ASCII `"` `'`.
   - **Typographic dashes**: em dash `—`, en dash `–` → replace with `--` or `-`.
   - **Fullwidth CJK punctuation**: `（` `）` `【` `】` `：` `；` → replace with ASCII equivalents.
   - **Unicode arrows/symbols**: `→` `←` `⇒` `…` → replace with Mermaid syntax or `...`.
   See `references/mermaid-v11-syntax.md` section 16 for the full replacement table.

10. **Special characters in sequence diagram messages** — Characters `{`, `}`, `[`, `]`, `"`
    in message text (after `:` in arrows) and Note text cause parser failures.
    Replace with Mermaid entity syntax: `#123;` `#125;` `#91;` `#93;` `#34;`.

**Warning checks (may cause rendering issues):**

11. **Deprecated `graph` keyword** — `graph` works but `flowchart` is recommended.
12. **HTML in labels** — Use `<br/>` not `<br>` for line breaks inside labels.
13. **Semicolons at line end** — Remove trailing `;`.
14. **Duplicate node IDs** — Same ID with different label shapes causes conflicts.

### Step 3 — Fix and Report

For each issue found:
1. Apply the fix directly in the Mermaid code block
2. Record what was changed (line number, before → after, rule)

Present a summary table after all fixes:

```
| Block # | Line | Rule           | Before              | After                |
|---------|------|----------------|----------------------|----------------------|
| 1       | 15   | special-char   | A[입력(값)]          | A["입력(값)"]        |
| 1       | 18   | reserved-word  | participant OPT as X | participant OPTA as X|
| 2       | 42   | message-escape | V-->>C: 200 OK {id}  | V-->>C: 200 OK #123;id#125; |
| 3       | 55   | smart-quote    | A["Label"]           | A["Label"]           |
```

### Step 4 — Validate (optional)

If the user wants extra confidence:
- Run `python scripts/fix_mermaid.py <file> --json` to verify zero issues remain
- Test at Mermaid Live Editor (mermaid.live)
- Or render locally with `npx @mermaid-js/mermaid-cli mmdc -i file.md`

## Key Principles

- **Fix conservatively**: Only change what's broken. Don't rewrite working diagrams.
- **Preserve intent**: The diagram's meaning and structure must not change.
- **Quote liberally**: When in doubt, wrap labels in double quotes — it never hurts.
- **Report clearly**: The user should understand exactly what changed and why.
- **Script first, manual second**: Use `scripts/fix_mermaid.py --fix` for bulk automated
  fixes (reserved words, Unicode, entity escaping), then manually review remaining issues
  (diagram type, arrows, structural problems).

## Reference

- `references/mermaid-v11-syntax.md` — Full syntax rule set with examples for each diagram type,
  Unicode replacement tables, reserved word documentation, and entity escaping guide.
- `scripts/fix_mermaid.py` — Bundled linter/fixer script (reserved words + Unicode + entity escaping).
