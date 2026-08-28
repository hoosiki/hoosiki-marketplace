# Install Morph MCP

Ensure Morph MCP is properly installed and running for Claude Code CLI.

Morph MCP provides fast file editing and codebase search capabilities via the Morph API.

## Prerequisites

- `MORPH_API_KEY` environment variable must be set before running this command
- Get your API key from https://morphllm.com

## Instructions

1. **Check Current Status**
   Run `claude mcp list` and check if morph-mcp is present and shows "✓ Connected"

2. **If Already Installed and Connected**
   - Output exactly: `morph-mcp already installed`
   - Stop here - do not proceed further

3. **Check MORPH_API_KEY**
   - Verify the environment variable is set:
     ```bash
     echo $MORPH_API_KEY
     ```
   - If empty or not set, report failure: `MORPH_API_KEY environment variable is not set`
   - Stop here if not set

4. **If Not Installed or Not Connected**
   - If morph-mcp exists but is not connected, first remove it:
     ```bash
     claude mcp remove morph-mcp -s user
     ```
   - Install Morph MCP:
     ```bash
     claude mcp add --scope user morph-mcp \
       -e MORPH_API_KEY=$MORPH_API_KEY \
       -- npx -y @morphllm/morphmcp
     ```

5. **Validate Installation**
   - Run `claude mcp list` again
   - Verify morph-mcp shows "✓ Connected"

## Error Handling

If installation fails:
- Ensure `MORPH_API_KEY` is set: `export MORPH_API_KEY=your_api_key`
- Ensure `npx` is installed (comes with Node.js)
- Get your API key from https://morphllm.com

## Notes

- Three tools are exposed, and **all of them are always exposed** — upstream no longer
  supports narrowing the set from the server side. Manage tool visibility on the client:

  | Tool | What it does |
  |------|--------------|
  | `edit_file` | Applies code changes at high throughput |
  | `codebase_search` | Natural-language code exploration, backed by WarpGrep |
  | `github_codebase_search` | Searches any public GitHub repo by URL or `owner/repo` |

- **Existing installs may carry a stale `ENABLED_TOOLS` value.** Earlier versions of this
  command set `ENABLED_TOOLS=edit_file,warpgrep_codebase_search`. That variable is no
  longer honored, and `warpgrep_codebase_search` no longer exists as a tool name — it is
  now `codebase_search`. Check with `claude mcp get morph-mcp`; if the variable is present,
  remove and reinstall using the command above to clear it
