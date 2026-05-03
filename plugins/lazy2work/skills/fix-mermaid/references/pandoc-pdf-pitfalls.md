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
6. [Unescaped Currency Dollar Sign](#6-unescaped-currency-dollar-sign)
7. [Unsafe LaTeX Characters in Inline Code](#7-unsafe-latex-characters-in-inline-code)
8. [Closing Dollar Preceded by Whitespace](#8-closing-dollar-preceded-by-whitespace)
9. [External References](#9-external-references)

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

- [ ] `fix_pandoc_blanks.py file.md` reports 0 errors (blank-line + unicode glyph + currency-dollar)
- [ ] Any remaining warnings have been reviewed by a human (long-mixed-cell, unsafe-inline-code-escape)
- [ ] No `Missing character` warnings in pandoc output
- [ ] No `Bad math environment delimiter` errors in lualatex output
- [ ] No `Missing number, treated as zero` errors in lualatex output
- [ ] No `\symcal allowed only in math mode` (or `\frac`/`\hat`/`\mathbb`) errors in lualatex output
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

## 6. Unescaped Currency Dollar Sign

Severity: **error** (auto-fixable by `fix_pandoc_blanks.py --fix`).

### 6.1 Symptoms

- lualatex emits: `! LaTeX Error: Bad math environment delimiter.`
- The error line points at table-cell separators and `\)` (math close)
  appearing where they don't belong (e.g., `l.1724 | Derwent Innovation | \)`)
- The PDF build fails — no output is produced

### 6.2 Root Cause

Pandoc's `tex_math_dollars` extension is on by default. It treats `$...$`
as inline math. The opening rule is permissive:

- Opening `$` is followed by a non-whitespace character
- Closing `$` is preceded by a non-whitespace character
- Closing `$` is **not** followed by a digit

A bare currency `$100` therefore opens math mode, since `$` is followed
by a non-whitespace digit. With Korean text the heuristic that disables
math (closing `$` followed by a digit) often fails — `$76.4억` looks
like math because `억` is not a digit.

When the document contains an **odd** number of unescaped currency `$`,
the last one opens a math mode that never closes. The math state leaks
through paragraphs and finally collides with a downstream pipe-table
row, where LaTeX sees `|` (math `|...|`) and `\)` (inline-math close)
in unexpected positions and aborts.

See `claudedocs/debug_md_to_pdfs_20260429.md` for a full incident report.

### 6.3 WRONG vs CORRECT

```
%% WRONG — pandoc parses these `$` as math delimiters
평균 budget $100K~$1M 사이.
**$76.4억** 매출, 시총 $1B 이상 → 현재 ~$200M

%% CORRECT — every currency `$` escaped with `\`
평균 budget \$100K~\$1M 사이.
**\$76.4억** 매출, 시총 \$1B 이상 → 현재 ~\$200M
```

Real math is unaffected — `$x_1$`, `$\alpha + \beta$`, `$\hat{V}_j$`
all have non-digits after the opening `$` and remain valid.

### 6.4 Detection Rule

| Rule | Trigger |
|---|---|
| `unescaped-currency-dollar` | `$` immediately followed by a digit (0–9) and not preceded by `\`. Detected outside fenced code blocks and inline backtick spans. |

The detection is conservative: only a digit after `$` triggers the rule.
That covers all observed currency cases (`$100`, `$76.4억`, `$1B`,
`$2.58억`) without false-positives on real math.

### 6.5 Why the Fix Is Safe

Pandoc's own rule says a closing `$` followed by a digit invalidates the
math span. So `$x = 1$2` is not valid math anyway — both `$` are text.
Auto-escaping any `$<digit>` therefore can never break a valid math
expression: real math will never have a closing `$` followed by a digit.

### 6.6 Auto-fix

```bash
python3 scripts/fix_pandoc_blanks.py report.md --fix
```

Replaces every `$<digit>` outside fenced code and inline backticks with
`\$<digit>`. Inline backtick code (`` `$1` ``, `` `$PATH` ``) is preserved
because the `$` there is a literal shell variable, not pandoc math.

### 6.7 Diagnostic Commands

```bash
# Locate every `$` occurrence
grep -n '\$' file.md

# Count `$` (odd count = leak risk)
grep -o '\$' file.md | wc -l

# List currency `$` (digit follows)
grep -nE '\$[0-9]' file.md
```

### 6.8 Prevention

- Always write currency as `\$` in Markdown destined for pandoc.
- For globally distributed documents, prefer `USD 76.4억` or `76.4억 달러`
  to sidestep the issue entirely.
- Disabling `tex_math_dollars` is **not** recommended if the document
  contains any real math (`$x$`, `$\alpha$`, etc.) — it will break those.

---

## 7. Unsafe LaTeX Characters in Inline Code

Severity: **warning** (never auto-fixed — the fix requires human choice
between three valid remediations).

### 7.1 Symptoms

- lualatex emits: `! Missing number, treated as zero.`
- The trace shows `\futurelet` and a line such as `\texttt{pass\^{}k}`
- The PDF build fails

### 7.2 Root Cause — Three-Layer Collision

This error appears only when **three** factors combine; remove any one
and the error disappears.

1. **Markdown source** — Inline backtick code containing a LaTeX-risky
   character: `` `pass^k` ``, `` `a~b` ``, `` `x&y` ``, etc.
2. **Pandoc escape** — Pandoc converts the inline code to
   `\texttt{pass\^{}k}`, escaping `^` as `\^{}` (LaTeX circumflex
   accent with empty argument).
3. **`pdf-korean.yaml` `\seqsplit` wrapper** — The line
   `\protected\def\texttt#1{\oldtexttt{\seqsplit{#1}}}` wraps every
   `\texttt` call in `\seqsplit`, which performs per-character splitting
   to allow long URLs / code tokens to break across page width.

`\seqsplit` walks the argument character by character and inserts
zero-width breakpoints. When it encounters `\^`, the splitter separates
the accent command from its `{}` argument. LaTeX, looking ahead with
`\futurelet`, then expects a numeric argument and emits
`Missing number, treated as zero`.

See `claudedocs/debug_md_to_pdfs_20260429_2.md` for the full incident
report and a step-by-step trace.

### 7.3 Risky Characters

| Markdown inline | Pandoc escape | `\seqsplit` outcome |
|---|---|---|
| `` `x^y` `` | `\^{}` | **breaks** — observed |
| `` `x~y` `` | `\~{}` | **breaks** — same mechanism |
| `` `x&y` `` | `\&` | breaks in some contexts |
| `` `x$y` `` | `\$` | breaks in some contexts |
| `` `x%y` `` | `\%` | breaks in some contexts |
| `` `x_y` `` | `\_` | usually OK |
| `` `x#y` `` | `\#` | usually OK |

Pandoc converts fenced code blocks to `\verb`/`lstlisting` (not
`\texttt`), so the `\seqsplit` wrapper does not apply there. **Only
inline backtick spans are at risk.**

### 7.4 Detection Rule

| Rule | Trigger |
|---|---|
| `unsafe-inline-code-escape` | An inline backtick span containing any of `^`, `~`, `&`, `$`, `%`. Detected outside fenced code blocks. |

Severity is `warning` because the linter cannot pick the right fix — the
choice depends on the meaning of the content.

### 7.5 Remediation Options (Manual)

In priority order:

1. **Math mode** (semantically best when the content is mathematical):

   ```
   Before: `pass^k`
   After:  $\text{pass}^k$
   ```

2. **Drop the backticks** (when the formatting is decorative):

   ```
   Before: `pass^k`
   After:  pass^k
   ```

3. **Change `pdf-korean.yaml`** (project-wide fix; needs regression
   testing on long URLs / paths):

   ```latex
   %% old
   \protected\def\texttt#1{\oldtexttt{\seqsplit{#1}}}

   %% candidate replacement
   \protected\def\texttt#1{\oldtexttt{\detokenize{#1}}}
   ```

4. **Pandoc option** (rarely worth it — has its own side effects):

   ```bash
   pandoc input.md --listings -o out.pdf
   ```

### 7.6 Diagnostic Commands

```bash
# Inline code containing ^ or ~
grep -nE '`[^`]*[\^~][^`]*`' file.md

# All five risky chars
grep -nE '`[^`]*[\^~&$%][^`]*`' file.md
```

### 7.7 Why This Differs from §6

§6 (currency `$`) is a Markdown authoring mistake — every pandoc
environment behaves the same. §7 is a project-specific configuration
limitation: standard pandoc renders `\texttt{pass\^{}k}` correctly; only
the `\seqsplit` wrapper added in `pdf-korean.yaml` breaks it. Fixes can
therefore go in either the Markdown or the YAML defaults.

---

## 8. Closing Dollar Preceded by Whitespace

Severity: **error** (auto-fixable by `fix_pandoc_blanks.py --fix`).

### 8.1 Symptoms

- lualatex emits: `! LaTeX Error: \symcal allowed only in math mode.`
  (or any `\frac`, `\hat`, `\mathbb`, `\sum` allowed only in math mode)
- The TeX trace shows `\$\mathcal{...}` — a literal `\$` followed
  immediately by a math-mode command
- The Markdown contains patterns like `$\mathcal{H}_1 = $ rest` or
  `$n_\alpha = $ rest` where the closing `$` has a SPACE in front

### 8.2 Root Cause

Pandoc's `tex_math_dollars` extension is strict about delimiter
boundaries:

| Position | Requirement |
|---|---|
| Opening `$` | followed by **non-whitespace** |
| Closing `$` | preceded by **non-whitespace** |
| Closing `$` | not followed by a digit |

Patterns like `$x = $` (note the space before the closing `$`) violate
the second rule, so pandoc treats both `$` as **literal characters**.
The LaTeX output becomes `\$x = \$` — both dollars are escaped to
text-mode literals. Any math-mode command between them
(`\mathcal`, `\frac`, `\hat`, `\sum`, `\int`, ...) is then evaluated in
text mode, where these commands are not defined → fatal error
`\symcal allowed only in math mode`.

### 8.3 WRONG vs CORRECT

```
%% WRONG — closing `$` preceded by space, math fails to parse
- $\mathcal{H}_1 = $ 1입자 Hilbert 공간

%% CORRECT — no whitespace before closing `$`
- $\mathcal{H}_1 =$ 1입자 Hilbert 공간

%% ALTERNATIVE — move `=` outside math mode
- $\mathcal{H}_1$ = 1입자 Hilbert 공간
```

LaTeX renders `$x =$` and `$x = $` identically in math mode because the
math typesetter normalizes binary-operator spacing automatically — so
the visual output is unchanged.

### 8.4 Detection Rule

| Rule | Trigger |
|---|---|
| `closing-dollar-trailing-space` | A closing `$` whose immediately preceding character is whitespace, with the opening `$` properly followed by non-whitespace, outside fenced code blocks. Currency `$<digit>` patterns are explicitly excluded (handled by §6). |

### 8.5 Why This Differs from §6 and §7

| Issue | Where it fails | Fix style |
|---|---|---|
| §6 currency `$` | `$<digit>` parsed as math opener | Auto-fix: escape `$` |
| §7 inline-code `^` | `\seqsplit` breaks LaTeX escape | Warning (3 choices) |
| §8 trailing space | Closing `$` rejected, math leaks | **Auto-fix: strip space** |

§6 and §8 are both pandoc-strict-rule violations, but at opposite ends
of the math span. §7 is a project-specific configuration limit, not a
pandoc rule violation.

### 8.6 Auto-fix

```bash
python3 scripts/fix_pandoc_blanks.py report.md --fix
```

Strips the offending whitespace inside the math span. The fix is safe:
LaTeX math typesetting normalizes spacing around `=`, `+`, `-`, `\cdot`
automatically, so visual output is unchanged.

### 8.7 Diagnostic Commands

```bash
# Lines with ` $ ` or `= $` patterns
grep -nE '\\$ |= \\$|[a-zA-Z}] \\$' file.md

# Test the fix on a single file
python3 scripts/fix_pandoc_blanks.py file.md
```

### 8.8 Prevention

When writing inline math in pandoc Markdown:

- Never leave a space immediately before a closing `$`
- If the `=` is "narrative" (between phrases), put it outside the math:
  `$x$ = some value` instead of `$x = $ some value`
- If the `=` is "mathematical" (inside the equation), keep both sides:
  `$x = y$` instead of `$x = $`
- Run the linter as a pre-flight check before `pandoc -d pdf-korean`

---

## 9. External References

- Pandoc Markdown: https://pandoc.org/MANUAL.html#pandocs-markdown
- Pandoc pipe_tables extension: https://pandoc.org/MANUAL.html#extension-pipe_tables
- LaTeX longtable: https://ctan.org/pkg/longtable
- lualatex fontspec: https://ctan.org/pkg/fontspec
- luaotfload (font fallback): https://ctan.org/pkg/luaotfload
