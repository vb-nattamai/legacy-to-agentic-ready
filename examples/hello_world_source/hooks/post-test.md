---
name: post-test
trigger: After running the test command
---

## Purpose

After `pytest` completes, this hook captures the test outcome and updates session state so the agent can decide whether to proceed with commits, flag regressions, or surface the known pitfalls relevant to any failures.

## Actions

1. Record the exit code and summary output from `pytest` into `agent-context.json` under the session state contract defined in `memory/schema.md`, marking the test run as passed or failed before any subsequent agent action proceeds.
2. If the test run failed, surface the following repo-specific pitfalls for agent review before any fix attempt:
   - The `_greetings` list is module-level state — it persists across requests within a process but resets on restart; tests that do not reset the list between runs may see stale data.
   - Flask's test client must import `app` from `app.py`; renaming that symbol breaks test discovery.
   - No CORS or authentication is configured; adding middleware may change response headers that tests assert on.
   - The in-memory store is a plain list with no thread safety; concurrent requests under a threaded server could cause race conditions.

## Context loaded

- Current session state from `agent-context.json`
- Session state contract from `memory/schema.md`
- Test command verified as: `pytest` (confidence: high, source: `pyproject.toml [tool.pytest]`)
- Python version requirement: `>=3.11` (source: `pyproject.toml requires-python`)
- Entry point: `app.py` (confidence: high, source: file tree root)

## Skipped when

- `AGENT_SKIP_HOOKS=true` environment variable is set.
- The test command was not `pytest` (i.e., a different test runner was invoked outside the verified configuration).
- `agent-context.json` is missing or unreadable, as session state cannot be reliably updated.