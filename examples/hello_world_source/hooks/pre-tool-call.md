---
name: pre-tool-call
trigger: Before any tool call that writes files
---

## Purpose

Guard against writes to restricted paths and load current session state before any file-writing tool call in this Flask/pytest repository.

## Actions

1. Load `agent-context.json` and `memory/schema.md` to retrieve current session state and verify the session state contract before proceeding with any write.
2. Block any tool call that attempts to write to `cost_report.json`, which is a restricted write path for this repository — abort the tool call and surface an explicit error if this path is the target.

## Context loaded

- `agent-context.json`: current agent session state (task context, progress, flags).
- `memory/schema.md`: session state contract defining required fields and structure that must remain consistent across writes.

## Skipped when

- `AGENT_SKIP_HOOKS=true` environment variable is set.
- The tool call is read-only (e.g., read, search, list) and does not write or modify any file.
- The target file path is neither `cost_report.json` nor any path covered by the session state contract in `memory/schema.md`.