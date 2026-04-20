---
name: fix-mermaid
description: >
  Fix Markdown rendering issues that block pandoc/lualatex PDF generation or
  Mermaid diagram display. Covers:
  (A) Mermaid syntax errors — reserved words, Unicode pitfalls, message escaping,
      "Syntax error in text mermaid version X.X.X", broken diagrams in
      GitHub/Obsidian/MkDocs.
  (B) Pandoc Markdown pitfalls — missing blank lines before lists/tables/fenced
      code blocks (auto-fix) and long table cells mixing bold with special
      symbols that cause LaTeX overfull hbox (warning-only).
  (C) Pandoc table cell overflow — long cells with bold + symbols.
  (D) Unicode glyph missing — characters like U+2212 (MINUS SIGN), U+2717
      (BALLOT X) that CJK fonts lack, causing silent disappearance in PDF
      (auto-fix).
  Triggers on: "mermaid error", "mermaid fix", "mermaid 수정", "mermaid 오류",
  "다이어그램 깨짐", "mermaid syntax", "mermaid 렌더링", "diagram broken",
  "mermaid validation", "pandoc 테이블 깨짐", "pandoc 리스트 렌더링",
  "md pdf 변환 문제", "테이블이 렌더링 안됨", "markdown lint",
  "pandoc blank line", "overfull hbox", "테이블 오버플로",
  "Missing character", "unicode glyph", "글리프 누락", "문자 누락",
  "U+2212", "마이너스 사라짐", "PDF 문자 깨짐".
---

# Fix Mermaid & Pandoc — Markdown Rendering Fixer

Repairs two classes of Markdown problems that break downstream rendering:

1. **Mermaid diagram syntax** — v11.x Langium parser compatibility (reserved
   words, Unicode, message escaping).
2. **Pandoc PDF pitfalls** — blank-line violations before block elements,
   long table cells mixing bold and special symbols that trigger LaTeX
   overfull hbox, and Unicode glyphs missing from CJK fonts that silently
   disappear in PDF output.

Pick the sub-workflow by the user's symptom.

## Decision Tree

| User symptom | Workflow |
|---|---|
| "Mermaid 렌더링 안 됨" / "Syntax error in text" / 다이어그램 깨짐 | **Workflow A — Mermaid** |
| "테이블/리스트가 PDF에서 깨짐" / "섹션이 깨져 보임" / "한 줄로 흐름" | **Workflow B — Pandoc Blanks** |
| "테이블이 페이지 폭 넘음" / "Overfull hbox" / 특정 셀만 밀림 | **Workflow C — Pandoc Cell Overflow** |
| "Missing character" / 문자 누락 / "마이너스 사라짐" / PDF에서 글자 빠짐 | **Workflow D — Unicode Glyph Missing** |
| 여러 증상 / md 파일 전반 정리 | **A + B + C + D 순차** |

---

## Workflow A — Mermaid Diagram Syntax

### Step A1 — Locate Mermaid Blocks

Read the target Markdown file and extract every fenced code block tagged as `mermaid`:

````
```mermaid
<diagram code>
```
````

Report how many blocks were found and their line numbers.

### Step A2 — Diagnose Each Block

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
8. **Unicode / invisible characters (Langium parser)** — Scan every line for:
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

10. **Deprecated `graph` keyword** — `graph` works but `flowchart` is recommended.
11. **HTML in labels** — Use `<br/>` not `<br>` for line breaks.
12. **Semicolons at line end** — Remove trailing `;`.
13. **Indentation inside subgraphs** — Not required but improves readability.
14. **Duplicate node IDs** — Same ID with different label shapes causes conflicts.

### Step A3 — Fix, Report, Validate

Apply fixes directly, record what changed, write the corrected file, and present a summary table.

```bash
# Automate
python3 scripts/fix_mermaid.py path/to/file.md --fix
python3 scripts/fix_mermaid.py docs/ --json
```

### Step A4 — mmdc Validation Loop (`--with-mmdc`)

Static rules catch the common cases, but the Mermaid CLI (`mmdc`) is the
ground truth: if it renders, it renders. This step closes the loop by
**running mmdc on every block, parsing its error output, and feeding the
findings back into the static fixer until the file is clean or no more
automatic fixes can be applied**.

