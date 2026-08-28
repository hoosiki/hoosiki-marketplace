# Install Serena MCP

Ensure Serena MCP is properly installed and running for Claude Code CLI.

Serena is a code intelligence MCP server from https://github.com/oraios/serena that
provides semantic code analysis and editing capabilities.

## Prerequisites

- Python **3.11–3.14** (`serena-agent` declares `>=3.11,<3.15`)
- `uv` — install with `brew install uv` if missing

## Instructions

1. **Check Current Status**
   Run `claude mcp list` and check if serena is present and shows "✓ Connected"

2. **If Already Installed and Connected**
   - Output exactly: `serena already installed`
   - Stop here - do not proceed further

3. **If serena exists but is not connected, remove it first**
   ```bash
   claude mcp remove serena -s user
   ```

4. **Install uv (if not already installed)**
   ```bash
   which uv || brew install uv
   ```

5. **Install Serena**
   ```bash
   uv tool install -p 3.13 serena-agent
   ```
   Verify the launcher is on PATH:
   ```bash
   serena --version
   ```

6. **Install Serena MCP**
   ```bash
   claude mcp add --scope user serena \
     -- serena start-mcp-server --context claude-code --project-from-cwd
   ```

7. **Validate Installation**
   - Run `claude mcp list` again
   - Verify serena shows "✓ Connected"

## Error Handling

If installation fails:
- Ensure `uv` is installed: `brew install uv`
- Verify Python 3.11–3.14 is available (`python3 --version`); 3.10 and 3.15+ are unsupported
- If `serena` is not found after step 5, ensure `~/.local/bin` is on your `PATH`
- Check network connection for PyPI access

## Notes

- `--context claude-code` disables tools that duplicate Claude Code's built-in capabilities
- `--project-from-cwd` auto-detects the project from the current working directory
  (via `.serena/project.yml` or `.git`)
- For a **single project** instead of a global install, substitute:
  `claude mcp add serena -- serena start-mcp-server --context claude-code --project "$(pwd)"`
- Upstream also recommends a system-prompt override, since recent Claude Code releases
  reduced adherence to Serena's tool instructions:
  ```bash
  claude --system-prompt="$(serena prompts print-cc-system-prompt-override)"
  ```
- **Alternative — run from git HEAD** instead of the PyPI release:
  ```bash
  claude mcp add --scope user serena -- \
    uvx --from git+https://github.com/oraios/serena serena start-mcp-server \
    --context claude-code --project-from-cwd
  ```
  This was the previously documented approach. It still works, but resolves the
  repository on every launch, which is slower and tracks unreleased dev builds.
  Prefer `uv tool install serena-agent` unless you need an unreleased fix
