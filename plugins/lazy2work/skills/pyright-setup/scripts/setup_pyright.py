#!/usr/bin/env python3
"""Detect Python version and add [tool.pyright] config to pyproject.toml."""

import re
import subprocess
import sys
from pathlib import Path


def detect_python_version(project_root: Path) -> str:
    """Detect Python version from the project environment.

    Priority:
    1. .venv interpreter
    2. pyproject.toml requires-python
    3. System python3
    """
    # 1) .venv python
    venv_python = project_root / ".venv" / "bin" / "python"
    if venv_python.exists():
        try:
            result = subprocess.run(
                [str(venv_python), "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass

    # 2) pyproject.toml requires-python
    pyproject = project_root / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text()
        match = re.search(r'requires-python\s*=\s*["\'].*?(\d+\.\d+)', content)
        if match:
            return match.group(1)

    # 3) System python3
    try:
        result = subprocess.run(
            ["python3", "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass

    return "3.12"


def detect_venv_name(project_root: Path) -> str:
    """Detect the virtual environment directory name."""
    for name in [".venv", "venv", ".env", "env"]:
        if (project_root / name / "bin" / "python").exists():
            return name
    return ".venv"


def has_pyright_config(content: str) -> bool:
    """Check if [tool.pyright] already exists in pyproject.toml."""
    return bool(re.search(r'^\[tool\.pyright\]', content, re.MULTILINE))


def add_pyright_config(project_root: Path) -> dict:
    """Add [tool.pyright] section to pyproject.toml.

    Returns a dict with keys: success, message, python_version, venv_name
    """
    pyproject = project_root / "pyproject.toml"
    if not pyproject.exists():
        return {"success": False, "message": "pyproject.toml not found"}

    content = pyproject.read_text()

    if has_pyright_config(content):
        return {"success": False, "message": "[tool.pyright] already exists in pyproject.toml"}

    python_version = detect_python_version(project_root)
    venv_name = detect_venv_name(project_root)

    pyright_block = f'''
# ==== pyright ====

[tool.pyright]
venvPath = "."
venv = "{venv_name}"
pythonVersion = "{python_version}"
'''

    # Insert before [tool.mypy] if it exists, otherwise append before the last tool section
    mypy_match = re.search(r'\n# ==== mypy ====', content)
    if mypy_match:
        insert_pos = mypy_match.start()
        new_content = content[:insert_pos] + pyright_block + content[insert_pos:]
    else:
        # Try to insert before the first [tool.*] section that comes after [tool.ruff] or similar
        # Otherwise append at the end
        new_content = content.rstrip() + "\n" + pyright_block

    pyproject.write_text(new_content)

    return {
        "success": True,
        "message": f"Added [tool.pyright] with pythonVersion=\"{python_version}\", venv=\"{venv_name}\"",
        "python_version": python_version,
        "venv_name": venv_name,
    }


if __name__ == "__main__":
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    result = add_pyright_config(root)
    if result["success"]:
        print(f"✅ {result['message']}")
    else:
        print(f"⚠️  {result['message']}")
        sys.exit(1)