**Prerequisites.** `mmdc` must be on `PATH`:

```bash
npm install -g @mermaid-js/mermaid-cli
mmdc --version   # 11.x or newer
```

**Run.**

```bash
python3 scripts/fix_mermaid.py path/to/file.md --with-mmdc
# or, for machine-readable output:
python3 scripts/fix_mermaid.py path/to/file.md --with-mmdc --json
```

**What happens per iteration (max 3):**

1. `process_file(apply_fix=True)` — runs the static linter (reserved words,
   Unicode, entity escaping). Any edits are written to disk.
2. `validate_file` — extracts every ```` ```mermaid ```` block, writes each
   to a temp file, invokes `mmdc -i tmp.mmd -o tmp.svg -q`, captures stderr.
3. `parse_mmdc_stderr` — matches `Parse error on line N:` and the
   `Expecting ..., got 'X'` line into a structured `MmdcError`.
4. `suggest_fix_for_mmdc_error` — maps the error to a named rule
   (`reserved-word`, `unquoted-label`, …) that the next iteration can act on.
5. If the set of errors is unchanged between iterations, the loop exits
   early — there is nothing left that the fixer knows how to repair, and
   human review is needed.

**Example output.**

```
=== docs/architecture.md ===
  iterations: 2
  static fixes applied: 3
  mmdc errors remaining: 0
  mmdc: all blocks render successfully.
```

Or, when automatic fixes are exhausted:

```
=== docs/broken.md ===
  iterations: 3
  static fixes applied: 1
  mmdc errors remaining: 1
    - block #0 line 14: got 'PS'
  suggestions:
    * unquoted-label: wrap the node label in double quotes — it contains
      unescaped (, ), [, ], {, or }
```

**Error → fix mapping (currently recognised):**

| mmdc signal | Detected rule | Auto-fix path |
|---|---|---|
| `got 'end' / 'opt' / 'alt' / …` expecting `participant` | `reserved-word` | Renames the participant ID via `SAFE_RENAMES` in `fix_mermaid.py` |
| `got 'PS' / 'SQS'` or `Expecting 'SQE', 'PE', …` | `unquoted-label` | Flags the label for manual quoting (the linter does not silently rewrite labels) |
| Any other `Parse error …` | *unknown* | Reported verbatim in the summary; user decides |

New error patterns go in `references/mermaid-v11-syntax.md` § "mmdc Error
Catalog" and in `_FLOWCHART_SHAPE_TOKENS` / `_RESERVED_WORD_TOKENS` in
`fix_mermaid.py`.

Optional shortcut: validation alone, no fixing — `python3
scripts/validate_mermaid.py path/to/file.md`.

---

## Workflow B — Pandoc Blank-Line Compliance

### When to Run

The user reports any of:

- Tables rendering as garbled inline text in PDF
- Bullet/numbered lists appearing on one line with dashes as plain text
- A specific section "looks broken" after PDF conversion
- Code blocks rendering as escaped backtick text

### Root Cause

Pandoc's Markdown parser requires a **blank line before every block element**
(list, pipe table, fenced code block). Without it, the block is silently
treated as an inline continuation of the preceding paragraph. Korean writers
often attach lists directly after `**라벨**:` which triggers this.

See `references/pandoc-pdf-pitfalls.md` § 1 "Missing Blank Line Before
Block Elements" for the full explanation and patterns.

### Step B1 — Lint

```bash
python3 scripts/fix_pandoc_blanks.py path/to/file.md
```

Detection rules (all auto-fixable, severity=error):

| Rule | Trigger |
|---|---|
| `missing-blank-before-list` | Bullet or numbered list item preceded by non-blank non-list text |
| `missing-blank-before-table` | Pipe table row preceded by non-blank non-table text |
| `missing-blank-before-fence` | ` ``` ` or `~~~` fence opener preceded by non-blank text |

Exceptions (no blank needed): heading before, same block continues, indented
nested list, top of file.

### Step B2 — Fix

