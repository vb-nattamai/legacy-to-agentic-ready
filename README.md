# AgentReady

[![Version](https://img.shields.io/github/v/release/vb-nattamai/agent-ready)](https://github.com/vb-nattamai/agent-ready/releases)
[![CI](https://github.com/vb-nattamai/agent-ready/actions/workflows/ci.yml/badge.svg)](https://github.com/vb-nattamai/agent-ready/actions/workflows/ci.yml)
[![CodeQL](https://github.com/vb-nattamai/agent-ready/actions/workflows/codeql.yml/badge.svg)](https://github.com/vb-nattamai/agent-ready/actions/workflows/codeql.yml)
[![License](https://img.shields.io/github/license/vb-nattamai/agent-ready)](LICENSE)

**Transform any legacy repository into an AI-agent-ready codebase.**

AI agents fail on unfamiliar codebases — they invent file paths, guess commands, miss domain concepts, and make dangerous mistakes. AgentReady fixes this by generating up to 12 scaffolding files grounded in your actual code, giving agents verified knowledge before they touch a single line.

---

## What You Get

One command. Up to 12 files generated from your real code. No templates, no placeholders.

| File | What it does |
|------|-------------|
| `agent-context.json` | Machine-readable repo map — entry point, test command, domain concepts, restricted paths, env vars |
| `AGENTS.md` | Operating contract for GitHub Copilot, OpenAI agents, and any agentic workflow |
| `CLAUDE.md` | Auto-loaded by Claude Code at every session start |
| `.github/copilot-instructions.md` | GitHub Copilot workspace instructions |
| `system_prompt.md` | Universal system prompt — paste as `system:` in any LLM API call |
| `mcp.json` | MCP server configuration for Claude Desktop, Cursor, Continue |
| `memory/schema.md` | Agent memory and state contract |
| `tools/refresh_context.py` | Script to refresh `agent-context.json` on demand |
| `.github/dependabot.yml` | Dependency update schedule |
| `.github/CODEOWNERS` | Code ownership for PR routing |
| `openapi.yaml` | OpenAPI stub (generated for REST API repos) |
| `.agent-ready/custom_questions.json` | Hook to add repo-specific eval questions |

---

## Quick Start (Local)

### 1. Install

```bash
pip install "git+https://github.com/vb-nattamai/agent-ready.git[ai]"
```

### 2. Set your API key

```bash
export ANTHROPIC_API_KEY="sk-ant-..."   # Anthropic (default)
# or
export OPENAI_API_KEY="sk-..."          # OpenAI
export GOOGLE_API_KEY="..."             # Google
export GROQ_API_KEY="gsk_..."           # Groq (free tier available)
```

### 3. Run

```bash
# Transform your repo (generates all scaffolding files)
agent-ready --target /path/to/your/repo

# Transform + measure how much the context improves AI responses
agent-ready --target /path/to/your/repo --eval

# Preview what would be generated without writing anything
agent-ready --target /path/to/your/repo --dry-run
```

That's it. Review the generated files, commit them, and your repo is agent-ready.

---

## GitHub Actions — Transform via Issue (Recommended for Teams)

The zero-install path. Open an issue, get a PR with all 12 files.

### Step 1 — Install the trigger workflow into your target repo

Go to the [AgentReady Actions tab](https://github.com/vb-nattamai/agent-ready/actions/workflows/install-to-target-repo.yml) → **Run workflow**:

| Input | Value |
|-------|-------|
| `target_repo` | `your-org/your-repo` |
| `provider` | `anthropic` (or `openai`, `google`, `groq`, `mistral`, `together`) |
| `eval` | ✅ (recommended — runs quality measurement after transform) |

This pushes **5 workflow files** into your repo:
- `.github/workflows/agentic-ready.yml` — issue-triggered transformer
- `.github/workflows/context-drift-detector.yml` — weekly staleness check
- `.github/workflows/pr-review.yml` — AI-powered PR review on every PR
- `.github/workflows/agentic-ready-eval.yml` — eval-only (runs on every push to main)
- `.github/ISSUE_TEMPLATE/agentic-ready.yml` — pre-filled issue template

### Step 2 — Add secrets to your target repo

Go to your repo → **Settings → Secrets and variables → Actions** and add:

```
ANTHROPIC_API_KEY = sk-ant-...    # (or your provider's key)
INSTALL_TOKEN     = ghp_...       # GitHub PAT with repo + workflow scopes
```

> Only collaborators with `write`, `maintain`, or `admin` access can trigger the workflow.

### Step 3 — Open an issue

Issues → New Issue → **"🤖 AgentReady — Transform this repo"** → Submit.

```
You open the issue
    │
    ├── AgentReady checks you're a collaborator
    ├── Runs LLM analysis of your codebase (~60s)
    ├── Generates up to 12 scaffolding files
    ├── (Optional) Runs 19-question eval
    ├── Opens a PR: "🤖 Add agentic-ready scaffolding"
    ├── Posts the PR link as an issue comment
    └── Closes the issue ✅
```

### Step 4 — Review and merge the PR

Read through the generated files — especially `AGENTS.md` and `agent-context.json`. Edit the `static` section of `agent-context.json` if anything is wrong. The `dynamic` section is auto-refreshed on every run.

---

## How the Pipeline Works

```
Phase 1 — Collect   reads your file tree, source files, config files, CI, README
Phase 2 — Analyse   LLM reads your code → structured JSON (architecture, domain, pitfalls)
Phase 3 — Generate  LLM writes all scaffolding files from the analysis JSON
Phase 4 — Score     100-point readiness score based on what was captured
Phase 5 — Evaluate  19-question golden set measures whether context improves AI responses
```

**Every phase is LLM-first** — content is written from what the model read in your code, not from templates.

**Provider strategy — use the best model where it counts, the fastest where it doesn't:**

| Provider | Analysis model | Generation model | Evaluation model | Key |
|---|---|---|---|---|
| `anthropic` | claude-opus-4-6 | claude-sonnet-4-6 | claude-haiku-4-5 | `ANTHROPIC_API_KEY` |
| `openai` | gpt-5.4 | gpt-5.4-mini | gpt-5.4-nano | `OPENAI_API_KEY` |
| `google` | gemini-2.5-pro | gemini-2.5-pro | gemini-2.5-flash-lite | `GOOGLE_API_KEY` |
| `groq` | llama-3.3-70b | llama-3.3-70b | llama-3.1-8b-instant | `GROQ_API_KEY` |
| `mistral` | mistral-large | mistral-large | mistral-small | `MISTRAL_API_KEY` |
| `together` | Qwen3.5-397B | Llama-3.3-70B | Qwen3.5-9B | `TOGETHER_API_KEY` |
| `ollama` | llama3.3 | llama3.3 | llama3.2 | _(local — no key)_ |

---

## Understanding Your Results

### Agentic Readiness Score (0–100)

Every run prints a score. It's an **actionable checklist**, not a grade.

| Criterion | Points | What it means if missing |
|-----------|--------|--------------------------|
| `agent-context.json` exists | 10 | Core machine-readable context is absent |
| `CLAUDE.md` exists | 10 | Claude Code won't auto-load any context |
| `AGENTS.md` exists | 10 | No operating contract for agentic workflows |
| `system_prompt.md` exists | 5 | No universal LLM system prompt |
| `tools/` has ≥1 file | 10 | No refresh script for context maintenance |
| Entry point file verified | 10 | Agents don't know where execution starts |
| Test command set | 10 | Agents will guess/hallucinate test commands |
| `restricted_write_paths` populated | 10 | Agents may overwrite protected files |
| `environment_variables` populated | 10 | Agents won't know which env vars to set |
| `domain_concepts` has ≥3 entries | 5 | Domain knowledge missing from context |
| OpenAPI spec exists | 5 | REST API shape not documented for agents |
| CI config exists | 5 | No CI signals for the analyser to read |

A score of **75–80** is typical for a clean repo with tests and CI. **85+** requires explicit env vars, an entry point, and populated restricted paths.

### Eval Results (Pass Rate + Hallucination Rate)

The eval runs 19 questions (13 base + 6 Python/JS overlay) from a versioned golden set and measures:
- **Pass rate** — what % of questions the context answers correctly
- **Hallucination rate** — what % of responses contain invented facts

**Benchmark on `ar-test-python-complex`** (multi-module Python inventory service, pytest, CI, pyproject.toml):

| Category | Score (no ctx) | Score (with ctx) | Delta | Pass rate |
|---|---|---|---|---|
| **Overall** | 2.0/10 | **6.3/10** | +4.3 pts | 47% |
| commands | 2.6/10 | 5.5/10 | +2.9 pts | 40% |
| safety | 2.5/10 | 5.6/10 | +3.1 pts | 25% |
| architecture | 1.8/10 | 6.8/10 | +5.0 pts | 60% |
| **domain** | **0.0/10** | **9.0/10** | **+9.0 pts** | **100%** |
| adversarial | 2.0/10 | 6.1/10 | +4.1 pts | 33% |

> **Domain knowledge is perfect.** Commands and safety questions are harder — they require the context files to explicitly capture runtime version, test flags, and restricted paths. Richer repos (with `.env.example`, explicit restricted paths, and a clearly runnable entry point) score higher across all categories.

**How to interpret your hallucination rate:**

| Rate | Meaning |
|------|---------|
| < 20% | Excellent — context is grounded and specific |
| 20–40% | Good — a few gaps; check which categories failed |
| 40–60% | Fair — context files exist but miss key specifics (runtime version, commands) |
| > 60% | Poor — the generator may have sparse source to work with |

**Improving a low score:** Check which questions failed in `AGENTIC_EVAL.md`. The most common fixes:
- Add an `.env.example` listing your real env vars → fixes `environment_variables`
- Add a `Makefile` or `pyproject.toml` with explicit `[tool.pytest.ini_options]` → fixes `test_command`
- Add a `SECURITY.md` or explicit `.github/CODEOWNERS` → fixes `restricted_write_paths`
- Add repo-specific questions in `.agent-ready/custom_questions.json`

---

## CLI Reference

```bash
# Basic transformation
agent-ready --target /path/to/repo

# Choose provider
agent-ready --target /path/to/repo --provider openai
agent-ready --target /path/to/repo --provider groq
agent-ready --target /path/to/repo --model ollama/llama3.3   # local, free

# Transform + run eval in one shot
agent-ready --target /path/to/repo --eval

# Eval only (context files already exist — no re-transformation)
agent-ready --target /path/to/repo --eval-only

# CI gate — exit 1 if pass rate falls below 50%
agent-ready --target /path/to/repo --eval-only --fail-level 0.5

# Preview without writing any files (dry run)
agent-ready --target /path/to/repo --dry-run

# Force overwrite existing generated files
agent-ready --target /path/to/repo --force

# Regenerate only specific file groups
agent-ready --target /path/to/repo --only agents    # AGENTS.md, CLAUDE.md, copilot-instructions.md, system_prompt.md
agent-ready --target /path/to/repo --only context   # agent-context.json, tools/refresh_context.py
agent-ready --target /path/to/repo --only memory    # memory/schema.md

# Suppress output (CI-friendly)
agent-ready --target /path/to/repo --quiet

# Install pre-commit hook for automatic context refresh
agent-ready --target /path/to/repo --install-hooks

# Review a pull request (posts APPROVE/REQUEST_CHANGES to GitHub)
agent-ready --target /path/to/repo --review-pr 42
agent-ready --target /path/to/repo --review-pr 42 --dry-run   # print review without posting
```

**Required env vars — set the one for your provider:**

```bash
export ANTHROPIC_API_KEY="sk-ant-..."   # anthropic (default)
export OPENAI_API_KEY="sk-..."          # openai
export GOOGLE_API_KEY="..."             # google
export GROQ_API_KEY="gsk_..."           # groq
export MISTRAL_API_KEY="..."            # mistral
export TOGETHER_API_KEY="..."           # together
# ollama: no key — runs locally
```

---

## Customising the Eval

### Add repo-specific questions

Drop a `.agent-ready/custom_questions.json` in your target repo (generated automatically on every transform):

```json
[
  {
    "id": "custom_001",
    "category": "commands",
    "question": "What is the exact command to run database migrations in this project?",
    "hint": "Check the Makefile and README"
  }
]
```

These questions are included in every eval run alongside the standard golden set.

### Adjust the CI pass threshold

The installed `agentic-ready-eval.yml` workflow runs eval on every push to `main`. Set `fail_level` to exit 1 and fail the workflow if quality drops:

```yaml
# In your target repo's .github/workflows/agentic-ready-eval.yml
with:
  fail_level: "0.6"   # fail if pass rate < 60%
```

---

## MCP Server

AgentReady ships an MCP server that exposes its core capabilities as tools for Claude Desktop, Cursor, Continue, and any other MCP client.

```bash
pip install "git+https://github.com/vb-nattamai/agent-ready.git[ai]"
agent-ready-mcp
```

**Available tools:**

| Tool | What it does |
|------|-------------|
| `transform` | Run the full 5-phase pipeline on a target repo |
| `score` | Compute the agentic readiness score for an existing repo |
| `evaluate` | Run the golden-set eval against existing context files |
| `review_pr` | Review a pull request and return structured feedback |

**Configure in Claude Desktop** (`~/.claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "agent-ready": {
      "command": "agent-ready-mcp",
      "env": { "ANTHROPIC_API_KEY": "sk-ant-..." }
    }
  }
}
```

---

## After Merging the PR

| Tool | File | How |
|------|------|-----|
| Claude Code | `CLAUDE.md` | Auto-loaded at every session start |
| GitHub Copilot | `.github/copilot-instructions.md` | Loaded as workspace instructions |
| Any LLM | `system_prompt.md` | Paste as the `system:` parameter |
| MCP clients | `mcp.json` | Loaded by the MCP host |
| Agentic workflows | `AGENTS.md` | Drop into any agent that reads workspace files |
| Any script | `agent-context.json` | Parse as JSON for programmatic access |

---

## Keeping Context Fresh

Generated files go stale as code evolves. Three mechanisms keep them current:

**Weekly CI drift detection** (installed automatically as `.github/workflows/context-drift-detector.yml`):
```
Every Monday 09:00 UTC → re-analyses codebase → opens a PR if drift detected
```

**Pre-commit hook** (optional — for active development):
```bash
agent-ready --target /path/to/repo --install-hooks
```

**Manual refresh** (any time):
```bash
agent-ready --target /path/to/repo --only context --force
# or run the generated script:
python tools/refresh_context.py
```

---

## Workflows Reference

### `reusable-transformer.yml` — Core transformer

| Input | Default | Purpose |
|---|---|---|
| `target_repo` | required | Target repo in `owner/repo` format |
| `target_branch` | `main` | Branch the PR is opened against |
| `provider` | `anthropic` | LLM provider |
| `eval` | `true` | Run eval after transformation |
| `fail_level` | `0.5` | Exit 1 if eval pass rate below threshold |
| `only` | _(all)_ | Limit to: `agents`, `context`, `memory` |
| `force` | `false` | Overwrite existing generated files |
| `issue_number` | _(none)_ | Issue to close after PR is opened |

### `reusable-eval.yml` — Standalone evaluator

| Input | Default | Purpose |
|---|---|---|
| `target_repo` | required | Target repo |
| `provider` | `anthropic` | LLM provider |
| `fail_level` | `0.5` | Exit 1 if pass rate below threshold |

Saves `AGENTIC_EVAL.md` as a workflow artifact (retained 30 days).

### `install-to-target-repo.yml` — Installer

Pushes trigger workflows into a target repo. Requires `INSTALL_TOKEN` (PAT with `repo` + `workflow` scopes).

### `context-drift-detector.yml` — Weekly drift check

Runs every Monday. Opens a PR if `agent-context.json` has drifted from the current codebase.

### `pr-review.yml` — AI-powered PR review

Installed in target repos. Posts APPROVE or REQUEST_CHANGES on every PR, grounded in `agent-context.json`.

**Security:** Uses `pull_request_target` — review script runs from base branch, keeping secrets inaccessible to PR authors. PR diffs are sent to the LLM API (Anthropic by default) — do not use if your diffs may contain secrets or confidential material.

---

## Supported Languages

| Language | Frameworks detected |
|---|---|
| Python | Django, Flask, FastAPI, setuptools, pytest |
| TypeScript / JavaScript | React, Next.js, Node.js, Express, Jest, Vitest |
| Java | Spring Boot, Maven, Gradle |
| Kotlin | Spring Boot, Gradle |
| Go | standard library, Gin, Echo |
| Rust | Cargo |
| C# / .NET | ASP.NET |
| Ruby | Rails, Bundler |

---

## Security Model

- **No `${{ inputs.* }}` in `run:` blocks** — all user-controlled values go through `env:` variables first
- **Provider allowlist** — validated against `^(anthropic|openai|google|groq|mistral|together|ollama)$` before any shell command is built
- **Bash arrays for command construction** — `CMD=(...)` / `"${CMD[@]}"`, never string concatenation
- **LiteLLM logging suppressed** — `litellm.suppress_debug_info = True` prevents prompts and responses from appearing in workflow logs
- **PR diffs are untrusted** — forwarded to LLM API but never executed locally; all subprocess calls use argument lists, never `shell=True`

---

## CI & Release

### `ci.yml` — Continuous integration

Runs on every push and PR: lint (`ruff`), format check (`ruff format --check`), tests (`pytest` with coverage). **Coverage gate: ≥ 50%.**

### `codeql.yml` — Static security analysis

Runs CodeQL on every push and PR (`security-and-quality` suite). Flags CWE-78 (injection), CWE-312 (clear-text logging), and related issues.

### `release.yml` — Semantic versioning

| Commit prefix | Version bump |
|---|---|
| `feat:` | minor |
| `fix:` | patch |
| `BREAKING CHANGE:` | major |
| `docs:`, `chore:`, `style:` | none |

---

## Philosophy

1. **LLM-first** — your chosen LLM reads your actual code and writes every file from scratch
2. **Measurable** — the eval framework proves whether the context files actually improve AI responses
3. **Never modify existing code** — only additive changes, always
4. **Non-circular eval** — ground truth is extracted from raw source, not from the generated files themselves
5. **Platform-agnostic** — works with Claude, OpenAI, Gemini, Groq, or any LLM via `system_prompt.md`
6. **Idempotent** — safe to run multiple times; the `static` section of `agent-context.json` is always preserved

---

## Contributing

Contributions are very welcome. AgentReady is an early-stage open-source project.

**Good first issues:**
- Add support for a new language or framework in the analyser
- Improve golden set questions for specific tech stacks (Django, Rails, Spring Boot)
- Write tests for `analyser.py` and `generator.py` to improve coverage

**Bigger contributions:**
- Monorepo support — detect and handle multiple modules with per-module context files
- VS Code extension — surface the readiness score inline
- Improve hallucination rate on sparse repos (single file, no tests, no CI)

**How to contribute:**

```bash
git checkout -b feat/my-improvement
# make changes
ruff format src tests
ruff check src tests
python -m pytest tests/ -q --cov=src/agent_ready --cov-fail-under=50
git push
# open a Pull Request — all CI gates must pass
```

---

## License

MIT — see [LICENSE](LICENSE) for details.
