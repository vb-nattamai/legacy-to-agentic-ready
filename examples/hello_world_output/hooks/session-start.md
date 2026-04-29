---
name: session-start
trigger: At the start of every Claude Code session
---

## Purpose

Load persisted project state and session contract at the beginning of each Claude Code session to ensure the agent operates with accurate, up-to-date context for this Flask/Python repository.

## Actions

1. Load `agent-context.json` to retrieve current project state, including any in-progress work, known pitfalls, and static configuration (build command: `pip install -r requirements.txt`, test command: `pytest`).
2. Read `memory/schema.md` to confirm the session state contract and understand the expected structure of any data written to or read from memory during this session.

## Context loaded

- **agent-context.json**: Current agent state including static project metadata (primary language: Python, framework: Flask, build system: pip), any dynamic state from prior sessions, and known pitfalls (e.g., application source files are not present in this repository — this is an example output directory showing AgentReady-generated artifacts only; no `requirements.txt` or `setup.py` is visible in the file tree so dependency information must be inferred from documentation).
- **memory/schema.md**: The session state contract defining valid memory fields, types, and constraints the agent must honour when reading or writing session state.

## Skipped when

- `AGENT_SKIP_HOOKS=true` environment variable is set.
- `agent-context.json` does not exist at the expected path (hook cannot load state that is not present).
- `memory/schema.md` does not exist (session state contract is unavailable; agent should flag this condition rather than proceeding silently).