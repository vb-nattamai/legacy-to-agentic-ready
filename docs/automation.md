# Automation Guide: GitHub & Gitea Workflows

This guide shows how to integrate AgentReady (`agent-ready`) into your CI/CD pipelines and issue trackers using GitHub Actions and Gitea Actions.

## Quick Start

### Option 1: Auto-trigger on Issues (Easiest)

Copy this file to your repo:

**Filename:** `.github/workflows/agentic-ready.yml`

```yaml
name: Agentic Ready
on:
  issues:
    types: [opened, labeled]
jobs:
  transform:
    if: |
      contains(github.event.issue.title, '[agentic-ready]') ||
      contains(github.event.issue.labels.*.name, 'agentic-ready')
    uses: vb-nattamai/agent-ready/.github/workflows/reusable-transformer.yml@main
    secrets: inherit
```

**To trigger:**
1. Open an issue in your repo with title `[agentic-ready] Transform this repo`
2. OR add the `agentic-ready` label to any issue
3. The workflow runs automatically, generates all files, and opens a PR

### Option 2: Call from Your Existing Pipeline

Add this step to any GitHub Actions workflow in your repo:

```yaml
- name: Make repo agentic-ready
  uses: vb-nattamai/agent-ready/.github/workflows/reusable-transformer.yml@main
  with:
    target_branch: main
    only: ''  # or 'agents', 'tools', 'context', 'memory'
    force: false
  secrets:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
    GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
```

**Run on schedule:**
```yaml
on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly Monday at midnight
```

### Option 3: Run on Deploy (One-off Setup)

```yaml
# In your .github/workflows/deploy.yml
- name: Setup agents on first deploy
  if: github.event_name == 'deployment' && github.payload.deployment.environment == 'production'
  uses: vb-nattamai/agent-ready/.github/workflows/reusable-transformer.yml@main
  secrets: inherit
```

---

## Workflow Inputs & Outputs

### `reusable-transformer.yml` Inputs

| Input | Type | Default | Description |
|-------|------|---------|-------------|
| `target_branch` | string | `main` | PR base branch |
| `only` | string | `` | Limit files: `agents`, `tools`, `context`, `memory`, or empty for all |
| `force` | boolean | `false` | Overwrite existing files |

### Environment Variables (Optional)

Set these as GitHub Secrets for LLM-enhanced features:

```bash
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
```

If not set, the transformer uses **static analysis only** (no external API calls).

---

## What Gets Generated

The workflow creates these files in your repo:

```
your-repo/
├── CLAUDE.md                  # Claude Code context
├── AGENTS.md                  # Agent contract
├── agent-context.json         # Machine-readable repo map
├── agents/
│   ├── system_prompt.md       # Universal system prompt
│   ├── openai_agent.py        # OpenAI Agents SDK entry
│   ├── gemini_agent.yaml      # Google ADK config
│   └── gemini_agent.py        # Google ADK Python
├── mcp.json                   # MCP server config
├── memory/
│   └── schema.md              # Memory schema
├── tools/                     # Language-specific tool scaffolds
│   ├── python_tools.py
│   ├── typescript_tools.ts
│   └── ...
└── AGENTIC_READINESS.md      # Audit & next steps
```

---

## GitHub Issue Trigger Workflow

### Sequence Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ User opens issue: [agentic-ready] Transform this repo       │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
         ┌─────────────────────────────────────┐
         │ GitHub Actions: issue-trigger.yml   │
         │ (triggered on issue open/labeled)   │
         └──────────────┬──────────────────────┘
                        │
        ┌───────────────┴───────────────┐
        │                               │
        ▼                               ▼
  Checkout repo                  Checkout toolkit
  (.agentic-toolkit/)            from GitHub
        │                               │
        └───────────────┬───────────────┘
                        │
                        ▼
              Set up Python 3.11
              Install dependencies
                        │
                        ▼
    run_transformer.py --target .
    ├─ Detect language, framework
    ├─ Detect build system
    ├─ Generate context files
    └─ Create tool scaffolds
                        │
                        ▼
         ┌──────────────────────────┐
         │ Files generated? (git diff)
         └──┬─────────────────────┬──┘
            │ YES                 │ NO
            ▼                     ▼
      Create branch         Exit 0
      agentic-ready/init    "Already up to date"
      Commit + push
            │
            ▼
    Create Pull Request
    ├─ Title: 🤖 Add agentic-ready scaffolding
    ├─ Body: from PR_TEMPLATE.md
    ├─ Label: agentic-ready
    └─ Link stored
            │
            ▼
    Comment on issue:
    ├─ Link to PR
    ├─ List of generated files
    └─ Instructions to review
            │
            ▼
    Add labels:
    ├─ agentic-ready-complete (success)
    └─ agentic-ready-failed (if error)
