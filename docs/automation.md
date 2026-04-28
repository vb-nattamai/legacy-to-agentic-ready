# Automation Guide: GitHub Actions Workflows

This guide explains how to integrate AgentReady into your repositories using GitHub Actions.

---

## Quick Start

The fastest path is the one-click installer:

1. Go to [agent-ready Actions → Install AgentReady to Target Repository](https://github.com/vb-nattamai/agent-ready/actions/workflows/install-to-target-repo.yml)
2. Click **Run workflow**
3. Enter your target repo (`owner/repo`), choose your LLM provider, and optionally enable eval
4. Done — the installer pushes the trigger workflow, opens an issue, and the transformation starts automatically

---

## How the Trigger Works

The workflow installed in your repo listens for a single event:

```yaml
on:
  issues:
    types: [labeled]
```

**Why `labeled` only (not `opened`)?**

Using `labeled` as the single trigger prevents duplicate runs. When the installer creates an issue and adds the label in one step, GitHub fires both `opened` and `labeled` — causing two simultaneous runs and two PRs. With `labeled` only:

- **Automated path** — installer creates issue → adds label → fires once
- **Manual retrigger** — add the `agentic-ready` label to any existing issue → fires once

---

## Installed Workflow (`agentic-ready.yml`)

This file is pushed into your target repo by the installer:

```yaml
name: Agentic Ready
on:
  issues:
    types: [labeled]

jobs:
  check-permission:
    if: contains(github.event.issue.labels.*.name, 'agentic-ready')
    runs-on: ubuntu-latest
    permissions:
      issues: read
    outputs:
      allowed: ${{ steps.check.outputs.allowed }}
    steps:
      - name: Check actor is a repo collaborator
        id: check
        uses: actions/github-script@v7
        with:
          script: |
            const { data: perm } = await github.rest.repos.getCollaboratorPermissionLevel({
              owner: context.repo.owner,
              repo: context.repo.repo,
              username: context.actor
            });
            const allowed = ['admin', 'write', 'maintain'];
            core.setOutput('allowed', allowed.includes(perm.permission) ? 'true' : 'false');

  transform:
    needs: check-permission
    if: needs.check-permission.outputs.allowed == 'true'
    uses: vb-nattamai/agent-ready/.github/workflows/reusable-transformer.yml@main
    with:
      target_repo: ${{ github.repository }}
      target_branch: ${{ github.event.repository.default_branch }}
      issue_number: ${{ github.event.issue.number }}
      provider: 'anthropic'  # or: openai, google, groq, mistral, together, ollama
      eval: true             # measures whether context files actually help
      fail_level: '0.0'      # set e.g. '0.8' to gate on eval pass rate
      force: false
      only: ''
    secrets: inherit
```

`secrets: inherit` means the reusable workflow receives secrets from the **caller repository**.
For installed `agentic-ready.yml` triggers, that caller is your target repo.

---

## What Happens When It Runs

```
Label added to issue
    │
    ├─ 1. Checks actor has write access to the repo
    ├─ 2. Calls reusable-transformer.yml in agent-ready
    ├─ 3. Analysis model reads your codebase (~60s)
    │      — reads source files, config, CI, README
    │      — extracts domain concepts, entry points, env vars, pitfalls
    ├─ 4. Generation model writes all scaffolding files from scratch
    │      — AGENTS.md, CLAUDE.md, .cursorrules, agent-context.json
    │      — system_prompt.md, mcp.json, memory/schema.md
    │      — skills/ (run-tests, build, lint, etc.), hooks/ (session-start, pre-tool-call, etc.)
    ├─ 5. Evaluation model measures whether context files improve AI responses
    │      — 19 questions, with and without context
    │      — saves AGENTIC_EVAL.md with per-question results
    ├─ 6. Opens a PR: "🤖 Add agentic-ready scaffolding"
    ├─ 7. Comments on the issue with the PR link
    └─ 8. Closes the issue ✅
```

---

## Generated Files

| File | Purpose |
|------|---------|
| `agent-context.json` | Machine-readable repo map — static section (edit once) + dynamic section (auto-refreshed) |
| `AGENTS.md` | Operating contract for GitHub Copilot and OpenAI agents |
| `CLAUDE.md` | Auto-loaded by Claude Code at every session start |
| `.cursorrules` | Auto-loaded by Cursor at project open |
| `system_prompt.md` | Paste as the `system` parameter in any LLM interface |
| `mcp.json` | MCP server configuration |
| `memory/schema.md` | Agent working memory schema |
| `skills/` | Slash-command skill definitions grounded in repo commands (run-tests, build, lint, etc.) |
| `hooks/` | Claude Code lifecycle hooks for session continuity (session-start, pre-tool-call, etc.) |
| `AGENTIC_EVAL.md` | Eval report — baseline vs with-context scores per category |

---

## Model Strategy

AgentReady uses a tiered model strategy within each provider — analysis uses the most capable model, evaluation uses the cheapest.

| Provider | Analysis | Generation | Evaluation | Secret |
|---|---|---|---|---|
| `anthropic` | claude-opus-4-6 | claude-sonnet-4-6 | claude-haiku-4-5 | `ANTHROPIC_API_KEY` |
| `openai` | gpt-5.4 | gpt-5.4-mini | gpt-5.4-nano | `OPENAI_API_KEY` |
| `google` | gemini-2.5-pro | gemini-2.5-pro | gemini-2.5-flash-lite | `GOOGLE_API_KEY` |
| `groq` | llama-3.3-70b | llama-3.3-70b | llama-3.1-8b-instant | `GROQ_API_KEY` |
| `mistral` | mistral-large | mistral-large | mistral-small | `MISTRAL_API_KEY` |
| `together` | Qwen3.5-397B | Llama-3.3-70B | Qwen3.5-9B | `TOGETHER_API_KEY` |
| `ollama` | llama3.3 | llama3.3 | llama3.2 | _(local — no key)_ |

---

## Manual Retrigger

To retrigger a transformation on any repo that already has the workflow installed:

1. Go to your repo → Issues → New Issue
2. Give it any title
3. Add the `agentic-ready` label
4. The workflow fires automatically

Or re-label an existing closed issue — same effect.

---

## Required Secrets

For installed issue-trigger runs (`agentic-ready.yml`), add secrets in the **target repo** under Settings → Secrets and variables → Actions:

| Secret | Provider | Description |
|--------|----------|-------------|
| `ANTHROPIC_API_KEY` | `anthropic` (default) | Claude Opus + Sonnet + Haiku |
| `OPENAI_API_KEY` | `openai` | GPT-5.4 / mini / nano |
| `GOOGLE_API_KEY` | `google` | Gemini 2.5 Pro / Flash |
| `GROQ_API_KEY` | `groq` | Llama 3.3 70B / 3.1 8B |
| `MISTRAL_API_KEY` | `mistral` | Mistral Large / Small |
| `TOGETHER_API_KEY` | `together` | Qwen3.5 / Llama-3.3 |
| _(none)_ | `ollama` | Runs locally — no secret needed |
| `INSTALL_TOKEN` | all | PAT with `repo` + `workflow` scopes |

### Secret Location by Run Mode

| Run mode | Where secrets must exist |
|---|---|
| Installed trigger in target repo (`agentic-ready.yml` via issues/labels) | Target repo secrets (passed to reusable workflow via `secrets: inherit`) |
| Manual run in `vb-nattamai/agent-ready` (`reusable-transformer.yml` via `workflow_dispatch`) | `agent-ready` repo secrets |

### Trust Boundary

- trigger is permission-gated (`admin`, `maintain`, or `write`)
- execution can push branches and open PRs in the target repo
- treat provider keys and `INSTALL_TOKEN` as privileged credentials
- prefer least-privilege repo-scoped tokens and rotate regularly

---

## Context Drift Detection

The installer also pushes a weekly drift detector:

```
.github/workflows/context-drift-detector.yml
```

Runs every Monday at 09:00 UTC. Detects if `agent-context.json` has structurally drifted from the codebase (ignoring `last_scanned` timestamp changes) and opens a PR if drift is found.

---

## Manual Refresh

To refresh context files at any time without opening an issue:

```bash
agent-ready --target /path/to/repo --only context --force
```

Or trigger via the Actions tab in `agent-ready`:

```
agent-ready → Actions → Agentic Ready Transformer → Run workflow
```

With inputs:
- `target_repo`: `owner/repo`
- `only`: `context`
- `force`: ✅

For this manual `agent-ready` run mode, secrets must be configured in the `agent-ready` repository.

---

## Eval as a CI Gate

To fail a PR if context quality drops below a threshold, set `fail_level` in your `agentic-ready.yml`:

```yaml
      fail_level: '0.8'  # fail if fewer than 80% of eval questions pass
```

This exits with code 1 if the pass rate is below the threshold, blocking the PR from being created.

---

## Gitea

Replace `.github/` with `.gitea/` — identical YAML syntax. The reusable workflow reference becomes:

```yaml
uses: your-gitea.com/vb-nattamai/agent-ready/.gitea/workflows/reusable-transformer.yml@main
```

PR creation uses the Gitea REST API via `curl` instead of the `gh` CLI.

---

## Troubleshooting

**Two PRs are created** — your `agentic-ready.yml` uses both `opened` and `labeled` triggers. Change to `labeled` only.

**Workflow not triggering** — confirm the `agentic-ready` label exists in the repo and Actions are enabled under Settings → Actions.

**403 on push** — `INSTALL_TOKEN` has expired or lacks `repo` + `workflow` scopes. Use the validate-token-permissions workflow in `agent-ready` to test before re-running.

**529 API overloaded** — the transformer has retry logic (up to 5 attempts with increasing waits). If all retries fail, wait 10–15 minutes and retrigger.
