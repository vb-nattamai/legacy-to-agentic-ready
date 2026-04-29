---
name: post-test
trigger: After running the test command
---

## Purpose

After `pytest` completes, this hook captures the test outcome and updates session state so the agent can decide whether to proceed with further changes or halt and surface failures.

## Actions

1. Record the exit code and summary output from `pytest` into `agent-context.json` under the session state block, following the contract defined in `memory/schema.md`.
2. If `pytest` exited with a non-zero code, mark the session as blocked and surface the failure to the agent before any subsequent tool calls proceed.

## Context loaded

- `agent-context.json`: Current session state is loaded to update the test result field and any blocking conditions.
- `memory/schema.md`: Consulted to confirm the correct field names and structure for writing test outcome state.

## Skipped when

- `AGENT_SKIP_HOOKS=true` environment variable is set.
- The test command (`pytest`) was not the command that triggered the current lifecycle event (i.e., this hook was reached via a non-test invocation).
- The agent is operating in a read-only or dry-run mode where state writes to `agent-context.json` are explicitly disabled.