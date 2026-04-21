# AgentReady

[![Version](https://img.shields.io/github/v/release/vb-nattamai/agent-ready)](https://github.com/vb-nattamai/agent-ready/releases)
[![CI](https://github.com/vb-nattamai/agent-ready/actions/workflows/ci.yml/badge.svg)](https://github.com/vb-nattamai/agent-ready/actions/workflows/ci.yml)
[![CodeQL](https://github.com/vb-nattamai/agent-ready/actions/workflows/codeql.yml/badge.svg)](https://github.com/vb-nattamai/agent-ready/actions/workflows/codeql.yml)
[![License](https://img.shields.io/github/license/vb-nattamai/agent-ready)](LICENSE)

Transform any legacy repository into an AI-agent-ready codebase — with real content written from your actual code, not template placeholders.

---

## Why AgentReady?

AI agents fail on unfamiliar codebases because they lack context — they invent file paths, guess commands, and miss domain concepts entirely. AgentReady fixes this by generating scaffolding files that give agents real, verified knowledge of your repository before they touch a single line of code.

**Measurable improvement — verified on real codebases:**

AgentReady v2 uses a **non-circular golden-set eval**: ground truth is extracted from raw source code (not the generated files), and the baseline uses a weak model with no context. This ensures the scores reflect genuine improvement rather than circular self-reference.

Typical results on well-structured repos with tests, CI, and env vars:
- Context score improvement: **+7–9 pts** over no-context baseline
- Pass rate: **85–100%** on the golden question set
- Hallucination rate: **<15%** (industry standard is <10–15% for RAG systems)

For minimal repos (single file, no tests, no CI), honest scores reflect that sparsity — the tool never inflates readiness.

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
Phase 5 — Evaluate  : golden-set questions (13 base + language overlay)
                      measure whether context files actually improve AI responses
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

# Transform + measure improvement in one shot
agent-ready --target /path/to/your/repo --eval

# Preview without writing any files
agent-ready --target /path/to/your/repo --dry-run
```

See [CLI Reference](#cli-reference) for all flags.

---

## GitHub Actions — Transform via Issue

The recommended way for teams. Open an issue in your repo, get a PR automatically.

### Step 1 — Install the trigger workflow

Run **"Install AgentReady to Target Repository"** from the [Actions tab](https://github.com/vb-nattamai/agent-ready/actions/workflows/install-to-target-repo.yml):

- **target_repo**: `myorg/my-legacy-api`
- **provider**: `anthropic` (or `openai`, `google`, `groq`, `mistral`, `together`, `ollama`)
- **eval**: ✅ enable eval after transformation (optional)

This pushes **five files** into your repo:
- `.github/workflows/agentic-ready.yml` — issue trigger (with eval enabled)
- `.github/workflows/context-drift-detector.yml` — weekly drift detection
- `.github/workflows/pr-review.yml` — AI-powered PR review
- `.github/workflows/agentic-ready-eval.yml` — eval-only (manual + push-triggered)
- `.github/ISSUE_TEMPLATE/agentic-ready.yml` — pre-filled issue form

### Step 2 — Add your secrets

For the installed issue-trigger flow, set secrets in your **target repo** (`.github/workflows/agentic-ready.yml` runs there and forwards them to the reusable workflow with `secrets: inherit`).

Target repo → Settings → Secrets and variables → Actions:

```
ANTHROPIC_API_KEY = sk-ant-...   # set the key for your chosen provider
INSTALL_TOKEN     = ghp_...       # PAT with repo + workflow scopes
```

> **Trust boundary:** Only collaborators with `admin`, `maintain`, or `write` access can trigger a run. The workflow can push branches and open PRs in the target repo — use a repo-scoped token where possible and rotate it regularly.

### Step 3 — Open an issue

Go to your repo → Issues → New Issue → **"🤖 AgentReady — Transform this repo"** → Submit.

```
Issue opened
    │
    ├─ 1. Checks you are a repo collaborator
    ├─ 2. Calls agent-ready's reusable transformer
    ├─ 3. Analysis model reads your codebase (~60s)
    ├─ 4. Generation model writes all scaffolding files
    ├─ 5. (Optional) Evaluation model runs golden-set questions across 5 categories
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
| `.github/copilot-instructions.md` | GitHub Copilot workspace instructions |
| `system_prompt.md` | Universal system prompt for any LLM |
| `mcp.json` | MCP server configuration |
| `memory/schema.md` | Agent memory/state contract |
| `tools/refresh_context.py` | Script to refresh `agent-context.json` on demand |
| `.github/dependabot.yml` | Dependency update configuration |
| `.github/CODEOWNERS` | Code ownership for PR routing |
| `openapi.yaml` | OpenAPI spec stub (generated for REST API repos) |
| `.agent-ready/custom_questions.json` | Hook for repo-specific eval questions |
| `AGENTIC_EVAL.md` | Evaluation report — verdict, scores, per-question breakdown |

> The `static` section of `agent-context.json` is safe to edit manually. The `dynamic` section is auto-refreshed on every scan.

---

## Eval Framework

AgentReady measures whether the generated files **actually improve AI responses** — not just whether the files exist. It answers: *"If an agent reads these context files, does it give better, safer, more accurate answers?"*

```bash
# Run eval right after transformation
agent-ready --target /path/to/repo --eval

# Run eval only (context files already exist)
agent-ready --target /path/to/repo --eval-only

# CI gate — fail the step if pass rate < 80%
agent-ready --target /path/to/repo --eval-only --fail-level 0.8
```

---

### Step 1 — Golden-set questions

AgentReady ships **versioned golden question sets** — not dynamically generated questions. This is the key difference from v1: questions are pre-authored by domain experts and are stable across runs, enabling reproducible benchmarking.

**Question sets (committed to `src/agent_ready/golden_sets/`):**

| Set | File | Loaded for |
|-----|------|-----------|
| Base | `base.json` | Every repo (13 questions) |
| Python | `python.json` | Python repos (+6 questions) |
| JavaScript/Node | `javascript.json` | JS/Node repos (+6 questions) |
| Java | `java.json` | Java repos (+4 questions) |
| Go | `go.json` | Go repos (+4 questions) |

Total: **13–19 questions per repo** depending on language.

**5 question categories:**

| Category | Count (base) | What it tests |
|---|---|---|
| **commands** | 3 | Exact test, build, and install commands |
| **safety** | 3 | Restricted paths, secret handling, injection prevention |
| **domain** | 2 | Business concepts, key domain terms |
| **architecture** | 3 | Entry point, language/framework, module layout |
| **adversarial** | 2 | Edge cases designed to induce hallucination |

**Custom questions for your repo:** Drop a `.agent-ready/custom_questions.json` file in your target repo and AgentReady will include those questions in every eval run — useful for testing domain-specific knowledge your standard golden set doesn't cover.

---

### Step 2 — Non-circular ground truth + baseline

This is what separates v2 from v1. **Ground truth is extracted from raw source code** — not from the generated context files — using a lightweight model (haiku-class). This breaks the circular loop where the same model that wrote the files also judges them.

Each question is then asked **twice** using deliberately asymmetric models:

1. **Baseline** — a weak, fast model with **zero context** (haiku-class). Represents what an AI agent knows *without* your scaffolding. This is a realistic floor — the kind of model a junior developer might use.
2. **With context** — a strong model with **all generated context files** loaded as the system prompt (`agent-context.json`, `AGENTS.md`, `CLAUDE.md`, `system_prompt.md`, `.github/copilot-instructions.md`, `memory/schema.md`). Represents what the agent knows *with* your scaffolding.

The delta between the two is the measurable value your scaffolding adds.

**Baseline models per provider:**

| Provider | Baseline (no context) | Context model |
|---|---|---|
| `anthropic` | claude-haiku-4-5 | claude-opus-4-6 |
| `openai` | gpt-4.1-mini | gpt-5.4 |
| `google` | gemini-1.5-flash-8b | gemini-2.5-pro |

---

### Step 3 — Three-judge panel (multi-agent)

The "with context" response goes through a **panel of three specialist judges**, each running concurrently with the same model but a different system prompt:

| Judge | Specialisation | Fails when… |
|---|---|---|
| 🔬 **Factual Accuracy** | Exact facts — commands, file paths, class names | Any flag, path, or name differs from ground truth |
| 🔄 **Semantic Equivalence** | Same meaning, different words | Meaning is materially wrong or incomplete |
| 🛡️ **Operational Safety** | Safe to act on | Response would break the build, leak a secret, or hallucinate a path |

**Verdict = majority vote** — at least **2 of 3 judges** must pass the response. This prevents a single overly strict or overly lenient judge from flipping the outcome. The final score is the mean of all three judges' 0–10 scores.

The baseline uses a single judge (it is a reference point only; the panel is applied where it matters — the context response).

```
Question: "How do I run the tests?"

  🔬 Factual:    8/10 ✓  (exact command present)
  🔄 Semantic:   9/10 ✓  (meaning correct)
  🛡️ Safety:    7/10 ✓  (safe to run)

  Panel vote:  3/3  →  ✅ PASS  (score: 8.0/10)
```

### Step 4 — Hallucination detection

Every context response is checked for hallucination: **did the model invent a specific file path, class name, function, or command that does not exist in the codebase?**

This uses a precise definition aligned with industry standards — reasonable inferences and setup recommendations are not hallucinations. Only fabricated codebase-specific facts count.

**Industry benchmark:** Production RAG systems target <10–15% hallucination rate. AgentReady's hallucination rate improves with codebase richness — sparse repos (1 file, no tests) naturally produce more "uncertain" answers that border on hallucination.

---



Results are saved to `AGENTIC_EVAL.md` in the repo root and include:

- **Verdict** — ✅ Strong / ⚠️ Moderate / ❌ Weak improvement
- **Score table** — baseline vs. context scores and delta per category
- **Per-question breakdown** — ground truth, judge panel votes and reasoning
- **What to Improve** — list of failed questions with what was missing

Example verdict line:

```
✅ Context files significantly improve AI responses (+6.4 pts, 87% pass rate)
```

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

# Review a PR and post a GitHub review
agent-ready --target /path/to/repo --review-pr 42

# Dry-run: see the review decision without posting
agent-ready --target /path/to/repo --review-pr 42 --dry-run
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

### `reusable-eval.yml` — Standalone evaluator

Runs evaluation only (no transformation) against any target repo. Called by the installed `agentic-ready-eval.yml` workflow and also dispatchable manually from the `agent-ready` Actions tab.

**Inputs:**

| Input | Default | Purpose |
|---|---|---|
| `target_repo` | required | Target repo in `owner/repo` format |
| `provider` | `anthropic` | LLM provider |
| `fail_level` | `0.5` | Exit 1 if pass rate below threshold |

**Outputs:** Saves `AGENTIC_EVAL.md` to the step summary and uploads it as a workflow artifact (retained 30 days).

### `reusable-transformer.yml` — Core transformer

The engine. Checks out the target repo, runs the LLM pipeline, optionally runs eval, opens a PR.

**Inputs:**

| Input | Default | Purpose |
|---|---|---|
| `target_repo` | required | Target repo in `owner/repo` format |
| `target_branch` | `main` | Branch the PR is opened against |
| `provider` | `anthropic` | LLM provider: `anthropic`, `openai`, `google`, `groq`, `mistral`, `together`, `ollama` |
| `eval` | `true` | Run eval after transformation |
| `fail_level` | `0.5` | Exit 1 if eval pass rate below threshold |
| `only` | _(all)_ | Limit: `agents`, `context`, `memory` |
| `force` | `false` | Overwrite existing generated files |
| `issue_number` | _(none)_ | Issue to close after PR is opened |

**Where secrets live:**

| Run mode | Secret location |
|---|---|
| Installed issue trigger in a target repo (`agentic-ready.yml`) | Target repo secrets (forwarded with `secrets: inherit`) |
| Manual run from `vb-nattamai/agent-ready` Actions tab (`workflow_dispatch`) | `agent-ready` repo secrets |

### `install-to-target-repo.yml` — One-click installer

Triggered manually from the Actions tab. Pushes trigger workflows into any target repo and creates the first transformation issue automatically.

**Requires:** `INSTALL_TOKEN` secret (PAT with `repo` + `workflow` scopes).

### `context-drift-detector.yml` — Weekly drift detection

Runs every Monday at 09:00 UTC. Detects if `agent-context.json` has structurally drifted from the current codebase and opens a PR if drift is found. Also installed into target repos by the installer.

### `pr-review.yml` — AI-powered PR review

Installs into target repos. Runs on every pull request and posts an **APPROVE** or **REQUEST_CHANGES** review grounded in `agent-context.json` — so the reviewer understands your architecture, restricted paths, domain concepts, and known pitfalls before reading a single line of diff.

**How it works:**
1. Checks out the base branch (never runs untrusted PR code)
2. Loads `agent-context.json` for architecture context
3. Fetches the PR diff via `gh pr diff`
4. Sends diff + context to the LLM for structured analysis
5. Posts a review with specific file/line comments

**Requires:** `ANTHROPIC_API_KEY` secret in the target repo (or your provider's key).

**Security note:** Uses `pull_request_target` — the review script always runs from the base branch, keeping secrets inaccessible to PR authors.

**Privacy note:** PR diffs and descriptions are sent to an external LLM API (Anthropic by default). Do not use this workflow if your diffs may contain secrets or confidential material not suitable for third-party processing.

### `agentic-ready-eval.yml` — Eval-only for target repos (installed template)

Installed as `.github/workflows/agentic-ready-eval.yml` in every target repo. Triggers:
- **Manual** — `workflow_dispatch` from the Actions tab (with optional `fail_level`)
- **Automatic** — on every `push` to `main` when scaffolding files (`AGENTS.md`, `CLAUDE.md`, `system_prompt.md`, `agent-context.json`) or `src/` change

This lets you track scaffolding quality over time independently of the full transformation. Results appear in the workflow step summary and as a downloadable `AGENTIC_EVAL.md` artifact.

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

### `ci.yml` — Continuous integration

Runs on every push and PR. Steps: lint (`ruff`), format check (`ruff format --check`), tests (`pytest` with coverage). **Coverage gate: ≥ 50%.**

### `codeql.yml` — Static security analysis

Runs CodeQL on every push and PR using the `security-and-quality` query suite. Flags CWE-78 (injection), CWE-312 (clear-text logging), and related issues.

---

## Security Model

All reusable workflows are hardened against GitHub Actions expression injection:

- **No `${{ inputs.* }}` or `${{ github.event.* }}` in `run:` blocks.** Every user-controlled value is assigned to an `env:` variable first and referenced as `$VAR` in shell.
- **Provider allowlist.** The `provider` input is validated against `^(anthropic|openai|google|groq|mistral|together|ollama)$` using bash `=~` before any shell command is constructed.
- **Secrets fallback.** All `secrets.INSTALL_TOKEN || github.token` patterns use the safe form: `secrets.INSTALL_TOKEN != '' && secrets.INSTALL_TOKEN || github.token`.
- **LiteLLM logging suppressed.** `litellm.suppress_debug_info = True` and `litellm.set_verbose = False` are set before every API call to prevent repo context, prompts, and LLM responses from appearing in workflow logs.
- **Bash arrays for command construction.** CLI commands are built with `CMD=(...)` / `CMD+=(...)` / `"${CMD[@]}"` — never string concatenation — to prevent word-splitting on user-supplied values.

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
| GitHub Copilot | `.github/copilot-instructions.md` | Workspace instructions loaded in Copilot Chat |
| Any LLM | `system_prompt.md` | Paste as the `system` parameter |
| MCP clients | `mcp.json` | Loaded by the MCP host |
| GitHub agents (AGENTS.md) | `AGENTS.md` | Drop into any agent that reads workspace files |

---

## MCP Server

AgentReady ships an MCP (Model Context Protocol) server that exposes its core capabilities as tools for any MCP-compatible client (Claude Desktop, Cursor, Continue, etc.).

```bash
# Install and start
pip install "git+https://github.com/vb-nattamai/agent-ready.git[ai]"
agent-ready-mcp
```

**Available tools:**

| Tool | Description |
|------|------------|
| `transform` | Transform a target repository — runs the full 5-phase pipeline |
| `score` | Compute the agentic readiness score for an already-transformed repo |
| `evaluate` | Run the golden-set eval against existing context files |
| `review_pr` | Review a pull request and return structured feedback |

**Configure in your MCP host** (e.g. Claude Desktop `~/.claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "agent-ready": {
      "command": "agent-ready-mcp",
      "env": {
        "ANTHROPIC_API_KEY": "sk-ant-..."
      }
    }
  }
}
```

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
- Improve cross-repo secret ergonomics while keeping least-privilege defaults
- Reasoning trace in eval — capture not just what was wrong but why the agent chose that path

**How to contribute:**

1. Fork this repository
2. Create a feature branch: `git checkout -b feat/my-improvement`
3. Commit with conventional commits: `feat:`, `fix:`, `docs:`
4. Run the full pre-push checklist:
   ```bash
   git pull --rebase \
     && ruff format src tests \
     && ruff check src tests \
     && python -m pytest tests/ -q --cov=src/agent_ready --cov-fail-under=50 \
     && git push
   ```
5. Open a Pull Request — all CI gates must pass: format check, lint, coverage ≥ 50%, CodeQL clean

Please open an issue first for significant changes so we can discuss the approach before you invest time building it.

---

## License

MIT — see [LICENSE](LICENSE) for details.
