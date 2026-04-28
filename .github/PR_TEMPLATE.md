## 🤖 Agentic Ready Scaffolding

This PR was generated automatically by [AgentReady](https://github.com/vb-nattamai/agent-ready).

### What was generated

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Persistent context for Claude Code — read at every session start |
| `AGENTS.md` | Agent contract: safe ops, forbidden ops, domain glossary |
| `.cursorrules` | Persistent context for Cursor — read at project open |
| `agent-context.json` | Machine-readable repo map for all platforms |
| `system_prompt.md` | Universal system prompt — works with any LLM |
| `mcp.json` | MCP server configuration for Claude Code and VS Code |
| `memory/schema.md` | Agent working memory and state contract |
| `skills/` | Slash-command skill definitions grounded in repo commands |
| `hooks/` | Claude Code lifecycle hooks for session continuity |
| `AGENTIC_EVAL.md` | Eval report — baseline vs. context scores (if eval was enabled) |

### Before merging

- [ ] Review `agent-context.json` — verify `domain_concepts`, `restricted_write_paths`, and `environment_variables` are accurate
- [ ] Review `AGENTS.md` — verify the domain glossary reflects real terms from your codebase
- [ ] Review `CLAUDE.md` — verify the module layout matches your actual directory structure
- [ ] Run your test suite to confirm no existing files were modified

### How to use after merging

**Claude Code:**
```bash
claude "Help me add a new feature to this repo"
# CLAUDE.md is read automatically at every session start
```

**GitHub Copilot / any agent:**
```bash
# Paste system_prompt.md as the system parameter in any LLM API call
# or reference AGENTS.md as context in your agent framework
```

**MCP clients (Claude Code, VS Code):**
```json
// mcp.json is ready to load — configure your MCP host to point at it
```

