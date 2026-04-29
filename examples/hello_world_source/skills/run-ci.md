---
name: run-ci
description: Trigger or simulate the CI pipeline.
---

## When to use this skill

Use this skill whenever you need to validate the full pipeline locally before pushing — or to reproduce a CI failure.

## Steps

1. Install dependencies: `pip install -e .`
2. Run the linter: `ruff check .`
3. Run the formatter check: `ruff format .`
4. Run the test suite: `pytest`
5. Confirm all steps exit with code 0.

## Expected output

A successful run produces:
- `ruff check .` — no output and exit code 0 (or a summary line such as `All checks passed.`)
- `ruff format .` — no output or a line confirming no files were reformatted, exit code 0
- `pytest` — a summary line such as `X passed in Xs` with no failures or errors, exit code 0

## Common failures

- **`ruff check` reports violations**: Fix the flagged lines (rules E, F, I enforced at line length 88) and re-run `ruff check .` until it exits cleanly.
- **`ruff format` reports files would be reformatted**: Run `ruff format .` without `--check` to apply formatting, then re-run the check step.
- **`pytest` fails due to accumulated greeting state**: The `_greetings` list is module-level mutable state. If tests that call `/greet/<name>` share a single app instance, greetings accumulate across test functions. Ensure each test function re-creates the Flask test client or resets `_greetings` between tests.
- **`pip install -e .` fails**: The project uses `pyproject.toml` as the authoritative dependency source (`flask>=2.3`, Python `>=3.11`). Do not edit `requirements.txt` for project dependencies — it is not the authoritative source. Verify `pyproject.toml` is well-formed and retry.
- **Wrong Python version**: This project requires Python `>=3.11`. Confirm your active interpreter with `python --version` and switch to a compliant version if needed.

## Notes

- `pip install -e '.[dev]'` will fall back silently to the base install because no `dev` extras section is defined in `pyproject.toml`. This is expected behaviour — the base install is sufficient to run CI.
- No secrets handling mechanism is configured in this repository. Establish one before adding any credentials.
- No irreversible operations are present in this codebase. State changes are ephemeral (in-memory only).