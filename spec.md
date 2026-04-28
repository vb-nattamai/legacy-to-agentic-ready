# AgentReady — New Artifacts Specification

## Context

AgentReady currently generates seven artifacts per transformation:
- `AGENTS.md`, `CLAUDE.md`, `system_prompt.md`, `agent-context.json`, `mcp.json`, `memory/schema.md`, `AGENTIC_EVAL.md`

This spec defines three new artifacts to add to the generation pipeline.

Priority order: skills/ first, then .cursorrules, then hooks/

---

## Artifact 1: `skills/` Directory

### What it is

A directory of slash-command skill definitions that tell Claude Code what actions it can perform in this specific repository. These are invocable workflows grounded in the repo's actual capabilities, not generic templates.

### Why it matters

`CLAUDE.md` tells the agent what the repo is. Skills tell the agent what it can do. Without skills, users build these manually over weeks. AgentReady should generate them on day one from repo analysis.

### Generation logic

Analyse the repo and generate one `.md` file per detected capability. Each skill file is a self-contained instruction set for a specific action.

Capability detection rules:

| Detected signal | Skill to generate |
|---|---|
| Test runner in `agent-context.json` (`pytest`, `mvn test`, `npm test`, etc.) | `skills/run-tests.md` |
| Build command detected | `skills/build.md` |
| Linter detected (`ruff`, `eslint`, `checkstyle`, etc.) | `skills/lint.md` |
| Docker / docker-compose present | `skills/start-local.md` |
| Migration framework detected (Flyway, Alembic, Liquibase) | `skills/run-migrations.md` |
| CI config present (`.github/workflows/`) | `skills/run-ci.md` |
| OpenAPI spec present | `skills/generate-api-docs.md` |
| Package manager detected (pip, npm, gradle, maven, cargo) | `skills/add-dependency.md` |

Minimum skills to always generate (even if commands are unknown):
- `skills/run-tests.md`
- `skills/build.md`

### File format

Each skill file must follow this exact structure:

```markdown
---
name: <skill-name>
description: <one sentence describing what this skill does>
---

## When to use this skill

<One sentence describing the trigger condition. Example: "Use this skill when asked to run the test suite.">

## Steps

1. <First step with exact command from agent-context.json>
2. <Second step>
3. <Validation step — how to confirm success>

## Expected output

<What a successful run looks like. Be specific.>

## Common failures

- **<Failure condition>**: <How to recover>
- **<Failure condition>**: <How to recover>

## Notes

<Any project-specific caveats detected from repo analysis. If none, omit this section.>
```

### Example output — `skills/run-tests.md` for a Python/pytest repo

```markdown
---
name: run-tests
description: Run the full test suite using pytest with project-configured settings.
---

## When to use this skill

Use this skill when asked to run tests, verify a change, or check test coverage.

## Steps

1. Ensure the virtual environment is active and dependencies are installed: `pip install -e ".[dev]"`
2. Run the test suite: `pytest`
3. Check the exit code — 0 means all tests passed.

## Expected output

```
============================= test session starts ==============================
collected N items
...
============================== N passed in Xs ==============================
```

## Common failures

- **ModuleNotFoundError**: Dependencies not installed. Run `pip install -e ".[dev]"` first.
- **Collection error**: Check `pyproject.toml` for `testpaths` configuration.
```

### Integration points

- Skills are generated in Stage 2 (Generation) alongside other artifacts.
- The analysis model must extract exact commands from the repo before skill generation.
- Commands must come from `agent-context.json` dynamic section, not be invented.
- If a command cannot be determined from analysis, the step must say: "Command not determinable from source — check your project's documentation."
- Skills directory must be included in `CLAUDE.md` under a "Available Skills" section listing each skill file and its purpose.

---

## Artifact 2: `.cursorrules`

### What it is

A Cursor-specific context file placed at the repo root. Cursor reads this file automatically when the repo is opened, equivalent to what `CLAUDE.md` does for Claude Code.

### Why it matters

Cursor is one of the most widely used AI coding tools. Users who clone an AgentReady-transformed repo and open it in Cursor currently find no context file. `.cursorrules` closes this gap.

### Generation logic

Generate `.cursorrules` from the same analysis output used to generate `CLAUDE.md`. The content is similar but formatted to Cursor's conventions.

Structure:

```
# <repo_name>

## Project overview
<Two sentence description of what the repo does, derived from analysis.>

## Language and framework
- Primary language: <from agent-context.json>
- Framework: <from agent-context.json>
- Build system: <from agent-context.json>

## Critical commands
- Install: <exact command>
- Build: <exact command>
- Test: <exact command>
- Run locally: <exact command or "Not determinable from source">

## Code conventions
<Conventions detected from repo analysis — naming, file structure, patterns.>

## Files and directories
- Entry point: <from agent-context.json static section>
- Tests: <detected test directory>
- Config: <detected config files>

## Do not modify
<Restricted write paths from agent-context.json static section.>

## Domain concepts
<Domain concepts from agent-context.json static section, if populated.>
```

