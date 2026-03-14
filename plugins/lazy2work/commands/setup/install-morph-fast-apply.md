# Install Morph Fast Apply MCP

Ensure Morph Fast Apply MCP is properly installed and running for Claude Code CLI.

Morph Fast Apply provides fast code application and transformation capabilities via the Morph API.

## Prerequisites

- `MORPH_API_KEY` environment variable must be set before running this command
- Get your API key from https://morphllm.com

## Instructions

1. **Check Current Status**
   Run `claude mcp list` and check if morph-fast-apply is present and shows "✓ Connected"

2. **If Already Installed and Connected**
   - Output exactly: `morph-fast-apply already installed`
   - Stop here - do not proceed further

3. **Check MORPH_API_KEY**
   - Verify the environment variable is set:
     ```bash
     echo $MORPH_API_KEY
     ```
   - If empty or not set, report failure: `MORPH_API_KEY environment variable is not set`

4. **If Not Installed or Not Connected**
   - If morph-fast-apply exists but is not connected, first remove it:
     ```bash
     claude mcp remove morph-fast-apply -s user
     ```
   - Install Morph Fast Apply MCP:
     ```bash
     claude mcp add morph-fast-apply \
       -e MORPH_API_KEY=$MORPH_API_KEY \
       -e ALL_TOOLS=true \
       -- npx -y @morph-llm/morph-fast-apply
     ```

5. **Validate Installation**
   - Run `claude mcp list` again
   - Verify morph-fast-apply shows "✓ Connected"

## Error Handling

If installation fails:
- Ensure `MORPH_API_KEY` is set: `export MORPH_API_KEY=your_api_key`
- Ensure `npx` is installed (comes with Node.js)
- Get your API key from https://morphllm.com

## Notes

- `ALL_TOOLS=true` enables all available tools
- To limit tools, replace `ALL_TOOLS=true` with specific tool configuration
