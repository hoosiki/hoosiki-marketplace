# Install Sequential Thinking MCP

Ensure Sequential Thinking MCP is properly installed and running for Claude Code CLI.

## Instructions

1. **Check Current Status**
   Run `claude mcp list` and check if sequential-thinking is present and shows "✓ Connected"

2. **If Already Installed and Connected**
   - Output exactly: `sequential-thinking already installed`
   - Stop here - do not proceed further

3. **If Not Installed or Not Connected**
   - If sequential-thinking exists but is not connected, first remove it:
     ```bash
     claude mcp remove sequential-thinking -s user
     ```
   - Install Sequential Thinking MCP:
     ```bash
     claude mcp add sequential-thinking npx -y @modelcontextprotocol/server-sequential-thinking -s user
     ```

4. **Validate Installation**
   - Run `claude mcp list` again
   - Verify sequential-thinking shows "✓ Connected"

## Error Handling

If installation fails:
- Ensure `npx` is installed (comes with Node.js)
- Verify Node.js version is 18+ (`node --version`)
