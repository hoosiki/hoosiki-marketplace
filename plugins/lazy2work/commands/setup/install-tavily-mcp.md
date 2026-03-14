# Install Tavily MCP

Ensure Tavily MCP is properly installed and running for Claude Code CLI.

Tavily MCP provides web search and research capabilities via the Tavily API.

## Prerequisites

- `TAVILY_API_KEY` environment variable must be set before running this command
- Get your API key from https://tavily.com

## Instructions

1. **Check Current Status**
   Run `claude mcp list` and check if tavily is present and shows "✓ Connected"

2. **If Already Installed and Connected**
   - Output exactly: `tavily already installed`
   - Stop here - do not proceed further

3. **Check TAVILY_API_KEY**
   - Verify the environment variable is set:
     ```bash
     echo $TAVILY_API_KEY
     ```
   - If empty or not set, report failure: `TAVILY_API_KEY environment variable is not set`
   - Stop here if not set

4. **If Not Installed or Not Connected**
   - If tavily exists but is not connected, first remove it:
     ```bash
     claude mcp remove tavily -s user
     ```
   - Install Tavily MCP:
     ```bash
     claude mcp add --transport http --scope user tavily "https://mcp.tavily.com/mcp/?tavilyApiKey=$TAVILY_API_KEY"
     ```

5. **Validate Installation**
   - Run `claude mcp list` again
   - Verify tavily shows "✓ Connected"
   - If connected: report success
   - If not connected: report failure with troubleshooting hints

## Error Handling

If installation fails, provide these troubleshooting hints:
- Ensure `TAVILY_API_KEY` is set: `export TAVILY_API_KEY=your_api_key`
- Check network connection to https://mcp.tavily.com
- Verify your Tavily API key is valid at https://tavily.com

## Notes

- Uses HTTP transport instead of stdio (connects to remote MCP server)
- API key is passed as URL parameter to Tavily's hosted MCP service
