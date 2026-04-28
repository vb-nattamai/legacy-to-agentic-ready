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
- [Evaluation Framework](#evaluation-framework)
- [Quick Start](#quick-start)
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
| `memory/schema.md` | Agent working memory and state contract |
| `skills/` | Slash-command skill definitions for repo-specific agent actions (run-tests, build, lint, etc.) |
| `hooks/` | Session-continuity hooks for Claude Code (session-start, pre-tool-call, post-test, pre-commit) |
| `AGENTIC_EVAL.md` | Evaluation report showing baseline and with-context scores per category |

---

## Evaluation Framework

Every transformation includes a structured evaluation that measures whether the generated context files produce a measurable improvement in agent response quality.

### Methodology

| Parameter | Value |
|---|---|
| Questions | 19 across 5 categories |
| Baseline model | claude-haiku-4-5 with no context |
| Context model | claude-opus-4-6 with all generated files |
| Judge | 3-panel majority vote (factual, semantic, safety) |
| Ground truth source | Raw source code — not the generated context files |

### Observed Results

Results across Python projects ranging from minimal single-file applications to multi-module systems:

| Category | Baseline | With Context | Improvement |
|---|---|---|---|
| **Overall** | 2.0-2.4 / 10 | 6.3-6.6 / 10 | +4.2-4.3 pts |
| Domain understanding | 0.0 / 10 | 7.8-9.0 / 10 | +7.8-9.0 pts |
| Architecture and structure | 1.8-2.2 / 10 | 6.8-7.3 / 10 | +5.0-5.1 pts |
| Build and run commands | 2.6-3.0 / 10 | 5.5-6.7 / 10 | +2.9-3.7 pts |
| Safety and restricted paths | 2.5-2.8 / 10 | 5.6-6.0 / 10 | +3.1-3.2 pts |
| Adversarial and edge cases | 2.0-2.7 / 10 | 5.3-6.1 / 10 | +2.6-4.1 pts |

The most consistent signal is domain understanding, which moves from 0 to 7.8-9.0 across all tested repositories. Without context, the model is unable to describe the system's purpose. With context, it answers correctly every time.

The adversarial category reflects a known limitation: when the correct answer is "not determinable from the available source files," the model with context sometimes produces confident but incorrect responses, treating the generated scaffolding files as authoritative project documentation. This is under active remediation.

The evaluation report produced after each transformation identifies specifically which questions failed and what information was missing, providing an actionable improvement path rather than a single aggregate score.

---

## Quick Start

The recommended path is the one-click installer available in the AgentReady Actions tab.

1. Navigate to [Actions → Install AgentReady to Target Repository](https://github.com/vb-nattamai/agent-ready/actions/workflows/install-to-target-repo.yml)
2. Click **Run workflow**
3. Enter the target repository in `owner/repo` format and select an LLM provider
4. The installer pushes a trigger workflow to the target repository, opens an issue, and applies the `agentic-ready` label
5. The transformation runs automatically and opens a pull request with all generated files

Review the pull request, fill in the `static` section of `agent-context.json` with project-specific details, and merge.

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
| `agent-ready --target /path/to/repo --eval-only` | Run evaluation against existing files only |
| `agent-ready --target /path/to/repo --review-pr 42` | Run PR review agent against PR number 42 |
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
