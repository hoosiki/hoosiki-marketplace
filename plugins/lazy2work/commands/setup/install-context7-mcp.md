# Install Context7 MCP

Ensure Context7 MCP is properly installed and running for Claude Code CLI.

## Instructions

1. **Check Current Status**
   Run `claude mcp list` and check if context7 is present and shows "✓ Connected"

2. **If Already Installed and Connected**
   - Output exactly: `context7 already installed`
   - Stop here - do not proceed further

3. **If Not Installed or Not Connected**
   - If context7 exists but is not connected, first remove it:
     ```bash
     claude mcp remove context7 -s user
     ```
   - Install Context7 MCP:
     ```bash
     claude mcp add context7 npx -y @upstash/context7-mcp -s user
     ```

4. **Validate Installation**
   - Run `claude mcp list` again
   - Verify context7 shows "✓ Connected"

## Error Handling

If installation fails:
- Ensure `npx` is installed (comes with Node.js)
- Verify Node.js version is 18+ (`node --version`)