### Constraints

- Must not invent commands. Use only what is in `agent-context.json`.
- If `static` section is empty (first run, not yet filled in), generate with placeholder comments noting what to fill in.
- Must be idempotent — regenerating must produce the same file given the same `agent-context.json`.

---

## Artifact 3: `hooks/` Directory

### What it is

A directory of Claude Code hook definitions that maintain agent state and context across sessions. Hooks fire at specific points in the Claude Code lifecycle.

### Why it matters

Without hooks, every Claude Code session starts cold. The agent has no memory of what changed in the last session, what decisions were made, or what the current state of the codebase is. Hooks provide session continuity grounded in the specific repo.

### Generation logic

Generate hooks based on what the repo contains. Not all hooks are appropriate for all repos.

Hook types to generate:

| Hook | When it fires | What it does | Generate when |
|---|---|---|---|
| `hooks/session-start.md` | At the start of every Claude Code session | Loads current git status, last modified files, open PRs if GitHub configured | Always |
| `hooks/pre-tool-call.md` | Before any tool call that writes files | Checks the target path against `restricted_write_paths` in `agent-context.json` | Always |
| `hooks/post-test.md` | After running the test command | Summarises pass/fail and logs to `memory/` | When test runner detected |
| `hooks/pre-commit.md` | Before a git commit | Runs linter if configured, reminds agent of commit message convention | When linter detected |

### File format

Each hook file must follow this structure:

```markdown
---
name: <hook-name>
trigger: <when this hook fires>
---

## Purpose

<One sentence describing what this hook does and why it exists for this repo.>

## Actions

1. <Specific action grounded in this repo's configuration>
2. <Second action>

## Context loaded

<What information this hook makes available to the agent.>

## Skipped when

<Conditions under which this hook should not execute.>
```

### Example output — `hooks/session-start.md`

```markdown
---
name: session-start
trigger: At the start of every Claude Code session
---

## Purpose

Load current repository state so the agent begins each session with accurate context rather than relying on potentially stale information from CLAUDE.md.

## Actions

1. Run `git status` and summarise unstaged and staged changes.
2. Run `git log --oneline -5` and note the last five commits.
3. Check `memory/` directory for any notes from the previous session.
4. Confirm the test command is available: `pytest --version`.

## Context loaded

- Current branch and any uncommitted changes
- Recent commit history
- Any agent memory from previous sessions
- Test runner availability

## Skipped when

- Running in CI (no interactive session)
- `AGENT_SKIP_HOOKS=true` environment variable is set
```

---

## Updated Generated Artifacts Table

After implementing all three, the README artifacts table becomes:

| File | Purpose |
|---|---|
| `AGENTS.md` | Operating contract for GitHub Copilot and OpenAI agents |
| `CLAUDE.md` | Automatically loaded by Claude Code at session start |
| `.cursorrules` | Automatically loaded by Cursor at project open |
| `system_prompt.md` | Universal system prompt compatible with any LLM interface |
| `agent-context.json` | Machine-readable repository map with static and dynamic sections |
| `mcp.json` | MCP server configuration for Claude and MCP-compatible clients |
| `memory/schema.md` | Agent working memory and state contract |
| `skills/` | Slash-command skill definitions for repo-specific agent actions |
| `hooks/` | Session continuity hooks for Claude Code |
| `AGENTIC_EVAL.md` | Evaluation report showing baseline and with-context scores per category |

---

## Implementation Notes for Claude Code

### Where to add generation calls

All three artifacts are generated in Stage 2 of the pipeline, alongside the existing generation calls. They receive the same analysis output as input.

The generation order within Stage 2:

1. `agent-context.json` (existing — must run first, others depend on it)
2. `AGENTS.md` (existing)
3. `CLAUDE.md` (existing — must run before skills, which reference it)
4. `.cursorrules` (new — derived from same input as CLAUDE.md)
5. `system_prompt.md` (existing)
6. `mcp.json` (existing)
7. `memory/schema.md` (existing)
8. `skills/` (new — depends on agent-context.json for commands)
9. `hooks/` (new — depends on agent-context.json for restricted paths and test command)

### Idempotency requirement

All three new artifacts must follow the existing idempotency contract: safe to run multiple times, existing files updated not duplicated, static section of `agent-context.json` never overwritten.

### Evaluation coverage

The 19-question evaluation framework must be extended to cover the new artifacts. Add at least:

- One question per skill file: "What is the exact command to run tests in this project?" — the skill file must provide a better answer than the baseline.
- One question covering `.cursorrules`: "What would you tell a developer opening this project in an AI coding tool for the first time?"
- One question covering hooks: "What should an AI agent check at the start of a session before making any changes?"

### Failure mode

If a command cannot be determined from source for a skill step, the step must explicitly say so. The existing adversarial failure pattern — confidently inventing answers — must not be repeated in skill files or hooks.
