#!/usr/bin/env python3
"""Mermaid diagram linter and auto-fixer for Markdown files.

Scans Markdown files for ```mermaid code blocks and detects/fixes:
  1. Sequence diagram reserved word conflicts (participant IDs)
  2. Unicode characters used as diagram *syntax* — zero-width characters in
     IDs, typographic dashes and Unicode arrows used as arrows, fullwidth
     punctuation used as delimiters or separators, curly quotes used as label
     delimiters, and Unicode punctuation in bare subgraph titles
  3. Unicode that has no safe automatic fix (left-pointing arrows, the
     ideographic full stop in syntax) — reported as warnings, never rewritten

Label and message text is never rewritten. Mermaid 11.12.2 and 12.1.0 render
every one of these characters inside labels, edge labels, messages, notes and
aliases, and converting them to ASCII there turns working diagrams into parse
errors (``D[데이터（원본）]`` → ``D[데이터(원본)]``).

Usage:
    python fix_mermaid.py <file_or_dir> [--fix] [--json]

    --fix   Apply fixes in place (default: lint-only, report issues)
    --json  Output results as JSON

Examples:
    python fix_mermaid.py docs/PROJECT_ANALYSIS.md
    python fix_mermaid.py docs/ --fix
    python fix_mermaid.py docs/api.md --json
"""
from __future__ import annotations

