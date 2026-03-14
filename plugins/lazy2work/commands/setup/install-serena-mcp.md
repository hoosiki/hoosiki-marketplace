# Install Serena MCP

Ensure Serena MCP is properly installed and running for Claude Code CLI.

Serena is a code intelligence MCP server from https://github.com/oraios/serena that provides semantic code analysis capabilities.

## Instructions

1. **Check Current Status**
   Run `claude mcp list` and check if serena is present and shows "✓ Connected"

2. **If Already Installed and Connected**
   - Output exactly: `serena already installed`
   - Stop here - do not proceed further

3. **If Not Installed or Not Connected**
   - If serena exists but is not connected, first remove it:
     ```bash
     claude mcp remove serena -s user
     ```

4. **Install uv (if not already installed)**
   - Check if uv is installed:
     ```bash
     which uv
     ```
   - If not installed, install uv via Homebrew:
     ```bash
     brew install uv
     ```

5. **Pre-fetch Serena package**
   - Download and cache Serena using uvx:
     ```bash
     uvx --from git+https://github.com/oraios/serena serena start-mcp-server --help
     ```

6. **Install Serena MCP**
   ```bash
   claude mcp add --scope user serena -- uvx --from git+https://github.com/oraios/serena serena start-mcp-server --context=claude-code --project-from-cwd
   ```

7. **Validate Installation**
   - Run `claude mcp list` again
   - Verify serena shows "✓ Connected"

## Error Handling

If installation fails:
- Ensure `uv` is installed: `brew install uv`
- Check network connection for GitHub access
- Verify Python 3.10+ is installed (`python --version`)

## Notes

- `--context=claude-code` disables tools that duplicate Claude Code's built-in capabilities
- `--project-from-cwd` enables automatic project detection from the current working directory
