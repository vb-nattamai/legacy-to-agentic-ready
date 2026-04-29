---
name: session-start
trigger: At the start of every Claude Code session
---

## Purpose

Load persisted session state and surface project-critical facts for this Flask/pytest repository so the agent begins each session with accurate context rather than rediscovering it.

## Actions

1. Read `agent-context.json` and extract current session state (task, progress, flags, and any in-progress work) as defined by the contract in `memory/schema.md`.
2. Surface the following verified project facts to the agent:
   - **Entry point:** `app.py`
   - **Python version:** `>=3.11`
   - **Install command:** detected as likely: `pip install -e '.[dev]' 2>/dev/null || pip install -r requirements.txt` — verify before use
   - **Test command:** `pytest` (high confidence — source: `pyproject.toml [tool.pytest]`)
   - **Lint command:** `ruff check .` (high confidence — source: `pyproject.toml [tool.ruff]`)
   - **Format command:** `ruff format .`
   - **Dependency management:** Edit `[project].dependencies` in `pyproject.toml` — do NOT edit `requirements.txt` for project dependencies
   - **Restricted write paths:** `cost_report.json` — the agent must not write to this file
3. Remind the agent of the following known pitfalls recorded in the analysis:
   - The `_greetings` list is module-level global state; it persists across requests in a single process but resets on restart, and tests that do not isolate state will see cross-test pollution.
   - Flask's test client must be obtained via `app.test_client()`; importing `app` directly and using `httpx` against localhost requires the server to actually be running.
   - All routes use `@app.get()` shorthand (Flask 2.x+); using `@app.route()` with `methods=['GET']` is equivalent but mixing styles can confuse linters.
   - There is no CORS, authentication, or input validation — adding middleware must be tested carefully to avoid breaking existing endpoint contracts.
   - `pyproject.toml` declares a setuptools build backend but there is no `setup.cfg` or package directory, so `pip install -e .` may fail without the `requirements.txt` fallback.

## Context loaded

- **`agent-context.json`:** Current session state including task description, progress markers, and any flags set by previous sessions.
- **`memory/schema.md`:** The schema contract defining the structure and fields expected in `agent-context.json`, used to validate that loaded state is well-formed before the agent proceeds.

## Skipped when

- `AGENT_SKIP_HOOKS=true` environment variable is set.
- `agent-context.json` does not exist (first-time setup; agent should create it conforming to `memory/schema.md` before proceeding).