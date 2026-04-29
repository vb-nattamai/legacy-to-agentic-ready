---
name: pre-tool-call
trigger: Before any tool call that writes files
---

## Purpose

Guard file-write operations in this Flask/pytest repository by validating the target path against known state and surfacing project-specific pitfalls before any file is modified.

## Actions

1. Load `agent-context.json` to read current session state (active branch, in-progress task, and any write constraints recorded at runtime) and load `memory/schema.md` to confirm the session state contract is satisfied before proceeding.
2. Verify the target write path is not restricted. `verified_facts.restricted_paths` is `not_found` for this repository — restricted write paths are not determinable from source. Until `agent-context.json` static.restricted_write_paths is populated after reviewing the repo, treat any write to `app.py` (the verified entry point) with extra caution: changes to the `app` symbol name or the `_greetings` module-level list will break Flask test-client imports and cause stale-state failures across pytest runs.
3. Before writing to `app.py` or any file under the `tests` directory, emit a warning if the change introduces a new HTTP method (POST, PUT, PATCH, DELETE) — the existing codebase uses `@app.get()` shorthand exclusively, and deviating from this pattern requires verifying that no test asserts on response headers that would be affected by new middleware.
4. Before writing any file, confirm the target does not add concurrency primitives to the `_greetings` list without a thread-safety mechanism, as the in-memory store is a plain list with no thread safety and concurrent writes under a threaded server can cause race conditions.

## Context loaded

- `agent-context.json`: current session state including task description, active file targets, and any runtime-recorded write constraints.
- `memory/schema.md`: session state contract defining required fields that must be present before a write proceeds.

## Skipped when

- `AGENT_SKIP_HOOKS=true` environment variable is set.
- The tool call is read-only (e.g., `read_file`, `list_directory`, `search`) and performs no write operation.
- The target file is a generated artifact outside the tracked source tree (e.g., a `.pyc` file or anything under `__pycache__`).