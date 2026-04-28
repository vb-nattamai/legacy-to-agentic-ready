---
name: session-start
trigger: At the start of every Claude Code session
---

## Purpose

Restore prior session state and surface key repository quirks for this single-file Flask app so the agent begins every session with accurate context.

## Actions

1. Load `agent-context.json` from the repository root to restore the current task, last known state, and any in-progress work from the previous session.
2. Read `memory/schema.md` to confirm the expected shape of session state, then validate that `agent-context.json` conforms to that contract before proceeding.
3. Remind the agent of the critical project pitfalls: `app.py` is a single-file module (not a package), the Flask app object and module both share the name `app` (watch for import collisions in `tests/`), `GREETING` is resolved once at module load time so environment changes require a reload, and `requirements-dev.txt` must include `pytest` and `pytest-cov` before running `pytest -q --cov=app`.
4. Verify the Python environment is ready by confirming dependencies are installed (`pip install -r requirements.txt -r requirements-dev.txt`) and that the entry point `app.py` exists at the repo root.

## Context loaded

- **agent-context.json** — current task description, progress markers, open decisions, and any deferred work from the prior session.
- **memory/schema.md** — the session state contract defining required and optional fields in `agent-context.json`.
- Repository pitfalls list (single-file module layout, dual `app` name, `GREETING` load-time binding, dev dependency requirements).

## Skipped when

- `AGENT_SKIP_HOOKS=true` environment variable is set.
- `agent-context.json` does not exist (first-ever session with no prior state to restore; the agent should create it instead).
- The session is explicitly flagged as a clean-slate reset by the user at startup.