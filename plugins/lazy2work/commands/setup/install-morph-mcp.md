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

4. **If Not Installed or Not Connected**
   - If morph-mcp exists but is not connected, first remove it:
     ```bash
     claude mcp remove morph-mcp -s user
     ```
   - Install Morph MCP:
     ```bash
     claude mcp add morph-mcp \
       --scope user \
       -e MORPH_API_KEY=$MORPH_API_KEY \
       -e ENABLED_TOOLS=edit_file,warpgrep_codebase_search \
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

- `ENABLED_TOOLS=edit_file,warpgrep_codebase_search` limits which tools are exposed
- To enable all tools, remove the `ENABLED_TOOLS` environment variable
