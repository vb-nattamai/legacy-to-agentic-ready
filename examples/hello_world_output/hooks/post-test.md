---
name: post-test
trigger: After running the test command
---

## Purpose

After `pytest -q --cov=app` completes, this hook captures test results and coverage data and writes them to session state so the agent can make informed decisions about code quality and next steps.

## Actions

1. Parse the exit code and stdout/stderr output from `pytest -q --cov=app` to determine pass/fail status, number of tests passed/failed/errored, and the `app` module coverage percentage reported by pytest-cov.
2. Load `agent-context.json`, update the `last_test_run` field with the timestamp, result summary (pass/fail counts, coverage percentage for `app`), and any failure messages, then write the updated context back to `agent-context.json`.

## Context loaded

- **agent-context.json**: Current session state is read before updating and written back after; the `last_test_run` field is populated with test outcome, coverage percentage for `app`, and a list of any failing test names.
- **memory/schema.md**: Consulted to ensure the `last_test_run` field and its subfields conform to the session state contract before writing.

## Skipped when

- `AGENT_SKIP_HOOKS=true` environment variable is set.
- The test command did not actually execute (e.g., it was interrupted before producing any output or exit code).
- `agent-context.json` is missing or unreadable and cannot be created, preventing safe state persistence.