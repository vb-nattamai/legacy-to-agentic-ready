# AgentReady

**Transform any repository into a structured, verifiable context layer for AI coding agents.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-2.8.0-green.svg)](https://github.com/vb-nattamai/agent-ready/releases)

---

## Overview

AI coding agents operating on unfamiliar repositories produce unreliable output not because of model capability limitations, but because they lack structured knowledge of the codebase. Without explicit context, agents hallucinate file paths, invent build commands, and make incorrect assumptions about domain logic and project conventions.

AgentReady addresses this at the source. It analyses a repository's structure, source files, CI configuration, and documentation, then generates a set of platform-specific context files that make the codebase legible to any AI agent. It then measures whether those files actually improve agent behaviour using a grounded evaluation framework.

**Supported providers:** Claude · OpenAI · Gemini · Groq · Mistral · Together · Ollama

---

## Table of Contents

- [How It Works](#how-it-works)
- [Generated Artifacts](#generated-artifacts)
- [Skills and Hooks](#skills-and-hooks)
- [Evaluation Framework](#evaluation-framework)
- [Quick Start](#quick-start)
- [Cost and Time](#cost-and-time)
- [Requirements](#requirements)
- [CLI Reference](#cli-reference)
- [GitHub Actions Integration](#github-actions-integration)
- [Model Strategy](#model-strategy)
- [Context Freshness](#context-freshness)
- [PR Review Agent](#pr-review-agent)
- [agent-context.json Structure](#agent-contextjson-structure)
- [Language and Framework Support](#language-and-framework-support)
- [Gitea Support](#gitea-support)
- [Design Principles](#design-principles)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## How It Works

AgentReady operates as a five-phase pipeline:

**Phase 1: Collect**
Mechanically reads the file tree, source files, configuration, CI pipelines, README, and build definitions. No LLM involved — pure file I/O.

**Phase 2: Analyse**
The analysis model reads the collected files and extracts domain concepts, entry points, environment variables, module layout, and known operational pitfalls specific to the codebase.

**Phase 3: Generate**
The generation model produces all scaffolding files from scratch based on the analysis output. No templates are filled in. Files are written for each supported agent platform, including the new `skills/`, `hooks/`, and `.cursorrules` artifacts.

**Phase 4: Score**
Computes a 100-point agentic readiness score based on which structured context criteria are satisfied.

**Phase 5: Evaluate**
The evaluation model runs 19 structured questions across five categories against the repository, comparing responses with and without the generated context files. Ground truth is derived from raw source code, not from the generated files, eliminating circularity. Results are written to `AGENTIC_EVAL.md` and surfaced in the pull request.

The output is a pull request containing all generated files and a quantified eval report.

---

## Generated Artifacts

| File | Purpose |
|---|---|
| `AGENTS.md` | Operating contract for GitHub Copilot and OpenAI agents — defines safe operations, forbidden operations, and domain glossary |
| `CLAUDE.md` | Automatically loaded by Claude Code at session start — includes module layout, conventions, and critical commands |
| `.cursorrules` | Automatically loaded by Cursor at project open — equivalent to `CLAUDE.md` for Cursor users |
| `system_prompt.md` | Universal system prompt compatible with any LLM interface |
| `agent-context.json` | Machine-readable repository map with static and dynamic sections |
| `mcp.json` | MCP server configuration for Claude and MCP-compatible clients |
| `openapi.yaml` | Auto-generated OpenAPI 3.1 stub — fill in paths and schemas, validate with Redocly |
| `memory/schema.md` | Agent working memory and state contract |
| `skills/` | Slash-command skill definitions for repo-specific agent actions (run-tests, build, lint, etc.) |
| `tools/` | Helper scripts for maintaining the agent context — includes `refresh_context.py` to re-run AgentReady and keep `agent-context.json` current as the codebase evolves |
| `cost_report.json` | Token usage and estimated USD cost breakdown per model — covers generation and evaluation phases |
| `hooks/` | Session-continuity hooks for Claude Code (session-start, pre-tool-call, post-test, pre-commit) |
| `AGENTIC_EVAL.md` | Evaluation report showing baseline and with-context scores per category |

---

## Skills and Hooks

AgentReady generates repo-specific skill definitions and session hooks in addition to context files. These go beyond telling the agent what the repo is — they tell it what it can do and how to maintain state across sessions.

### Skills

Skills are invocable slash-command definitions placed in the `skills/` directory. Each skill is a self-contained instruction set for a specific repo action, grounded in the commands detected during analysis.

Skills generated depend on what the repo contains:

| Detected signal | Skill generated |
|---|---|
| Test runner detected | `skills/run-tests.md` |
| Build command detected | `skills/build.md` |
| Linter detected | `skills/lint.md` |
| Docker or docker-compose present | `skills/start-local.md` |
| Migration framework detected | `skills/run-migrations.md` |
| CI config present | `skills/run-ci.md` |
| OpenAPI spec present | `skills/generate-api-docs.md` |
| Package manager detected | `skills/add-dependency.md` |

`skills/run-tests.md` and `skills/build.md` are always generated. If exact commands are not determinable from source, the skill file explicitly states what is not known and where to find the information. Commands in skill files come from `agent-context.json`. Skills never invent commands.

### Hooks

Hooks are session continuity definitions placed in the `hooks/` directory. They fire at specific points in the Claude Code lifecycle to load current repository state and enforce constraints.

| Hook | When it fires | Always generated |
|---|---|---|
| `hooks/session-start.md` | Start of every Claude Code session | Yes |
| `hooks/pre-tool-call.md` | Before any file-writing tool call | Yes |
| `hooks/post-test.md` | After running the test command | When test runner detected |
| `hooks/pre-commit.md` | Before a git commit | When linter detected |

The `pre-tool-call` hook checks the target path against `restricted_write_paths` in `agent-context.json` before any write operation. This enforces the non-destructive constraint at the tool level, not just at the instruction level.

---

## Evaluation Framework

Every transformation includes a structured evaluation that measures whether the generated context files produce a measurable improvement in agent response quality.

### Methodology

| Parameter | Value |
|---|---|
| Questions | 19 across 5 categories |
| Baseline model | claude-sonnet-4-6 with no context |
| Context model | claude-sonnet-4-6 with all generated files |
| Judge | claude-haiku-4-5 — 3-panel majority vote (factual, semantic, safety) |
| Ground truth source | Raw source code — not the generated context files |

### Observed Results

Results from the hello_world example — a minimal Flask REST API with 4 endpoints, pytest tests, pyproject.toml, and CI. Eval design: sonnet vs sonnet baseline, haiku judge.

| Category | Baseline (no ctx) | With Context | Improvement | Pass rate |
|---|---|---|---|---|
| **Overall** | 1.7 / 10 | **5.7 / 10** | +4.0 pts | 47% (9/19) |
| Commands | 2.8 / 10 | **6.2 / 10** | +3.4 pts | 40% |
| Safety | 2.2 / 10 | **6.8 / 10** | +4.6 pts | 75% |
| Architecture | 0.8 / 10 | **4.8 / 10** | +4.0 pts | 40% |
| Domain | 0.0 / 10 | **6.3 / 10** | +6.3 pts | 50% |
| Adversarial | 1.7 / 10 | **4.5 / 10** | +2.8 pts | 33% |

Both baseline and context responses use the same model (sonnet), so scores reflect the impact of context files alone — not model capability differences.

The strongest signal is domain understanding (+6.3 pts) and safety (+4.6 pts). Without context, sonnet scores 0/10 on domain questions. With context it reaches 6.3/10 — the agent can describe the system's purpose and key concepts.

The adversarial category reflects a known limitation: when the correct answer is "not determinable from the available source files," the model with context sometimes produces confident but incorrect responses, treating the generated scaffolding files as authoritative project documentation. This is under active remediation.

The evaluation report produced after each transformation identifies specifically which questions failed and what information was missing, providing an actionable improvement path rather than a single aggregate score.

### Evaluating existing context files

The evaluation framework works on any repository — not just ones AgentReady transformed.
If you have written `CLAUDE.md` or `AGENTS.md` by hand, run:

```bash
agent-ready --target /path/to/repo --eval-only
```

This scores whatever context files exist and tells you exactly which questions failed and what information was missing. Use it as a benchmark before and after manual edits.

```bash
# Evaluate and fail CI if pass rate is below 60%
agent-ready --target /path/to/repo --eval-only --fail-level 0.6
```

---

## Quick Start

The recommended path is the one-click installer available in the AgentReady Actions tab.

1. Navigate to [Actions → Install AgentReady to Target Repository](https://github.com/vb-nattamai/agent-ready/actions/workflows/install-to-target-repo.yml)
2. Click **Run workflow**
3. Enter the target repository in `owner/repo` format and select an LLM provider
4. The installer pushes a trigger workflow to the target repository, opens an issue, and applies the `agentic-ready` label
5. The transformation runs automatically and opens a pull request with all generated files

Review the pull request, fill in the `static` section of `agent-context.json` with project-specific details, and merge.

For a complete example of what AgentReady generates, see [`examples/hello_world_output/`](examples/hello_world_output/) — a full transformation output against a minimal Python/Flask project, including skills, hooks, and all context files.

---

## Cost and Time

### How long does a transformation take?

A full transformation on a typical repository takes 3-8 minutes end to end.

| Phase | Approximate time |
|---|---|
| Analysis (reads codebase) | 30-90 seconds |
| Generation (writes all files) | 60-180 seconds |
| Evaluation (19 questions) | 60-120 seconds |
| Total | 3-8 minutes |

Time scales with repository size. A minimal single-file repo completes in under 3 minutes. A large multi-module repo with many source files may take up to 10 minutes.

### How many LLM calls does it make?

A full transformation makes approximately 50-65 LLM calls depending on which artifacts are generated.

| Stage | Calls |
|---|---|
| Analysis | 1 |
| Generation (per artifact) | 1 per file — approximately 8-12 total |
| Skill generation | 1 per skill — 2-8 depending on repo |
| Hook generation | 1 per hook — 2-4 depending on repo |
| Evaluation (19 questions × 2 models) | 38 |
| Total | Approximately 50-65 |

### Approximate cost per provider

Costs are based on observed runs including the full evaluation phase (38 LLM calls across baseline and context models). A minimal single-file repo costs approximately $1.35. Larger repos with more source files will cost more.

| Provider | Model tier | Approximate cost per run |
|---|---|---|
| Anthropic (default) | Opus / Sonnet / Haiku | $1.00 - $1.50 |
| OpenAI | GPT-4o / GPT-4o-mini | $0.10 - $0.30 |
| Google | Gemini 2.5 Pro / Flash | $0.05 - $0.20 |
| Groq | Llama 3.3 70B | $0.01 - $0.05 |
| Mistral | Large / Small | $0.05 - $0.15 |
| Together | Qwen / Llama | $0.02 - $0.08 |
| Ollama | Local models | Free (local compute only) |

> These are estimates based on typical repository sizes. Your actual cost depends on the number of source files, their length, and which artifacts are generated. Run with `--dry-run` first to preview what will be generated without incurring any cost.

### How to reduce cost

- Use `--provider groq` or `--provider together` for the lowest cost per run.
- Use `--eval-only` or omit `--eval` to skip the evaluation step — this removes the 38 evaluation calls and reduces cost by approximately 60%.
- Use `--only agents` or `--only context` to regenerate specific artifacts only, rather than running the full pipeline.
- Use Ollama for fully local, zero-cost runs (quality will vary by model).

---

## Requirements

- Python 3.9 or higher
- An API key for the chosen LLM provider

```bash
# Anthropic (default)
export ANTHROPIC_API_KEY="sk-ant-..."

# OpenAI
export OPENAI_API_KEY="sk-..."

# Google
export GOOGLE_API_KEY="..."

# Groq
export GROQ_API_KEY="..."

# Mistral
export MISTRAL_API_KEY="..."

# Together
export TOGETHER_API_KEY="..."

# Ollama — no key required; requires a running local Ollama instance
```

---

## CLI Reference

```bash
# Install (with LLM support)
pip install "git+https://github.com/vb-nattamai/agent-ready.git[ai]"

# Or install from source for development
git clone https://github.com/vb-nattamai/agent-ready.git
cd agent-ready
pip install -e '.[dev]'
```

| Command | Description |
|---|---|
| `agent-ready --target /path/to/repo --provider anthropic` | Full transformation with evaluation |
| `agent-ready --target /path/to/repo --dry-run` | Preview generated files without writing |
| `agent-ready --target /path/to/repo --only context --force` | Regenerate context map only |
| `agent-ready --target /path/to/repo --only agents` | Regenerate agent instruction files only |
| `agent-ready --target /path/to/repo --eval` | Run evaluation after transformation |
| `agent-ready --target /path/to/repo --eval-only` | Evaluate existing context files without running transformation |
| `agent-ready --target /path/to/repo --eval-only --fail-level 0.6` | Evaluate and fail if pass rate is below 60% |
| `agent-ready --target /path/to/repo --review-pr 42` | Run PR review agent against PR number 42 |
| `agent-ready --target /path/to/repo --eval --fail-level 0.8` | Fail if eval pass rate is below 80% — use as a CI gate |
| `agent-ready --target /path/to/repo --quiet` | Suppress output for CI pipelines |

---

## GitHub Actions Integration

### Trigger Mechanism

The installer pushes a workflow to the target repository that triggers on issue labelling:

```yaml
on:
  issues:
    types: [labeled]
```

Using `labeled` as the sole trigger prevents duplicate runs. When the installer creates an issue and applies the label in a single operation, GitHub fires both `opened` and `labeled` events. Listening only to `labeled` ensures the transformation runs exactly once.

To retrigger a transformation on a repository that already has the workflow installed, apply the `agentic-ready` label to any existing issue.

### Execution Flow

```
agentic-ready label applied to issue
    |
    +-- 1. Verify actor has write access to the repository
    +-- 2. Analysis model reads full codebase (~60 seconds)
    +-- 3. Generation model writes all scaffolding files
    |       Includes: AGENTS.md, CLAUDE.md, .cursorrules, system_prompt.md,
    |                 agent-context.json, mcp.json, memory/schema.md,
    |                 skills/ (2-8 files), hooks/ (2-4 files)
    +-- 4. Evaluation model runs 19 questions (baseline vs with-context)
    +-- 5. Open pull request: "Add agentic-ready scaffolding"
    +-- 6. Post PR link as comment on the triggering issue
    +-- 7. Close the issue
```

### Evaluation as a CI Gate

Set `fail_level` in the installed `agentic-ready.yml` to block pull request creation if context quality falls below a defined threshold:

```yaml
fail_level: '0.8'  # fail if fewer than 80% of 19 evaluation questions pass
```

### Required Secrets

Configure the following secrets in the target repository under Settings → Secrets and variables → Actions:

| Secret | Required for |
|---|---|
| `ANTHROPIC_API_KEY` | provider: anthropic (default) |
| `OPENAI_API_KEY` | provider: openai |
| `GOOGLE_API_KEY` | provider: google |
| `GROQ_API_KEY` | provider: groq |
| `MISTRAL_API_KEY` | provider: mistral |
| `TOGETHER_API_KEY` | provider: together |
| `INSTALL_TOKEN` | All providers — PAT with `repo` and `workflow` scopes |

For manual runs triggered directly from the AgentReady Actions tab, secrets must be configured in the `agent-ready` repository rather than the target repository.

---

## Model Strategy

AgentReady applies a tiered model strategy within each provider. The most capable model is used for analysis, a mid-tier model for generation, and the most cost-efficient model for evaluation.

> During evaluation, the generation model is used for both baseline and context responses (ensuring a fair comparison). The evaluation model acts as the judge.

| Provider | Analysis | Generation | Evaluation |
|---|---|---|---|
| `anthropic` | claude-opus-4-6 | claude-sonnet-4-6 | claude-haiku-4-5 |
| `openai` | gpt-5.4 | gpt-5.4-mini | gpt-5.4-nano |
| `google` | gemini-2.5-pro | gemini-2.5-pro | gemini-2.5-flash-lite |
| `groq` | llama-3.3-70b | llama-3.3-70b | llama-3.1-8b-instant |
| `mistral` | mistral-large | mistral-large | mistral-small |
| `together` | Qwen3.5-397B | Llama-3.3-70B | Qwen3.5-9B |
| `ollama` | llama3.3 | llama3.3 | llama3.2 |

---

## Context Freshness

Generated context becomes stale as the codebase evolves. AgentReady provides two mechanisms to maintain accuracy.

**Automated weekly drift detection** is installed into the target repository by the installer. It runs every Monday at 09:00 UTC, detects structural drift in `agent-context.json` relative to the current codebase, and opens a pull request if updates are required. No manual action is needed.

**Manual refresh** regenerates the context map on demand:

```bash
agent-ready --target /path/to/repo --only context --force
```

---

## PR Review Agent

AgentReady includes an LLM-powered pull request review agent. Reviews are grounded in the repository's `agent-context.json`, ensuring that feedback respects the project's domain conventions, restricted paths, and architectural constraints.

```bash
agent-ready --target /path/to/repo --review-pr 42
```

The agent posts an `APPROVE` or `REQUEST_CHANGES` review directly to GitHub. A workflow template is also available that runs the review agent automatically on every pull request opened in the target repository.

---

## agent-context.json Structure

The repository context map is divided into two sections with different update semantics.

**Static section** — edited manually once after the initial transformation. Contains project identity, entry points, restricted write paths, required environment variables, and domain concepts. This section is never overwritten by subsequent tool runs.

**Dynamic section** — regenerated automatically on every scan. Contains the current module layout, last scanned timestamp, and derived agent capabilities. Updated by the weekly drift detector and manual refresh commands.

This separation preserves manual domain knowledge while keeping structural metadata current.

---

## Language and Framework Support

| Language | Detected Frameworks and Runtimes |
|---|---|
| Python | Django, Flask, FastAPI, scripts |
| TypeScript / JavaScript | React, Next.js, Node.js, Express |
| Java | Spring Boot, Maven, Gradle |
| Go | Gin, Echo, standard library |
| Rust | Cargo |
| C# / .NET | ASP.NET, console applications |
| Ruby | Rails |

Generic fallback templates are applied for languages and frameworks not listed above.

---

## Gitea Support

AgentReady supports Gitea with identical workflow YAML syntax. Replace `.github/` with `.gitea/` throughout. The reusable workflow reference becomes:

```yaml
uses: your-gitea.com/vb-nattamai/agent-ready/.gitea/workflows/reusable-transformer.yml@main
```

See [docs/automation.md](docs/automation.md) for full Gitea configuration including the collaborator permission check via the Gitea REST API.

---

## Design Principles

- **Non-destructive** — existing files are never modified; only new files are created
- **Grounded** — all generated content is derived from analysis of actual repository contents, not from templates or hallucination
- **Measured** — every transformation includes a quantified evaluation of output quality
- **Idempotent** — safe to run multiple times; subsequent runs update generated files without duplication
- **Transparent** — every generated file includes a header identifying it as generated and describing its purpose
- **Actionable** — skills and hooks extend context into executable instructions, so agents know not just what the repo is but what they can do in it

---

## Troubleshooting

**Two pull requests are created on the same transformation**
The installed `agentic-ready.yml` is listening to both `opened` and `labeled` issue events. Change the trigger to `labeled` only.

**Workflow does not trigger after labelling an issue**
Confirm the `agentic-ready` label exists in the target repository and that GitHub Actions is enabled under Settings → Actions → General.

**403 error when pushing generated files**
The `INSTALL_TOKEN` has expired or does not have the required `repo` and `workflow` scopes. Use the token validation workflow in the AgentReady Actions tab before re-running.

**529 API overloaded errors**
The transformer includes retry logic with up to five attempts and increasing wait intervals. If all retries are exhausted, wait 10-15 minutes and retrigger by applying the label to a new issue.

---

## Contributing

Contributions are welcome. Please open an issue to discuss significant changes before submitting a pull request.

```bash
git checkout -b feature/your-improvement
git commit -m "feat: description of change"
git push origin feature/your-improvement
# Open a pull request against main
```

Commit message prefixes determine version bumps on merge to `main`:

| Prefix | Version bump |
|---|---|
| `feat:` | Minor (1.x.0) |
| `fix:` | Patch (1.0.x) |
| `BREAKING CHANGE:` | Major (x.0.0) |
| `docs:` `chore:` `style:` `test:` `refactor:` | No bump |

---

## License

MIT — see [LICENSE](LICENSE) for details.
