---
name: pyright-setup
description: "Detect Python version from the project's virtual environment and add [tool.pyright] configuration to pyproject.toml. Use when: (1) setting up a new Python project for Neovim/VS Code LSP, (2) user reports 'Import could not be resolved' errors from Pyright/basedpyright, (3) user asks to configure pyright, (4) user mentions LSP import resolution issues in their editor. Triggers on: 'pyright', 'import could not be resolved', 'LSP setup', 'configure pyright', 'pyright config'."
---

# Pyright Setup

Add `[tool.pyright]` configuration to `pyproject.toml` by auto-detecting the Python version and virtual environment.

## When to Run

- User reports "Import X could not be resolved" in Neovim, VS Code, or any Pyright-based LSP
- User asks to set up pyright for a Python project
- A new Python project needs LSP configuration

## Workflow

1. Run the setup script to detect Python version and venv, then inject config into pyproject.toml:

```bash
python3 scripts/setup_pyright.py /path/to/project
```

2. The script auto-detects:
   - **Python version**: from `.venv` interpreter → `requires-python` in pyproject.toml → system python3
   - **Venv directory**: checks `.venv`, `venv`, `.env`, `env` in order

3. Inserts before `[tool.mypy]` if present, otherwise appends to the file:

```toml
# ==== pyright ====

[tool.pyright]
venvPath = "."
venv = ".venv"
pythonVersion = "3.13"
```

4. Skips if `[tool.pyright]` already exists.

5. Remind user to restart their LSP (`:LspRestart` in Neovim, or reload window in VS Code).
