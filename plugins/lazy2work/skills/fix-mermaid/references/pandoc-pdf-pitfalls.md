# Pandoc PDF Rendering Reference — Common Pitfalls and Fixes

Pitfalls encountered in `pandoc -d pdf-korean` (lualatex + Korean fonts)
workflows, with detection and remediation guidance. Background knowledge
for `fix_pandoc_blanks.py`; also usable as a human pre-flight checklist.

## Table of Contents

1. [Missing Blank Line Before Block Elements](#1-missing-blank-line-before-block-elements)
2. [Long Table Cells Mixing Bold and Special Symbols](#2-long-table-cells-mixing-bold-and-special-symbols)
3. [Font Fallback for Korean and Emoji](#3-font-fallback-for-korean-and-emoji)
4. [Pre-conversion Checklist](#4-pre-conversion-checklist)
5. [Unicode Glyph Missing in CJK Fonts](#5-unicode-glyph-missing-in-cjk-fonts)
6. [External References](#6-external-references)

---

## 1. Missing Blank Line Before Block Elements

Severity: **error** (auto-fixable by `fix_pandoc_blanks.py --fix`).

### 1.1 Symptoms

One or more of these appear in the rendered PDF:

- Bullet or numbered lists render as a single paragraph of text with literal dashes
- Table headers render as paragraph text with literal `|` characters
- A section "looks broken" after conversion — in reality an internal list/table is broken
- Fenced code blocks render as escaped backticks plus inline text

### 1.2 Root Cause

Pandoc's Markdown parser requires a **blank line before every block element**
(list, pipe table, fenced code block). Without it, the block is silently
treated as an inline continuation of the preceding paragraph. The result
appears as garbled text in the PDF rather than a proper block environment.

Korean writers frequently produce this pattern because `**Label**:` is often
followed directly by a list without an intervening blank line.

### 1.3 WRONG vs CORRECT

```
%% WRONG — list glued to the previous line
**Features**:
- Item 1
- Item 2

%% CORRECT — blank line before the list
**Features**:

- Item 1
- Item 2
```

Tables:

```
%% WRONG
Result:
| col | value |
|---|---|
| a | 1 |

%% CORRECT
Result:

| col | value |
|---|---|
| a | 1 |
```

Fenced code blocks:

```
%% WRONG
Example:
```python
x = 1
```

%% CORRECT
Example:

``(triple-backtick)`python
x = 1
``(triple-backtick)`
```

### 1.4 Why It Looks Intermittent

Whether the block is parsed correctly without a blank line depends on the
Markdown dialect (`markdown_github` vs `markdown` vs `markdown_strict`),
pandoc version, and surrounding context. This makes the bug appear
non-reproducible. The only reliable rule is: **always put a blank line
before a block element**.

### 1.5 Detection Rules

All three rules are auto-fixable (severity=error):

| Rule | Trigger |
|------|---------|
| `missing-blank-before-list` | A line starting with `- `, `* `, `+ `, or `1. ` preceded by non-blank non-list text |
| `missing-blank-before-table` | A pipe-table row preceded by non-blank non-table text |
| `missing-blank-before-fence` | A ` ``` ` or `~~~` opener preceded by non-blank text |

Exceptions (no blank line needed):

- The previous line is a heading (starts with `#`)
- The previous line is part of the same block (list item continues, table row continues)
- The previous line is an indented continuation (e.g., a nested list)
- The block starts at the top of the file

### 1.6 Automated Detection and Fix

```bash
# Lint only (error + warning report)
python3 scripts/fix_pandoc_blanks.py report.md

# Auto-fix errors only (warnings are never modified)
python3 scripts/fix_pandoc_blanks.py report.md --fix

# JSON output for CI pipelines
python3 scripts/fix_pandoc_blanks.py docs/ --json
```

---

## 2. Long Table Cells Mixing Bold and Special Symbols

Severity: **warning** (never auto-fixed — requires human judgment).

### 2.1 Symptoms

- Table converts to `longtable` successfully but specific rows overflow the page width
- Cell contents wrap in awkward ways
- LaTeX log shows repeated `Overfull \hbox` warnings

### 2.2 Root Cause

Pandoc maps pipe tables to `longtable` with columns sized as equal fractions
of `\linewidth` (e.g., 4 columns → each `\linewidth * 0.25`). A cell
combining the following patterns defeats LaTeX hyphenation:

- `**bold**` markup (disrupts token boundaries)
- Middle dot `·` or em/en dash `—`/`–`
- Parenthetical annotations `(...)`
- Plus / percent signs `+`, `%`

The `\sloppy` + `\emergencystretch` + `\seqsplit` mitigations in
`pdf-korean.yaml` handle most cases, but the combination above still
overflows.

### 2.3 Risky Pattern

```
%% WARNING — long cell with bold + symbols + parens + dash
| Model | Note |
|---|---|
| **Fine-tuned Llama-3.1-8B** | Up to **+40%** (7B·8B) — SynthCypher |
```

### 2.4 Detection Criteria

A cell is flagged (`long-mixed-cell`, severity=warning) when:

- Cell length ≥ 25 characters
- AND either:
  - Cell contains `**bold**` markup **and** at least one risky symbol
  - Cell contains two or more distinct risky symbols

Risky symbols: `·`, `—`, `–`, `+`, `(`, `)`.

### 2.5 Remediation (Manual)

Apply in priority order:

1. **Remove bold** inside the cell (move emphasis to a caption or footnote)
2. **Shorten the cell** (pull parenthetical annotations into a sentence or bullet outside the table)
3. **Restructure the table** (reduce columns, e.g., 4 → 3)
4. **Split the wide row** into a bullet list underneath the table

Before editing, verify the `pdf-korean.yaml` mitigations are active:

- `\sloppy`
- `\emergencystretch=3em`
- `\seqsplit` wrapper on `\texttt`

If these are active and the warning persists, the cell content itself
requires restructuring.

### 2.6 WRONG vs CORRECTED Example

```
%% WARNING
| Model | Note |
|---|---|
| **Fine-tuned Llama-3.1-8B** | Up to **+40%** (7B·8B) — SynthCypher |

%% FIXED (bold removed, parens moved to caption)
| Model | Note |
|---|---|
| Fine-tuned Llama-3.1-8B | Up to +40% gain |

Caption: 7B–8B parameter models evaluated on SynthCypher.
```

### 2.7 Automated Detection

```bash
python3 scripts/fix_pandoc_blanks.py report.md
```

Example output:

```
Sev      |  Line | Rule                             | Context
------------------------------------------------------------------------
warning  |   197 | long-mixed-cell                  | **Fine-tuned GPT-4o**
warning  |   198 | long-mixed-cell                  | Up to **+40%** (7B·8B)
```

---

## 3. Font Fallback for Korean and Emoji

Severity: **configuration** (one-time setup, not auto-fixable).

### 3.1 Symptoms

- Emoji characters (🎯, 🚀, etc.) render as `□` or empty boxes
- Korean text inside monospace (code) regions renders incorrectly
- Mixed CJK + Latin text shows inconsistent baseline

### 3.2 Fix

Add fallback configuration to the `header-includes` section of
`pdf-korean.yaml`:

```latex
\directlua{
  luaotfload.add_fallback("emojifallback", {"Noto Emoji:mode=harf;"})
  luaotfload.add_fallback("monofallback",  {"Apple SD Gothic Neo:mode=harf;", "Noto Emoji:mode=harf;"})
}
\setmainfont{Apple SD Gothic Neo}[RawFeature={fallback=emojifallback}]
\setsansfont{Apple SD Gothic Neo}[RawFeature={fallback=emojifallback}]
\setmonofont{JetBrainsMono Nerd Font Mono}[RawFeature={fallback=monofallback}]
```

### 3.3 Prerequisites

- `Noto Emoji` font installed: `brew install --cask font-noto-emoji`
- Korean main font (`Apple SD Gothic Neo`) available on the system (pre-installed on macOS)
- Monospace font with Nerd Font glyphs (`JetBrainsMono Nerd Font Mono`) installed

### 3.4 Verification

Render a small test document containing:

```
한글 테스트 🎯

inline `코드 한글` test

\```python
# 한글 주석
x = "값"
\```
```

Confirm each of the following renders correctly:
- Korean text in body
- Emoji
- Korean inside inline backticks
- Korean inside fenced code blocks

---

## 4. Pre-conversion Checklist

Run each check before `pandoc -d pdf-korean ...`:

- [ ] `fix_pandoc_blanks.py file.md` reports 0 errors (blank-line + unicode glyph)
- [ ] Any remaining warnings have been reviewed by a human
- [ ] No `Missing character` warnings in pandoc output
- [ ] `fix_mermaid.py file.md` reports 0 issues
- [ ] `~/.pandoc/defaults/pdf-korean.yaml` exists and its referenced filter paths resolve
- [ ] `mmdc --version` succeeds (required if the document contains Mermaid)
- [ ] Required fonts installed: `Apple SD Gothic Neo`, `JetBrainsMono Nerd Font Mono`, `Noto Emoji`

Optional quality checks:

- [ ] Table cells with bold + symbols have been reviewed for overflow risk
- [ ] Lists and tables have a blank line before them
- [ ] Fenced code blocks have a blank line before them

---

## 5. Unicode Glyph Missing in CJK Fonts

Severity: **error** (auto-fixable by `fix_pandoc_blanks.py --fix`).

### 5.1 Symptoms

- pandoc emits: `[WARNING] Missing character: There is no − (U+2212) in font ...`
- Characters silently disappear in the PDF (e.g., `1−r/c` becomes `1r/c`)
- Check/ballot marks (`✗`, `✓`) render as blank spaces in tables

### 5.2 Root Cause

LLM-generated text (Claude, GPT, etc.) and web copy-paste frequently
introduce Unicode look-alike characters. These are visually identical to
ASCII equivalents but use different code points that CJK fonts lack:

| Appears as | ASCII (safe) | Unicode (dangerous) | Origin |
|---|---|---|---|
| `-` (minus) | U+002D HYPHEN-MINUS | **U+2212 MINUS SIGN** | LLM math output |
| `X` (ballot) | X or `--` | **U+2717 BALLOT X** | Web copy-paste |
| `X` (heavy ballot) | X or `--` | **U+2718 HEAVY BALLOT X** | Web copy-paste |

The font fallback chain (`luaotfload.add_fallback`) covers emoji but not
these mathematical/typographic symbols. When lualatex encounters a character
not in the font, it emits a warning and **omits the character entirely**.

### 5.3 Why Math Mode Is Safe

Content inside `$...$` or `$$...$$` is rendered by LaTeX math fonts (e.g.,
Latin Modern Math), which include full Unicode mathematical symbol coverage.
The same U+2212 that fails in text mode works perfectly in math mode.

### 5.4 Detection

```bash
python3 scripts/fix_pandoc_blanks.py report.md
```

Rule: `unicode-glyph-missing` (severity=error, auto-fixable).

Scans all lines outside fenced code blocks and math spans for characters
in the dangerous glyph map. Reports each affected line with the specific
Unicode code points found.

### 5.5 Auto-fix

```bash
python3 scripts/fix_pandoc_blanks.py report.md --fix
```

Replaces each dangerous character with its ASCII equivalent. Preserves:

- Content inside `$...$` and `$$...$$` (math mode)
- Content inside fenced code blocks

### 5.6 Prevention

When writing Markdown for PDF conversion:

1. Use `$...$` math mode for mathematical expressions instead of backtick
   inline code — LaTeX math fonts handle Unicode correctly
2. Avoid copy-pasting from web/PDF sources without checking for Unicode
   look-alikes
3. Run the linter before `pandoc -d pdf-korean` as a pre-flight check

---

## 6. External References

- Pandoc Markdown: https://pandoc.org/MANUAL.html#pandocs-markdown
- Pandoc pipe_tables extension: https://pandoc.org/MANUAL.html#extension-pipe_tables
- LaTeX longtable: https://ctan.org/pkg/longtable
- lualatex fontspec: https://ctan.org/pkg/fontspec
- luaotfload (font fallback): https://ctan.org/pkg/luaotfload
