#!/usr/bin/env python3
"""Pandoc Markdown linter/fixer for PDF rendering pitfalls.

Detects and (where safe) fixes two classes of issues that break
`pandoc -d pdf-korean` (lualatex/xelatex) PDF output:

1. Missing blank line before a block element (list / pipe table / fenced
   code block). Pandoc silently merges the block into the preceding
   paragraph, producing garbled PDF output. **Auto-fixed.**

2. Long pipe-table cells mixing `**bold**` with special symbols (`·`,
   `—`, parentheses, `+`). These cause overfull hbox warnings and page
   overflow in longtable. **Warning only** (human judgment required —
   options are removing bold, shortening the cell, or restructuring the
   table).

Companion to fix_mermaid.py — both cover common pandoc PDF rendering
pitfalls. See ../references/pandoc-pdf-pitfalls.md for background.

Usage:
    python fix_pandoc_blanks.py <file_or_dir> [--fix] [--json]

    --fix   Apply safe fixes in place (blank-line issues only).
            Warnings are always reported but never auto-fixed.
    --json  Output results as JSON.

Examples:
    python fix_pandoc_blanks.py report.md
    python fix_pandoc_blanks.py docs/ --fix
    python fix_pandoc_blanks.py report.md --json
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


def process_file(filepath: Path, apply_fix: bool = False) -> list[Issue]:
    """Scan a single Markdown file, optionally applying safe fixes.

    Args:
        filepath: Path to the Markdown file to process.
        apply_fix: If True, write blank-line fixes back. Warnings are
            always reported but never modify the file.

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
    all_issues = blank_issues + cell_issues + glyph_issues
    if apply_fix and (blank_issues or glyph_issues):
        fixed = lines
        if blank_issues:
            fixed = fix_lines(fixed)
        if glyph_issues:
            fixed = fix_unicode_glyphs(fixed)
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
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    targets = _collect_targets(args)
    all_issues: list[dict[str, str | int]] = []
    for filepath in targets:
        for issue in process_file(filepath, apply_fix=apply_fix):
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
