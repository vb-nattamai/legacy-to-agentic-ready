
# AgentReady

[![Version](https://img.shields.io/github/v/release/vb-nattamai/agent-ready)](https://github.com/vb-nattamai/agent-ready/releases)
[![License](https://img.shields.io/github/license/vb-nattamai/agent-ready)](LICENSE)

**This repo is superseded by [vb-nattamai/agent-ready](https://github.com/vb-nattamai/agent-ready)**

---

## Quick Start

### 1. Install via pip (recommended)

```bash
pip install git+https://github.com/vb-nattamai/agent-ready.git
```

### 2. Run the transformer against your target repo

```bash
# Basic usage (static analysis only)
agent-ready --target /path/to/your/repo

# With LLM enhancement (if API key is set)
agent-ready --target /path/to/your/repo --provider anthropic

# Preview without writing files
agent-ready --target /path/to/your/repo --dry-run
```

---

### Alternate: Clone and run manually (advanced)

```bash
git clone https://github.com/vb-nattamai/agent-ready.git
cd agent-ready
python scripts/run_transformer.py --target /path/to/your/repo
```

## Quick Start

### 1. Clone this toolkit

```bash
git clone https://github.com/vb-nattamai/agent-ready.git
cd agent-ready
```

### 2. Run the transformer against your target repo

```bash
# Basic usage (static analysis only)
python scripts/run_transformer.py --target /path/to/your/repo

# With LLM enhancement (if API key is set)
python scripts/run_transformer.py --target /path/to/your/repo --provider anthropic

# Preview without writing files
python scripts/run_transformer.py --target /path/to/your/repo --dry-run
```

### 3. Review and commit the generated files

The transformer will:
1. **Scan** your repository structure, languages, and frameworks
2. **Generate** platform-specific agent instruction files
3. **Create** a machine-readable context map (`agent-context.json`)
4. **Scaffold** tool templates matching your repo's languages
5. **Output** all files into your target repo (no existing files are modified)

```bash
# Review changes
git status

# Commit
git add -A
git commit -m "feat: Add AI-agent-ready scaffolding"

# Push
git push origin main
```

---

## Repository Structure

```
agent-ready/
├── README.md                          # This file
├── LICENSE                            # MIT License
├── VERSION                            # Current version string (e.g. 1.1.0)
├── CHANGELOG.md                       # Release history (auto-updated by release.yml)
├── .github/
│   ├── agents/
│   │   └── agent-ready.agent.md        # GitHub Copilot agent definition
│   └── workflows/
│       ├── reusable-transformer.yml   # Core transformer — called by other workflows
│       ├── install-to-repo.yml        # One-click install into any target repo
│       ├── context-refresh.yml        # Weekly scheduled context drift detection
│       ├── test-dry-run.yml           # Manual dry-run preview (no files written)
│       └── release.yml               # Semantic versioning & GitHub Releases on push
├── .claude/
│   └── agents/
│       └── agent-ready.agent.md        # Claude Code agent definition
├── docs/
│   └── automation.md                  # Gitea-specific setup notes
├── prompts/
│   └── agent-ready-universal.md        # Universal LLM prompt
│   ├── install-workflow.yml           # Installed into target repos: issue trigger (Path A)
│   ├── context-refresh-workflow.yml   # Installed into target repos: weekly drift detection
│   ├── issue-template-agentic-ready.yml # Installed into target repos: pre-filled issue form
│   ├── agent-context.template.json    # Repo context map template
│   ├── AGENTS.template.md             # GitHub/OpenAI agent instructions
│   ├── CLAUDE.template.md             # Claude agent instructions
│   ├── system_prompt.template.md      # Universal system prompt
│   ├── mcp.template.json              # MCP server config template
│   ├── tool.python.template.py        # Python tool scaffold
│   ├── tool.typescript.template.ts    # TypeScript tool scaffold
│   ├── tool.java.template.java        # Java tool scaffold
│   └── tool.go.template.go            # Go tool scaffold
└── scripts/
    ├── run_transformer.py             # Main transformer script (~850 lines)
    └── generate_changelog.py          # Conventional-commit changelog generator
```

---

## Workflows

This repo ships six GitHub Actions workflows. Three live **in this repo** (automation tooling), and one is a **template** users copy into their target repos.

### `reusable-transformer.yml` — Core transformer (called, not triggered directly)

The shared engine. Called by `install-to-repo.yml` and the trigger workflow installed in target repos.

**Inputs:**
| Input | Default | Purpose |
|---|---|---|
| `target_branch` | `main` | Branch the PR is opened against |
| `only` | _(all)_ | Limit generation: `agents`, `tools`, `context`, or `memory` |
| `force` | `false` | Overwrite existing generated files |
| `issue_number` | _(none)_ | Issue to close after PR is opened |

**What it does:**
1. Checks out the target repo and clones `agent-ready` as `.agentic-toolkit`
2. Runs `scripts/run_transformer.py --target .`
3. Commits all generated files to a new `agentic-ready/...` branch
4. Opens a PR titled "🤖 Add agentic-ready scaffolding"
5. If `issue_number` is set: comments on the issue with the PR link, then closes it

---

### `install-to-repo.yml` — One-click install into any repo

Triggered manually from the **Actions tab** in this repo. Pushes the issue-trigger workflow into any GitHub repo you own, so users don't have to copy files manually.

**Inputs:**
| Input | Required | Purpose |
|---|---|---|
| `target_repo` | ✅ | Target repo in `owner/repo` format |
| `target_branch` | no | Branch to commit to (default: `main`) |

**What it does:**
1. Validates the `owner/repo` format
2. Clones the target repo using `INSTALL_TOKEN` (needs `repo` + `workflow` scopes)
3. Copies `templates/install-workflow.yml` → `.github/workflows/agentic-ready.yml`
4. Copies `templates/context-refresh-workflow.yml` → `.github/workflows/context-refresh.yml`
5. Copies `templates/issue-template-agentic-ready.yml` → `.github/ISSUE_TEMPLATE/agentic-ready.yml`
6. Commits and pushes directly to the target branch

**Requires:** `INSTALL_TOKEN` secret set in this repo (PAT with `repo` + `workflow` scopes on the target org).

After running, open an issue in the target repo titled `[agentic-ready] Transform this repo` to trigger the transformation.

---

### `context-refresh.yml` — Reusable drift detector

This workflow serves two purposes:

**1. In this repo (agent-ready itself):** Runs on schedule (Monday 09:00 UTC) and via manual dispatch to keep agent-ready's own `agent-context.json` fresh. Useful when testing the workflow itself.

**2. In target repos:** Invoked via `workflow_call` from `templates/context-refresh-workflow.yml`, which `install-to-repo.yml` pushes into target repos. This is the primary purpose — every transformed repo gets weekly drift detection automatically.

**What it does:**
1. Runs `run_transformer.py --only context --force --quiet` against the calling repo
2. Checks `git diff agent-context.json`
3. If **no drift**: prints "✅ up to date" and exits cleanly
4. If **drift detected**: opens a PR with just the updated `agent-context.json` for human review

---

### `test-dry-run.yml` — Preview against any target repo

Triggered manually from the **Actions tab**. Runs the transformer in read-only mode against any repo — nothing is committed, nothing is overwritten. Pass `owner/repo` to preview a target repo; leaving it as `.` just runs a smoke test against agent-ready itself.

**Inputs:**
| Input | Default | Purpose |
|---|---|---|
| `target_repo` | `.` _(smoke test of agent-ready)_ | Set to `owner/repo` to preview a target before triggering real transformation |
| `verify` | `false` | Run LLM verification after dry-run (requires `ANTHROPIC_API_KEY` secret) |

**What it does:**
1. Runs `run_transformer.py --dry-run --verbose`
2. Prints every file that *would* be created/updated, with the predicted readiness score
3. Optionally verifies the generated context is correct using Claude Haiku
4. Prints next-step instructions in the summary

**Typical usage:** before opening a `[agentic-ready]` issue in a target repo, run this pointed at that repo to confirm what will be generated with zero side effects.

---

### `release.yml` — Semantic versioning on every push to `main`

Runs automatically on every push to `main`. Parses commit messages to decide whether to bump the version.

**Version bump rules:**
| Commit prefix | Bump |
|---|---|
| `feat:` | minor (e.g. 1.1.0 → 1.2.0) |
| `fix:` | patch (e.g. 1.1.0 → 1.1.1) |
| `BREAKING CHANGE:` | major (e.g. 1.1.0 → 2.0.0) |
| `docs:`, `chore:`, `style:`, `test:`, `refactor:` | no bump |

**What it does (when a bump is needed):**
1. Updates `VERSION` file and version string in `scripts/run_transformer.py`
2. Generates a changelog entry from commits since the last tag (via `scripts/generate_changelog.py`)
3. Prepends the entry to `CHANGELOG.md`
4. Commits as `chore: bump version to X.Y.Z [skip ci]` (the `[skip ci]` prevents a loop)
5. Creates a git tag `vX.Y.Z` and a GitHub Release

**Requires:** No secrets — uses the default `GITHUB_TOKEN` with `contents: write` permission.

---

### Templates installed into target repos

These files are not workflows in this repo — they are pushed into target repos by `install-to-repo.yml` (or copied manually):

**`templates/install-workflow.yml`** → `.github/workflows/agentic-ready.yml` in target repo
Listens for issues titled `[agentic-ready]` and calls `reusable-transformer.yml` via `workflow_call`. This is the main trigger (Path A).

**`templates/context-refresh-workflow.yml`** → `.github/workflows/context-refresh.yml` in target repo
Runs every Monday and calls `context-refresh.yml` via `workflow_call`. Keeps `agent-context.json` fresh after the initial transformation without any manual action.

**`templates/issue-template-agentic-ready.yml`** → `.github/ISSUE_TEMPLATE/agentic-ready.yml` in target repo
A GitHub issue form with a pre-filled title (`[agentic-ready] Transform this repo`), a scope dropdown, a domain hints textarea, and a checklist. Ensures the trigger title is always correct and reminds users to open the issue **in their own repo, not in `agent-ready`**.

---

## Usage Modes

### Mode 1: Full Automation (Recommended)

```bash
python scripts/run_transformer.py --target /path/to/repo
```

Scans the repo and generates all applicable files, prints 100-point readiness score.

> **No LLM required.** The transformer is pure static analysis — it reads your files, detects languages, parses build configs, and generates templates without any API calls. Zero cost, works fully offline. An LLM (Claude Haiku) is only invoked if you explicitly pass `--verify`.

### Mode 2: Selective Generation

```bash
# Only generate AGENTS.md and CLAUDE.md
python scripts/run_transformer.py --target /path/to/repo --only agents

# Only generate tool templates
python scripts/run_transformer.py --target /path/to/repo --only tools

# Only generate the context map
python scripts/run_transformer.py --target /path/to/repo --only context

# Only generate memory schema
python scripts/run_transformer.py --target /path/to/repo --only memory
```

### Mode 3: Dry Run (Preview Without Writing)

```bash
python scripts/run_transformer.py --target /path/to/repo --dry-run
```

Shows what would be generated without writing any files. Perfect for testing!

### Mode 4: Optional LLM Verification

```bash
# Verify generated context with Claude Haiku (optional — requires API key)
python scripts/run_transformer.py --target /path/to/repo --verify
```

Asks Claude Haiku to cross-check that the generated `agent-context.json` is accurate:
- Does `entry_point` actually exist on disk?
- Is `test_command` executable?
- Does `primary_language` match the actual codebase?

Exit code 0 = context is valid. Use as a CI gate.

**Requires:** `ANTHROPIC_API_KEY` environment variable. The base transformer never calls any LLM — this step is entirely optional.

### Mode 5: Keep Context Fresh (Automatic)

```bash
# Install pre-commit hook for automatic dynamic section refresh
python scripts/run_transformer.py --target /path/to/repo --install-hooks

# Specify where the toolkit lives (for hook to find it)
git -C /path/to/repo config agentic.toolkit-path /path/to/agent-ready
```

After this, whenever `.py`, `.ts`, `.js`, `.java`, `.go` files change:
- Pre-commit hook runs automatically
- Refreshes `agent-context.json` dynamic section only
- Static section (manual edits) is never touched

### Mode 6: Quiet Output (CI-Friendly)

```bash
# Suppress banner, only show file list
python scripts/run_transformer.py --target /path/to/repo --quiet
```

Useful in CI pipelines to reduce noise.

### Mode 7: Use as an AI Agent

Copy `.github/agents/agentic-readiness-transformer.md` into your repo and let your AI agent run the transformation interactively. The agent definition includes:
- 5-phase architecture (Audit, Core, Platform-Specific, Readiness, Validation)
- Multi-language tool definitions
- Security constraints and validation checklist

---

## Usage Examples

### Example 1: Java/Maven Project (bowling-kata)

**Before:** A classic Java kata with just `pom.xml`, `README.md`, and source code.

```bash
cd ~/projects/bowling-kata
python ~/agent-ready/scripts/run_transformer.py --target .
```

**Output:**
```
╔══════════════════════════════════════════════╗
║   🤖 AgentReady Transformer v1.1.1           ║
╚══════════════════════════════════════════════╝

🔍 Analyzing repository: /path/to/bowling-kata
  📁 Found 5 files
  🌐 Languages: Java
  🔧 Build system: maven

  ✅ Created: agent-context.json
  ✅ Created: AGENTS.md
  ✅ Created: CLAUDE.md
  ✅ Created: system_prompt.md
  ✅ Created: mcp.json
  ✅ Created: tools/ExampleTool.java

──────────────────────────────────────────────
✅ Transformation Complete
──────────────────────────────────────────────
  Project:    bowling-kata
  Languages:  Java
  Frameworks: None detected
  Build:      maven

  Generated Files:
    ✓ agent-context.json
    ✓ AGENTS.md
    ✓ CLAUDE.md
    ✓ system_prompt.md
    ✓ mcp.json
    ✓ tools/ExampleTool.java

  No existing files were modified.
```

**What was generated:**

1. **AGENTS.md** — Copilot/OpenAI agent instructions:
   ```markdown
   # AGENTS.md — bowling-kata
   ## Project Overview
   **bowling-kata** — Uncle Bob's classic kata...
   
   - **Primary Languages:** Java
   - **Build System:** maven
   
   ## Commands
   ```
   mvn install              # Install dependencies
   mvn package              # Build
   mvn test                 # Test
   mvn exec:java            # Run
   ```
   ```

2. **CLAUDE.md** — Claude Code instructions with DO's and DON'Ts:
   ```markdown
   # CLAUDE.md — bowling-kata
   ## Critical Commands
   ```
   mvn install              # Install dependencies
   mvn package              # Build
   mvn test                 # Test
   ```
   
   ## Rules — ALWAYS Follow
   1. Always run `mvn test` after changes
   2. Always run `mvn checkstyle:check` before committing
   3. Use PascalCase for all new files
   ...
   ```

3. **agent-context.json** — Machine-readable metadata:
   ```json
   {
     "project_name": "bowling-kata",
     "primary_languages": ["Java"],
     "build_system": "maven",
     "commands": {
       "install": "mvn install",
       "build": "mvn package",
       "test": "mvn test"
     },
     "conventions": {
       "naming": "PascalCase",
       "structure": "single-package"
     }
   }
   ```

4. **system_prompt.md** — Universal LLM prompt with full context
5. **mcp.json** — MCP server configuration for Claude
6. **tools/ExampleTool.java** — Java tool template scaffold

**After pushing to GitHub:**
```bash
git add -A
git commit -m "feat: Add AI-agent-ready scaffolding"
git push origin main
```

Now when you use Claude Code, GitHub Copilot, or any AI agent on this repo, they'll have:
- ✅ Exact build commands that work
- ✅ Correct file paths (no hallucinations)
- ✅ Code conventions to follow
- ✅ Known pitfalls to avoid
- ✅ Testing strategies

### Example 2: Python Project (selective generation)

```bash
# Only generate agent instructions, not tool templates
python ~/agent-ready/scripts/run_transformer.py --target /path/to/fastapi-app --only agents
```

Output:
```
✅ Transformation Complete
──────────────────────────────────────────────
  Project:    fastapi-app
  Languages:  Python
  Frameworks: FastAPI
  Build:      pip

  Generated Files:
    ✓ AGENTS.md
    ✓ CLAUDE.md
    ✓ system_prompt.md
```

### Example 3: Dry-run (preview without writing)

```bash
python ~/agent-ready/scripts/run_transformer.py --target /path/to/myrepo --dry-run
```

Output:
```
[DRY RUN] Would create: AGENTS.md
[DRY RUN] Would create: CLAUDE.md
[DRY RUN] Would create: agent-context.json
[DRY RUN] Would create: system_prompt.md
[DRY RUN] Would create: mcp.json
[DRY RUN] Would create: tools/example_tool.py
```

### Example 4: Node.js/TypeScript Project

```bash
python ~/agent-ready/scripts/run_transformer.py --target /path/to/nextjs-app
```

**Detected:**
- Languages: TypeScript, JavaScript
- Frameworks: Next.js, React
- Build: npm
- Scripts: build, dev, test (from package.json)

**Generated:**
```
✅ Transformation Complete
──────────────────────────────────────────────
  Project:    nextjs-app
  Languages:  TypeScript, JavaScript
  Frameworks: Next.js, React
  Build:      npm

  Generated Files:
    ✓ AGENTS.md          (npm run build, npm test, npm run dev)
    ✓ CLAUDE.md          (strict rules for React patterns)
    ✓ system_prompt.md   (TypeScript/React conventions)
    ✓ agent-context.json
    ✓ mcp.json
    ✓ tools/example_tool.ts
```

### After Generation: Using with AI Agents

Once generated, you can use the files in three ways:

#### 1. **GitHub Copilot / OpenAI**
- Attach `AGENTS.md` to your conversation
- Start with: "Using this context, help me build a new feature"

#### 2. **Claude Code / Anthropic**
- Copy `CLAUDE.md` into your Claude Chat context
- Claude will follow the rules automatically

#### 3. **Any LLM** (ChatGPT, Gemini, Llama, etc.)
- Use the `system_prompt.md` as your system prompt
- Full context with exact commands and conventions

---

## 🎯 CLI Reference

Quick lookup for all transformer commands:

```bash
# Basic transformation
python scripts/run_transformer.py --target /path/to/repo

# Preview changes (no files written)
python scripts/run_transformer.py --target /path/to/repo --dry-run

# Verify context with Claude Haiku
python scripts/run_transformer.py --target /path/to/repo --verify

# Install pre-commit hooks for automatic dynamic refresh
python scripts/run_transformer.py --target /path/to/repo --install-hooks

# Only generate agents (no tools, context, memory)
python scripts/run_transformer.py --target /path/to/repo --only agents

# Only generate tools (no agents, context, memory)
python scripts/run_transformer.py --target /path/to/repo --only tools

# Suppress output (quiet mode for CI)
python scripts/run_transformer.py --target /path/to/repo --quiet

# Force overwrite existing files
python scripts/run_transformer.py --target /path/to/repo --force

# Verbose output (detailed logging)
python scripts/run_transformer.py --target /path/to/repo --verbose

# Help and available options
python scripts/run_transformer.py --help
```

**Environment variables:**
```bash
# Optional: for LLM-enhanced verification
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."
export GOOGLE_API_KEY="..."

# Optional: custom toolkit path for pre-commit hooks
git config agentic.toolkit-path /path/to/agent-ready
```

---

## 🤖 Using the Transformer as an AI Agent

The transformer itself is **agentic-ready**! Use it with Claude, OpenAI, or any LLM:

```bash
# Copy the agent definition to your repo
cp .github/agents/agentic-readiness-transformer.md /path/to/target-repo/.github/agents/

# Open in Claude Code
# Claude will read the agent definition and understand how to run transformations
```

**Agent capabilities:**
- 📊 **Audit phase:** Analyze repo structure, language, frameworks, entry points
- 🔧 **Core files:** Generate universal agent context files (AGENTS.md, CLAUDE.md, system_prompt.md)
- 🌐 **Platform files:** Create platform-specific agents (OpenAI, Gemini, VS Code Copilot, Claude)
- ✅ **Validation:** Run security checks, constraint verification, cross-platform parity checks
- 📈 **Scoring:** Calculate 100-point readiness and recommend improvements

The agent definition includes:
- **Phase 1:** Full repo audit checklist (identity, architecture, observability)
- **Phase 2:** Universal core files (agent-context.json, AGENTS.md, tools, memory schema)
- **Phase 3:** Platform-specific agent files (OpenAI SDK, Google ADK, VS Code, universal)
- **Phase 4:** AGENTIC_READINESS.md with score and recommendations
- **Phase 5:** Validation checklist (no invented paths, stack consistency, idempotency)

---

## 🚀 Using GitHub Issues & Actions to Transform a Legacy Repo

Three paths depending on how much control you want. All produce the same result: a PR in your repo with all agentic scaffolding files.

> **TL;DR — Just want it to work?**  
> Run **"Install Agentic Ready to Repo"** from the [Actions tab in agent-ready](https://github.com/vb-nattamai/agent-ready/actions/workflows/install-to-repo.yml), enter your repo name → it pushes everything. Then open an issue **in your own repo** using the pre-filled form at `Issues → New Issue → 🤖 AgentReady — Transform this repo`.

> ⚠️ **Do not open issues in `vb-nattamai/agent-ready`** — issues there do nothing. The trigger workflow must be installed in **your** repo.

**Which path is right for you?**

| | Path A | Path B | Path C |
|---|---|---|---|
| **Best for** | Solo devs, quick start | Teams, risk-averse orgs | Platform / many repos |
| **Setup** | Copy 1 file, once | Copy 1 file, once | Run 1 workflow from here |
| **Trigger** | Open an issue | Run from Actions tab | Automated |
| **Preview before writing?** | No | Yes (dry-run) | No |
| **Writes files to repo?** | Yes (via PR) | No (preview only) | Yes (via PR, after Path A) |

```
Your legacy repo
      │
      ├─ Path A: Open an issue            → Workflow triggers → PR opened automatically
      ├─ Path B: Run workflow manually    → Dry-run first, then trigger real transformation
      └─ Path C: Use install workflow     → One-time setup, then use Path A forever
```

---

### Path A — Issue Trigger (Recommended, Zero Setup)

**Step 1: Copy this file into your legacy repo**

Create `.github/workflows/agentic-ready.yml` in your repo:

```bash
# Copy directly from agent-ready
curl -o .github/workflows/agentic-ready.yml \
  https://raw.githubusercontent.com/vb-nattamai/agent-ready/main/templates/install-workflow.yml

# Also grab the issue form template (recommended)
mkdir -p .github/ISSUE_TEMPLATE
curl -o .github/ISSUE_TEMPLATE/agentic-ready.yml \
  https://raw.githubusercontent.com/vb-nattamai/agent-ready/main/templates/issue-template-agentic-ready.yml

git add .github/ && git commit -m "feat: add AgentReady trigger workflow" && git push
```

> **Or use Path C** (Install workflow) to do all of the above automatically.

**Step 2: Open an issue to trigger the transformation**

Go to **your repo** → Issues → New Issue.

If you installed the issue template, you'll see **"🤖 AgentReady — Transform this repo"** in the template list. Click it — the title is pre-filled and there's a checklist to guide you. Just click Submit.

If you skipped the template, create an issue with this exact title:
```
[agentic-ready] Transform this repo
```

> ⚠️ **Open in YOUR repo, not in `vb-nattamai/agent-ready`.** Issues in agent-ready do not trigger transformations.

**Step 3: What happens automatically**

```
Issue opened
    │
    ├─ 1. Checks you are a repo collaborator (blocks unauthorized runs)
    ├─ 2. Clones your repo
    ├─ 3. Runs scanner: detects language, frameworks, build system, entry point
    ├─ 4. Generates all agentic scaffolding files (see list below)
    ├─ 5. Opens a PR titled "🤖 Add agentic-ready scaffolding"
    ├─ 6. Comments on your issue with a link to the PR
    └─ 7. Closes the issue automatically ✅
```

**Step 4: Review and merge the PR**

The PR contains:

| File | Purpose |
|------|---------|
| `agent-context.json` | Machine-readable repo map (static + dynamic sections) |
| `AGENTS.md` | Agent contract — safe ops, forbidden ops, domain glossary |
| `CLAUDE.md` | Claude Code auto-loaded context |
| `system_prompt.md` | Universal system prompt for any LLM |
| `mcp.json` | MCP server configuration |
| `tools/<lang>Tool.*` | Tool scaffold in your repo's primary language |
| `memory/schema.md` | Agent memory/state contract |

Review each file, fill in any `<placeholder>` values, then merge.

> **Tip:** The `static` section of `agent-context.json` is for your manual edits. The `dynamic` section is automatically refreshed. Edit `static` before merging.

**Step 5: Improve the readiness score (optional but recommended)**

The first run will score around **40–50 / 100**. This is expected — the transformer generates the file structure automatically but cannot guess your domain-specific details.

To reach 80–100, open `agent-context.json` in the PR and fill in the `static` section:

```json
"static": {
  "entry_point": "src/main/java/com/example/Application.java",
  "test_command": "mvn test",
  "restricted_write_paths": ["src/main/resources/application.properties"],
  "environment_variables": ["DATABASE_URL", "API_KEY", "PORT"],
  "domain_concepts": [
    "Frame: single bowling turn (2 rolls max)",
    "Strike: all 10 pins on first roll",
    "Spare: all 10 pins across 2 rolls"
  ]
}
```

Re-run the transformer after merging to see the updated score in `AGENTIC_READINESS.md`.

---

### Path B — Dry-Run First (Recommended for Teams)

Before opening an issue, preview exactly what will be generated without writing any files.

**Step 1: Copy this file into your legacy repo**

Create `.github/workflows/agentic-ready-preview.yml`:

```yaml
name: Agentic Ready — Preview
on:
  workflow_dispatch:
    inputs:
      verify:
        description: "Verify context with Claude Haiku after generation"
        required: false
        default: "false"
        type: boolean

permissions:
  contents: read

jobs:
  preview:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Clone transformer toolkit
        run: git clone --depth 1 https://github.com/vb-nattamai/agent-ready.git /tmp/toolkit

      - name: Dry-run (no files written)
        run: |
          python /tmp/toolkit/scripts/run_transformer.py \
            --target . \
            --dry-run \
            --verbose

      - name: Verify context (optional)
        if: github.event.inputs.verify == 'true'
        run: |
          if [ -z "$ANTHROPIC_API_KEY" ]; then
            echo "⚠️  ANTHROPIC_API_KEY not set — skipping verification"
            exit 0
          fi
          python /tmp/toolkit/scripts/run_transformer.py \
            --target . \
            --dry-run \
            --verify
        continue-on-error: true
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

**Step 2: Run it from the Actions tab**

1. Go to your repo → **Actions**
2. Select **"Agentic Ready — Preview"**
3. Click **Run workflow**
4. Read the output — it shows every file that would be created and the 100-point readiness score
5. If satisfied, proceed to Path A to trigger the real transformation

---

### Path C — One-Click Install into Any Repo

If you maintain many repos, use the install workflow to push the trigger file automatically.

**From this (agent-ready) repo:**

1. Go to **[Actions → "Install Agentic Ready to Repo"](https://github.com/vb-nattamai/agent-ready/actions/workflows/install-to-repo.yml)**
2. Click **Run workflow**
3. Enter your target repo: `myorg/my-legacy-api`
4. Click **Run workflow**

This pushes three files into `myorg/my-legacy-api`:
- `.github/workflows/agentic-ready.yml` — issue trigger
- `.github/workflows/context-refresh.yml` — weekly drift detection
- `.github/ISSUE_TEMPLATE/agentic-ready.yml` — pre-filled issue form

Then go to **`myorg/my-legacy-api` Issues → New Issue → "🤖 AgentReady — Transform this repo"** and click Submit.

> **Requires:** A `INSTALL_TOKEN` secret in this repo with `repo` scope on the target org, or set `GITHUB_TOKEN` if the target is in the same org.

---

### What gets generated — full walk-through

Here is what the resulting PR looks like for a Java/Maven legacy repo:

**Detected:**
```
📁 Found 8 files
🌐 Languages: Java
🔧 Build system: maven
📦 Entry point: src/main/java/com/example/App.java
```

**Generated files:**

`agent-context.json` — static section you edit once, dynamic section auto-refreshed:
```json
{
  "static": {
    "repo_name": "my-api",
    "primary_language": "Java",
    "frameworks": ["Spring Boot"],
    "entry_point": "src/main/java/com/example/App.java",
    "restricted_write_paths": ["src/main/resources/db/migration"]
  },
  "dynamic": {
    "last_scanned": "2026-03-25T09:00:00Z",
    "module_layout": { "controllers": "src/main/java/.../controller" },
    "test_command": "mvn test",
    "build_command": "mvn package"
  }
}
```

`AGENTS.md` — defines what agents can and cannot do:
```markdown
## Safe operations
- Read any file under src/
- Call any tool defined in tools/
- Suggest code changes as diffs without applying them

## Forbidden operations
- Write to src/main/resources/db/migration
- Bypass service layer to access DB directly
- Modify public API contracts without human approval
```

`CLAUDE.md` — auto-loaded by Claude Code on every session.

`tools/ExampleTool.java` — scaffold in your repo's language, ready to implement.

**Readiness score printed in the PR:**
```
──────────────────────────────────────
  AGENTIC READINESS SCORE: 85 / 100
──────────────────────────────────────
  ✅ agent-context.json exists     +10
  ✅ CLAUDE.md exists              +10
  ✅ AGENTS.md exists              +10
  ✅ tools/ has files              +10
  ✅ Entry point exists            +10
  ✅ Test command set              +10
  ✅ CI config exists              +5
  ⚠️  OpenAPI spec missing          +0
  ⚠️  environment_variables empty   +0
  💡 Add openapi.yml and fill in
     environment_variables to reach 100
──────────────────────────────────────
```

---

### After merging the PR

Once merged, any AI agent tool pointed at your repo will automatically find and use these files:

| Tool | File it reads | How |
|------|--------------|-----|
| Claude Code | `CLAUDE.md` | Auto-loaded at session start |
| GitHub Copilot | `.github/agents/*.agent.md` | Copilot Chat dropdown |
| OpenAI Agents SDK | `agents/openai_agent.py` | `python agents/openai_agent.py` |
| Any LLM | `system_prompt.md` | Paste as `system` parameter |
| MCP clients | `mcp.json` | Loaded by MCP host |

---

### Gitea

Replace `.github/` with `.gitea/` — identical YAML syntax:

```yaml
uses: your-gitea.com/vb-nattamai/agent-ready/.gitea/workflows/reusable-transformer.yml@main
```

**See [docs/automation.md](docs/automation.md) for Gitea-specific setup including collaborator check via API.**

---


## 🏆 Agentic Readiness Score

Every run outputs a **100-point readiness score** based on:

| Criterion | Points | How to get it |
|-----------|--------|---------------|
| `agent-context.json` exists | 10 | Auto-generated |
| `CLAUDE.md` exists | 10 | Auto-generated |
| `AGENTS.md` exists | 10 | Auto-generated |
| `system_prompt.md` exists | 5 | Auto-generated |
| `tools/` has ≥1 file | 10 | Auto-generated |
| Entry point file exists | 10 | Fill `static.entry_point` in `agent-context.json` |
| Test command set | 10 | Fill `static.test_command` |
| `restricted_write_paths` populated | 10 | Fill `static.restricted_write_paths` |
| `environment_variables` populated | 10 | Fill `static.environment_variables` |
| `domain_concepts` has ≥3 entries | 5 | Fill `static.domain_concepts` |
| OpenAPI spec exists | 5 | Add `openapi.yaml` to your repo |
| CI config exists | 5 | Auto-detected |

**Why does the first run score ~40–50?**

The transformer can auto-generate the file structure but cannot read your mind — domain-specific values like `entry_point`, `test_command`, and `domain_concepts` are left as `<placeholder>` for you to fill in. This is intentional: the score gives you an actionable to-do list, not a failing grade.

**First run (typical):**
```
──────────────────────────────────────
  AGENTIC READINESS SCORE: 45 / 100
──────────────────────────────────────
  ✅ agent-context.json               +10
  ✅ CLAUDE.md                        +10
  ✅ AGENTS.md                        +10
  ⬜ system_prompt.md                  +0   ← not yet generated
  ✅ tools/ has files                 +10
  ⬜ entry_point exists                +0   ← fill in agent-context.json
  ⬜ test_command set                  +0   ← fill in agent-context.json
  ⬜ restricted_write_paths            +0   ← fill in agent-context.json
  ⬜ environment_variables             +0   ← fill in agent-context.json
  ⬜ domain_concepts ≥3               +0   ← fill in agent-context.json
  ⬜ OpenAPI spec                      +0
  ✅ CI config exists                  +5
```

**After filling in `agent-context.json` static section:**
```
──────────────────────────────────────
  AGENTIC READINESS SCORE: 95 / 100
──────────────────────────────────────
  ✅ agent-context.json               +10
  ✅ CLAUDE.md                        +10
  ✅ AGENTS.md                        +10
  ✅ system_prompt.md                  +5
  ✅ tools/ has files                 +10
  ✅ entry_point exists               +10
  ✅ test_command set                 +10
  ✅ restricted_write_paths           +10
  ✅ environment_variables            +10
  ✅ domain_concepts ≥3               +5
  ⬜ OpenAPI spec                      +0   ← optional
  ✅ CI config exists                  +5
  ─────────────────────────────────────
  💡 Add openapi.yaml to reach 100/100
──────────────────────────────────────
```

Use this score to drive adoption — set a team standard (e.g. "merge requires score ≥ 80").

---

## �🔄 Keeping context fresh

`agent-context.json` goes stale when your codebase changes. Three ways to keep it current:

**Pre-commit hook (recommended for local development)**
```bash
python scripts/run_transformer.py --target /path/to/your-repo --install-hooks
git -C /path/to/your-repo config agentic.toolkit-path /path/to/agent-ready
```
✅ Automatically refreshes the **dynamic section** of `agent-context.json` whenever source files change.

**What it does:**
- Watches for changes to `.py`, `.ts`, `.js`, `.java`, `.go` files
- On `git commit`, regenerates: `module_layout`, `domain_concepts`, `agent_capabilities`
- Never modifies the `static` section (your manual edits are safe)
- Blocks commit if verification fails (can be overridden with `--no-verify`)

**Weekly CI refresh (recommended for teams)**

If you used `install-to-repo.yml` to set up the repo, this is already installed as `.github/workflows/context-refresh.yml` in the target repo. If you set up manually, copy `templates/context-refresh-workflow.yml` into `.github/workflows/context-refresh.yml`:

```yaml
name: AgentReady — Context Refresh
on:
  schedule:
    - cron: '0 9 * * 1'   # Every Monday at 09:00 UTC
  workflow_dispatch:
jobs:
  refresh:
    permissions:
      contents: write
      pull-requests: write
    uses: vb-nattamai/agent-ready/.github/workflows/context-refresh.yml@main
    secrets: inherit
```

✅ Runs every Monday, detects drift in `agent-context.json`, opens a PR if updates needed

**Manual refresh**
```bash
python scripts/run_transformer.py --target /path/to/your-repo --only context --force
```

---

## ✅ Verify your context

After generating or updating, run the LLM verifier to confirm context is correct:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
python scripts/run_transformer.py --target /path/to/your-repo --verify
```

**Output:**
```
──────────────────────────────────────
  VERIFICATION RESULTS
──────────────────────────────────────
  entry_point:     ✅ PASS (src/main.py exists, imports correctly)
  test_command:    ✅ PASS (pytest runs successfully)
  primary_language: ✅ PASS (Python codebase confirmed)
  ─────────────────────────────────────
  Overall:         ✅ VALID — All critical fields verified
──────────────────────────────────────
```

**Exit codes:**
- `0` = context is valid and an LLM can use it safely
- `1` = context has gaps or inconsistencies

**Use as a CI gate:**
```yaml
- name: Verify agentic context
  run: |
    python scripts/run_transformer.py --target . --verify
    # Fails if verification fails; blocks merge
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

---

## Supported Languages & Frameworks

The transformer auto-detects:

- **Python** (Django, Flask, FastAPI, scripts)
- **TypeScript / JavaScript** (React, Next.js, Node.js, Express)
- **Java** (Spring Boot, Maven, Gradle)
- **Go** (standard library, Gin, Echo)
- **Rust** (Cargo-based projects)
- **C# / .NET** (ASP.NET, console apps)
- **Ruby** (Rails, gems)
- And more via generic fallback templates

---

## 🎯 Recent Improvements (v1.1.0)

This release includes 7 major enhancements:

### 1️⃣ **Security** — Collaborator Authentication
Prevent unauthorized transformations via GitHub Actions:
```yaml
- name: Check actor is a repo collaborator
  uses: github-script@v6
  with:
    script: |
      const collaborators = await github.rest.repos.listCollaborators({
        owner: context.repo.owner,
        repo: context.repo.repo,
      });
      if (!collaborators.data.some(c => c.login === context.actor)) {
        throw new Error('Only collaborators can trigger this workflow');
      }
```

### 2️⃣ **Freshness** — Pre-commit Hooks
Never let `agent-context.json` go stale:
```bash
python scripts/run_transformer.py --target /path/to/repo --install-hooks
```
Automatically refreshes the **dynamic section** on every commit (module_layout, domain_concepts, agent_capabilities). The **static section** (your manual edits) is never touched.

### 3️⃣ **Freshness** — Weekly CI Refresh
Scheduled workflow that detects drift and opens PRs. Installed automatically into target repos by `install-to-repo.yml` as `.github/workflows/context-refresh.yml`, which calls `context-refresh.yml` in agent-ready via `workflow_call`:
```yaml
on:
  schedule:
    - cron: '0 9 * * 1'  # Monday 09:00 UTC
```
See `templates/context-refresh-workflow.yml` for the template pushed into target repos.

### 4️⃣ **Quality** — Optional LLM Verification
The base transformer is **pure static analysis** — no LLM, no API key required. Optionally, validate generated context using Claude Haiku:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
python scripts/run_transformer.py --target /path/to/repo --verify
```
Checks that:
- ✅ `entry_point` file actually exists on disk
- ✅ `test_command` is executable
- ✅ `primary_language` matches the actual codebase

Exit code 0 means context is valid. Use as a CI gate.

### 5️⃣ **Structure** — Static/Dynamic JSON Split
`agent-context.json` now has two sections:

**Static section** (set once, manually editable, never overwritten)
```json
{
  "static": {
    "repo_name": "...",
    "primary_language": "...",
    "frameworks": [...],
    "entry_point": "...",
    "restricted_write_paths": [...]
  }
}
```

**Dynamic section** (auto-refreshed on every scan)
```json
{
  "dynamic": {
    "last_scanned": "...",
    "module_layout": {...},
    "domain_concepts": [...],
    "agent_capabilities": [...]
  }
}
```

This preserves your manual edits while keeping context fresh.

### 6️⃣ **Scoring** — 100-Point Readiness System
Every transformation outputs a score:

```
──────────────────────────────────────
  AGENTIC READINESS SCORE: 95 / 100
──────────────────────────────────────
  ✅ agent-context.json exists        +10
  ✅ CLAUDE.md exists                 +10
  ✅ AGENTS.md exists                 +10
  ✅ agents/system_prompt.md exists   +5
  ✅ tools/ has files                 +10
  ✅ Entry point exists               +10
  ✅ Test command set                 +10
  ✅ restricted_write_paths set       +10
  ✅ environment_variables set        +10
  ✅ domain_concepts populated        +5
  ⚠️ OpenAPI spec missing             +0
  ✅ CI config exists                 +5
  ──────────────────────────────────
  💡 To improve your score:
     - Add OpenAPI/Swagger spec for API documentation
```

Drives adoption — teams want high scores!

### 7️⃣ **Documentation** — Updated README
- "Keeping context fresh" section (3 strategies)
- "Verify your context" section with CI gate examples
- "CLI Reference" quick lookup table
- Agent definition for the transformer itself
- Agentic readiness scoring explained

---

## Philosophy

1. **Never modify existing code** — only add new files
2. **Never hallucinate** — all generated content is derived from actual repo analysis
3. **Platform-agnostic** — generates files for every major AI agent platform
4. **Idempotent** — safe to run multiple times; existing generated files are updated, not duplicated
5. **Transparent** — every generated file includes a header explaining what it is and why it exists

---

## Contributing

1. Fork this repository
2. Create a feature branch (`git checkout -b feature/my-improvement`)
3. Commit your changes (`git commit -am 'Add new template for X'`)
4. Push to the branch (`git push origin feature/my-improvement`)
5. Open a Pull Request

---

## License

MIT — see [LICENSE](LICENSE) for details.
