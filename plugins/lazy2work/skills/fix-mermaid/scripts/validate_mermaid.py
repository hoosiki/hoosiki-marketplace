#!/usr/bin/env python3
"""Mermaid diagram validator using the mmdc CLI.

Extracts ```mermaid fenced blocks from a Markdown file, renders each one
through the Mermaid CLI (mmdc), and reports parse/render errors back to
the caller as structured data. Consumed by fix_mermaid.py to drive a
feedback loop: static fix → mmdc validate → parse error → targeted fix.

Usage:
    python validate_mermaid.py <file> [--json]

Examples:
    python validate_mermaid.py docs/architecture.md
    python validate_mermaid.py docs/api.md --json
"""
from __future__ import annotations

import json
import logging
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MMDC_TIMEOUT_SECONDS: int = 60
MMDC_ERROR_LINE_RE: re.Pattern[str] = re.compile(r"Parse error on line (\d+):")
MMDC_CONTEXT_RE: re.Pattern[str] = re.compile(r"Parse error on line \d+:\s*\n(.+?)\n[-^]+\^", re.DOTALL)
MMDC_EXPECTED_RE: re.Pattern[str] = re.compile(r"Expecting\s+(.+?),\s+got\s+'([^']+)'", re.DOTALL)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class MermaidBlock:
    """A single fenced mermaid block extracted from a Markdown file.

    Attributes:
        index: Zero-based block number within the file.
        start_line: 1-based line number of the ```mermaid fence line. The first
            code line sits at ``start_line + 1`` and mmdc reports parse errors
            relative to the code, so ``file_line == start_line + mmdc_line``.
        code: The diagram source (without the fences).

    Examples:
        >>> b = MermaidBlock(index=0, start_line=3, code="flowchart TD\\nA --> B")
        >>> b.start_line
        3
    """

    index: int
    start_line: int
    code: str


@dataclass
class MmdcError:
    """A parsed mmdc parse/render error.

    Attributes:
        line: 1-based line number inside the mermaid block where the parser choked.
        got: The unexpected token reported by the Langium/Jison parser.
        expected: Tokens the parser was expecting at that point.
        context: Short snippet from the diagram showing the offending region.

    Examples:
        >>> e = MmdcError(line=3, got="end", expected=["participant"], context="...")
        >>> e.got
        "end"
    """

    line: int
    got: str
    expected: list[str] = field(default_factory=list)
    context: str = ""


@dataclass
class MmdcResult:
    """Outcome of a single mmdc invocation.

    Attributes:
        success: Whether mmdc exited with code 0.
        error: Parsed error detail if mmdc failed and emitted a Parse error.
        raw_stderr: Full stderr output, kept for debugging and unknown error classes.

    Examples:
        >>> r = MmdcResult(success=True, error=None, raw_stderr="")
        >>> r.success
        True
    """

    success: bool
    error: MmdcError | None
    raw_stderr: str = ""


@dataclass
class ValidationError:
    """A validation error mapped back to the original Markdown file.

    Attributes:
        block_index: Index of the mermaid block inside the file.
        file_line: 1-based line number in the original .md file where the problem occurs.
        block_line: 1-based line number inside the mermaid block (as reported by mmdc).
        mmdc_error: The underlying mmdc parse error.
        raw_stderr: Verbatim stderr for debugging.

    Examples:
        >>> e = ValidationError(block_index=0, file_line=5, block_line=3, mmdc_error=None)
        >>> e.file_line
        5
    """

    block_index: int
    file_line: int
    block_line: int
    mmdc_error: MmdcError | None
    raw_stderr: str = ""

    def to_dict(self) -> dict[str, object]:
        """Serialize to a JSON-safe dict.

        Returns:
            Dictionary containing all fields plus unpacked mmdc_error.

        Examples:
            >>> e = ValidationError(block_index=0, file_line=5, block_line=3, mmdc_error=None)
            >>> e.to_dict()["block_index"]
            0
        """
        mmdc: dict[str, object] | None = None
        if self.mmdc_error is not None:
            mmdc = {
                "line": self.mmdc_error.line,
                "got": self.mmdc_error.got,
                "expected": self.mmdc_error.expected,
                "context": self.mmdc_error.context,
            }
        return {
            "block_index": self.block_index,
            "file_line": self.file_line,
            "block_line": self.block_line,
            "mmdc_error": mmdc,
            "raw_stderr": self.raw_stderr,
        }


