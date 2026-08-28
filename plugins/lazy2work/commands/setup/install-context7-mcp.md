# Install Context7 MCP

Ensure Context7 MCP is properly installed and running for Claude Code CLI.

Context7 provides up-to-date, version-specific documentation for libraries and frameworks.

## Prerequisites

- An API key is **recommended** (free at https://context7.com/dashboard) — it raises
  rate limits. Set `CONTEXT7_API_KEY` before running this command to use the hosted
  server; without it, fall back to the local stdio server in step 4b.

## Instructions

1. **Check Current Status**
   Run `claude mcp list` and check if context7 is present and shows "✓ Connected"

2. **If Already Installed and Connected**
   - Output exactly: `context7 already installed`
   - Stop here - do not proceed further

3. **If context7 exists but is not connected, remove it first**
   ```bash
   claude mcp remove context7 -s user
   ```

4. **Install Context7 MCP**

   **4a. Hosted server (recommended)** — requires `CONTEXT7_API_KEY`:
   ```bash
   claude mcp add --scope user --transport http context7 \
     https://mcp.context7.com/mcp \
     --header "Authorization: Bearer $CONTEXT7_API_KEY"
   ```

   **4b. Local stdio server (no API key)** — lower rate limits:
   ```bash
   claude mcp add --scope user context7 -- npx -y @upstash/context7-mcp
   ```

5. **Validate Installation**
   - Run `claude mcp list` again
   - Verify context7 shows "✓ Connected"

## Error Handling

If installation fails:
- Hosted: verify the key at https://context7.com/dashboard and check network access
  to https://mcp.context7.com
- Local: ensure `npx` is installed (comes with Node.js) and Node.js is 18+ (`node --version`)

## Notes

- Upstream also ships an interactive installer, `npx ctx7 setup`, which handles
  authentication and lets you pick CLI+Skills or MCP mode. This command performs the
  equivalent MCP-mode setup non-interactively
- Upstream's README now documents only the hosted endpoint. The `@upstash/context7-mcp`
  stdio package is still published and functional, and remains the zero-config option
  when no API key is available
- Put the flags **before** the server name and separate the subprocess with `--`;
  `claude mcp add` treats trailing tokens as command arguments
