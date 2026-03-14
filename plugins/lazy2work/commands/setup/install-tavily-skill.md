# Install Tavily Skills

Install the Tavily skill pack for Claude Code from https://github.com/tavily-ai/skills

Tavily Skills provide slash commands (`/search`, `/research`, `/extract`, `/crawl`, `/tavily-best-practices`) that enable web search, research, content extraction, and website crawling capabilities directly in Claude Code.

## Prerequisites

- Node.js 18+ and `npx` must be available
- A Tavily account (sign up at https://tavily.com if needed)
- Authentication: either `TAVILY_API_KEY` env var or OAuth login via browser

## Instructions

1. **Check if Tavily Skills are Already Installed**
   - Check if the skill files already exist:
     ```bash
     find . -path "*/.agents/skills/*/SKILL.md" 2>/dev/null | head -5
     ```
   - If 5 SKILL.md files exist (search, research, extract, crawl, tavily-best-practices), output: `tavily skills already installed`

2. **Check npx Availability**
   ```bash
   which npx && npx --version
   ```
   - If npx is not found, report: `npx is not available. Install Node.js 18+ first.`

3. **Install Tavily Skills**
   ```bash
   npx -y skills add https://github.com/tavily-ai/skills -y
   ```

4. **Verify Installation**
   ```bash
   find .agents/skills -name "SKILL.md" 2>/dev/null
   ```
   Expected skills (5 total):
   - `search/SKILL.md` - Web search optimized for LLMs
   - `research/SKILL.md` - Comprehensive topic research with citations
   - `extract/SKILL.md` - Clean content extraction from URLs
   - `crawl/SKILL.md` - Multi-page website crawling
   - `tavily-best-practices/SKILL.md` - Best practices reference

5. **Configure Authentication**
   - If `TAVILY_API_KEY` is not set:
     - **Option A (Recommended)**: OAuth will auto-trigger on first skill use
     - **Option B**: Set API key manually: `export TAVILY_API_KEY=your_api_key_here`

## Error Handling

If installation fails:
- Ensure Node.js 18+ is installed: `node --version`
- Check network connectivity to GitHub and npm registry
- Check https://github.com/tavily-ai/skills for updated instructions

## Notes

- Skills are different from MCP servers — they are Claude Code extensions that provide slash commands
- Authentication uses JWT tokens cached in `~/.mcp-auth/`
- Source repository: https://github.com/tavily-ai/skills (MIT License)
