# Install Tavily Skills

Install the Tavily skill pack for Claude Code from https://github.com/tavily-ai/skills

Tavily Skills provide web search, research, content extraction, site mapping, and
crawling as Claude Code skills.

## Prerequisites

- A Tavily account (sign up at https://tavily.com if needed)
- Authentication: either `TAVILY_API_KEY` env var or OAuth login via browser
- For the `npx` method: Node.js 18+ and `npx`

## Instructions

1. **Check if Tavily Skills are Already Installed**
   ```bash
   ls ~/.agents/skills/ 2>/dev/null | grep -i '^tavily-'
   claude plugin list 2>/dev/null | grep -i tavily
   ```
   - If the 8 skills below are already present, output: `tavily skills already installed`
     and stop here

2. **Install — pick one method**

   **2a. Claude Code plugin (recommended for Claude Code)**
   The same repository doubles as a plugin marketplace, which is the native path:
   ```bash
   claude plugin marketplace add tavily-ai/skills
   claude plugin install tavily@tavily-plugins --scope user --yes
   ```

   **2b. `skills` CLI (cross-agent: Claude Code, Cursor, and others)**
   ```bash
   npx -y skills add https://github.com/tavily-ai/skills --global --all
   ```
   `--global` installs to user level (`~/.agents/skills/`) rather than the current
   project; `--all` is shorthand for `--skill '*' --agent '*' -y`.

3. **Verify Installation**

   For method 2a:
   ```bash
   ls ~/.claude/plugins/cache/tavily-plugins/tavily/*/skills/
   ```
   For method 2b:
   ```bash
   ls ~/.agents/skills/ | grep '^tavily-'
   ```

   Expected skills (8 total):

   | Skill | Purpose |
   |---|---|
   | `tavily-search` | Web search optimized for LLMs |
   | `tavily-research` | Comprehensive topic research with citations |
   | `tavily-extract` | Clean content extraction from URLs |
   | `tavily-crawl` | Multi-page website crawling |
   | `tavily-map` | Discover a site's URLs without extracting content |
   | `tavily-cli` | Direct Tavily CLI usage |
   | `tavily-dynamic-search` | Programmatic search with context isolation |
   | `tavily-best-practices` | Best practices reference for integrations |

4. **Configure Authentication**
   - If `TAVILY_API_KEY` is not set:
     - **Option A (Recommended)**: OAuth will auto-trigger on first skill use
     - **Option B**: Set API key manually: `export TAVILY_API_KEY=your_api_key_here`

## Error Handling

If installation fails:
- Ensure Node.js 18+ is installed: `node --version` (method 2b only)
- Check network connectivity to GitHub and the npm registry
- For method 2a, confirm the marketplace was added: `claude plugin marketplace list`
- Check https://github.com/tavily-ai/skills for updated instructions

## Notes

- Skills are different from MCP servers — they are prompt-level extensions, not tool
  servers. Installing these does not replace `/setup:install-tavily-mcp`, and the two
  can coexist
- **Skill names are prefixed.** They were once `search`, `research`, `extract`, and
  `crawl`; they are now all `tavily-`-prefixed, and `tavily-map`, `tavily-cli`, and
  `tavily-dynamic-search` were added. Any workflow referencing the old bare names needs
  updating
- The `skills` CLI is `vercel-labs/skills` on npm; `npx -y skills@latest --help` lists
  current flags
- Source repository: https://github.com/tavily-ai/skills (MIT License)