```bash
python3 scripts/fix_pandoc_blanks.py path/to/file.md --fix
```

The script inserts a single blank line before every offending block. It
**never removes** content and **never touches** content inside fenced code
blocks.

### Step B3 — Verify

```bash
python3 scripts/fix_pandoc_blanks.py path/to/file.md
# → OK: No issues found.

pandoc -d pdf-korean --resource-path=$(dirname path/to/file.md) \
  path/to/file.md --output=path/to/file.pdf
```

---

## Workflow C — Pandoc Table Cell Overflow (Warning)

### When to Run

- LaTeX log shows repeated `Overfull \hbox` warnings
- Specific table rows overflow the page width in the generated PDF
- Tables look broken despite passing Workflow B

### Root Cause

Pandoc converts pipe tables to `longtable` with columns set to
`\linewidth * 0.25` (equal split for 4 columns). Cells mixing:

- `**bold**` markup (interferes with token boundaries)
- Middle dot `·` or em/en dash `—`/`–`
- Parenthetical annotations `(...)`
- Plus/percent signs `+`, `%`

cannot be split by `\sloppy` + `\emergencystretch` + `\seqsplit` alone, so
the row overflows.

**Example (risky)**:

```markdown
| 모델 | 비고 |
|---|---|
| **Fine-tuned Llama-3.1-8B** | 최대 **+40%** (7B·8B에서) — SynthCypher |
```

### Step C1 — Detect

The same script reports `long-mixed-cell` warnings:

```bash
python3 scripts/fix_pandoc_blanks.py path/to/file.md
```

Example output:

```
warning  |   197 | long-mixed-cell                  | **Fine-tuned GPT-4o**
warning  |   198 | long-mixed-cell                  | 최대 **+40%** (7B·8B에서)
```

Detection criteria:

- Cell length ≥ 25 chars
- AND (`**bold**` + risky symbol) OR (≥ 2 risky symbols in the cell)
- Risky symbols: `·`, `—`, `–`, `+`, `(`, `)`

### Step C2 — Remediate (Manual)

**Not auto-fixable** — the resolution requires human judgment. Options in
priority order:

1. **Remove bold** from the cell (move emphasis to caption/footnote).
2. **Shorten the cell** — pull parenthetical annotations into a following
   sentence or bullet list.
3. **Restructure the table** — reduce columns (4 → 3), or convert a wide
   row into a sub-bullet under the table.

First verify the `pdf-korean.yaml` mitigations are already active:
- `\sloppy`
- `\emergencystretch=3em`
- `\seqsplit` wrapper on `\texttt`

If those are present and the warning still appears, the cell content itself
is the root cause — apply one of the options above.

### Step C3 — Re-run

```bash
python3 scripts/fix_pandoc_blanks.py path/to/file.md
# → warnings should be gone (or acknowledged as accepted risk)
```

---

## Workflow D — Unicode Glyph Missing (Auto-fix)

### When to Run

The user reports any of:

- pandoc warning: `Missing character: There is no − (U+2212)` or similar
- Characters (minus, check mark, ballot X) disappear in the PDF
- "마이너스가 사라졌어" / "문자가 빠졌어" / "PDF에서 글자가 깨져"

### Root Cause

LLM-generated text and web copy-paste often introduce Unicode look-alike
characters that are visually identical to ASCII but use different code points.
CJK fonts like Apple SD Gothic Neo lack glyphs for these characters, so
lualatex silently drops them from the PDF.

| Appears as | ASCII (safe) | Unicode (dangerous) |
|---|---|---|
| `-` (minus) | U+002D HYPHEN-MINUS | **U+2212 MINUS SIGN** |
| `X` (ballot) | X | **U+2717 BALLOT X** |
| `X` (heavy ballot) | X | **U+2718 HEAVY BALLOT X** |

Content inside `$...$` math mode is **skipped** — LaTeX math fonts handle
these characters correctly.

See `references/pandoc-pdf-pitfalls.md` § 5 "Unicode Glyph Missing in
CJK Fonts" for the full explanation.

### Step D1 — Lint

```bash
python3 scripts/fix_pandoc_blanks.py path/to/file.md
```

