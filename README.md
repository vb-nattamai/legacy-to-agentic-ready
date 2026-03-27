# AgentReady

[![Version](https://img.shields.io/github/v/release/vb-nattamai/agent-ready)](https://github.com/vb-nattamai/agent-ready/releases)
[![License](https://img.shields.io/github/license/vb-nattamai/agent-ready)](LICENSE)

Transform any legacy repository into an AI-agent-ready codebase — with real content, not placeholders.

---

## How it works

AgentReady runs in two modes:

**Static mode** (default, no API key needed) — scans your repo, fills templates, scores ~40–50/100 on first run. Good for a quick scaffold.

**LLM-first mode** (`--llm`, requires `ANTHROPIC_API_KEY`) — Claude Opus reads your actual code, understands your domain, and writes every output file from scratch. Scores ~85/100 on first run with real content.

```
Phase 1 — Collect   : reads file tree, source files, config, CI, README
Phase 2 — Analyse   : Claude Opus infers domain concepts, entry points,
                      env vars, restricted paths, architecture
Phase 3 — Generate  : Claude Sonnet writes AGENTS.md, CLAUDE.md,
                      system_prompt.md, agent-context.json, memory/schema.md
Phase 4 — Score     : 100-point readiness score + AGENTIC_READINESS.md
```

---

## Quick Start

### Install

```bash
pip install git+https://github.com/vb-nattamai/agent-ready.git
```

### Run (static mode — no API key)

```bash
agent-ready --target /path/to/your/repo
```

### Run (LLM-first mode — real content)

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
agent-ready --target /path/to/your/repo --llm
```

### Preview without writing files

```bash
agent-ready --target /path/to/your/repo --dry-run
agent-ready --target /path/to/your/repo --llm --dry-run
```

---

## GitHub Actions — Transform via Issue

The recommended way for teams. Open an issue in your repo, get a PR automatically.

### Step 1 — Install the trigger workflow

Run **"Install Agentic Ready to Repo"** from the [Actions tab](https://github.com/vb-nattamai/agent-ready/actions/workflows/install-to-repo.yml):

- **target_repo**: `myorg/my-legacy-api`
- **llm**: ✅ (enable LLM-first mode)

This pushes three files into your repo:
- `.github/workflows/agentic-ready.yml` — issue trigger
- `.github/workflows/context-refresh.yml` — weekly drift detection
- `.github/ISSUE_TEMPLATE/agentic-ready.yml` — pre-filled issue form

### Step 2 — Add your API key

In your target repo → Settings → Secrets and variables → Actions:

```
ANTHROPIC_API_KEY = sk-ant-...
```

### Step 3 — Open an issue

Go to your repo → Issues → New Issue → **"🤖 AgentReady — Transform this repo"** → Submit.

```
Issue opened
    │
    ├─ 1. Checks you are a repo collaborator
    ├─ 2. Calls agent-ready's reusable transformer
    ├─ 3. Claude Opus analyses your codebase (~60s)
    ├─ 4. Claude Sonnet writes all scaffolding files
    ├─ 5. Opens a PR: "🤖 Add agentic-ready scaffolding"
    ├─ 6. Comments on your issue with the PR link
    └─ 7. Closes the issue ✅
```

### Step 4 — Review and merge the PR

| File | Purpose |
|------|---------|
| `agent-context.json` | Machine-readable repo map (static + dynamic sections) |
| `AGENTS.md` | Agent contract — safe ops, forbidden ops, real domain glossary |
| `CLAUDE.md` | Claude Code auto-loaded context with real rules |
| `system_prompt.md` | Universal system prompt for any LLM |
| `mcp.json` | MCP server configuration |
| `memory/schema.md` | Agent memory/state contract |

> The `static` section of `agent-context.json` is safe to edit manually. The `dynamic` section is auto-refreshed.

---

## CLI Reference

```bash
# LLM-first transformation (recommended)
agent-ready --target /path/to/repo --llm

# Static transformation (no API key needed)
agent-ready --target /path/to/repo

# Selective generation
agent-ready --target /path/to/repo --llm --only agents
agent-ready --target /path/to/repo --llm --only context
agent-ready --target /path/to/repo --llm --only memory

# Preview without writing
agent-ready --target /path/to/repo --llm --dry-run

# Force overwrite existing files
agent-ready --target /path/to/repo --llm --force

# Suppress output (CI-friendly)
agent-ready --target /path/to/repo --llm --quiet

# Install pre-commit hook for automatic context refresh
agent-ready --target /path/to/repo --install-hooks

# Verify generated context with Claude Haiku
agent-ready --target /path/to/repo --verify
```

**Environment variables:**

```bash
export ANTHROPIC_API_KEY="sk-ant-..."   # Required for --llm mode
export OPENAI_API_KEY="sk-..."          # Optional
export GOOGLE_API_KEY="..."             # Optional
```

---

## Agentic Readiness Score

Every run outputs a 100-point score:

| Criterion | Points |
|-----------|--------|
| `agent-context.json` exists | 10 |
| `CLAUDE.md` exists | 10 |
| `AGENTS.md` exists | 10 |
| `system_prompt.md` exists | 5 |
| `tools/` has ≥1 file | 10 |
| Entry point file exists | 10 |
| Test command set | 10 |
| `restricted_write_paths` populated | 10 |
| `environment_variables` populated | 10 |
| `domain_concepts` has ≥3 entries | 5 |
| OpenAPI spec exists | 5 |
| CI config exists | 5 |

**Static mode first run:** ~40–50/100 (placeholders in most fields)

**LLM-first mode first run:** ~85/100 (real content from code analysis)

---

## Workflows

### `reusable-transformer.yml` — Core transformer

Runs inside `agent-ready`. Checks out the target repo, runs the transformer, opens a PR. All secrets (`ANTHROPIC_API_KEY`, `INSTALL_TOKEN`) live only in `agent-ready` — target repos only need `ANTHROPIC_API_KEY` for LLM mode.

**Inputs:**

| Input | Default | Purpose |
|---|---|---|
| `target_repo` | required | Target repo in `owner/repo` format |
| `target_branch` | `main` | Branch the PR is opened against |
| `llm` | `false` | Enable LLM-first mode |
| `only` | _(all)_ | Limit generation: `agents`, `tools`, `context`, `memory` |
| `force` | `false` | Overwrite existing generated files |
| `issue_number` | _(none)_ | Issue to close after PR is opened |

### `install-to-repo.yml` — One-click install

Triggered manually from the Actions tab. Pushes trigger workflows into any target repo.

**Requires:** `INSTALL_TOKEN` secret (PAT with `repo` + `workflow` scopes).

### `context-refresh.yml` — Weekly drift detection

Runs every Monday. Detects if `agent-context.json` has drifted from the current codebase and opens a PR if so.

### `test-dry-run.yml` — Preview without writing

Runs the transformer in read-only mode against any repo. Use before the real transformation.

### `release.yml` — Semantic versioning

Bumps version, updates CHANGELOG.md, and creates a GitHub Release on every push to `main`.

| Commit prefix | Bump |
|---|---|
| `feat:` | minor |
| `fix:` | patch |
| `BREAKING CHANGE:` | major |
| `docs:`, `chore:`, `style:` | none |

---

## Keeping Context Fresh

**Pre-commit hook** (local development):

```bash
agent-ready --target /path/to/repo --install-hooks
git -C /path/to/repo config agentic.toolkit-path /path/to/agent-ready
```

Refreshes the `dynamic` section of `agent-context.json` automatically on every commit. The `static` section is never touched.

**Weekly CI refresh** (teams): installed automatically by `install-to-repo.yml` as `.github/workflows/context-refresh.yml`.

**Manual refresh:**

```bash
agent-ready --target /path/to/repo --only context --force
```

---

## Supported Languages & Frameworks

- **Python** (Django, Flask, FastAPI)
- **TypeScript / JavaScript** (React, Next.js, Node.js, Express)
- **Java** (Spring Boot, Maven, Gradle)
- **Kotlin** (Spring Boot, Gradle)
- **Go** (standard library, Gin, Echo)
- **Rust** (Cargo)
- **C# / .NET** (ASP.NET)
- **Ruby** (Rails)

---

## After Merging the PR

| Tool | File it reads | How |
|------|--------------|-----|
| Claude Code | `CLAUDE.md` | Auto-loaded at session start |
| GitHub Copilot | `.github/agents/*.agent.md` | Copilot Chat dropdown |
| Any LLM | `system_prompt.md` | Paste as system parameter |
| MCP clients | `mcp.json` | Loaded by MCP host |

---

## Philosophy

1. **LLM-first** — real content from real code analysis, not template placeholders
2. **Never modify existing code** — only additive changes
3. **Never hallucinate** — all generated content grounded in what the LLM actually read
4. **Platform-agnostic** — works with Claude, OpenAI, Gemini, or any LLM
5. **Idempotent** — safe to run multiple times

---

## Contributing

1. Fork this repository
2. Create a feature branch (`git checkout -b feature/my-improvement`)
3. Commit with conventional commits (`feat:`, `fix:`, `BREAKING CHANGE:`)
4. Push and open a Pull Request

---

## License

MIT — see [LICENSE](LICENSE) for details.