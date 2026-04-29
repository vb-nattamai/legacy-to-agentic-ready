---
name: post-test
trigger: After running the test command
---

## Purpose

After `pytest` completes, this hook captures the test outcome and updates session state so the agent knows whether it is safe to proceed with commits, refactors, or further code changes in this Flask repository.

## Actions

1. Record the exit code and summary output from `pytest` into `agent-context.json` under the session state fields defined in `memory/schema.md`, marking the last-known test status as passing or failing.
2. If the test run failed, flag the session as blocked and surface the known pitfall most relevant to the failure — specifically checking for cross-test global state pollution caused by the module-level `_greetings` list persisting across test cases, which is identified as a likely source of test-isolation failures in this repository.
3. If the test run passed, confirm that `cost_report.json` was not modified during the test run, since it is a restricted write path that must not be altered by test execution.

## Context loaded

- Current session state from `agent-context.json` (last test status, blocking flags, session metadata).
- Session state contract from `memory/schema.md` (field names and types required when writing test results back to context).
- The test command in use is `pytest` (source: `pyproject.toml [tool.pytest]`, confidence: high).

## Skipped when

- `AGENT_SKIP_HOOKS=true` environment variable is set.
- The test command was not `pytest` (e.g., the agent ran a targeted script directly rather than the project test suite).
- `agent-context.json` is not present or is not writable, preventing safe state persistence.