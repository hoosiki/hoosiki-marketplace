# Install Sequential Thinking MCP

Ensure Sequential Thinking MCP is properly installed and running for Claude Code CLI.

Sequential Thinking provides a structured, revisable chain-of-thought tool for breaking
down complex problems.

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
     claude mcp add --scope user sequential-thinking \
       -- npx -y @modelcontextprotocol/server-sequential-thinking
     ```

4. **Validate Installation**
   - Run `claude mcp list` again
   - Verify sequential-thinking shows "✓ Connected"

## Error Handling

If installation fails:
- Ensure `npx` is installed (comes with Node.js)
- Verify Node.js version is 18+ (`node --version`)

## Notes

- Maintained in the official `modelcontextprotocol/servers` repository and actively
  published; unlike several sibling reference servers, it has not been archived
- Put the flags **before** the server name and separate the subprocess with `--`;
  `claude mcp add` treats trailing tokens as command arguments, so a trailing `-s user`
  is fragile