```

---

## Manual Installation to Another Repo

Use the **`install-to-repo.yml`** workflow to add agentic-ready to any other GitHub repo.

### Steps:

1. Go to your AgentReady (`agent-ready`) repo
2. Click **Actions** → **Install Agentic Ready to Repo**
3. Click **Run workflow**
4. Fill in:
   - **target_repo:** `myorg/my-app`
   - **target_branch:** `main`
5. Click **Run workflow**

This creates `.github/workflows/agentic-ready.yml` in the target repo automatically.

**Required secret:** `INSTALL_TOKEN` — a GitHub PAT with `repo` and `workflow` scopes.

---

## Gitea Integration (Self-Hosted)

Gitea Actions uses the same YAML syntax as GitHub Actions but with Gitea-specific actions and APIs.

### Gitea Issue Trigger (Same as GitHub)

**Filename:** `.gitea/workflows/agentic-ready.yml` in your Gitea instance

```yaml
name: Agentic Ready (Gitea)
on:
  issues:
    types: [opened, labeled]
jobs:
  transform:
    if: |
      contains(github.event.issue.title, '[agentic-ready]') ||
      contains(github.event.issue.labels.*.name, 'agentic-ready')
    uses: your-gitea-instance.com/vb-nattamai/agent-ready/.gitea/workflows/reusable-transformer.yml@main
    secrets: inherit
```

### Gitea Pipeline Trigger

```yaml
# In your .gitea/workflows/deploy.yml
- name: Make repo agentic-ready
  uses: your-gitea-instance.com/vb-nattamai/agent-ready/.gitea/workflows/reusable-transformer.yml@main
  with:
    target_branch: main
  secrets:
    GITEA_TOKEN: ${{ secrets.GITEA_TOKEN }}
```

#### Gitea Specifics:

- Actions live in `.gitea/workflows/` instead of `.github/workflows/`
- Use `gitea.com/actions/checkout` instead of `actions/checkout`
- PR creation uses Gitea REST API (not `gh` CLI)
- Issue comments use Gitea API with `curl`
- Secret: `GITEA_TOKEN` — personal access token with `api` scope

---

## Configuration Examples

### Weekly Refresh (Any Repo)

Add to your repo:

```yaml
# .github/workflows/weekly-agentic-update.yml
name: Weekly Agentic Update
on:
  schedule:
    - cron: '0 0 * * 0'  # Sundays at midnight UTC
jobs:
  update:
    uses: vb-nattamai/agent-ready/.github/workflows/reusable-transformer.yml@main
    with:
      target_branch: main
      force: false
    secrets:
      ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

### Partial Generation (Tools Only)

```yaml
- name: Generate tools only
  uses: vb-nattamai/agent-ready/.github/workflows/reusable-transformer.yml@main
  with:
    only: tools
  secrets: inherit
```

### Force Overwrite

```yaml
- name: Regenerate all files
  uses: vb-nattamai/agent-ready/.github/workflows/reusable-transformer.yml@main
  with:
    force: true
  secrets: inherit
```

---

## Troubleshooting

### PR Already Exists

If you run the workflow twice, it creates `agentic-ready/update` branch on the second run to avoid conflicts.

### LLM Features Not Available

If `ANTHROPIC_API_KEY` (or equivalent) is not set, the transformer automatically falls back to **static analysis mode** — no errors, just fewer details in generated prompts.

### Workflow Not Triggering in Target Repo

- Ensure `.github/workflows/agentic-ready.yml` exists in the target repo
- Check that the issue title contains `[agentic-ready]` exactly
- Verify the `agentic-ready` label exists in the target repo
- Check Actions are enabled: **Settings** → **Actions** → **Allow all actions**

### Gitea Token Errors

- Create a Gitea personal access token: **Settings** → **API Tokens**
- Grant `api` scope
- Add as `GITEA_TOKEN` secret in Gitea Actions secrets

---

## FAQ

**Q: Can I customize the generated files?**  
A: Yes! Before merging the PR, edit the generated files. Replace `{{PLACEHOLDER}}` values with your actual domain concepts, API endpoints, etc.

**Q: What if I already have agent scaffolding?**  
A: Use `--force` flag to regenerate. Existing files are backed up or skipped depending on your setup.

**Q: Can I run this in my CI/CD without GitHub Actions?**  
A: Yes! The core tool is `scripts/run_transformer.py`. Run it locally:
```bash
python scripts/run_transformer.py --target /path/to/repo
```

**Q: Does this modify my existing code?**  
A: No. The transformer only creates new files in `agents/`, `tools/`, `memory/`, etc. No existing files are touched.

**Q: Can I call this from non-GitHub platforms?**  
A: Yes! Use `scripts/run_transformer.py` directly. The GitLab CI / Jenkins / CircleCI integration is a wrapper around the Python script.

---

## Next Steps

1. **Copy the issue-trigger workflow** to your repo
2. **Open an issue** with title `[agentic-ready] Transform this repo`
3. **Review the PR** generated by the workflow
4. **Merge** to activate agentic context
5. **Use** with Claude Code, OpenAI Agents SDK, or any LLM
