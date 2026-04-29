---
name: session-start
trigger: At the start of every Claude Code session
---

## Purpose

Load persisted session state and surface repository-specific constraints so the agent begins each session with accurate context about this Flask/pytest Python project.

## Actions

1. Read `agent-context.json` and validate it against the session state contract defined in `memory/schema.md`; surface any missing or stale fields to the agent before work begins.
2. Remind the agent of the following verified facts for this repository:
   - **Entry point:** `app.py`
   - **Run command:** `python app.py`
   - **Test command:** `pytest` *(confidence: high — from `pyproject.toml [tool.pytest]`)*
   - **Install command:** `pip install -e .` *(confidence: inferred — detected as likely: `pip install -e .` — verify before use)*
   - **Python version required:** `>=3.11`
   - **Restricted write paths:** Not determinable from source — fill in `agent-context.json` static.restricted_write_paths after reviewing your repo
3. Surface the following known pitfalls to the agent at session open:
   - The `_greetings` list is module-level state — it persists across requests within a process but resets on restart; tests that do not reset the list between runs may see stale data.
   - Flask's test client must import `app` from `app.py`; renaming that symbol breaks test discovery.
   - All endpoints are GET-only; adding POST/PUT endpoints requires careful attention since the existing pattern uses `@app.get()` shorthand.
   - No CORS or authentication is configured; adding middleware may change response headers that tests assert on.
   - The in-memory store is a plain list with no thread safety; concurrent requests under a threaded server could cause race conditions.

## Context loaded

- Current agent state loaded from `agent-context.json` (task progress, flags, prior decisions).
- Session state contract and field definitions from `memory/schema.md`.
- Verified repository commands, Python version (`>=3.11`), entry point (`app.py`), and known pitfall list as enumerated above.

## Skipped when

- `AGENT_SKIP_HOOKS=true` environment variable is set.
- `agent-context.json` does not exist on disk (first-time setup not yet completed — agent should prompt the user to initialize it before proceeding).
- `memory/schema.md` does not exist on disk (schema contract unavailable — agent should warn and proceed without schema validation).