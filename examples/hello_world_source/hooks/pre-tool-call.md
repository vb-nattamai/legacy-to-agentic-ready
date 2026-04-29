---
name: pre-tool-call
trigger: Before any tool call that writes files
---

## Purpose

Guard file writes in this Flask/pytest repository by loading current session state and verifying that no write targets a path that conflicts with known project structure before proceeding.

## Actions

1. Load `agent-context.json` to retrieve current session state (active branch, in-progress task, any session-scoped flags) and check `memory/schema.md` for the session state contract before allowing the write to proceed.
2. Confirm the target file path exists within the known repository structure (root-level `app.py`, `tests/` directory, `pyproject.toml`) and is not being written in a way that would shadow or corrupt the Flask app entry point `app.py` or the pytest configuration in `pyproject.toml`; restricted write paths: Not determinable from source — fill in `agent-context.json` static.restricted_write_paths after reviewing your repo.

## Context loaded

- Current session state from `agent-context.json` (task identity, branch, flags).
- Session state contract from `memory/schema.md` (field definitions and required keys).
- Target file path from the pending tool call, validated against known project files.

## Skipped when

- `AGENT_SKIP_HOOKS=true` environment variable is set.
- The tool call is a read-only operation (no file content is being written or modified).
- The write target is a recognised tooling artifact (`agent-context.json`, `CLAUDE.md`, `AGENTS.md`, `cost_report.json`, `AGENTIC_EVAL.md`).