# ---------------------------------------------------------------------------
# Executable discovery
# ---------------------------------------------------------------------------


def find_mmdc_executable() -> str | None:
    """Locate the mmdc binary on PATH.

    Returns:
        Absolute path to mmdc, or None if it is not installed.

    Examples:
        >>> find_mmdc_executable()  # doctest: +SKIP
        "/opt/homebrew/bin/mmdc"
    """
    return shutil.which("mmdc")


# ---------------------------------------------------------------------------
# Block extraction
# ---------------------------------------------------------------------------


def extract_mermaid_blocks(filepath: Path) -> list[MermaidBlock]:
    """Extract every ```mermaid fenced block from a Markdown file.

    Args:
        filepath: Path to the Markdown file.

    Returns:
        List of MermaidBlock entries in file order. Empty list if none found.

    Examples:
        >>> extract_mermaid_blocks(Path("README.md"))  # doctest: +SKIP
        [MermaidBlock(index=0, start_line=12, code='flowchart TD\\nA --> B')]
    """
    content = filepath.read_text(encoding="utf-8")
    lines = content.split("\n")
    blocks: list[MermaidBlock] = []

    in_block = False
    block_start = 0
    buffer: list[str] = []
    index = 0

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not in_block and stripped == "```mermaid":
            in_block = True
            block_start = i + 1  # 1-based line number of the ```mermaid fence
            buffer = []
            continue
        if in_block and stripped == "```":
            blocks.append(MermaidBlock(index=index, start_line=block_start, code="\n".join(buffer)))
            index += 1
            in_block = False
            buffer = []
            continue
        if in_block:
            buffer.append(line)

    return blocks


# ---------------------------------------------------------------------------
# Stderr parsing
# ---------------------------------------------------------------------------


def parse_mmdc_stderr(stderr: str) -> MmdcError | None:
    """Parse mmdc's Parse error output into structured fields.

    Args:
        stderr: Verbatim stderr from an `mmdc` invocation.

    Returns:
        MmdcError if a Parse error was detected, otherwise None.

    Examples:
        >>> err = parse_mmdc_stderr("Error: Parse error on line 3:\\n...foo\\n---^\\nExpecting 'A', got 'B'")
        >>> err.line
        3
        >>> err.got
        "B"
    """
    line_match = MMDC_ERROR_LINE_RE.search(stderr)
    if line_match is None:
        return None

    line_no = int(line_match.group(1))

    expected: list[str] = []
    got = ""
    expected_match = MMDC_EXPECTED_RE.search(stderr)
    if expected_match is not None:
        expected_raw = expected_match.group(1)
        got = expected_match.group(2)
        # Tokens are quoted with single quotes and comma-separated.
        expected = [t.strip().strip("'") for t in expected_raw.split(",") if t.strip()]

    context = ""
    context_match = MMDC_CONTEXT_RE.search(stderr)
    if context_match is not None:
        context = context_match.group(1).strip()

    return MmdcError(line=line_no, got=got, expected=expected, context=context)


# ---------------------------------------------------------------------------
# mmdc invocation
# ---------------------------------------------------------------------------


