# Install Morph Fast Apply MCP (deprecated)

> **This command is deprecated. Use `/setup:install-morph-mcp` instead.**

The npm package this command installed, `@morph-llm/morph-fast-apply`, is deprecated
upstream. Its published deprecation notice reads:

> This package has moved to @morphllm/morphmcp. See https://morphllm.com/

`@morphllm/morphmcp` supersedes it and provides the same fast-apply capability through
the `edit_file` tool, alongside `codebase_search` and `github_codebase_search`.

## Instructions

1. **Redirect to the current command**
   - Output exactly: `morph-fast-apply is deprecated — use /setup:install-morph-mcp`
   - Do not install `@morph-llm/morph-fast-apply`

2. **If a legacy `morph-fast-apply` server is still registered, remove it**
   - Check with `claude mcp list`
   - If present:
     ```bash
     claude mcp remove morph-fast-apply -s user
     ```

3. **Install the replacement**
   - Follow `/setup:install-morph-mcp`

## Notes

- Kept as a redirect rather than deleted so that existing references to this command
  fail loudly with a pointer instead of silently installing a deprecated package
- `ALL_TOOLS=true`, which this command used to set, has no effect on `@morphllm/morphmcp` —
  all three tools are always exposed and visibility is managed client-side
