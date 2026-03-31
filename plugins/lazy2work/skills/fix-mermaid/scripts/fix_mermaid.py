#!/usr/bin/env python3
"""Mermaid diagram linter and auto-fixer for Markdown files.

Scans Markdown files for ```mermaid code blocks and detects/fixes:
  1. Sequence diagram reserved word conflicts (participant IDs)
  2. Special characters in message text ({, }, [, ], ")
  3. Unicode issues (smart quotes, fullwidth CJK, invisible chars, typographic dashes)

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
import re
import sys
import unicodedata
from pathlib import Path

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
# Unicode replacement maps
# ---------------------------------------------------------------------------

SMART_QUOTES: dict[str, str] = {
    "\u201c": '"',  # left double
    "\u201d": '"',  # right double
    "\u2018": "'",  # left single
    "\u2019": "'",  # right single
    "\u201e": '"',  # low double
    "\u00ab": '"',  # guillemet left
    "\u00bb": '"',  # guillemet right
}

TYPOGRAPHIC_DASHES: dict[str, str] = {
    "\u2014": "--",  # em dash
    "\u2013": "-",   # en dash
    "\u2010": "-",   # hyphen char
    "\u2212": "-",   # minus sign
}

FULLWIDTH_CJK: dict[str, str] = {
    "\uff08": "(",  # fullwidth (
    "\uff09": ")",  # fullwidth )
    "\u3010": "[",  # 【
    "\u3011": "]",  # 】
    "\uff5b": "{",  # fullwidth {
    "\uff5d": "}",  # fullwidth }
    "\uff1a": ":",  # fullwidth :
    "\uff1b": ";",  # fullwidth ;
    "\uff0c": ",",  # fullwidth ,
    "\u3002": ".",  # 。
    "\uff1d": "=",  # fullwidth =
    "\uff1e": ">",  # fullwidth >
    "\uff1c": "<",  # fullwidth <
    "\uff5c": "|",  # fullwidth |
}

INVISIBLE_CHARS: set[str] = {
    "\u200b",  # zero-width space
    "\u200c",  # zero-width non-joiner
    "\u200d",  # zero-width joiner
    "\u2060",  # word joiner
    "\ufeff",  # BOM
    "\u00ad",  # soft hyphen
}

UNICODE_SPACES: dict[str, str] = {
    "\u00a0": " ",  # non-breaking space
    "\u202f": " ",  # narrow no-break space
    "\u2009": " ",  # thin space
    "\u200a": " ",  # hair space
    "\u2007": " ",  # figure space
}

UNICODE_ARROWS: dict[str, str] = {
    "\u2192": "-->",   # →
    "\u2190": "<--",   # ←
    "\u2194": "<-->",  # ↔
    "\u21d2": "==>",   # ⇒
    "\u21d0": "<==",   # ⇐
    "\u2026": "...",   # …
}

# Mermaid entity escapes for message text
ENTITY_MAP: dict[str, str] = {
    "{": "#123;",
    "}": "#125;",
    "[": "#91;",
    "]": "#93;",
    '"': "#34;",
}

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

PARTICIPANT_RE = re.compile(r"^\s*participant\s+(\S+)\s+as\s+", re.IGNORECASE)
ARROW_MSG_RE = re.compile(r"^(\s*\S+\s*-[-]?>>?\+?\s*-?\s*\S+\s*:\s*)(.*)")
NOTE_MSG_RE = re.compile(
    r"^(\s*Note\s+(?:right of|left of|over)\s+[^:]+:\s*)(.*)", re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Issue dataclass
# ---------------------------------------------------------------------------

class Issue:
    """Represents a single detected problem."""

    def __init__(
        self,
        line: int,
        rule: str,
        before: str,
        after: str,
        block: int = 0,
    ) -> None:
        self.line = line
        self.rule = rule
        self.before = before
        self.after = after
        self.block = block

    def to_dict(self) -> dict[str, str | int]:
        """Convert to JSON-serializable dict."""
        return {
            "block": self.block,
            "line": self.line,
            "rule": self.rule,
            "before": self.before,
            "after": self.after,
        }


# ---------------------------------------------------------------------------
# Unicode fixes (applied to all lines inside mermaid blocks)
# ---------------------------------------------------------------------------

def fix_unicode(line: str) -> tuple[str, list[str]]:
    """Replace problematic Unicode characters with ASCII equivalents.

    Args:
        line: A single line of mermaid code.

    Returns:
        Tuple of (fixed line, list of applied rule names).
    """
    rules: list[str] = []
    original = line

    # Invisible characters: delete
    for ch in INVISIBLE_CHARS:
        if ch in line:
            line = line.replace(ch, "")
            rules.append("invisible-char")

    # Unicode spaces → ASCII space
    for ch, repl in UNICODE_SPACES.items():
        if ch in line:
            line = line.replace(ch, repl)
            rules.append("unicode-space")

    # Smart quotes → ASCII quotes
    for ch, repl in SMART_QUOTES.items():
        if ch in line:
            line = line.replace(ch, repl)
            rules.append("smart-quote")

    # Typographic dashes → ASCII dashes
    for ch, repl in TYPOGRAPHIC_DASHES.items():
        if ch in line:
            line = line.replace(ch, repl)
            rules.append("typo-dash")

    # Fullwidth CJK punctuation → ASCII
    for ch, repl in FULLWIDTH_CJK.items():
        if ch in line:
            line = line.replace(ch, repl)
            rules.append("fullwidth-cjk")

    # Unicode arrows → Mermaid arrows (only in non-arrow contexts)
    for ch, repl in UNICODE_ARROWS.items():
        if ch in line:
            line = line.replace(ch, repl)
            rules.append("unicode-arrow")

    if line != original:
        return line, list(set(rules))
    return line, []


# ---------------------------------------------------------------------------
# Message entity escaping
# ---------------------------------------------------------------------------

def escape_message_text(text: str) -> str:
    """Replace {, }, [, ], \" in message text with Mermaid entities.

    Args:
        text: Message text portion (after : in arrows/notes).

    Returns:
        Escaped text safe for Mermaid parsing.
    """
    for ch, entity in ENTITY_MAP.items():
        text = text.replace(ch, entity)
    return text


def fix_message_line(line: str) -> tuple[str, bool]:
    """Escape special chars in arrow/note message text.

    Args:
        line: A single line inside a mermaid block.

    Returns:
        Tuple of (fixed line, whether changes were made).
    """
    for regex in (ARROW_MSG_RE, NOTE_MSG_RE):
        match = regex.match(line)
        if match:
            prefix = match.group(1)
            message = match.group(2)
            if any(ch in message for ch in "{}[]\""):
                return prefix + escape_message_text(message), True
    return line, False


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
    if not block_lines or block_lines[0].strip() != "sequenceDiagram":
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
        List of issues found.
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

            # Phase 2: Unicode + message escaping (line by line)
            fixed_block: list[str] = []
            for j, bline in enumerate(block_lines):
                line_num = block_start + j + 1  # 1-based

                # Unicode fixes
                fixed, unicode_rules = fix_unicode(bline)
                if unicode_rules:
                    all_issues.append(Issue(
                        line=line_num,
                        rule=",".join(unicode_rules),
                        before=bline.strip(),
                        after=fixed.strip(),
                        block=block_num,
                    ))
                    bline = fixed

                # Message entity escaping
                escaped, changed = fix_message_line(bline)
                if changed:
                    all_issues.append(Issue(
                        line=line_num,
                        rule="message-escape",
                        before=bline.strip(),
                        after=escaped.strip(),
                        block=block_num,
                    ))
                    bline = escaped

                fixed_block.append(bline)

            result_lines.extend(fixed_block)
            result_lines.append(line)  # closing ```
            i += 1
            continue

        if in_mermaid:
            block_lines.append(line)
        else:
            result_lines.append(line)

        i += 1

    if apply_fix and all_issues:
        filepath.write_text("\n".join(result_lines), encoding="utf-8")

    return all_issues


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
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

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
    for filepath in targets:
        issues = process_file(filepath, apply_fix=apply_fix)
        for issue in issues:
            d = issue.to_dict()
            d["file"] = str(filepath)
            all_issues.append(d)

    if output_json:
        print(json.dumps({"issues": all_issues, "total": len(all_issues)}, indent=2))
    elif not all_issues:
        print("OK: No Mermaid issues found.")
    else:
        action = "Fixed" if apply_fix else "Found"
        print(f"{action} {len(all_issues)} issue(s):\n")
        print(f"{'Block':>5} | {'Line':>4} | {'Rule':<20} | Before")
        print("-" * 80)
        for d in all_issues:
            before = str(d["before"])
            if len(before) > 50:
                before = before[:50] + "..."
            print(f"{d['block']:>5} | {d['line']:>4} | {d['rule']:<20} | {before}")

        if not apply_fix:
            print(f"\nRun with --fix to apply corrections.")

    return 1 if all_issues else 0


if __name__ == "__main__":
    sys.exit(main())
