---
name: post-test
trigger: After running the test command
---

## Purpose

After `pytest` completes, this hook records the test outcome and surfaces known state-isolation pitfalls specific to this repo so the agent can decide whether failures require test-client or app-level fixes.

## Actions

1. Load current session state from `agent-context.json` and validate it against the contract defined in `memory/schema.md`; update the session's last-test-result field with the `pytest` exit code and timestamp.
2. If `pytest` reported failures, surface the following repo-specific pitfall for agent review: the `_greetings` list is module-level mutable state in `app.py` — greetings accumulate across test functions unless the test client or app object is re-created per test in the `tests/` directory.

## Context loaded

- Current session state from `agent-context.json` (last-test-result, active task, prior pitfall acknowledgements).
- Session state contract from `memory/schema.md` (field definitions and required keys).
- Verified test command: `pytest` (source: `pyproject.toml [tool.pytest]`, confidence: high).
- Known domain concepts in scope: Greetings (in-memory store, module-level `_greetings` list in `app.py`) and Service Identity (root endpoint returning name and version, `app.py`).

## Skipped when

- `AGENT_SKIP_HOOKS=true` environment variable is set.
- The test command was not `pytest` (hook is bound to the verified test command for this repo and should not run for ad-hoc script invocations).
- `agent-context.json` is absent or unreadable (hook cannot record outcome without a valid session state file).