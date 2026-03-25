## 🤖 Agentic Ready Scaffolding

This PR was generated automatically by [legacy-to-agentic-ready](https://github.com/vb-nattamai/agent-ready).

### What was generated

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Persistent context for Claude Code — read at every session start |
| `AGENTS.md` | Agent contract: safe ops, forbidden ops, domain glossary |
| `agent-context.json` | Machine-readable repo map for all platforms |
| `agents/system_prompt.md` | Universal system prompt — works with any LLM |
| `agents/openai_agent.py` | OpenAI Agents SDK entry point |
| `agents/gemini_agent.yaml` | Google ADK no-code config |
| `agents/gemini_agent.py` | Google ADK Python agent |
| `mcp.json` | MCP server configuration for Claude Code and VS Code |
| `tools/` | Tool scaffolds matching detected language(s) |
| `memory/schema.md` | Memory and state contract |
| `AGENTIC_READINESS.md` | Audit report and next steps |

### Before merging

- [ ] Review `agent-context.json` — verify `domain_concepts`, `restricted_write_paths`, and `environment_variables` are accurate
- [ ] Review `AGENTS.md` — verify the domain glossary reflects real terms from your codebase
- [ ] Review `CLAUDE.md` — verify the module layout matches your actual directory structure
- [ ] Replace any remaining `{{PLACEHOLDER}}` values in generated files
- [ ] Run your test suite to confirm no existing files were modified

### How to use after merging

**Claude Code:**
```bash
claude "Help me add a new feature to this repo"
# Claude reads CLAUDE.md automatically
```

**OpenAI Agents SDK:**
```bash
python agents/openai_agent.py
```

**Google ADK:**
```bash
adk run agents/gemini_agent.yaml
```

**Any LLM:**
Use `agents/system_prompt.md` as the `system` parameter in any API call.