def run_mmdc(code: str, work_dir: Path) -> MmdcResult:
    """Run mmdc on a single diagram and return a structured result.

    The diagram is written to a temporary .mmd file inside work_dir; mmdc is
    invoked with -i pointing at that file and -o pointing at a .svg file
    that we never read. Only the exit code and stderr matter.

    Args:
        code: Mermaid diagram source (no fences).
        work_dir: Directory to use for the temporary input/output files.

    Returns:
        MmdcResult with success flag, parsed error, and raw stderr.

    Examples:
        >>> result = run_mmdc("flowchart TD\\nA --> B", Path("/tmp"))  # doctest: +SKIP
        >>> result.success
        True
    """
    mmdc = find_mmdc_executable()
    if mmdc is None:
        return MmdcResult(success=False, error=None, raw_stderr="mmdc not found on PATH")

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".mmd",
        dir=str(work_dir),
        delete=False,
        encoding="utf-8",
    ) as tmp_in:
        tmp_in.write(code)
        input_path = Path(tmp_in.name)

    output_path = input_path.with_suffix(".svg")
    cmd = [mmdc, "-i", str(input_path), "-o", str(output_path), "-q"]

    try:
        proc = subprocess.run(  # noqa: S603 — mmdc path comes from shutil.which
            cmd,
            capture_output=True,
            text=True,
            timeout=MMDC_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired:
        logger.warning("mmdc timed out after %ds", MMDC_TIMEOUT_SECONDS)
        return MmdcResult(success=False, error=None, raw_stderr=f"timeout after {MMDC_TIMEOUT_SECONDS}s")
    finally:
        for p in (input_path, output_path):
            try:
                p.unlink()
            except FileNotFoundError:
                pass

    if proc.returncode == 0:
        return MmdcResult(success=True, error=None, raw_stderr=proc.stderr)

    error = parse_mmdc_stderr(proc.stderr)
    return MmdcResult(success=False, error=error, raw_stderr=proc.stderr)


# ---------------------------------------------------------------------------
# File-level validation
# ---------------------------------------------------------------------------


def validate_file(filepath: Path) -> list[ValidationError]:
    """Validate every mermaid block in a Markdown file via mmdc.

    Args:
        filepath: Path to the Markdown file.

    Returns:
        One ValidationError per failed block (empty list if all pass).

    Examples:
        >>> validate_file(Path("clean.md"))  # doctest: +SKIP
        []
    """
    blocks = extract_mermaid_blocks(filepath)
    errors: list[ValidationError] = []
    work_dir = filepath.parent

    for block in blocks:
        result = run_mmdc(block.code, work_dir)
        if result.success:
            continue
        block_line = result.error.line if result.error is not None else 1
        file_line = block.start_line + block_line  # fence line + mmdc's 1-based code line
        errors.append(
            ValidationError(
                block_index=block.index,
                file_line=file_line,
                block_line=block_line,
                mmdc_error=result.error,
                raw_stderr=result.raw_stderr,
            ),
        )

    return errors


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------


def main() -> int:
    """Run the validator as a CLI.

    Returns:
        Exit code. 0 if no errors, 1 if validation failed, 2 if mmdc is missing.

    Examples:
        >>> main()  # doctest: +SKIP
        0
    """
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return 0

    if find_mmdc_executable() is None:
        print("ERROR: mmdc not found on PATH. Install via `npm i -g @mermaid-js/mermaid-cli`.", file=sys.stderr)
        return 2

    output_json = "--json" in sys.argv
    positional = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not positional:
        print("Usage: validate_mermaid.py <file> [--json]", file=sys.stderr)
        return 2

    filepath = Path(positional[0])
    if not filepath.is_file():
        print(f"ERROR: {filepath} is not a file", file=sys.stderr)
        return 2

    errors = validate_file(filepath)

    if output_json:
        payload = {"file": str(filepath), "errors": [e.to_dict() for e in errors], "total": len(errors)}
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 1 if errors else 0

    if not errors:
        print("OK: All mermaid blocks render successfully.")
        return 0

    print(f"Found {len(errors)} mmdc error(s):\n")
    for e in errors:
        got = e.mmdc_error.got if e.mmdc_error is not None else "?"
        expected = ", ".join(e.mmdc_error.expected[:5]) if e.mmdc_error is not None else "?"
        print(f"  block #{e.block_index} — file line {e.file_line} (block line {e.block_line})")
        print(f"    got '{got}', expected one of: {expected}")
        if e.mmdc_error is not None and e.mmdc_error.context:
            print(f"    context: {e.mmdc_error.context[:80]}")
        print()

    return 1


if __name__ == "__main__":
    sys.exit(main())
