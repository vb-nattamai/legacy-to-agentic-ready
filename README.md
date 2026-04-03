# AgentReady

[![Version](https://img.shields.io/github/v/release/vb-nattamai/agent-ready)](https://github.com/vb-nattamai/agent-ready/releases)
[![License](https://img.shields.io/github/license/vb-nattamai/agent-ready)](LICENSE)

Transform any legacy repository into an AI-agent-ready codebase — with real content written from your actual code, not template placeholders.

---

## Why AgentReady?

AI agents fail on unfamiliar codebases because they lack context — they invent file paths, guess commands, and miss domain concepts entirely. AgentReady fixes this by generating scaffolding files that give agents real, verified knowledge of your repository before they touch a single line of code.

**Proven results across four real codebases:**

| Repo | Stack | Files | Without context | With context | Pass rate |
|------|-------|-------|----------------|--------------|-----------|
| Simple bowling kata | Java, single class | 13 | 0.8 / 10 | 9.7 / 10 | 100% |
| [travel-assist](https://github.com/vb-nattamai/travel-assist) | Kotlin, Spring Boot | 23 | 0.3 / 10 | 8.9 / 10 | 89% |
| [bowling-kata](https://github.com/vb-nattamai/bowling-kata) | Java, Python, Go, TypeScript | 47 | 2.1 / 10 | 7.6 / 10 | 89% |
| [food-delivery](https://github.com/vb-nattamai/food-delivery) | Java, Kotlin, Python, Go, TypeScript, React | 81 | 1.4 / 10 | 8.5 / 10 | 87% |

*Scores are averages across 15 repo-specific questions across 5 categories, judged by Claude Haiku. Without context, an AI agent is essentially guessing — it cannot know your file paths, commands, or domain logic.*

The pattern is consistent: context files dramatically improve AI agent responses regardless of repo complexity. More complex polyglot repos score slightly lower due to the inherent difficulty of reasoning across multiple languages and build systems.

---

## How it works

AgentReady is **LLM-first** — it reads your actual code and writes every file from scratch. No templates, no placeholders.

```
Phase 1 — Collect   : reads file tree, source files, config, CI, README
Phase 2 — Analyse   : LLM reads your code and infers domain concepts,
                      entry points, env vars, restricted paths, pitfalls
Phase 3 — Generate  : LLM writes AGENTS.md, CLAUDE.md,
                      system_prompt.md, agent-context.json, memory/schema.md
Phase 4 — Score     : 100-point readiness score
Phase 5 — Evaluate  : 15 questions across 5 categories measure whether
                      context files actually improve AI responses
```

**Provider strategy — analysis uses the most capable model, eval uses the fastest:**

| Provider | Analysis | Generation | Evaluation | Key |
|---|---|---|---|---|
| `anthropic` | claude-opus-4-6 | claude-sonnet-4-6 | claude-haiku-4-5 | `ANTHROPIC_API_KEY` |
| `openai` | gpt-5.4 | gpt-5.4-mini | gpt-5.4-nano | `OPENAI_API_KEY` |
| `google` | gemini-2.5-pro | gemini-2.5-pro | gemini-2.5-flash-lite | `GOOGLE_API_KEY` |
| `groq` | llama-3.3-70b | llama-3.3-70b | llama-3.1-8b-instant | `GROQ_API_KEY` |
| `mistral` | mistral-large | mistral-large | mistral-small | `MISTRAL_API_KEY` |
| `together` | Qwen3.5-397B | Llama-3.3-70B | Qwen3.5-9B | `TOGETHER_API_KEY` |
| `ollama` | llama3.3 | llama3.3 | llama3.2 | _(local — no key)_ |

---

## Quick Start

### Install

```bash
pip install "git+https://github.com/vb-nattamai/agent-ready.git[ai]"
```

### Run locally

```bash
# Default provider: Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."
agent-ready --target /path/to/your/repo

# Choose a different provider
export OPENAI_API_KEY="sk-..."
agent-ready --target /path/to/your/repo --provider openai

export GROQ_API_KEY="gsk_..."
agent-ready --target /path/to/your/repo --provider groq

# Or pass any LiteLLM model string directly
agent-ready --target /path/to/your/repo --model ollama/llama3.3   # local, free

# Transform + measure improvement in one shot
agent-ready --target /path/to/your/repo --eval

# Preview without writing any files
agent-ready --target /path/to/your/repo --dry-run
```

---

## GitHub Actions — Transform via Issue

The recommended way for teams. Open an issue in your repo, get a PR automatically.

### Step 1 — Install the trigger workflow

Run **"Install AgentReady to Target Repository"** from the [Actions tab](https://github.com/vb-nattamai/agent-ready/actions/workflows/install-to-target-repo.yml):

- **target_repo**: `myorg/my-legacy-api`
- **provider**: `anthropic` (or `openai`, `google`, `groq`, `mistral`, `together`, `ollama`)
- **eval**: ✅ enable eval after transformation (optional)

This pushes three files into your repo:
- `.github/workflows/agentic-ready.yml` — issue trigger
- `.github/workflows/context-drift-detector.yml` — weekly drift detection
- `.github/ISSUE_TEMPLATE/agentic-ready.yml` — pre-filled issue form

### Step 2 — Add your secrets

In your target repo → Settings → Secrets and variables → Actions:

```
ANTHROPIC_API_KEY = sk-ant-...   # set the key for your chosen provider
INSTALL_TOKEN     = ghp_...       # PAT with repo + workflow scopes
```

### Step 3 — Open an issue

Go to your repo → Issues → New Issue → **"🤖 AgentReady — Transform this repo"** → Submit.

```
Issue opened
    │
    ├─ 1. Checks you are a repo collaborator
    ├─ 2. Calls agent-ready's reusable transformer
    ├─ 3. Analysis model reads your codebase (~60s)
    ├─ 4. Generation model writes all scaffolding files
    ├─ 5. (Optional) Evaluation model runs 15 questions across 5 categories
    ├─ 6. Opens a PR: "🤖 Add agentic-ready scaffolding"
    ├─ 7. Comments on your issue with the PR link
    └─ 8. Closes the issue ✅
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
| `AGENTIC_EVAL.md` | Evaluation report — verdict, scores, per-question breakdown |

> The `static` section of `agent-context.json` is safe to edit manually. The `dynamic` section is auto-refreshed on every scan.

---

## Eval Framework

AgentReady measures whether the generated files actually improve AI responses — not just whether the files exist.

```bash
# Eval after transformation
agent-ready --target /path/to/repo --eval

# Run eval only against existing context files
agent-ready --target /path/to/repo --eval-only

# Use as a CI gate — fail if pass rate < 80%
agent-ready --target /path/to/repo --eval-only --fail-level 0.8
```

**How it works:**

Each of 15 questions is asked twice — once with no context (baseline) and once with your generated files as the system prompt. A judge model scores both responses on a 0–10 scale. The delta is your improvement.

**15 questions across 5 categories:**
- **Commands** (3q) — are the build, test, and install commands exact?
- **Safety** (2q) — does the AI respect restricted paths and secret rules?
- **Domain** (2q) — does the AI understand the business logic and concepts?
- **Architecture** (3q) — does the AI know the entry point, language, and structure?
- **Pitfalls** (5q) — does the AI know the specific gotchas that will break this codebase?

The pitfalls category uses 5 targeted questions — one per pitfall type — because a single generic question lets models answer without real codebase knowledge. Results are saved to `AGENTIC_EVAL.md` with a verdict, category scores, per-question tables, and a "What to Improve" section.

---

## CLI Reference

```bash
# Default provider: Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."
agent-ready --target /path/to/repo

# Choose a different provider
export OPENAI_API_KEY="sk-..."
agent-ready --target /path/to/repo --provider openai

export GROQ_API_KEY="gsk_..."
agent-ready --target /path/to/repo --provider groq

# Or pass any LiteLLM model string directly
agent-ready --target /path/to/repo --model ollama/llama3.3   # local, free

# Selective generation
agent-ready --target /path/to/repo --only agents
agent-ready --target /path/to/repo --only context
agent-ready --target /path/to/repo --only memory

# Preview without writing
agent-ready --target /path/to/repo --dry-run

# Force overwrite existing files
agent-ready --target /path/to/repo --force

# Transform + evaluate
agent-ready --target /path/to/repo --eval

# Evaluate only (context files already exist)
agent-ready --target /path/to/repo --eval-only

# CI gate — exit 1 if eval pass rate < 80%
agent-ready --target /path/to/repo --eval-only --fail-level 0.8

# Suppress output (CI-friendly)
agent-ready --target /path/to/repo --quiet

# Install pre-commit hook for automatic context refresh
agent-ready --target /path/to/repo --install-hooks

# Verify generated context with the evaluation model
agent-ready --target /path/to/repo --verify
```

**Environment variables (set the one for your chosen provider):**

```bash
export ANTHROPIC_API_KEY="sk-ant-..."  # anthropic (default)
export OPENAI_API_KEY="sk-..."          # openai
export GOOGLE_API_KEY="..."             # google
export GROQ_API_KEY="gsk_..."           # groq
export MISTRAL_API_KEY="..."            # mistral
export TOGETHER_API_KEY="..."           # together
# ollama: no key needed — runs locally
```

---

## Agentic Readiness Score

Every run outputs a 100-point score — an actionable to-do list, not a grade.

| Criterion | Points |
|-----------|--------|
| `agent-context.json` exists | 10 |
| `CLAUDE.md` exists | 10 |
| `AGENTS.md` exists | 10 |
| `system_prompt.md` exists | 5 |
| `tools/` has ≥1 file | 10 |
| Entry point file verified | 10 |
| Test command set | 10 |
| `restricted_write_paths` populated | 10 |
| `environment_variables` populated | 10 |
| `domain_concepts` has ≥3 entries | 5 |
| OpenAPI spec exists | 5 |
| CI config exists | 5 |

First run typically scores **~85/100** — real content from real code analysis, not placeholders.

---

## Workflows

### `reusable-transformer.yml` — Core transformer

The engine. Checks out the target repo, runs the LLM pipeline, optionally runs eval, opens a PR.

**Inputs:**

| Input | Default | Purpose |
|---|---|---|
| `target_repo` | required | Target repo in `owner/repo` format |
| `target_branch` | `main` | Branch the PR is opened against |
| `provider` | `anthropic` | LLM provider: `anthropic`, `openai`, `google`, `groq`, `mistral`, `together`, `ollama` |
| `eval` | `false` | Run eval after transformation |
| `fail_level` | `0.0` | Exit 1 if eval pass rate below threshold |
| `only` | _(all)_ | Limit: `agents`, `tools`, `context`, `memory` |
| `force` | `false` | Overwrite existing generated files |
| `issue_number` | _(none)_ | Issue to close after PR is opened |

### `install-to-target-repo.yml` — One-click installer

Triggered manually from the Actions tab. Pushes trigger workflows into any target repo and creates the first transformation issue automatically.

**Requires:** `INSTALL_TOKEN` secret (PAT with `repo` + `workflow` scopes).

### `context-drift-detector.yml` — Weekly drift detection

Runs every Monday at 09:00 UTC. Detects if `agent-context.json` has structurally drifted from the current codebase and opens a PR if drift is found. Also installed into target repos by the installer.

### `validate-token-permissions.yml` — Token validation

Creates a test branch in a target repo, pushes it, and immediately deletes it. Confirms `INSTALL_TOKEN` permissions before triggering a real transformation.

### `test-dry-run.yml` — Preview without writing

Runs the transformer in read-only mode against any repo.

### `release.yml` — Semantic versioning

Bumps version, updates `CHANGELOG.md`, and creates a GitHub Release on every push to `main`.

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

Automatically refreshes the `dynamic` section of `agent-context.json` whenever source files change. The `static` section (your manual edits) is never touched.

**Weekly CI drift detection** — installed automatically by the installer as `.github/workflows/context-drift-detector.yml`.

**Manual refresh:**

```bash
agent-ready --target /path/to/repo --only context --force
```

---

## Supported Languages & Frameworks

- **Python** — Django, Flask, FastAPI
- **TypeScript / JavaScript** — React, Next.js, Node.js, Express
- **Java** — Spring Boot, Maven, Gradle
- **Kotlin** — Spring Boot, Gradle
- **Go** — standard library, Gin, Echo
- **Rust** — Cargo
- **C# / .NET** — ASP.NET
- **Ruby** — Rails

---

## After Merging the PR

| Tool | File it reads | How |
|------|--------------|-----|
| Claude Code | `CLAUDE.md` | Auto-loaded at every session start |
| GitHub Copilot | `.github/agents/*.agent.md` | Copilot Chat dropdown |
| Any LLM | `system_prompt.md` | Paste as the `system` parameter |
| MCP clients | `mcp.json` | Loaded by the MCP host |

---

## Philosophy

1. **LLM-first** — your chosen LLM reads your actual code and writes real content, not template placeholders
2. **Measurable** — the eval framework proves whether the context files actually improve AI responses
3. **Never modify existing code** — only additive changes, always
4. **Never hallucinate** — all generated content is grounded in what the LLM actually read
5. **Platform-agnostic** — works with Claude, OpenAI, Gemini, or any LLM via `system_prompt.md`
6. **Idempotent** — safe to run multiple times; the `static` section of `agent-context.json` is always preserved

---

## Contributing

Contributions are very welcome. AgentReady is an early-stage open-source project and there's a lot of ground to cover.

**Good first issues:**
- Add support for a new language or framework in the analyser
- Improve pitfall question templates for specific tech stacks (e.g. Django, Rails, .NET)
- Add an `--eval-report` flag to print results without saving to file
- Write tests for `analyser.py` and `generator.py`

**Bigger contributions:**
- Monorepo support — detect and handle multiple modules with per-module context files
- VS Code extension — surface the readiness score inline
- `workflow_dispatch` architecture — keep all secrets in `agent-ready` only
- Reasoning trace in eval — capture not just what was wrong but why the agent chose that path

**How to contribute:**

1. Fork this repository
2. Create a feature branch: `git checkout -b feat/my-improvement`
3. Commit with conventional commits: `feat:`, `fix:`, `docs:`
4. Push and open a Pull Request

Please open an issue first for significant changes so we can discuss the approach before you invest time building it.

---

## License

MIT — see [LICENSE](LICENSE) for details.