import json
import logging
import re
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from validate_mermaid import (
    MmdcError,
    ValidationError,
    find_mmdc_executable,
    validate_file,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Reserved words (sequence diagram)
# ---------------------------------------------------------------------------

RESERVED_WORDS: dict[str, str] = {
    "opt": "optional fragment",
    "alt": "alternative paths",
    "par": "parallel execution",
    "loop": "loop block",
    "rect": "highlight region",
    "note": "note annotation",
    "end": "block terminator",
    "and": "parallel separator",
    "else": "alternative separator",
    "break": "break block",
    "critical": "critical section",
    "activate": "activation bar",
    "deactivate": "deactivation bar",
}

SAFE_RENAMES: dict[str, str] = {
    "opt": "OPTA",
    "alt": "ALTR",
    "par": "PRSR",
    "loop": "LOOPN",
    "rect": "RCTL",
    "note": "NOTEB",
    "end": "ENDP",
    "and": "ANDN",
    "else": "ELSN",
    "break": "BRKN",
    "critical": "CRIT",
    "activate": "ACTV",
    "deactivate": "DEACTV",
}

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

PARTICIPANT_RE = re.compile(r"^\s*participant\s+(\S+)\s+as\s+", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Unicode rules
# ---------------------------------------------------------------------------
#
# Every rule here was decided by rendering small cases with mmdc on Mermaid
# 11.12.2 and 12.1.0 (references/mermaid-v11-syntax.md §16). Inside label and
# message text every character below renders as-is, so the rules only touch
# the *syntax* of a line: node IDs, arrows, separators, label delimiters.
#
# Dropped after that evidence (they render identically to ASCII everywhere):
# U+FEFF BOM, the Unicode spaces U+00A0/U+202F/U+2009/U+200A/U+2007, single
# curly quotes, guillemets, U+2026 ellipsis, and the sequence-message entity
# escaping of { } [ ] ".

INVISIBLE_CHARS: frozenset[str] = frozenset({
    "\u200b",  # zero-width space
    "\u200c",  # zero-width non-joiner
    "\u200d",  # zero-width joiner
    "\u2060",  # word joiner
    "\u00ad",  # soft hyphen
})

# Typographic dashes are rewritten only inside an arrow (a dash run that ends
# in ">"); the run is then clamped to a length the diagram's grammar accepts.
TYPOGRAPHIC_DASHES: dict[str, str] = {
    "\u2014": "--",  # em dash (what autocorrect makes of "--")
    "\u2013": "-",   # en dash
    "\u2010": "-",   # hyphen
    "\u2212": "-",   # minus sign
}

# Fullwidth punctuation is rewritten only where it is flowchart syntax
# (shape delimiters after an ID, edge-label pipes, arrows, `;`, `,` and CSS
# `:`), plus the fullwidth colon used as the label separator of a sequence,
# class or state line. U+3002 is not here: `B。` → `B.` renders a node named
# "B.", so it is reported as a warning instead.
FULLWIDTH_PUNCT: dict[str, str] = {
    "\uff08": "(",  # fullwidth (
    "\uff09": ")",  # fullwidth )
    "\u3010": "[",  # 【
    "\u3011": "]",  # 】
    "\uff5b": "{",  # fullwidth {
    "\uff5d": "}",  # fullwidth }
    "\uff1a": ":",  # fullwidth :
    "\uff1b": ";",  # fullwidth ;
    "\uff0c": ",",  # fullwidth ,
    "\uff1d": "=",  # fullwidth =
    "\uff1e": ">",  # fullwidth >
    "\uff1c": "<",  # fullwidth <
    "\uff5c": "|",  # fullwidth |
}
FULLWIDTH_COLON = "\uff1a"
IDEOGRAPHIC_FULL_STOP = "\u3002"

# Curly double quotes are rewritten only when they delimit a whole label that
# fails unquoted (see SMART_QUOTE_LABEL_RE).
SMART_OPEN_QUOTES = "\u201c\u201e"   # “ „
SMART_CLOSE_QUOTES = "\u201d\u201c"  # ” “
SMART_QUOTES = "\u201c\u201d\u201e"
# Characters that make an unquoted flowchart label fail to parse.
LABEL_NEEDS_QUOTES = set('()[]{}|"')

# Unicode arrows are rewritten only where an arrow is expected.
FLOWCHART_ARROWS: dict[str, str] = {
    "\u2192": "-->",   # →
    "\u2194": "<-->",  # ↔
    "\u21d2": "==>",   # ⇒
}
EDGE_ARROWS: dict[str, str] = {"\u2192": "-->"}   # class and state diagrams
SEQUENCE_ARROWS: dict[str, str] = {"\u2192": "->>"}
# No ASCII arrow renders for these without swapping the operands.
UNSUPPORTED_ARROWS = "\u2190\u21d0\u2194\u21d2"  # ← ⇐ ↔ ⇒

# Characters that make a bare (unquoted, unbracketed) subgraph title fail.
_SUBGRAPH_TITLE_HAZARDS: frozenset[str] = frozenset(
    set(INVISIBLE_CHARS) | set(TYPOGRAPHIC_DASHES) | set(FULLWIDTH_PUNCT)
    | {IDEOGRAPHIC_FULL_STOP} | set(SMART_QUOTES) | set(FLOWCHART_ARROWS) | set(UNSUPPORTED_ARROWS),
)

_DASH_ARROW_RE = re.compile("<?[-\u2010\u2013\u2014\u2212]+(?=>)")
# A free-standing typographic dash that opens a flowchart edge label.
_EDGE_LABEL_DASH_RE = re.compile("(?<=\\s)[\u2010\u2013\u2014\u2212]+(?=\\s.*>)")
_INLINE_EDGE_OPEN_RE = re.compile(r"(?<![-=.])(?:--|==|-\.)(?=\s)")
_INLINE_EDGE_CLOSE_RE = re.compile(r"\s(?:--|==|\.-)")
_SEQ_TEXT_KEYWORD_RE = re.compile(
    r"\s*(?:loop|alt|else|opt|par_over|par|and|critical|option|break|rect|box|title"
    r"|accTitle|accDescr|links?|properties|details)\b",
    re.IGNORECASE,
)
_SEQ_PARTICIPANT_RE = re.compile(r"\s*(?:create\s+)?(?:participant|actor)\s", re.IGNORECASE)
_SEQ_NOTE_RE = re.compile(r"\s*note\s", re.IGNORECASE)
SMART_QUOTE_LABEL_RE = re.compile(
    "(?<=[\\[({|>/\\\\])([\u201c\u201e])([^\"\u201c\u201d\u201e\\n]*)([\u201d\u201c])(?=[\\])}|/\\\\])",
)

Span = tuple[int, int]


# ---------------------------------------------------------------------------
# Issue dataclass
# ---------------------------------------------------------------------------

class Issue:
    """Represents a single detected problem.

    Attributes:
        line: 1-based line number in the Markdown file.
        rule: Comma-separated rule name(s).
        before: The stripped line before the fix.
        after: The stripped line after the fix (equal to ``before`` for warnings).
        block: 1-based index of the mermaid block.
        severity: ``"error"`` when auto-fixed, ``"warning"`` when it needs a human.

    Examples:
        >>> Issue(3, "typo-dash", "A –> B", "A --> B").to_dict()["severity"]
        'error'
        >>> Issue(3, "unicode-arrow-manual", "A ← B", "A ← B", severity="warning").severity
        'warning'
    """

    def __init__(
        self,
        line: int,
        rule: str,
        before: str,
        after: str,
        block: int = 0,
        severity: str = "error",
    ) -> None:
        """Initialize an Issue.

        Args:
            line: 1-based line number in the Markdown file.
            rule: Comma-separated rule name(s).
            before: The stripped line before the fix.
            after: The stripped line after the fix.
            block: 1-based index of the mermaid block.
            severity: ``"error"`` (auto-fixed) or ``"warning"`` (manual).

        Examples:
            >>> Issue(1, "invisible-char", "A\\u200b --> B", "A --> B", block=2).block
            2
        """
        self.line = line
        self.rule = rule
        self.before = before
        self.after = after
        self.block = block
        self.severity = severity

    def to_dict(self) -> dict[str, str | int]:
        """Convert to a JSON-serializable dict.

        Returns:
            Dict with block, line, rule, severity, before and after.

        Examples:
            >>> sorted(Issue(1, "r", "a", "b").to_dict())
            ['after', 'before', 'block', 'line', 'rule', 'severity']
        """
        return {
            "block": self.block,
            "line": self.line,
            "rule": self.rule,
            "severity": self.severity,
            "before": self.before,
            "after": self.after,
        }


# ---------------------------------------------------------------------------
# Label-text detection: which parts of a line are text, not syntax
# ---------------------------------------------------------------------------

def _is_id_char(ch: str) -> bool:
    """Return True if ``ch`` can end a flowchart node ID.

    Args:
        ch: A single character.

    Returns:
        True for letters, digits and underscore (any script).

    Examples:
        >>> _is_id_char("A"), _is_id_char("가"), _is_id_char("-")
        (True, True, False)
    """
    return ch.isalnum() or ch == "_"


def _quote_end(line: str, start: int) -> int:
    """Return the index just past the ASCII double quote closing ``line[start]``.

    Args:
        line: The line being scanned.
        start: Index of an opening ``"``.

    Returns:
        Index after the closing quote, or ``len(line)`` if it is unclosed.

    Examples:
        >>> _quote_end('A["x"] --> B', 2)
        5
    """
    close = line.find('"', start + 1)
    return len(line) if close == -1 else close + 1


def _bracket_end(line: str, start: int) -> int:
    """Return the index just past the bracket matching ``line[start]``.

    Nesting is counted across ``()``, ``[]`` and ``{}`` together, and quoted
    strings are skipped, so ``A(["x (y)"])`` is one span.

    Args:
        line: The line being scanned.
        start: Index of an opening ``(``, ``[`` or ``{``.

    Returns:
        Index after the matching closer, or ``len(line)`` if unbalanced.

    Examples:
        >>> line = 'A(["x (y)"]) --> B'
        >>> line[1:_bracket_end(line, 1)]
        '(["x (y)"])'
    """
    depth = 0
    i = start
    while i < len(line):
        ch = line[i]
        if ch == '"':
            i = _quote_end(line, i)
            continue
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return len(line)


def _quote_spans(line: str) -> list[Span]:
    """Return the spans of ASCII double-quoted strings in ``line``.

    Args:
        line: A single line of mermaid code.

    Returns:
        List of ``(start, end)`` index pairs, end exclusive.

    Examples:
        >>> _quote_spans('state "a b" as S1')
        [(6, 11)]
    """
    spans: list[Span] = []
    i = line.find('"')
    while i != -1:
        end = _quote_end(line, i)
        spans.append((i, end))
        i = line.find('"', end)
    return spans


def _first_separator(line: str) -> int:
    """Return the index of the first ``:`` or ``：`` outside quotes and brackets.

    Args:
        line: A single line of a sequence, class or state diagram.

    Returns:
        The index, or -1 if the line has no separator.

    Examples:
        >>> _first_separator('A --> B : uses "x:y"')
        8
        >>> _first_separator("A->>B\\uff1a hi")
        5
        >>> _first_separator("S1 --> S2")
        -1
    """
    i = 0
    while i < len(line):
        ch = line[i]
        if ch == '"':
            i = _quote_end(line, i)
            continue
        if ch in "([{":
            i = _bracket_end(line, i)
            continue
        if ch in (":", FULLWIDTH_COLON):
            return i
        i += 1
    return -1


def _flowchart_text_spans(line: str) -> list[Span]:
    """Return the label-text spans of a flowchart line.

    Text is: quoted strings, node-shape contents (``[..]``, ``(..)``,
    ``{..}``, ``>..]`` and every nested form), edge labels (``|..|`` and
    ``-- .. -->`` / ``== .. ==>`` / ``-. .. .->``), ``@{..}`` metadata, bare
    subgraph titles, and the rest of ``title`` / ``accTitle`` / ``accDescr`` /
    ``click`` lines. Unclosed constructs extend to the end of the line, which
    only ever protects more.

    Args:
        line: A single flowchart line.

    Returns:
        List of ``(start, end)`` index pairs, end exclusive.

    Examples:
        >>> line = "A[데이터（원본）] -->|라벨（1）| B"
        >>> [line[s:e] for s, e in _flowchart_text_spans(line)]
        ['[데이터（원본）]', '|라벨（1）|']
        >>> line = "A -- 값—값 --> B"
        >>> [line[s:e] for s, e in _flowchart_text_spans(line)]
        [' 값—값']
        >>> [line[s:e] for s, e in _flowchart_text_spans("A（데이터） --> B")]
        []
    """
    n = len(line)
    keyword = re.match(r"\s*(?:(?:accTitle|accDescr)\b|click\s+\S+)", line)
    if keyword:
        return [(keyword.end(), n)]
    subgraph = re.match(r"\s*subgraph\s+", line)
    if subgraph and _is_bare_subgraph_title(line[subgraph.end():]):
        return [(subgraph.end(), n)]

    spans: list[Span] = []
    i = 0
    while i < n:
        ch = line[i]
        if ch == '"':
            end = _quote_end(line, i)
        elif line.startswith("@{", i):
            end = _bracket_end(line, i + 1)
        elif ch in "([{":
            end = _bracket_end(line, i)
        elif ch == ">" and i > 0 and _is_id_char(line[i - 1]):
            close = line.find("]", i + 1)
            end = n if close == -1 else close + 1
        elif ch == "|":
            close = line.find("|", i + 1)
            end = n if close == -1 else close + 1
        else:
            opener = _INLINE_EDGE_OPEN_RE.match(line, i)
            closer = _INLINE_EDGE_CLOSE_RE.search(line, opener.end()) if opener else None
            if opener and closer:
                spans.append((opener.end(), closer.start()))
                i = closer.start() + 1
            else:
                i += 1
            continue
        spans.append((i, end))
        i = end
    return spans


def _is_bare_subgraph_title(rest: str) -> bool:
    """Return True if the text after ``subgraph`` is an unquoted, unbracketed title.

    Args:
        rest: The part of the line after ``subgraph`` and its whitespace.

    Returns:
        True for ``subgraph Title text``; False for ``subgraph id [Title]``
        and ``subgraph "Title"``.

    Examples:
        >>> _is_bare_subgraph_title("처리（원본）")
        True
        >>> _is_bare_subgraph_title('S ["처리（원본）"]')
        False
    """
    return bool(rest.strip()) and not rest.lstrip().startswith('"') and "[" not in rest


def _rewrite_outside(
    line: str,
    spans: list[Span],
    rewrite: Callable[[str], str],
) -> str:
    """Apply ``rewrite`` to every part of ``line`` that is not inside ``spans``.

    Args:
        line: The line to rewrite.
        spans: Protected ``(start, end)`` ranges, sorted and non-overlapping.
        rewrite: Callable ``str -> str`` applied to each unprotected segment.

    Returns:
        The rewritten line.

    Examples:
        >>> _rewrite_outside("ab[cd]ef", [(2, 6)], str.upper)
        'AB[cd]EF'
    """
    out: list[str] = []
    pos = 0
    for start, end in sorted(spans):
        if start < pos:
            continue
        out.append(rewrite(line[pos:start]))
        out.append(line[start:end])
        pos = end
    out.append(rewrite(line[pos:]))
    return "".join(out)


def _outside_text(line: str, spans: list[Span]) -> str:
    """Return ``line`` with the protected ``spans`` removed.

    Args:
        line: The line.
        spans: Protected ``(start, end)`` ranges.

    Returns:
        The syntax part of the line only.

    Examples:
        >>> _outside_text("ab[cd]ef", [(2, 6)])
        'abef'
    """
    return "".join(ch for i, ch in enumerate(line) if not any(s <= i < e for s, e in spans))


# ---------------------------------------------------------------------------
# Unicode fixes for the syntax part of a line
# ---------------------------------------------------------------------------

def _drop_invisible(segment: str) -> str:
    """Delete zero-width characters and soft hyphens.

    Args:
        segment: Syntax text (never label text).

    Returns:
        The segment without INVISIBLE_CHARS.

    Examples:
        >>> _drop_invisible("A\\u200b --> B\\u00ad")
        'A --> B'
    """
    return "".join(ch for ch in segment if ch not in INVISIBLE_CHARS)


def _fix_dash_arrows(segment: str, family: str) -> str:
    """Rewrite typographic dashes inside arrows, clamped to a valid length.

    Only dash runs that end in ``>`` and contain a typographic dash are
    touched. Flowchart, class and state links need at least two dashes, so
    ``–>`` becomes ``-->``; sequence arrows take at most two, so ``-—>>``
    becomes ``-->>``. In a flowchart, a free-standing typographic dash that
    opens an edge label (``A — yes —> B``, autocorrected ``-- yes -->``)
    becomes ``--`` as well.

    Args:
        segment: Syntax text (never label text).
        family: Diagram family from ``diagram_family``.

    Returns:
        The segment with arrow dashes in ASCII.

    Examples:
        >>> _fix_dash_arrows("A \\u2013> B", "flowchart")
        'A --> B'
        >>> _fix_dash_arrows("A-\\u2014>>B", "sequence")
        'A-->>B'
        >>> _fix_dash_arrows("A\\u2013>>B", "sequence")
        'A->>B'
        >>> _fix_dash_arrows("A \\u2014 yes \\u2014> B", "flowchart")
        'A -- yes --> B'
        >>> _fix_dash_arrows("Front\\u2013end", "flowchart")
        'Front\\u2013end'
    """
    if family == "flowchart":
        segment = _EDGE_LABEL_DASH_RE.sub("--", segment)

    def repl(match: re.Match[str]) -> str:
        run = match.group(0)
        if not any(ch in TYPOGRAPHIC_DASHES for ch in run):
            return run
        head = "<" if run.startswith("<") else ""
        dashes = "".join(TYPOGRAPHIC_DASHES.get(ch, ch) for ch in run.lstrip("<"))
        too_long = family == "sequence" and len(dashes) > 2
        too_short = family != "sequence" and len(dashes) < 2
        return head + ("--" if too_long or too_short else dashes)

    return _DASH_ARROW_RE.sub(repl, segment)


def _fix_arrow_chars(segment: str, mapping: dict[str, str]) -> str:
    """Replace Unicode arrow characters with the family's ASCII arrow.

    Args:
        segment: Syntax text (never label text).
        mapping: Character → ASCII arrow for this diagram family.

    Returns:
        The rewritten segment.

    Examples:
        >>> _fix_arrow_chars("A \\u2192 B", FLOWCHART_ARROWS)
        'A --> B'
        >>> _fix_arrow_chars("A\\u2192B", SEQUENCE_ARROWS)
        'A->>B'
    """
    for ch, repl in mapping.items():
        segment = segment.replace(ch, repl)
    return segment


def _fix_fullwidth(segment: str) -> str:
    """Replace fullwidth punctuation with ASCII (flowchart syntax only).

    Args:
        segment: Flowchart syntax text (never label text).

    Returns:
        The rewritten segment.

    Examples:
        >>> _fix_fullwidth("A\\uff08데이터\\uff09 --\\uff1e B")
        'A(데이터) --> B'
    """
    for ch, repl in FULLWIDTH_PUNCT.items():
        segment = segment.replace(ch, repl)
    return segment


def _convert_separator(line: str) -> str:
    """Turn a fullwidth colon used as the label separator into ``:``.

    A ``：`` followed by an ASCII ``:`` with no whitespace in between
    (``A->>B：x: hi``) may be part of an ID, so it is left alone.

    Args:
        line: A sequence, class or state line.

    Returns:
        The line with its separator in ASCII.

    Examples:
        >>> _convert_separator("A->>B\\uff1a \\uac12\\uff1b")
        'A->>B: \\uac12\\uff1b'
        >>> _convert_separator("A->>B\\uff1ax: hi")
        'A->>B\\uff1ax: hi'
    """
    sep = _first_separator(line)
    if sep == -1 or line[sep] != FULLWIDTH_COLON:
        return line
    rest = line[sep + 1:]
    colon = rest.find(":")
    if colon > 0 and not any(ch.isspace() for ch in rest[:colon]):
        return line
    return line[:sep] + ":" + rest


def _fix_smart_quote_labels(line: str, always: bool) -> str:
    """Turn curly quotes that delimit a whole label into ASCII quotes.

    ``A[“a (b)”]`` fails because the parentheses are unquoted; ``A["a (b)"]``
    renders. When the label would render without quoting (``A[“데이터”]``),
    the curly quotes are part of the text and stay, unless ``always`` is set
    (class labels, which must be quoted).

    Args:
        line: A flowchart or class line.
        always: Convert even when the label text needs no quoting.

    Returns:
        The line with delimiter quotes in ASCII.

    Examples:
        >>> _fix_smart_quote_labels("A[\\u201ca (b)\\u201d] --> B", always=False)
        'A["a (b)"] --> B'
        >>> _fix_smart_quote_labels("A[\\u201c\\ub370\\uc774\\ud130\\u201d] --> B", always=False)
        'A[\\u201c\\ub370\\uc774\\ud130\\u201d] --> B'
    """
    quoted = _quote_spans(line)

    def repl(match: re.Match[str]) -> str:
        if any(s <= match.start() < e for s, e in quoted):
            return match.group(0)
        inner = match.group(2)
        if not always and not LABEL_NEEDS_QUOTES.intersection(inner):
            return match.group(0)
        return f'"{inner}"'

    return SMART_QUOTE_LABEL_RE.sub(repl, line)


def _fix_subgraph_title(line: str) -> str:
    """Quote a bare subgraph title that contains Unicode punctuation.

    A bare title (``subgraph 처리（원본）``) fails on any of these characters,
    and converting them to ASCII does not help (``subgraph 처리(원본)`` fails
    too), so the title is wrapped in double quotes instead. A title that is
    entirely wrapped in curly quotes gets ASCII quotes.

    Args:
        line: A flowchart line.

    Returns:
        The line with its title quoted, or unchanged.

    Examples:
        >>> _fix_subgraph_title("    subgraph \\ucc98\\ub9ac\\uff08\\uc6d0\\ubcf8\\uff09")
        '    subgraph "\\ucc98\\ub9ac\\uff08\\uc6d0\\ubcf8\\uff09"'
        >>> _fix_subgraph_title("    subgraph \\u201c\\ucc98\\ub9ac\\u201d")
        '    subgraph "\\ucc98\\ub9ac"'
        >>> _fix_subgraph_title("    subgraph \\ucc98\\ub9ac \\ub2e8\\uacc4")
        '    subgraph \\ucc98\\ub9ac \\ub2e8\\uacc4'
    """
    match = re.match(r"(\s*subgraph\s+)(.*?)(\s*)$", line)
    if not match or not _is_bare_subgraph_title(match.group(2)):
        return line
    head, title, tail = match.groups()
    if '"' in title or not _SUBGRAPH_TITLE_HAZARDS.intersection(title):
        return line
    if len(title) > 1 and title[0] in SMART_OPEN_QUOTES and title[-1] in SMART_CLOSE_QUOTES:
        title = title[1:-1]
    return f'{head}"{title}"{tail}'


def _sequence_syntax_end(line: str) -> tuple[int, bool]:
    """Return where the syntax part of a sequence line ends.

    Args:
        line: A sequence-diagram line.

    Returns:
        ``(end, is_message)``: index where text starts (``len(line)`` if
        none) and whether the syntax part may hold an arrow.

    Examples:
        >>> _sequence_syntax_end("A->>B: hi")
        (6, True)
        >>> _sequence_syntax_end("participant A as Alice")
        (17, False)
        >>> _sequence_syntax_end("loop every minute")
        (4, False)
    """
    keyword = _SEQ_TEXT_KEYWORD_RE.match(line)
    if keyword:
        return keyword.end(), False
    if _SEQ_PARTICIPANT_RE.match(line):
        alias = re.search(r"\sas\s", line, re.IGNORECASE)
        meta = line.find("@{")
        ends = [i for i in (alias.end() if alias else -1, meta) if i != -1]
        return (min(ends) if ends else len(line)), False
    sep = _first_separator(line)
    end = len(line) if sep == -1 else sep + 1
    return end, not _SEQ_NOTE_RE.match(line)


def _manual_unicode(segment: str, family: str) -> list[str]:
    """Return warning rule names for Unicode syntax with no safe auto-fix.

    Args:
        segment: The syntax part of a line, after auto-fixes.
        family: Diagram family from ``diagram_family``.

    Returns:
        Warning rule names (possibly empty).

    Examples:
        >>> _manual_unicode("A \\u2190 B", "flowchart")
        ['unicode-arrow-manual']
        >>> _manual_unicode("A --> B\\u3002", "flowchart")
        ['fullwidth-period']
    """
    rules: list[str] = []
    if any(ch in UNSUPPORTED_ARROWS for ch in segment):
        rules.append("unicode-arrow-manual")
    if family == "flowchart" and IDEOGRAPHIC_FULL_STOP in segment:
        rules.append("fullwidth-period")
    return rules


def fix_unicode(line: str, family: str = "flowchart") -> tuple[str, list[str], list[str]]:
    """Fix Unicode characters used as Mermaid syntax, leaving label text alone.

    Args:
        line: A single line of mermaid code (not a comment or front matter).
        family: Diagram family from ``diagram_family``. ``"other"`` diagrams
            are never rewritten.

    Returns:
        Tuple of (fixed line, auto-fix rule names, warning rule names).

    Examples:
        >>> fix_unicode("    D[\\ub370\\uc774\\ud130\\uff08\\uc6d0\\ubcf8\\uff09]")
        ('    D[\\ub370\\uc774\\ud130\\uff08\\uc6d0\\ubcf8\\uff09]', [], [])
        >>> fix_unicode("    A\\uff08\\ub370\\uc774\\ud130\\uff09 \\u2014> B")[:2]
        ('    A(\\ub370\\uc774\\ud130) --> B', ['typo-dash', 'fullwidth-cjk'])
        >>> fix_unicode("    A->>B\\uff1a \\uac12\\uff1b\\uac12", "sequence")[:2]
        ('    A->>B: \\uac12\\uff1b\\uac12', ['fullwidth-cjk'])
        >>> fix_unicode("    A \\u2190 B")
        ('    A \\u2190 B', [], ['unicode-arrow-manual'])
        >>> fix_unicode('    state "\\uac12\\u2190\\uac12" as S1', "state")
        ('    state "\\uac12\\u2190\\uac12" as S1', [], [])
    """
    if family == "other":
        return line, [], []
    rules: list[str] = []

    def apply(name: str, new: str) -> None:
        nonlocal line
        if new != line:
            rules.append(name)
            line = new

    if family == "flowchart":
        apply("smart-quote", _fix_smart_quote_labels(line, always=False))
        apply("subgraph-title-quote", _fix_subgraph_title(line))
        # Spans are recomputed after every pass: an ASCII edge-label opener
        # produced by the dash pass protects that label from later passes.
        # The dash pass runs again last to catch `—＞` once `＞` is ASCII.
        passes: list[tuple[str, Callable[[str], str]]] = [
            ("invisible-char", _drop_invisible),
            ("typo-dash", lambda s: _fix_dash_arrows(s, family)),
            ("unicode-arrow", lambda s: _fix_arrow_chars(s, FLOWCHART_ARROWS)),
            ("fullwidth-cjk", _fix_fullwidth),
            ("typo-dash", lambda s: _fix_dash_arrows(s, family)),
        ]
        for name, rewrite in passes:
            apply(name, _rewrite_outside(line, _flowchart_text_spans(line), rewrite))
        warnings = _manual_unicode(_outside_text(line, _flowchart_text_spans(line)), family)
        return line, list(dict.fromkeys(rules)), warnings

    # sequence, class, state: the syntax part is everything before the label text
    if family != "sequence" or not (_SEQ_TEXT_KEYWORD_RE.match(line) or _SEQ_PARTICIPANT_RE.match(line)):
        apply("fullwidth-cjk", _convert_separator(line))
    if family == "class" and re.match(r"\s*class\s+[^\s\[]+\[", line):
        apply("smart-quote", _fix_smart_quote_labels(line, always=True))
    if family == "state":
        apply("smart-quote", re.sub(
            "^(\\s*state\\s+)[\u201c\u201e]([^\"\u201c\u201d\u201e]*)[\u201d\u201c](?=\\s+as\\s)",
            r'\1"\2"', line))
    if family == "sequence":
        end, is_message = _sequence_syntax_end(line)
    else:
        sep = _first_separator(line)
        end, is_message = (len(line) if sep == -1 else sep), True
    head, tail = line[:end], line[end:]
    protect = _quote_spans(head) if family != "sequence" else []
    new_head = _rewrite_outside(head, protect, _drop_invisible)
    apply("invisible-char", new_head + tail)
    head = new_head
    if is_message:
        arrows = SEQUENCE_ARROWS if family == "sequence" else EDGE_ARROWS
        new_head = _rewrite_outside(head, protect, lambda s: _fix_dash_arrows(s, family))
        apply("typo-dash", new_head + tail)
        head = new_head
        new_head = _rewrite_outside(head, protect, lambda s: _fix_arrow_chars(s, arrows))
        apply("unicode-arrow", new_head + tail)
        head = new_head
    warnings = _manual_unicode(_outside_text(head, _quote_spans(head)), family) if is_message else []
    return line, rules, warnings


# ---------------------------------------------------------------------------
# Diagram type detection
# ---------------------------------------------------------------------------

def diagram_header(block_lines: list[str]) -> str:
    """Return the diagram type declaration line of a mermaid block.

    Skips an optional leading YAML front matter block (``---`` ... ``---``),
    blank lines, and ``%%`` comments/directives. Mermaid v12 changed the
    default theme, look, and layout, and its release notes tell authors to
    pin the old ones in front matter, so the declaration is often not the
    first line of the block.

    Args:
        block_lines: Lines inside a mermaid block (without the fences).

    Returns:
        The stripped declaration line (e.g. ``"sequenceDiagram"``), or an
        empty string if the block has no declaration.

    Examples:
        >>> diagram_header(["sequenceDiagram", "A->>B: hi"])
        'sequenceDiagram'
        >>> diagram_header(["---", "config:", "  look: classic", "---", "sequenceDiagram"])
        'sequenceDiagram'
        >>> diagram_header(["%% comment", "flowchart TD"])
        'flowchart TD'
    """
    i = 0
    while i < len(block_lines) and not block_lines[i].strip():
        i += 1
    if i < len(block_lines) and block_lines[i].strip() == "---":
        i += 1
        while i < len(block_lines) and block_lines[i].strip() != "---":
            i += 1
        i += 1  # skip the closing ---
    for line in block_lines[i:]:
        stripped = line.strip()
        if not stripped or stripped.startswith("%%"):
            continue
        return stripped
    return ""


def diagram_family(header: str) -> str:
    """Map a diagram declaration to the family the Unicode rules understand.

    Args:
        header: The declaration line from ``diagram_header``.

    Returns:
        ``"flowchart"``, ``"sequence"``, ``"class"``, ``"state"``, or
        ``"other"`` (never rewritten by the Unicode rules).

    Examples:
        >>> diagram_family("graph TD"), diagram_family("sequenceDiagram")
        ('flowchart', 'sequence')
        >>> diagram_family("stateDiagram-v2"), diagram_family("\\u200bclassDiagram")
        ('state', 'class')
        >>> diagram_family("gantt")
        'other'
    """
    words = "".join(ch for ch in header if ch not in INVISIBLE_CHARS and ch != "\ufeff").split()
    keyword = words[0] if words else ""
    if keyword in ("flowchart", "graph", "flowchart-elk"):
        return "flowchart"
    if keyword == "sequenceDiagram":
        return "sequence"
    if keyword in ("classDiagram", "classDiagram-v2"):
        return "class"
    if keyword in ("stateDiagram", "stateDiagram-v2"):
        return "state"
    return "other"


def _text_only_lines(block_lines: list[str], family: str) -> set[int]:
    """Return indices of block lines that hold only text or configuration.

    These are never rewritten: YAML front matter, ``%%`` comments, class
    member bodies, multi-line state notes and ``accDescr { ... }`` blocks.

    Args:
        block_lines: Lines inside a mermaid block.
        family: Diagram family from ``diagram_family``.

    Returns:
        Set of 0-based line indices.

    Examples:
        >>> sorted(_text_only_lines(["---", "title: x", "---", "classDiagram", "class A {", "+f（）", "}"], "class"))
        [0, 1, 2, 5, 6]
    """
    skip: set[int] = set()
    i = 0
    while i < len(block_lines) and not block_lines[i].strip():
        i += 1
    if i < len(block_lines) and block_lines[i].strip() == "---":
        skip.add(i)
        i += 1
        while i < len(block_lines) and block_lines[i].strip() != "---":
            skip.add(i)
            i += 1
        skip.add(i)
    closer: re.Pattern[str] | None = None
    for j, line in enumerate(block_lines):
        stripped = line.strip()
        if j in skip:
            continue
        if closer is not None:
            skip.add(j)
            if closer.search(stripped):
                closer = None
        elif stripped.startswith("%%"):
            skip.add(j)
        elif re.match(r"accDescr\s*\{", stripped) and "}" not in stripped:
            closer = re.compile(r"\}")
        elif family == "class" and re.match(r"class\s+\S+.*\{$", stripped):
            closer = re.compile(r"^\}")
        elif family == "state" and re.match(r"note\s+(?:left|right)\s+of\s+[^:]+$", stripped, re.IGNORECASE):
            closer = re.compile(r"^end\s+note$", re.IGNORECASE)
    return skip


def fix_block_unicode(
    block_lines: list[str],
    block_start: int,
    block_num: int,
) -> tuple[list[str], list[Issue]]:
    """Apply the Unicode rules to every syntax line of one mermaid block.

    Args:
        block_lines: Lines inside the mermaid block (without the fences).
        block_start: 0-based file index of the block's first line.
        block_num: 1-based block index.

    Returns:
        Tuple of (fixed lines, issues). Auto-fixes have severity ``error``,
        Unicode that needs a human has severity ``warning``.

    Examples:
        >>> lines, issues = fix_block_unicode(["flowchart TD", "    A \\u2013> B[\\uac12\\u2013\\uac12]"], 0, 1)
        >>> lines[1], issues[0].rule
        ('    A --> B[\\uac12\\u2013\\uac12]', 'typo-dash')
    """
    family = diagram_family(diagram_header(block_lines))
    skipped = _text_only_lines(block_lines, family)
    header = next((j for j, ln in enumerate(block_lines) if j not in skipped and ln.strip()), -1)
    fixed_block: list[str] = []
    issues: list[Issue] = []
    for j, bline in enumerate(block_lines):
        line_num = block_start + j + 1
        if j in skipped:
            fixed_block.append(bline)
            continue
        if j == header:
            fixed = _drop_invisible(bline)
            fix_rules, warn_rules = (["invisible-char"] if fixed != bline else []), []
        else:
            fixed, fix_rules, warn_rules = fix_unicode(bline, family)
        if fix_rules:
            issues.append(Issue(line_num, ",".join(fix_rules), bline.strip(), fixed.strip(), block_num))
        if warn_rules:
            issues.append(Issue(
                line_num, ",".join(warn_rules), fixed.strip(), fixed.strip(), block_num, severity="warning",
            ))
        fixed_block.append(fixed)
    return fixed_block, issues


# ---------------------------------------------------------------------------
# Reserved word detection & fix
# ---------------------------------------------------------------------------

def find_reserved_word_issues(
    block_lines: list[str],
    start_line: int,
    block_num: int,
) -> tuple[list[Issue], dict[str, str]]:
    """Detect reserved word conflicts in participant IDs.

    Args:
        block_lines: Lines inside a mermaid block.
        start_line: 1-based line number of block start in the file.
        block_num: Block index.

    Returns:
        Tuple of (issues found, rename map {old_id: new_id}).
    """
    if not block_lines or diagram_header(block_lines) != "sequenceDiagram":
        return [], {}

    issues: list[Issue] = []
    rename_map: dict[str, str] = {}

    for i, line in enumerate(block_lines):
        match = PARTICIPANT_RE.match(line)
        if match:
            pid = match.group(1)
            if pid.lower() in RESERVED_WORDS:
                safe_name = SAFE_RENAMES.get(pid.lower(), pid + "X")
                new_line = line.replace(
                    f"participant {pid} ",
                    f"participant {safe_name} ",
                    1,
                )
                issues.append(Issue(
                    line=start_line + i,
                    rule="reserved-word",
                    before=line.strip(),
                    after=new_line.strip(),
                    block=block_num,
                ))
                rename_map[pid] = safe_name

    return issues, rename_map


def apply_renames(block_lines: list[str], rename_map: dict[str, str]) -> list[str]:
    """Replace reserved participant IDs throughout the block.

    Args:
        block_lines: Lines of the mermaid block.
        rename_map: Mapping of old ID → new safe ID.

    Returns:
        Updated block lines.
    """
    if not rename_map:
        return block_lines

    result: list[str] = []
    for line in block_lines:
        for old, new in rename_map.items():
            # Replace whole-word occurrences of the ID
            line = re.sub(rf"\b{re.escape(old)}\b", new, line)
        result.append(line)
    return result


# ---------------------------------------------------------------------------
# Main processing
# ---------------------------------------------------------------------------

def process_file(filepath: Path, apply_fix: bool = False) -> list[Issue]:
    """Process a single Markdown file for Mermaid issues.

    Args:
        filepath: Path to the Markdown file.
        apply_fix: If True, write fixes back to file.

    Returns:
        List of issues found: auto-fixes (severity ``error``) and Unicode
        that needs manual review (severity ``warning``). The file is only
        rewritten when a fix changed it.
    """
    content = filepath.read_text(encoding="utf-8")
    lines = content.split("\n")
    all_issues: list[Issue] = []
    result_lines: list[str] = []

    in_mermaid = False
    block_num = 0
    block_start = 0
    block_lines: list[str] = []

    i = 0
    while i < len(lines):
        line = lines[i]

        if line.strip() == "```mermaid":
            in_mermaid = True
            block_num += 1
            block_start = i + 1  # 0-based index of first content line
            block_lines = []
            result_lines.append(line)
            i += 1
            continue

        if in_mermaid and line.strip() == "```":
            in_mermaid = False

            # Phase 1: Reserved word detection
            rw_issues, rename_map = find_reserved_word_issues(
                block_lines, block_start + 1, block_num,
            )
            all_issues.extend(rw_issues)

            # Apply renames if needed
            if rename_map:
                block_lines = apply_renames(block_lines, rename_map)

            # Phase 2: Unicode in diagram syntax (label text is never touched).
            # Sequence-message entity escaping of { } [ ] " was retired: both
            # Mermaid 11.12.2 and 12.1.0 render those characters unescaped.
            fixed_block, unicode_issues = fix_block_unicode(block_lines, block_start, block_num)
            all_issues.extend(unicode_issues)

            result_lines.extend(fixed_block)
            result_lines.append(line)  # closing ```
            i += 1
            continue

        if in_mermaid:
            block_lines.append(line)
        else:
            result_lines.append(line)

        i += 1

    if apply_fix and result_lines != lines:
        filepath.write_text("\n".join(result_lines), encoding="utf-8")

    return all_issues


# ---------------------------------------------------------------------------
# mmdc feedback loop
# ---------------------------------------------------------------------------


@dataclass
class FixSuggestion:
    """A suggested fix in response to a specific mmdc error.

    Attributes:
        rule: Name of the fix rule that applies (e.g. "reserved-word", "unquoted-label").
        hint: Human-readable hint shown to the user / logged.

    Examples:
        >>> s = FixSuggestion(rule="reserved-word", hint="rename 'end' → 'ENDP'")
        >>> s.rule
        'reserved-word'
    """

    rule: str
    hint: str


@dataclass
class FeedbackReport:
    """Aggregate outcome of the static-fix + mmdc-validate feedback loop.

    Attributes:
        iterations: Number of fix/validate cycles performed (>= 1).
        static_issues: Issues detected and fixed by the static linter passes.
        final_errors: Remaining mmdc errors after all iterations (empty == success).
        suggestions: Per-iteration list of suggestions derived from mmdc errors.

    Examples:
        >>> r = FeedbackReport(iterations=1, static_issues=[], final_errors=[], suggestions=[])
        >>> r.iterations
        1
    """

    iterations: int
    static_issues: list[Issue] = field(default_factory=list)
    final_errors: list[ValidationError] = field(default_factory=list)
    suggestions: list[list[FixSuggestion]] = field(default_factory=list)


# Tokens that mmdc reports as `got '...'` when a sequence-diagram reserved word
# was used as a participant identifier. Matches RESERVED_WORDS above.
_RESERVED_WORD_TOKENS: frozenset[str] = frozenset(RESERVED_WORDS.keys())

# Flowchart / graph tokens that appear in the `Expecting 'X', ..., got 'Y'`
# list when a bracket / paren / brace inside a label was not quoted.
_FLOWCHART_SHAPE_TOKENS: frozenset[str] = frozenset({
    "SQE",   # ]
    "PE",    # )
    "DOUBLECIRCLEEND",
    "STADIUMEND",
    "SUBROUTINEEND",
    "CYLINDEREND",
    "DIAMOND_STOP",
})


def suggest_fix_for_mmdc_error(error: MmdcError) -> FixSuggestion | None:
    """Map a parsed mmdc error to a concrete fix suggestion.

    Args:
        error: The structured error emitted by parse_mmdc_stderr.

    Returns:
        A FixSuggestion if a known pattern matches, None otherwise.

    Examples:
        >>> err = MmdcError(line=3, got="end", expected=["participant"], context="")
        >>> suggest_fix_for_mmdc_error(err).rule
        'reserved-word'
    """
    got_lower = error.got.lower()
    if got_lower in _RESERVED_WORD_TOKENS and "participant" in error.expected:
        safe = SAFE_RENAMES.get(got_lower, got_lower.upper() + "X")
        return FixSuggestion(
            rule="reserved-word",
            hint=f"rename participant ID '{error.got}' → '{safe}' (reserved keyword)",
        )

    if error.got in {"PS", "SQS", "DOUBLECIRCLESTART"} or any(
        t in _FLOWCHART_SHAPE_TOKENS for t in error.expected
    ):
        return FixSuggestion(
            rule="unquoted-label",
            hint="wrap the node label in double quotes — it contains "
            "unescaped (, ), [, ], {, or }",
        )

    return None


def fix_with_mmdc_feedback(
    filepath: Path,
    max_iterations: int = 3,
) -> FeedbackReport:
    """Iteratively apply static fixes and validate with mmdc until clean or stuck.

    Strategy (per iteration):
        1. Run ``process_file(apply_fix=True)`` to apply static rules.
        2. Run ``validate_file`` (mmdc) to surface remaining parse errors.
        3. Derive fix suggestions from the errors via ``suggest_fix_for_mmdc_error``.
        4. If the second iteration produces the same errors as the first,
           terminate early — we have nothing more to try automatically.

    Args:
        filepath: Markdown file to repair and validate.
        max_iterations: Maximum number of fix/validate cycles. Defaults to 3.

    Returns:
        FeedbackReport summarizing what happened.

    Raises:
        FileNotFoundError: If filepath does not exist.

    Examples:
        >>> fix_with_mmdc_feedback(Path("diagram.md"))  # doctest: +SKIP
        FeedbackReport(iterations=1, ...)
    """
    if not filepath.is_file():
        raise FileNotFoundError(filepath)

    all_static_issues: list[Issue] = []
    all_suggestions: list[list[FixSuggestion]] = []
    previous_error_keys: set[tuple[int, int, str]] = set()
    iterations = 0
    final_errors: list[ValidationError] = []

    for iteration in range(1, max_iterations + 1):
        iterations = iteration

        issues = process_file(filepath, apply_fix=True)
        all_static_issues.extend(issues)

        final_errors = validate_file(filepath)
        if not final_errors:
            all_suggestions.append([])
            logger.info("mmdc validation clean after iteration %d", iteration)
            break

        suggestions: list[FixSuggestion] = []
        current_error_keys: set[tuple[int, int, str]] = set()
        for err in final_errors:
            if err.mmdc_error is not None:
                suggestion = suggest_fix_for_mmdc_error(err.mmdc_error)
                if suggestion is not None:
                    suggestions.append(suggestion)
                current_error_keys.add(
                    (err.block_index, err.file_line, err.mmdc_error.got),
                )
        all_suggestions.append(suggestions)

        if iteration > 1 and current_error_keys == previous_error_keys:
            logger.info("mmdc errors did not change — giving up after iteration %d", iteration)
            break
        previous_error_keys = current_error_keys

    return FeedbackReport(
        iterations=iterations,
        static_issues=all_static_issues,
        final_errors=final_errors,
        suggestions=all_suggestions,
    )


def _print_feedback_summary(filepath: Path, report: FeedbackReport) -> None:
    """Print a human-readable summary of a feedback-loop run.

    Args:
        filepath: File that was processed.
        report: The FeedbackReport returned by fix_with_mmdc_feedback.

    Examples:
        >>> _print_feedback_summary(Path("x.md"), FeedbackReport(iterations=1))  # doctest: +SKIP
    """
    print(f"\n=== {filepath} ===")
    print(f"  iterations: {report.iterations}")
    fixes = [i for i in report.static_issues if i.severity == "error"]
    warnings = {(i.line, i.rule) for i in report.static_issues if i.severity == "warning"}
    print(f"  static fixes applied: {len(fixes)}")
    if warnings:
        print(f"  warnings (manual review): {len(warnings)}")
    if report.final_errors:
        print(f"  mmdc errors remaining: {len(report.final_errors)}")
        for err in report.final_errors:
            got = err.mmdc_error.got if err.mmdc_error is not None else "?"
            print(f"    - block #{err.block_index} line {err.file_line}: got '{got}'")
        flat = [s for batch in report.suggestions for s in batch]
        if flat:
            print("  suggestions:")
            for s in flat[:5]:
                print(f"    * {s.rule}: {s.hint}")
    else:
        print("  mmdc: all blocks render successfully.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    """CLI entry point.

    Returns:
        Exit code (0: no issues, 1: issues found/fixed).
    """
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return 0

    apply_fix = "--fix" in sys.argv
    output_json = "--json" in sys.argv
    with_mmdc = "--with-mmdc" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    if with_mmdc and find_mmdc_executable() is None:
        print(
            "ERROR: --with-mmdc requires mmdc on PATH. "
            "Install via `npm i -g --allow-scripts=puppeteer @mermaid-js/mermaid-cli`.",
            file=sys.stderr,
        )
        return 2

    targets: list[Path] = []
    for arg in args:
        p = Path(arg)
        if p.is_file():
            targets.append(p)
        elif p.is_dir():
            targets.extend(sorted(p.rglob("*.md")))
        else:
            print(f"Warning: {arg} not found, skipping", file=sys.stderr)

    all_issues: list[dict[str, str | int]] = []
    all_mmdc_errors: list[dict[str, object]] = []
    for filepath in targets:
        if with_mmdc:
            report = fix_with_mmdc_feedback(filepath)
            for issue in report.static_issues:
                d = issue.to_dict()
                d["file"] = str(filepath)
                all_issues.append(d)
            for err in report.final_errors:
                d = err.to_dict()
                d["file"] = str(filepath)
                all_mmdc_errors.append(d)
            if not output_json:
                _print_feedback_summary(filepath, report)
            continue

        issues = process_file(filepath, apply_fix=apply_fix)
        for issue in issues:
            d = issue.to_dict()
            d["file"] = str(filepath)
            all_issues.append(d)

    if output_json:
        payload: dict[str, object] = {"issues": all_issues, "total": len(all_issues)}
        if with_mmdc:
            payload["mmdc_errors"] = all_mmdc_errors
            payload["mmdc_total"] = len(all_mmdc_errors)
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    elif with_mmdc:
        # Feedback summary is already printed per file; nothing more to say here.
        pass
    elif not all_issues:
        print("OK: No Mermaid issues found.")
    else:
        errors = [d for d in all_issues if d["severity"] == "error"]
        warnings = [d for d in all_issues if d["severity"] == "warning"]
        action = "Fixed" if apply_fix else "Found"
        print(f"{action} {len(errors)} issue(s), {len(warnings)} warning(s):\n")
        print(f"{'Sev':<7} | {'Block':>5} | {'Line':>4} | {'Rule':<20} | Before")
        print("-" * 88)
        for d in all_issues:
            before = str(d["before"])
            if len(before) > 50:
                before = before[:50] + "..."
            print(f"{d['severity']:<7} | {d['block']:>5} | {d['line']:>4} | {d['rule']:<20} | {before}")

        if warnings:
            print("\nWarnings need manual review (no safe automatic fix).")
        if errors and not apply_fix:
            print("\nRun with --fix to apply corrections.")

    if with_mmdc:
        # Exit status mirrors the ground truth: only unresolved mmdc errors fail.
        return 1 if all_mmdc_errors else 0
    return 1 if all_issues else 0


if __name__ == "__main__":
    sys.exit(main())
