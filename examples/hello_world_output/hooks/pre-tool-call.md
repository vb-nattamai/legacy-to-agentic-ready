---
name: pre-tool-call
trigger: Before any tool call that writes files
---

## Purpose

Guard file write operations by validating target paths against restricted write paths and loading current session state before any file is modified in this Flask/Python repository.

## Actions

1. Load current agent state from `agent-context.json` and verify session contract against `memory/schema.md` before proceeding with any write operation.
2. Check the target write path against restricted write paths — restricted_write_paths is empty in the current analysis input; confirm actual restricted paths by reviewing and updating `agent-context.json` static.restricted_write_paths after inspecting your repository, as no restricted paths were determinable from source.

## Context loaded

- `agent-context.json`: Current agent state, session metadata, and static repository configuration including `static.restricted_write_paths`.
- `memory/schema.md`: Session state contract defining required fields and structure that must remain valid across writes.

## Skipped when

- `AGENT_SKIP_HOOKS=true` environment variable is set.
- The tool call is a read-only operation (no file modification is performed).
- The target path has already been validated within the same session turn and no session state has changed since last validation.