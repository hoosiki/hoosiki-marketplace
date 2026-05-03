#!/usr/bin/env python3
"""Pandoc Markdown linter/fixer for PDF rendering pitfalls.

Detects and (where safe) fixes six classes of issues that break
`pandoc -d pdf-korean` (lualatex/xelatex) PDF output:

1. Missing blank line before a block element (list / pipe table / fenced
   code block). Pandoc silently merges the block into the preceding
   paragraph, producing garbled PDF output. **Auto-fixed.**

2. Long pipe-table cells mixing `**bold**` with special symbols (`·`,
   `—`, parentheses, `+`). These cause overfull hbox warnings and page
   overflow in longtable. **Warning only** (human judgment required —
   options are removing bold, shortening the cell, or restructuring the
   table).

3. Unicode glyphs that CJK fonts (e.g. Apple SD Gothic Neo) silently drop
   in lualatex. Two sub-classes:
     - Always-on: symbols like U+2212 (MINUS SIGN) and U+2717 (BALLOT X)
       that have ASCII equivalents. **Auto-fixed.**
     - Opt-in (`--latin1-normalize`): Latin-1 Supplement diacritics
       (á, é, ñ, ü, ß, ...) that the CJK font may not cover. Off by
       default because auto-romanization is lossy on proper nouns
       (Román → Roman). Enable explicitly when you accept the trade-off.

4. Unescaped currency `$` immediately followed by a digit (e.g., `$100`,
   `$76.4억`). Pandoc's `tex_math_dollars` extension parses these as
   inline math delimiters; an odd count leaks math mode into downstream
   tables, producing `Bad math environment delimiter` errors.
   **Auto-fixed** (replaced with `\\$`).

5. Inline backtick code containing LaTeX-risky characters (`^`, `~`,
   `&`, `$`, `%`). Pandoc escapes these as `\\^{}`, `\\~{}`, etc.; the
   `\\seqsplit` wrapper in pdf-korean.yaml then breaks the escape into
   per-glyph tokens, causing `Missing number, treated as zero`.
   **Warning only** — fix requires human judgment (math mode, backtick
   removal, or settings change).

6. Inline math with a trailing space before the closing `$` (e.g.,
   ``$\\mathcal{H}_1 = $ rest``). Pandoc's ``tex_math_dollars`` rule
   requires the closing ``$`` to NOT be preceded by whitespace; when
   violated, both ``$`` are emitted as literal ``\\$``, leaving any
   math-mode commands inside (``\\mathcal``, ``\\frac``, ...) in text
   mode and triggering ``\\symcal allowed only in math mode`` (or
   similar) errors. **Auto-fixed** by stripping the trailing whitespace
   before the closing ``$``.

Companion to fix_mermaid.py — both cover common pandoc PDF rendering
pitfalls. See ../references/pandoc-pdf-pitfalls.md for background.

Usage:
    python fix_pandoc_blanks.py <file_or_dir> [--fix] [--json] [--latin1-normalize]

    --fix                Apply safe fixes in place (blank-line, unicode-glyph,
                         currency-dollar). Long-mixed-cell and unsafe-inline-
                         code warnings are reported but never auto-fixed.
    --json               Output results as JSON.
    --latin1-normalize   Detect (and, with --fix, romanize) Latin-1 Supplement
                         diacritics. Opt-in because romanization is lossy.

Examples:
    python fix_pandoc_blanks.py report.md
    python fix_pandoc_blanks.py docs/ --fix
    python fix_pandoc_blanks.py report.md --json
    python fix_pandoc_blanks.py report.md --fix --latin1-normalize
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_BULLET_RE = re.compile(r"^[-*+]\s")
_NUMLIST_RE = re.compile(r"^\d+\.\s")
_INDENT_RE = re.compile(r"^\s+\S")
_FENCE_RE = re.compile(r"^\s{0,3}(```|~~~)")

_LONG_CELL_THRESHOLD = 25
_RISKY_SYMBOLS = ("·", "—", "–", "+", "(", ")")

# Unicode characters that cause "Missing character" warnings in lualatex
# when the main text font (e.g. Apple SD Gothic Neo) lacks the glyph.
# Each value is (replacement, description).
_UNICODE_GLYPH_MAP: dict[str, tuple[str, str]] = {
    "\u2212": ("-", "MINUS SIGN"),
    "\u2717": ("--", "BALLOT X"),
    "\u2718": ("--", "HEAVY BALLOT X"),
}

_MATH_SPAN_RE = re.compile(r"\$\$[^$]+\$\$|\$[^$]+\$")

# Inline backtick code spans (single-backtick form). Used to mask code
# regions when scanning for currency `$` and to extract code content
# when scanning for LaTeX-risky escape characters.
_INLINE_CODE_RE = re.compile(r"`[^`\n]+`")

# A `$` immediately followed by a digit, NOT already escaped with a
# backslash. Pandoc's `tex_math_dollars` extension parses such `$` as
# an inline math delimiter; pairing odd-numbered currency markers leaks
# math mode and produces `Bad math environment delimiter` errors. The
# safe fix is to escape every `$<digit>` to `\$<digit>`.
_CURRENCY_DOLLAR_RE = re.compile(r"(?<!\\)\$(?=\d)")

# Characters that, when placed inside inline backtick code, are escaped
# by pandoc as `\^{}`, `\~{}`, `\&`, `\$`, `\%`. The pdf-korean.yaml
# `\seqsplit` wrapper on `\texttt` then attempts per-character splitting,
# breaking the escape sequence. Warning-only — see references for
# remediation options (math mode, backtick removal, settings change).
_RISKY_INLINE_CHARS: tuple[str, ...] = ("^", "~", "&", "$", "%")

# Inline math span where the closing `$` is preceded by whitespace,
# violating pandoc's `tex_math_dollars` rule (the closing `$` must NOT
# be preceded by whitespace). Pattern breakdown:
#   (?<!\\)\$    — opening `$`, not already escaped
#   (?=\S)       — opening must be immediately followed by non-whitespace
#   ([^$\n]*?)   — content (non-greedy, no nested `$`, single line)
#   (\s+)        — one or more whitespace chars (the bug)
#   \$           — closing `$`
#   (?!\d)       — closing must not be followed by a digit (otherwise
#                  it is a currency-dollar concern handled elsewhere)
_CLOSING_DOLLAR_TRAILING_SPACE_RE = re.compile(
    r"(?<!\\)\$(?=\S)([^$\n]*?)(\s+)\$(?!\d)"
)

# Pre-compiled pattern for un-escaped dollar positions on a line.
_UNESCAPED_DOLLAR_RE = re.compile(r"(?<!\\)\$")


def _parse_dollar_pairs(line: str) -> list[dict[str, int | bool | None]]:
    """Pair up unescaped ``$`` characters and validate each pair.

    Pandoc's ``tex_math_dollars`` rule treats a sequential pair of ``$``
    characters as inline math iff:

    - the opening ``$`` is immediately followed by non-whitespace
    - the closing ``$`` is immediately preceded by non-whitespace
    - the closing ``$`` is not immediately followed by a digit

    This helper does exactly that: it scans the line for unescaped
    ``$``, pairs them sequentially, and reports the validity of each
    constraint per pair. Both rules in this module use this helper to
    avoid false-positives on math-heavy text.

    Args:
        line: A single line of Markdown text (with or without newline).

    Returns:
        List of dicts. Each dict has keys ``open`` (int position of
        opening ``$``), ``close`` (int position of closing ``$``, or
        ``None`` if the opening is unpaired), ``open_valid`` (bool),
        ``close_prev_valid`` (bool), ``close_next_valid`` (bool), and
        ``is_math`` (bool — True iff all three checks pass).

    Examples:
        >>> pairs = _parse_dollar_pairs("$x = y$")
        >>> pairs[0]["is_math"]
        True
        >>> pairs = _parse_dollar_pairs("$x = $ rest")
        >>> pairs[0]["close_prev_valid"]
        False
        >>> pairs = _parse_dollar_pairs("lone $100")
        >>> pairs[0]["close"] is None
        True
    """
    positions = [m.start() for m in _UNESCAPED_DOLLAR_RE.finditer(line)]
    pairs: list[dict[str, int | bool | None]] = []
    i = 0
    while i + 1 < len(positions):
        op = positions[i]
        cl = positions[i + 1]
        op_valid = (op + 1 < len(line)) and not line[op + 1].isspace()
        cl_prev_valid = (cl > 0) and not line[cl - 1].isspace()
        cl_next_valid = (cl + 1 >= len(line)) or not line[cl + 1].isdigit()
        pairs.append({
            "open": op,
            "close": cl,
            "open_valid": op_valid,
            "close_prev_valid": cl_prev_valid,
            "close_next_valid": cl_next_valid,
            "is_math": op_valid and cl_prev_valid and cl_next_valid,
        })
        i += 2
    if i < len(positions):
        op = positions[i]
        pairs.append({
            "open": op,
            "close": None,
            "open_valid": (op + 1 < len(line)) and not line[op + 1].isspace(),
            "close_prev_valid": False,
            "close_next_valid": False,
            "is_math": False,
        })
    return pairs

# Latin-1 Supplement diacritics (U+00C0..U+00FF) that CJK-only mainfonts
# may silently drop when rendering PDF via lualatex. Opt-in only —
# romanization is lossy for proper nouns. Each value is
# (ASCII replacement, short description for issue context).
_LATIN1_SUPPLEMENT_MAP: dict[str, tuple[str, str]] = {
    "\u00c0": ("A", "À A-GRAVE"),
    "\u00c1": ("A", "Á A-ACUTE"),
    "\u00c2": ("A", "Â A-CIRCUMFLEX"),
    "\u00c3": ("A", "Ã A-TILDE"),
    "\u00c4": ("A", "Ä A-DIAERESIS"),
    "\u00c5": ("A", "Å A-RING"),
    "\u00c6": ("AE", "Æ AE-LIGATURE"),
    "\u00c7": ("C", "Ç C-CEDILLA"),
    "\u00c8": ("E", "È E-GRAVE"),
    "\u00c9": ("E", "É E-ACUTE"),
    "\u00ca": ("E", "Ê E-CIRCUMFLEX"),
    "\u00cb": ("E", "Ë E-DIAERESIS"),
    "\u00cc": ("I", "Ì I-GRAVE"),
    "\u00cd": ("I", "Í I-ACUTE"),
    "\u00ce": ("I", "Î I-CIRCUMFLEX"),
    "\u00cf": ("I", "Ï I-DIAERESIS"),
    "\u00d0": ("D", "Ð ETH"),
    "\u00d1": ("N", "Ñ N-TILDE"),
    "\u00d2": ("O", "Ò O-GRAVE"),
    "\u00d3": ("O", "Ó O-ACUTE"),
    "\u00d4": ("O", "Ô O-CIRCUMFLEX"),
    "\u00d5": ("O", "Õ O-TILDE"),
    "\u00d6": ("O", "Ö O-DIAERESIS"),
    "\u00d8": ("O", "Ø O-STROKE"),
    "\u00d9": ("U", "Ù U-GRAVE"),
    "\u00da": ("U", "Ú U-ACUTE"),
    "\u00db": ("U", "Û U-CIRCUMFLEX"),
    "\u00dc": ("U", "Ü U-DIAERESIS"),
    "\u00dd": ("Y", "Ý Y-ACUTE"),
    "\u00de": ("Th", "Þ THORN"),
    "\u00df": ("ss", "ß SHARP-S"),
    "\u00e0": ("a", "à a-grave"),
    "\u00e1": ("a", "á a-acute"),
    "\u00e2": ("a", "â a-circumflex"),
    "\u00e3": ("a", "ã a-tilde"),
    "\u00e4": ("a", "ä a-diaeresis"),
    "\u00e5": ("a", "å a-ring"),
    "\u00e6": ("ae", "æ ae-ligature"),
    "\u00e7": ("c", "ç c-cedilla"),
    "\u00e8": ("e", "è e-grave"),
    "\u00e9": ("e", "é e-acute"),
    "\u00ea": ("e", "ê e-circumflex"),
    "\u00eb": ("e", "ë e-diaeresis"),
    "\u00ec": ("i", "ì i-grave"),
    "\u00ed": ("i", "í i-acute"),
    "\u00ee": ("i", "î i-circumflex"),
    "\u00ef": ("i", "ï i-diaeresis"),
    "\u00f0": ("d", "ð eth"),
    "\u00f1": ("n", "ñ n-tilde"),
    "\u00f2": ("o", "ò o-grave"),
    "\u00f3": ("o", "ó o-acute"),
    "\u00f4": ("o", "ô o-circumflex"),
    "\u00f5": ("o", "õ o-tilde"),
    "\u00f6": ("o", "ö o-diaeresis"),
    "\u00f8": ("o", "ø o-stroke"),
    "\u00f9": ("u", "ù u-grave"),
    "\u00fa": ("u", "ú u-acute"),
    "\u00fb": ("u", "û u-circumflex"),
    "\u00fc": ("u", "ü u-diaeresis"),
    "\u00fd": ("y", "ý y-acute"),
    "\u00fe": ("th", "þ thorn"),
    "\u00ff": ("y", "ÿ y-diaeresis"),
}


class Issue:
    """A single linting violation or warning.

    Attributes:
        line: 1-based line number of the offending content.
        rule: Rule identifier.
        context: Short snippet of the offending line.
        severity: Either "error" (auto-fixable) or "warning" (manual).

    Examples:
        >>> Issue(1, "r", "c", "error").to_dict()["severity"]
        'error'
    """

    line: int
    rule: str
    context: str
    severity: str

    def __init__(self, line: int, rule: str, context: str, severity: str) -> None:
        """Initialize an Issue.

        Args:
            line: 1-based line number of the finding.
            rule: Rule identifier (e.g., "missing-blank-before-list").
            context: Short snippet for display.
            severity: "error" if auto-fixable, "warning" otherwise.

        Examples:
            >>> Issue(3, "missing-blank-before-table", "| a |", "error").line
            3
        """
        self.line = line
        self.rule = rule
        self.context = context
        self.severity = severity

    def to_dict(self) -> dict[str, str | int]:
        """Convert to a JSON-serializable dict.

        Returns:
            Dictionary containing line, rule, context, and severity.

        Examples:
            >>> Issue(1, "r", "c", "error").to_dict()
            {'line': 1, 'rule': 'r', 'context': 'c', 'severity': 'error'}
        """
        return {
            "line": self.line,
            "rule": self.rule,
            "context": self.context,
            "severity": self.severity,
        }


def _is_table_row(stripped: str) -> bool:
    """Return True if the stripped line looks like a pipe-table row.

    Args:
        stripped: Line content with trailing whitespace removed.

    Returns:
        True when the line both starts and ends with `|`.

    Examples:
        >>> _is_table_row("| a | b |")
        True
        >>> _is_table_row("not a table")
        False
    """
    return stripped.startswith("|") and stripped.endswith("|")


def _is_delimiter_row(stripped: str) -> bool:
    """Return True if the line is the `|---|---|` delimiter row.

    Args:
        stripped: Line content with trailing whitespace removed.

    Returns:
        True when the line is a pipe table delimiter row.

    Examples:
        >>> _is_delimiter_row("|---|---|")
        True
        >>> _is_delimiter_row("| a | b |")
        False
    """
    if not _is_table_row(stripped):
        return False
    cells = [c.strip() for c in stripped.strip("|").split("|")]
    return all(re.match(r"^:?-+:?$", c) for c in cells)


def _classify(line: str) -> str | None:
    """Classify a line as a block-start that requires a preceding blank line.

    Args:
        line: Raw line content (including trailing newline).

    Returns:
        Rule name if the line starts a block element, else None.

    Examples:
        >>> _classify("- a\\n")
        'missing-blank-before-list'
        >>> _classify("| a | b |\\n")
        'missing-blank-before-table'
        >>> _classify("plain\\n") is None
        True
    """
    stripped = line.rstrip()
    if _BULLET_RE.match(line) or _NUMLIST_RE.match(line):
        return "missing-blank-before-list"
    if _is_table_row(stripped):
        return "missing-blank-before-table"
    if _FENCE_RE.match(line):
        return "missing-blank-before-fence"
    return None


def _prev_allows_block(prev: str) -> bool:
    """Return True if the previous line permits a block start without a blank.

    A previous line that is blank, a heading, part of the same block, or
    indented continuation does not require a blank line to precede the next
    block.

    Args:
        prev: The previous line (raw, including trailing newline).

    Returns:
        True if no blank line is required before the next block.

    Examples:
        >>> _prev_allows_block("")
        True
        >>> _prev_allows_block("# H\\n")
        True
        >>> _prev_allows_block("plain\\n")
        False
    """
    prev_stripped = prev.rstrip()
    if prev_stripped == "":
        return True
    if prev_stripped.startswith("#"):
        return True
    if _BULLET_RE.match(prev) or _NUMLIST_RE.match(prev):
        return True
    if _is_table_row(prev_stripped):
        return True
    if _FENCE_RE.match(prev):
        return True
    if _INDENT_RE.match(prev):
        return True
    return False


def _is_risky_cell(cell: str) -> bool:
    """Return True if a cell is long AND mixes bold markup with risky symbols.

    A cell is flagged when its length exceeds the threshold AND it either
    contains bold markup next to a risky symbol, or contains multiple
    distinct risky symbols. This catches the overfull-hbox prone pattern
    described in references/pandoc-pdf-pitfalls.md.

    Args:
        cell: Single-cell content (trimmed).

    Returns:
        True when the cell should trigger a warning.

    Examples:
        >>> _is_risky_cell("short")
        False
        >>> _is_risky_cell("**Fine-tuned Llama-3.1-8B** + (7B·8B) — note")
        True
    """
    if len(cell) < _LONG_CELL_THRESHOLD:
        return False
    has_bold = "**" in cell
    present = [s for s in _RISKY_SYMBOLS if s in cell]
    if has_bold and present:
        return True
    if len(present) >= 2:
        return True
    return False


def check_lines(lines: list[str]) -> list[Issue]:
    """Detect block starts missing a preceding blank line.

    Walks the file line by line, tracking fenced-code state so that
    list-like or table-like content inside fences is never misreported.

    Args:
        lines: File lines (each including trailing newline).

    Returns:
        List of Issue instances with severity="error".

    Examples:
        >>> check_lines(["a\\n", "- b\\n"])[0].rule
        'missing-blank-before-list'
        >>> check_lines(["a\\n", "\\n", "- b\\n"])
        []
    """
    issues: list[Issue] = []
    in_fence = False
    for i, line in enumerate(lines):
        if _FENCE_RE.match(line):
            if not in_fence:
                prev = lines[i - 1] if i > 0 else "\n"
                if not _prev_allows_block(prev):
                    issues.append(Issue(
                        line=i + 1,
                        rule="missing-blank-before-fence",
                        context=line.rstrip()[:80],
                        severity="error",
                    ))
                in_fence = True
            else:
                in_fence = False
            continue
        if in_fence:
            continue
        rule = _classify(line)
        if rule is None:
            continue
        prev = lines[i - 1] if i > 0 else "\n"
        if _prev_allows_block(prev):
            continue
        issues.append(Issue(
            line=i + 1,
            rule=rule,
            context=line.rstrip()[:80],
            severity="error",
        ))
    return issues


def check_table_cells(lines: list[str]) -> list[Issue]:
    """Detect risky long cells mixing bold and special symbols.

    These cells commonly trigger LaTeX overfull hbox warnings and page
    overflow in pandoc-generated longtable environments. Detection is
    conservative and warning-only — no auto-fix is attempted because the
    resolution requires human judgment.

    Args:
        lines: File lines (each including trailing newline).

    Returns:
        List of Issue instances with severity="warning".

    Examples:
        >>> lines = ["\\n", "| m |\\n", "|---|\\n", "| **A** + (B·C) — long enough content |\\n"]
        >>> check_table_cells(lines)[0].rule
        'long-mixed-cell'
    """
    issues: list[Issue] = []
    in_fence = False
    for i, line in enumerate(lines):
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        stripped = line.rstrip()
        if not _is_table_row(stripped):
            continue
        if _is_delimiter_row(stripped):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        for cell in cells:
            if _is_risky_cell(cell):
                issues.append(Issue(
                    line=i + 1,
                    rule="long-mixed-cell",
                    context=cell[:80],
                    severity="warning",
                ))
    return issues


def _mask_math_spans(line: str) -> str:
    """Replace math spans ($...$, $$...$$) with placeholder characters.

    This allows character-level checks on the non-math portions of a line
    without accidentally flagging content inside LaTeX math mode.

    Args:
        line: A single line of Markdown text.

    Returns:
        The line with math spans replaced by spaces of equal length.

    Examples:
        >>> _mask_math_spans("text $x-y$ more")
        'text       more'
        >>> _mask_math_spans("no math here")
        'no math here'
    """
    return _MATH_SPAN_RE.sub(lambda m: " " * len(m.group()), line)


def _has_dangerous_glyph(text: str) -> bool:
    """Return True if the text contains any Unicode glyph from the map.

    Args:
        text: Text to scan.

    Returns:
        True if at least one dangerous glyph is present.

    Examples:
        >>> _has_dangerous_glyph("1\u2212r")
        True
        >>> _has_dangerous_glyph("1-r")
        False
    """
    return any(ch in text for ch in _UNICODE_GLYPH_MAP)


def _replace_glyphs(line: str) -> str:
    """Replace dangerous Unicode glyphs with ASCII equivalents.

    Only replaces characters outside of math spans ($...$, $$...$$).

    Args:
        line: A single line of Markdown text.

    Returns:
        The line with dangerous glyphs replaced in text regions only.

    Examples:
        >>> _replace_glyphs("1\u2212r")
        '1-r'
        >>> _replace_glyphs("$\u2212$ and \u2212")
        '$\u2212$ and -'
    """
    if not _has_dangerous_glyph(line):
        return line

    math_spans = list(_MATH_SPAN_RE.finditer(line))
    if not math_spans:
        for ch, (repl, _desc) in _UNICODE_GLYPH_MAP.items():
            line = line.replace(ch, repl)
        return line

    # Build result preserving math spans
    result: list[str] = []
    pos = 0
    for m in math_spans:
        # Process text before this math span
        segment = line[pos:m.start()]
        for ch, (repl, _desc) in _UNICODE_GLYPH_MAP.items():
            segment = segment.replace(ch, repl)
        result.append(segment)
        result.append(m.group())  # preserve math span as-is
        pos = m.end()
    # Process text after last math span
    segment = line[pos:]
    for ch, (repl, _desc) in _UNICODE_GLYPH_MAP.items():
        segment = segment.replace(ch, repl)
    result.append(segment)
    return "".join(result)


def check_unicode_glyphs(lines: list[str]) -> list[Issue]:
    """Detect Unicode characters that cause Missing character warnings in lualatex.

    Scans all lines outside fenced code blocks and math mode for Unicode
    characters that common CJK fonts (e.g. Apple SD Gothic Neo) lack,
    causing them to silently disappear in PDF output.

    Args:
        lines: File lines (each including trailing newline).

    Returns:
        List of Issue instances with severity="error" (auto-fixable).

    Examples:
        >>> check_unicode_glyphs(["1\u2212r\\n"])[0].rule
        'unicode-glyph-missing'
        >>> check_unicode_glyphs(["$\u2212$\\n"])
        []
    """
    issues: list[Issue] = []
    in_fence = False
    for i, line in enumerate(lines):
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        masked = _mask_math_spans(line)
        if _has_dangerous_glyph(masked):
            found = [
                f"U+{ord(ch):04X} {desc}"
                for ch, (_repl, desc) in _UNICODE_GLYPH_MAP.items()
                if ch in masked
            ]
            issues.append(Issue(
                line=i + 1,
                rule="unicode-glyph-missing",
                context=", ".join(found),
                severity="error",
            ))
    return issues


def fix_unicode_glyphs(lines: list[str]) -> list[str]:
    """Replace dangerous Unicode glyphs with ASCII equivalents.

    Preserves content inside fenced code blocks and math spans.

    Args:
        lines: Original file lines.

    Returns:
        New list of lines with dangerous glyphs replaced.

    Examples:
        >>> fix_unicode_glyphs(["1\u2212r\\n"])
        ['1-r\\n']
        >>> fix_unicode_glyphs(["$\u2212$\\n"])
        ['$\u2212$\\n']
    """
    out: list[str] = []
    in_fence = False
    for line in lines:
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            out.append(line)
            continue
        if in_fence:
            out.append(line)
            continue
        out.append(_replace_glyphs(line))
    return out


def _has_latin1_glyph(text: str) -> bool:
    """Return True if the text contains any Latin-1 Supplement diacritic.

    Args:
        text: Text to scan.

    Returns:
        True if at least one mapped Latin-1 Supplement character is present.

    Examples:
        >>> _has_latin1_glyph("Rom\u00e1n")
        True
        >>> _has_latin1_glyph("Roman")
        False
    """
    return any(ch in text for ch in _LATIN1_SUPPLEMENT_MAP)


def _replace_latin1(line: str) -> str:
    """Replace Latin-1 Supplement diacritics with ASCII equivalents.

    Only replaces characters outside of math spans ($...$, $$...$$).

    Args:
        line: A single line of Markdown text.

    Returns:
        The line with Latin-1 diacritics romanized in text regions only.

    Examples:
        >>> _replace_latin1("Rom\u00e1n")
        'Roman'
        >>> _replace_latin1("$Rom\u00e1n$ and Rom\u00e1n")
        '$Rom\u00e1n$ and Roman'
    """
    if not _has_latin1_glyph(line):
        return line

    math_spans = list(_MATH_SPAN_RE.finditer(line))
    if not math_spans:
        for ch, (repl, _desc) in _LATIN1_SUPPLEMENT_MAP.items():
            line = line.replace(ch, repl)
        return line

    result: list[str] = []
    pos = 0
    for m in math_spans:
        segment = line[pos:m.start()]
        for ch, (repl, _desc) in _LATIN1_SUPPLEMENT_MAP.items():
            segment = segment.replace(ch, repl)
        result.append(segment)
        result.append(m.group())
        pos = m.end()
    segment = line[pos:]
    for ch, (repl, _desc) in _LATIN1_SUPPLEMENT_MAP.items():
        segment = segment.replace(ch, repl)
    result.append(segment)
    return "".join(result)


def check_latin1_supplement(lines: list[str]) -> list[Issue]:
    """Detect Latin-1 Supplement diacritics outside code/math regions.

    Opt-in companion to :func:`check_unicode_glyphs`. Apple SD Gothic Neo
    and several other CJK-oriented mainfonts do not reliably cover the
    Latin-1 Supplement block (U+00A0-U+00FF), so accented letters in
    proper nouns (``Román``, ``Orús``) render as tofu or disappear.

    This check is only invoked when the caller explicitly opts in via
    ``--latin1-normalize`` because automatic romanization is lossy:
    ``Román → Roman`` discards the Spanish diacritic. Callers should
    weigh that trade-off.

    Args:
        lines: File lines (each including trailing newline).

    Returns:
        List of Issue instances with rule="latin1-supplement-glyph" and
        severity="error" (auto-fixable once opted in).

    Examples:
        >>> check_latin1_supplement(["Rom\u00e1n\\n"])[0].rule
        'latin1-supplement-glyph'
        >>> check_latin1_supplement(["Roman\\n"])
        []
    """
    issues: list[Issue] = []
    in_fence = False
    for i, line in enumerate(lines):
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        masked = _mask_math_spans(line)
        if not _has_latin1_glyph(masked):
            continue
        found = [
            f"U+{ord(ch):04X} {desc}"
            for ch, (_repl, desc) in _LATIN1_SUPPLEMENT_MAP.items()
            if ch in masked
        ]
        issues.append(Issue(
            line=i + 1,
            rule="latin1-supplement-glyph",
            context=", ".join(found),
            severity="error",
        ))
    return issues


def fix_latin1_supplement(lines: list[str]) -> list[str]:
    """Romanize Latin-1 Supplement diacritics outside code/math regions.

    Companion to :func:`check_latin1_supplement`. Preserves content
    inside fenced code blocks and inline/display math spans.

    Args:
        lines: Original file lines.

    Returns:
        New list of lines with diacritics replaced by their ASCII
        equivalents per :data:`_LATIN1_SUPPLEMENT_MAP`.

    Examples:
        >>> fix_latin1_supplement(["Rom\u00e1n Or\u00fas\\n"])
        ['Roman Orus\\n']
        >>> fix_latin1_supplement(["```\\n", "Rom\u00e1n\\n", "```\\n"])
        ['```\\n', 'Rom\u00e1n\\n', '```\\n']
    """
    out: list[str] = []
    in_fence = False
    for line in lines:
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            out.append(line)
            continue
        if in_fence:
            out.append(line)
            continue
        out.append(_replace_latin1(line))
    return out


def _mask_inline_code(line: str) -> str:
    """Replace inline backtick code spans with spaces of equal length.

    Allows position-preserving scans on the surrounding text without
    matching content inside ``\\texttt`` regions.

    Args:
        line: A single line of Markdown text.

    Returns:
        The line with each ``\\`...\\``` span replaced by a same-length
        run of ASCII spaces.

    Examples:
        >>> _mask_inline_code("see `$1` and $100")
        'see      and $100'
        >>> _mask_inline_code("no code")
        'no code'
    """
    return _INLINE_CODE_RE.sub(lambda m: " " * len(m.group()), line)


def _currency_dollar_positions(line: str) -> list[int]:
    """Return positions of ``$`` chars that are currency (not valid math).

    A ``$`` immediately followed by a digit is "currency-style". This
    helper returns only those that are NOT inside a valid pandoc math
    span — preventing false positives on ``$1$``, ``$0, 1, 2$`` etc.

    Args:
        line: Single line of text.

    Returns:
        List of character positions where ``$`` is unescaped, followed
        by a digit, and not part of a valid math pair.

    Examples:
        >>> _currency_dollar_positions("가격 $100")
        [3]
        >>> _currency_dollar_positions("$1$ valid math")
        []
        >>> _currency_dollar_positions("$100K~$1M leak")
        [0, 6]
    """
    pairs = _parse_dollar_pairs(line)
    bad: list[int] = []
    for pair in pairs:
        if pair["is_math"]:
            continue
        op = pair["open"]
        assert isinstance(op, int)
        if op + 1 < len(line) and line[op + 1].isdigit():
            bad.append(op)
        cl = pair["close"]
        if isinstance(cl, int) and cl + 1 < len(line) and line[cl + 1].isdigit():
            bad.append(cl)
    return sorted(set(bad))


def check_currency_dollar(lines: list[str]) -> list[Issue]:
    r"""Detect unescaped currency ``$`` outside valid math spans.

    Pandoc's ``tex_math_dollars`` extension treats a paired ``$``
    sequence as math iff opening is followed by non-whitespace, closing
    is preceded by non-whitespace, and closing is not followed by a
    digit. A ``$<digit>`` outside such a valid pair (e.g., ``$100`` with
    no closing pair, or ``$100K~$1M`` whose closing is followed by a
    digit) leaks math state and causes ``Bad math environment delimiter``
    errors. Real math like ``$1$`` or ``$0, 1, 2, \ldots$`` is preserved
    because their pairs ARE valid math.

    The check is auto-fixable: replace each currency ``$`` with ``\$``.

    Args:
        lines: File lines (each including trailing newline).

    Returns:
        List of Issue instances with rule ``unescaped-currency-dollar``
        and severity ``error``.

    Examples:
        >>> check_currency_dollar(["가격 $100\n"])[0].rule
        'unescaped-currency-dollar'
        >>> check_currency_dollar(["수식 $1$ 정상\n"])
        []
        >>> check_currency_dollar(["\\$100\n"])
        []
    """
    issues: list[Issue] = []
    in_fence = False
    for i, line in enumerate(lines):
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        masked = _mask_inline_code(line)
        for pos in _currency_dollar_positions(masked):
            start = max(0, pos - 5)
            end = min(len(line), pos + 10)
            snippet = line[start:end].rstrip()
            issues.append(Issue(
                line=i + 1,
                rule="unescaped-currency-dollar",
                context=snippet[:80],
                severity="error",
            ))
    return issues


def _escape_currency_in_segment(segment: str) -> str:
    """Insert ``\\`` before every currency ``$`` in a code-free segment.

    Args:
        segment: Text outside fenced code and inline backticks.

    Returns:
        Segment with currency-style ``$`` escaped (math-style ``$``
        preserved).

    Examples:
        >>> _escape_currency_in_segment("가격 $100")
        '가격 \\\\$100'
        >>> _escape_currency_in_segment("수식 $1$ 정상")
        '수식 $1$ 정상'
    """
    positions = _currency_dollar_positions(segment)
    if not positions:
        return segment
    result: list[str] = []
    last = 0
    for pos in positions:
        result.append(segment[last:pos])
        result.append("\\$")
        last = pos + 1
    result.append(segment[last:])
    return "".join(result)


def fix_currency_dollar(lines: list[str]) -> list[str]:
    r"""Escape currency ``$`` outside valid math spans and code regions.

    Preserves: valid math (``$1$``, ``$0, 1, 2$``), fenced code blocks,
    inline backtick code (where ``$`` is a literal shell variable), and
    already-escaped ``\\$``.

    Args:
        lines: Original file lines.

    Returns:
        New list of lines with currency-style ``$`` escaped.

    Examples:
        >>> fix_currency_dollar(["$100\n"])
        ['\\$100\n']
        >>> fix_currency_dollar(["use `$1` here\n"])
        ['use `$1` here\n']
        >>> fix_currency_dollar(["수식 $1$ 정상\n"])
        ['수식 $1$ 정상\n']
        >>> fix_currency_dollar(["$100K~$1M\n"])
        ['\\$100K~\\$1M\n']
    """
    out: list[str] = []
    in_fence = False
    for line in lines:
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            out.append(line)
            continue
        if in_fence:
            out.append(line)
            continue
        if "`" not in line:
            out.append(_escape_currency_in_segment(line))
            continue
        result: list[str] = []
        pos = 0
        for m in _INLINE_CODE_RE.finditer(line):
            segment = line[pos:m.start()]
            result.append(_escape_currency_in_segment(segment))
            result.append(m.group())
            pos = m.end()
        segment = line[pos:]
        result.append(_escape_currency_in_segment(segment))
        out.append("".join(result))
    return out


def check_unsafe_inline_code(lines: list[str]) -> list[Issue]:
    r"""Detect inline backtick code containing LaTeX-risky characters.

    Inline code with ``^``, ``~``, ``&``, ``$``, or ``%`` is escaped by
    pandoc as ``\\^{}``, ``\\~{}``, ``\\&``, ``\\$``, ``\\%``. The
    ``\\seqsplit`` wrapper applied to ``\\texttt`` in pdf-korean.yaml
    then attempts per-character splitting, which separates the escape
    command from its argument and triggers
    ``! Missing number, treated as zero`` in lualatex.

    Warning-only — three valid remediations need human choice:

    - rewrite as math mode: `` `pass^k` `` → ``$\\text{pass}^k$``
    - drop backticks: `` `pass^k` `` → plain ``pass^k``
    - switch to ``\\detokenize`` in pdf-korean.yaml

    Args:
        lines: File lines (each including trailing newline).

    Returns:
        List of Issue instances with rule ``unsafe-inline-code-escape``
        and severity ``warning``.

    Examples:
        >>> check_unsafe_inline_code(["use `pass^k` here\n"])[0].rule
        'unsafe-inline-code-escape'
        >>> check_unsafe_inline_code(["call `pass@k` here\n"])
        []
    """
    issues: list[Issue] = []
    in_fence = False
    for i, line in enumerate(lines):
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for m in _INLINE_CODE_RE.finditer(line):
            content = m.group()
            if any(ch in content for ch in _RISKY_INLINE_CHARS):
                issues.append(Issue(
                    line=i + 1,
                    rule="unsafe-inline-code-escape",
                    context=content[:80],
                    severity="warning",
                ))
    return issues


def _trailing_space_close_positions(line: str) -> list[int]:
    """Return positions of closing ``$`` chars violating the trailing-space rule.

    A pair is a violation when:
    - opening ``$`` is valid (followed by non-whitespace)
    - closing ``$`` is preceded by whitespace
    - closing ``$`` is not immediately followed by a digit (otherwise
      it is a currency-dollar concern handled elsewhere)

    Args:
        line: Single line of text.

    Returns:
        List of character positions of offending closing ``$``.

    Examples:
        >>> _trailing_space_close_positions(r"$x = $ rest")
        [5]
        >>> _trailing_space_close_positions(r"$q$와 $p$")
        []
    """
    pairs = _parse_dollar_pairs(line)
    return [
        pair["close"]  # type: ignore[misc]
        for pair in pairs
        if isinstance(pair["close"], int)
        and pair["open_valid"]
        and not pair["close_prev_valid"]
        and pair["close_next_valid"]
    ]


def check_closing_dollar_trailing_space(lines: list[str]) -> list[Issue]:
    r"""Detect inline math whose closing ``$`` is preceded by whitespace.

    Pandoc's ``tex_math_dollars`` rule requires the closing ``$`` to be
    IMMEDIATELY preceded by non-whitespace. Patterns like
    ``$\mathcal{H}_1 = $ rest`` violate that rule, so pandoc emits both
    ``$`` as literal ``\$``, leaving any math-mode command
    (``\mathcal``, ``\frac``, ...) in text mode and producing
    ``! LaTeX Error: \symcal allowed only in math mode``.

    Detection is pair-based via :func:`_parse_dollar_pairs` so adjacent
    valid math spans (``$q$ and $p$``) are not falsely flagged.

    Args:
        lines: File lines (each including trailing newline).

    Returns:
        List of Issue instances with rule
        ``closing-dollar-trailing-space`` and severity ``error``.

    Examples:
        >>> check_closing_dollar_trailing_space([r"$x = $ y" + "\n"])[0].rule
        'closing-dollar-trailing-space'
        >>> check_closing_dollar_trailing_space([r"$x = y$" + "\n"])
        []
        >>> check_closing_dollar_trailing_space([r"$q$와 $p$" + "\n"])
        []
    """
    issues: list[Issue] = []
    in_fence = False
    for i, line in enumerate(lines):
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for pos in _trailing_space_close_positions(line):
            start = max(0, pos - 10)
            end = min(len(line), pos + 5)
            snippet = line[start:end].rstrip()
            issues.append(Issue(
                line=i + 1,
                rule="closing-dollar-trailing-space",
                context=snippet[:80],
                severity="error",
            ))
    return issues


def fix_closing_dollar_trailing_space(lines: list[str]) -> list[str]:
    r"""Strip whitespace before a closing ``$`` for offending pairs only.

    Companion to :func:`check_closing_dollar_trailing_space`. Preserves
    content inside fenced code blocks and never modifies adjacent valid
    math spans.

    Args:
        lines: Original file lines.

    Returns:
        New list of lines with offending trailing whitespace removed.

    Examples:
        >>> fix_closing_dollar_trailing_space([r"$x = $ y" + "\n"])
        ['$x =$ y\n']
        >>> fix_closing_dollar_trailing_space([r"$x   $ y" + "\n"])
        ['$x$ y\n']
        >>> fix_closing_dollar_trailing_space([r"$q$와 $p$" + "\n"])
        ['$q$와 $p$\n']
    """
    out: list[str] = []
    in_fence = False
    for line in lines:
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            out.append(line)
            continue
        if in_fence:
            out.append(line)
            continue
        positions = _trailing_space_close_positions(line)
        if not positions:
            out.append(line)
            continue
        result: list[str] = []
        last = 0
        for pos in positions:
            # Find start of whitespace run before this `$`
            ws_start = pos
            while ws_start > last and line[ws_start - 1].isspace():
                ws_start -= 1
            result.append(line[last:ws_start])
            result.append("$")
            last = pos + 1
        result.append(line[last:])
        out.append("".join(result))
    return out


def fix_lines(lines: list[str]) -> list[str]:
    """Return a new list with blank lines inserted before offending blocks.

    Only blank-line violations are fixed. Warning-only issues (cell
    overflow) are never modified.

    Args:
        lines: Original file lines.

    Returns:
        New list of lines with safe fixes applied.

    Examples:
        >>> fix_lines(["x\\n", "- a\\n"])
        ['x\\n', '\\n', '- a\\n']
        >>> fix_lines(["x\\n", "\\n", "- a\\n"])
        ['x\\n', '\\n', '- a\\n']
    """
    out: list[str] = []
    in_fence = False
    for line in lines:
        if _FENCE_RE.match(line):
            if not in_fence:
                prev = out[-1] if out else "\n"
                if not _prev_allows_block(prev):
                    out.append("\n")
                in_fence = True
                out.append(line)
                continue
            in_fence = False
            out.append(line)
            continue
        if in_fence:
            out.append(line)
            continue
        rule = _classify(line)
        if rule is not None:
            prev = out[-1] if out else "\n"
            if not _prev_allows_block(prev):
                out.append("\n")
        out.append(line)
    return out


def process_file(
    filepath: Path,
    apply_fix: bool = False,
    normalize_latin1: bool = False,
) -> list[Issue]:
    """Scan a single Markdown file, optionally applying safe fixes.

    Args:
        filepath: Path to the Markdown file to process.
        apply_fix: If True, write blank-line and unicode-glyph fixes back.
            Long-mixed-cell warnings are always reported but never modify
            the file.
        normalize_latin1: If True, additionally detect and (when combined
            with ``apply_fix``) romanize Latin-1 Supplement diacritics.
            Off by default because romanization is lossy for proper nouns.

    Returns:
        Combined list of detected issues (errors + warnings).

    Examples:
        >>> from pathlib import Path
        >>> import tempfile
        >>> with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
        ...     _ = f.write("x\\n- a\\n")
        ...     p = Path(f.name)
        >>> any(i.rule == "missing-blank-before-list" for i in process_file(p))
        True
    """
    text = filepath.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    blank_issues = check_lines(lines)
    cell_issues = check_table_cells(lines)
    glyph_issues = check_unicode_glyphs(lines)
    currency_issues = check_currency_dollar(lines)
    inline_code_issues = check_unsafe_inline_code(lines)
    closing_dollar_issues = check_closing_dollar_trailing_space(lines)
    latin1_issues = check_latin1_supplement(lines) if normalize_latin1 else []
    all_issues = (
        blank_issues
        + cell_issues
        + glyph_issues
        + currency_issues
        + inline_code_issues
        + closing_dollar_issues
        + latin1_issues
    )
    needs_write = (
        blank_issues
        or glyph_issues
        or currency_issues
        or closing_dollar_issues
        or latin1_issues
    )
    if apply_fix and needs_write:
        fixed = lines
        if blank_issues:
            fixed = fix_lines(fixed)
        if glyph_issues:
            fixed = fix_unicode_glyphs(fixed)
        if currency_issues:
            fixed = fix_currency_dollar(fixed)
        if closing_dollar_issues:
            fixed = fix_closing_dollar_trailing_space(fixed)
        if latin1_issues:
            fixed = fix_latin1_supplement(fixed)
        filepath.write_text("".join(fixed), encoding="utf-8")
    return all_issues


def _collect_targets(args: list[str]) -> list[Path]:
    """Resolve CLI arguments to a list of Markdown files.

    Args:
        args: Positional CLI arguments (file or directory paths).

    Returns:
        Sorted list of .md file paths.

    Examples:
        >>> _collect_targets([])
        []
    """
    targets: list[Path] = []
    for arg in args:
        p = Path(arg)
        if p.is_file():
            targets.append(p)
        elif p.is_dir():
            targets.extend(sorted(p.rglob("*.md")))
    return targets


def _print_table(all_issues: list[dict[str, str | int]], apply_fix: bool) -> None:
    """Print a human-readable issue table.

    Args:
        all_issues: Collected issue dicts with an extra "file" key.
        apply_fix: Whether fixes were applied (affects the heading label).

    Examples:
        >>> _print_table([], False)
        OK: No issues found.
    """
    if not all_issues:
        print("OK: No issues found.")
        return
    errors = [d for d in all_issues if d["severity"] == "error"]
    warnings = [d for d in all_issues if d["severity"] == "warning"]
    action = "Fixed" if apply_fix else "Found"
    print(f"{action} {len(errors)} error(s), {len(warnings)} warning(s):\n")
    print(f"{'Sev':<8} | {'Line':>5} | {'Rule':<32} | Context")
    print("-" * 96)
    for d in all_issues:
        context = str(d["context"])
        if len(context) > 40:
            context = context[:40] + "..."
        print(f"{d['severity']:<8} | {d['line']:>5} | {d['rule']:<32} | {context}")
    if warnings:
        print("\nWarnings require manual review (not auto-fixable).")
    if errors and not apply_fix:
        print("Run with --fix to apply blank-line corrections.")


def main() -> int:
    """CLI entry point.

    Returns:
        Exit code: 0 if no issues, 1 if any issues were found.

    Examples:
        >>> callable(main)
        True
    """
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return 0
    apply_fix = "--fix" in sys.argv
    output_json = "--json" in sys.argv
    normalize_latin1 = "--latin1-normalize" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    targets = _collect_targets(args)
    all_issues: list[dict[str, str | int]] = []
    for filepath in targets:
        issues = process_file(
            filepath,
            apply_fix=apply_fix,
            normalize_latin1=normalize_latin1,
        )
        for issue in issues:
            d = issue.to_dict()
            d["file"] = str(filepath)
            all_issues.append(d)
    if output_json:
        print(json.dumps({"issues": all_issues, "total": len(all_issues)}, indent=2))
    else:
        _print_table(all_issues, apply_fix)
    return 1 if all_issues else 0


if __name__ == "__main__":
    sys.exit(main())