Detection rule (auto-fixable, severity=error):

| Rule | Trigger |
|---|---|
| `unicode-glyph-missing` | Unicode character from the dangerous glyph map found in text (outside math mode and fenced code) |

### Step D2 — Fix

```bash
python3 scripts/fix_pandoc_blanks.py path/to/file.md --fix
```

The script replaces each dangerous Unicode character with its ASCII
equivalent. Math mode (`$...$`, `$$...$$`) and fenced code blocks are
preserved.

### Step D3 — Verify

```bash
python3 scripts/fix_pandoc_blanks.py path/to/file.md
# → OK: No issues found.

pandoc -d pdf-korean path/to/file.md -o output.pdf
# → No "Missing character" warnings
```

### Step D4 — (Opt-in) Latin-1 Supplement romanization

Apple SD Gothic Neo and similar CJK-oriented mainfonts may silently drop
Latin-1 Supplement diacritics (`á`, `é`, `í`, `ó`, `ú`, `ñ`, `ü`, `ß`,
etc.). Symptom: `Román Orús` renders as `Rom□n Or□s` or `Rom Or` in the PDF.

**Opt-in only** — auto-romanization is lossy for proper nouns
(`Román → Roman`). Use only when the trade-off is acceptable or when the
document has no non-ASCII content you want to preserve.

Detection rule (severity=error, only reported when flag is present):

| Rule | Trigger |
|---|---|
| `latin1-supplement-glyph` | Any Latin-1 Supplement diacritic (U+00C0–U+00FF subset) found outside math mode and fenced code |

```bash
# Detect without fixing
python3 scripts/fix_pandoc_blanks.py path/to/file.md --latin1-normalize

# Apply romanization (combine with --fix)
python3 scripts/fix_pandoc_blanks.py path/to/file.md --fix --latin1-normalize
```

Preferred alternative when originals matter: replace the offending
token(s) manually with Korean transliteration plus ASCII romanization,
e.g. `로만 오루스(Roman Orus)`.

---

## Key Principles

- **Fix conservatively**: Only change what's broken.
- **Preserve intent**: Meaning and structure must not change.
- **Quote liberally (Mermaid)**: When in doubt, wrap labels in quotes.
- **Blank-line generously (Pandoc)**: One blank before every block is always safe.
- **Warnings are not errors**: Cell overflow needs human judgment — do not
  auto-strip bold or rewrite cells without confirmation.
- **Report clearly**: The user should understand exactly what changed and why.

## Edge Cases

### Mermaid

- **Multiple diagram types in one file**: Check each block independently.
- **Nested quotes**: Use single quotes inside double-quoted labels, or `&quot;`.
- **Very long labels**: Keep them quoted; don't split nodes unless asked.
- **Code blocks inside labels**: Not supported; suggest alternatives.

### Pandoc Blanks

- **Indented nested list**: Child bullet after parent is not flagged.
- **Content inside fenced code blocks**: Always skipped — `- a` inside
  ``` ``` ``` is not a list to the linter.

### Pandoc Cells

- **Short cells** (< 25 chars) with bold + symbols: Not flagged — LaTeX
  handles them.
- **Long plain cells** without bold/symbols: Not flagged — wrap naturally.
- **Non-pipe-table lines** with stray `|`: Ignored.

### Pandoc Unicode Glyphs

- **Math mode** (`$...$`, `$$...$$`): Always skipped — LaTeX math fonts
  handle Unicode math symbols correctly.
- **Fenced code blocks**: Always skipped — code is not rendered by the
  text font engine.
- **Backtick inline code**: Replaced — pandoc converts these to `\texttt`
  which uses the monospace text font (same glyph-missing issue).

## References

- `references/mermaid-v11-syntax.md` — Mermaid v11 syntax rules, replacement
  tables, and the mmdc error catalog used by the feedback loop.
- `references/pandoc-pdf-pitfalls.md` — Pandoc PDF rendering pitfalls
  (blank-line compliance, long-mixed-cell overflow, font fallback
  configuration, pre-conversion checklist).
- `scripts/validate_mermaid.py` — mmdc wrapper used by Workflow A4.
