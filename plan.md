# Implementation Plan — New Artifacts (skills/, .cursorrules, hooks/)

## Overview

Add three new artifact types to the AgentReady generation pipeline, in priority order:
1. `skills/` — slash-command skill definitions
2. `.cursorrules` — Cursor context file
3. `hooks/` — Claude Code session-continuity hooks

---

## Step 1: Update `analyser.py` — Circular-analysis prevention

**File:** `src/agent_ready/analyser.py`

Changes:
- Add `.cursorrules` to `SKIP_AGENT_FILES` set
- Add `"skills"` and `"hooks"` to `SKIP_AGENT_DIRS` set

---

## Step 2: Add generation functions to `generator.py`

**File:** `src/agent_ready/generator.py`

### 2a. `.cursorrules` — deterministic (no LLM call)

Add `build_cursorrules(analysis)` function:
- Formats analysis data into Cursor's conventions
- Uses only data from analysis dict — never invents commands
- Falls back to `"Not determinable from source"` for missing commands
- Idempotent: same input → same output

### 2b. `skills/` — LLM-generated per skill

Add these functions:
- `detect_skills(analysis) -> list[str]` — inspects analysis fields to determine which skills to generate:
  - `test_command` present → `run-tests`
  - `build_command` present → `build`
  - linter in frameworks/tools → `lint`
  - docker/docker-compose in config_files hint or frameworks → `start-local`
  - migration framework detected → `run-migrations`
  - `has_ci` is True → `run-ci`
  - `has_openapi` is True → `generate-api-docs`
  - `build_system` (pip/npm/gradle/maven/cargo) → `add-dependency`
  - Always include `run-tests` and `build` even if commands unknown

- `generate_skill_file(model, skill_name, analysis) -> str` — single LLM call that produces a skill .md file following the exact format from the spec. The prompt instructs the model to use exact commands from analysis and say "Command not determinable from source — check your project's documentation" if unknown.

### 2c. `hooks/` — LLM-generated per hook

Add these functions:
- `detect_hooks(analysis) -> list[str]` — determines which hooks to generate:
  - Always: `session-start`, `pre-tool-call`
  - `test_command` present → `post-test`
  - Linter detected → `pre-commit`

- `generate_hook_file(model, hook_name, analysis) -> str` — single LLM call per hook following the exact format from the spec.

---

## Step 3: Add methods to `LLMGenerator` class

**File:** `src/agent_ready/generator.py` — `LLMGenerator` class

Add three private methods:
- `_cursorrules()` — calls `build_cursorrules()`, writes `.cursorrules`
- `_skills()` — calls `detect_skills()`, then for each skill calls `generate_skill_file()`, writes `skills/<name>.md`
- `_hooks()` — calls `detect_hooks()`, then for each hook calls `generate_hook_file()`, writes `hooks/<name>.md`

Update `generate_all()` to call these three methods in order:
1. (existing) `_agent_context()`
2. (existing) `_agents_md()`
3. (existing) `_claude_md()`
4. **(new)** `_cursorrules()`
5. (existing) `_system_prompt()`
6. (existing) `_mcp_json()`
7. (existing) `_memory_schema()`
8. **(new)** `_skills()`
9. **(new)** `_hooks()`
10. (existing) `_refresh_context_script()`
11. (existing) `_dependabot_yml()`
12. (existing) `_custom_questions_starter()`
13. (existing) `_openapi_stub()`
14. (existing) `_codeowners()` — also update to include skills/, hooks/, .cursorrules

---

## Step 4: Update `CLAUDE.md` generation prompt

**File:** `src/agent_ready/generator.py` — `generate_claude_md()`

Append a step 8 to the prompt asking the model to include an "## Available Skills" section that lists each skill file and its one-line purpose. This section is placed after "After Every Change".

---

## Step 5: Update `build_codeowners()` to cover new artifacts

**File:** `src/agent_ready/generator.py` — `build_codeowners()`

Add entries for `.cursorrules`, `skills/`, `hooks/` to the generated CODEOWNERS file.

---

## Step 6: Add tests

**File:** `tests/test_generator.py`

Add tests:
- `test_build_cursorrules_uses_analysis_data` — assert key fields from analysis appear in output
- `test_build_cursorrules_no_invented_commands` — when command fields are empty, output contains fallback text
- `test_detect_skills_always_includes_run_tests_and_build` — even with empty analysis
- `test_detect_skills_linter_adds_lint_skill` — analysis with ruff in frameworks → lint skill present
- `test_detect_skills_docker_adds_start_local` — analysis with docker present → start-local skill present
- `test_detect_hooks_always_includes_session_start_and_pre_tool_call`
- `test_detect_hooks_test_runner_adds_post_test`
- `test_detect_hooks_linter_adds_pre_commit`
- `test_generate_skill_file_uses_retry_wrapper` — mock `_call`, verify it's invoked with correct model/prompt containing skill name
- `test_generate_hook_file_uses_retry_wrapper` — same pattern

---

## Step 7: Verify

Run:
```bash
PYTHONPATH=src pytest -q --cov=src/agent_ready --cov-report=term-missing --cov-fail-under=50
ruff check src/agent_ready tests
ruff format --check src/agent_ready tests
```

---

## Status

- [x] Step 1 — analyser.py SKIP sets
- [x] Step 2a — build_cursorrules()
- [x] Step 2b — detect_skills() + generate_skill_file()
- [x] Step 2c — detect_hooks() + generate_hook_file()
- [x] Step 3 — LLMGenerator methods + generate_all() wiring
- [x] Step 4 — CLAUDE.md prompt update
- [x] Step 5 — CODEOWNERS update
- [x] Step 6 — Tests
- [x] Step 7 — Verify (177 tests pass, 64% coverage, ruff lint clean)
