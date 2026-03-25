# 🤖 legacy-to-agentic-ready

**A toolkit you drop onto any existing repository to generate all scaffolding files that make it understandable and operable by AI agents — without hallucinations, without invented paths, without breaking existing code.**

> **Supports:** Claude · OpenAI · Gemini · Any LLM

---

## Why This Exists

AI coding agents (Copilot, Claude Code, Cursor, Aider, etc.) work **dramatically better** when a repository contains structured context files that describe:

- What the repo does and how it's organized
- Where key files live and what they contain
- What tools, APIs, and conventions are available
- How to build, test, and deploy

Without these files, agents hallucinate paths, invent APIs, and produce code that doesn't compile. **This toolkit fixes that.**

---

## What It Generates

When you run the transformer on your repository, it produces:

| File | Purpose | Platform |
|------|---------|----------|
| `AGENTS.md` | Agent instruction file | GitHub Copilot / OpenAI |
| `CLAUDE.md` | Agent instruction file | Claude Code / Anthropic |
| `system_prompt.md` | Universal system prompt | Any LLM |
| `agent-context.json` | Machine-readable repo map | All platforms |
| `mcp.json` | MCP server configuration | Claude / MCP-compatible |
| `tool.*.template.*` | Tool scaffolds (Python, TS, Java, Go) | All platforms |

---

## Requirements

- **Python 3.9+**
- **pip** (or your preferred package manager)
- **(Optional)** Anthropic, OpenAI, or Google API key for LLM-enhanced generation

```bash
# Required
python --version  # Should be 3.9 or higher

# Optional — install for LLM-enhanced generation
pip install anthropic>=0.40.0

# Set API keys (optional)
export ANTHROPIC_API_KEY="sk-ant-..."   # For Claude
export OPENAI_API_KEY="sk-..."          # For OpenAI
export GOOGLE_API_KEY="..."             # For Gemini
```

---

## Quick Start

### 1. Clone this toolkit

```bash
git clone https://github.com/vb-nattamai/legacy-to-agentic-ready.git
cd legacy-to-agentic-ready
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
legacy-to-agentic-ready/
├── README.md                          # This file
├── LICENSE                            # MIT License
├── .github/
│   └── agents/
│       └── repo-to-agentic.agent.md   # GitHub Copilot agent definition
├── .claude/
│   └── agents/
│       └── repo-to-agentic.agent.md   # Claude Code agent definition
├── prompts/
│   └── repo-to-agentic-universal.md   # Universal LLM prompt
├── templates/
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
    └── run_transformer.py             # Main transformer script
```

---

## Usage Modes

### Mode 1: Full Automation (Recommended)

```bash
python scripts/run_transformer.py --target /path/to/repo
```

Scans the repo and generates all applicable files.

### Mode 2: Selective Generation

```bash
# Only generate AGENTS.md and CLAUDE.md
python scripts/run_transformer.py --target /path/to/repo --only agents

# Only generate tool templates
python scripts/run_transformer.py --target /path/to/repo --only tools

# Only generate the context map
python scripts/run_transformer.py --target /path/to/repo --only context
```

### Mode 3: Dry Run

```bash
python scripts/run_transformer.py --target /path/to/repo --dry-run
```

Shows what would be generated without writing any files.

### Mode 4: Use as an AI Agent

Copy `.github/agents/repo-to-agentic.agent.md` or `.claude/agents/repo-to-agentic.agent.md` into your repo and let your AI agent run the transformation interactively.

---

## Usage Examples

### Example 1: Java/Maven Project (bowling-kata)

**Before:** A classic Java kata with just `pom.xml`, `README.md`, and source code.

```bash
cd ~/projects/bowling-kata
python ~/legacy-to-agentic-ready/scripts/run_transformer.py --target .
```

**Output:**
```
╔══════════════════════════════════════════════╗
║   🤖 Repo-to-Agentic Transformer v1.0.0     ║
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
python ~/legacy-to-agentic-ready/scripts/run_transformer.py --target /path/to/fastapi-app --only agents
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
python ~/legacy-to-agentic-ready/scripts/run_transformer.py --target /path/to/myrepo --dry-run
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
python ~/legacy-to-agentic-ready/scripts/run_transformer.py --target /path/to/nextjs-app
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
