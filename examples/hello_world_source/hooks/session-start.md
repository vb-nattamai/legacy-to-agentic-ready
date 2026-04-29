---
name: session-start
trigger: At the start of every Claude Code session
---

## Purpose

Initialise the agent's working context at the start of every session by loading project state and surfacing the key facts needed to work safely in this Flask repository.

## Actions

1. Load `agent-context.json` to restore current project state, including any in-progress work, known pitfalls, and prior decisions recorded from the previous session.
2. Check `memory/schema.md` to confirm the session state contract is satisfied before proceeding with any task.
3. Surface the following verified project facts to the agent:
   - **Entry point:** `app.py` (serves as both the Flask app module and the runnable entry point — importing it triggers route registration and `_greetings` list initialisation)
   - **Run command:** `python app.py`
   - **Install command:** `pip install -e .` (authoritative source: `pyproject.toml`; do not edit `requirements.txt` for project dependencies)
   - **Test command:** `pytest`
   - **Lint command:** `ruff check .`
   - **Format command:** `ruff format .`
   - **Python version:** `>=3.11`
   - **Dependency manager:** `pyproject.toml` — add dependencies to the `[project].dependencies` list
4. Remind the agent of the active potential pitfalls for this session:
   - The `_greetings` list is module-level mutable state; tests that call `/greet/<name>` accumulate greetings across test functions unless the test client or app is re-created per test.
   - `app.py` is both the module and the entry point; module-level import triggers side effects.
   - Data is in-memory only — not thread-safe and lost on restart.
   - `pip install -e '.[dev]'` will fail (no `dev` extras defined) and fall back to `requirements.txt`; use `pip install -e .` instead.
   - The Flask test client must be obtained from the `app` object in `app.py`; renaming that variable breaks tests.

## Context loaded

- **`agent-context.json`:** Current session state, in-progress task notes, and prior decisions.
- **`memory/schema.md`:** Session state contract defining the expected shape of `agent-context.json`.
- **Domain concepts (from source):**
  - *Greetings* — in-memory store (`_greetings` list in `app.py` line 7); intentionally simple, no database.
  - *Service Identity* — root endpoint returning service name and version (`app.py` line 10).
- **Secrets:** No secrets handling mechanism is configured in this repository. Establish one before adding any credentials.
- **Irreversible operations:** No irreversible operations are present in this codebase. State changes are ephemeral (in-memory only).
- **Restricted write paths:** Not determinable from source — fill in `agent-context.json` static.restricted_write_paths after reviewing your repo.

## Skipped when

- `AGENT_SKIP_HOOKS=true` environment variable is set.
- `agent-context.json` does not exist (first-time setup not yet completed; agent should prompt the user to initialise it before proceeding).
- `memory/schema.md` does not exist (session state contract is undefined; agent should warn the user before continuing