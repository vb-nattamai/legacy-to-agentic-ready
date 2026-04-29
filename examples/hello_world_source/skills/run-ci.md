---
name: run-ci
description: Trigger or simulate the CI pipeline.
---

## When to use this skill

Use this skill when you need to simulate or verify the full CI pipeline locally, including dependency installation, linting, and test execution.

## Steps

1. Install dependencies:
   ```
   pip install -e '[dev]' 2>/dev/null || pip install -r requirements.txt
   ```
2. Run the linter to check for style and import issues:
   ```
   ruff check .
   ```
3. Run the formatter check:
   ```
   ruff format .
   ```
4. Run the test suite:
   ```
   pytest
   ```
5. Confirm all steps exited with code `0`.

## Expected output

A successful run produces:
- No output or only informational messages from the install step
- `ruff check .` exits with no violations reported
- `ruff format .` exits cleanly with no files reformatted (in CI, unformatted files indicate a failure)
- `pytest` reports all tests collected from the `tests` directory passing, with a summary line such as `N passed` and exit code `0`

## Common failures

- **`pip install -e .` fails with a build backend error**: The `pyproject.toml` declares a setuptools build backend but there may be no package directory present. The build command includes a fallback: `pip install -r requirements.txt`. Confirm which path succeeded before proceeding.
- **Cross-test pollution causing unexpected failures**: The `_greetings` list is module-level global state that persists across requests within a single process. Tests that do not isolate or reset this state will interfere with each other. Ensure each test resets relevant state before asserting.
- **`ruff check .` reports violations**: Fix reported `E`, `F`, or `I` rule violations in the flagged files before re-running. Line length limit is 88 characters.
- **`pytest` cannot import the Flask app**: Ensure the install step completed successfully and that Flask `>=2.3` is available. Do not attempt to hit a live server with `httpx` against localhost unless the app is actually running; use `app.test_client()` instead.
- **Python version mismatch**: This project requires Python `>=3.11`. Verify the active interpreter with `python --version` before running any steps.

## Notes

- Do not write to `cost_report.json` during CI simulation. This path is restricted.
- `pyproject.toml` is the authoritative source for project dependencies. Do not edit `requirements.txt` to add project dependencies; add them to the `[project].dependencies` list in `pyproject.toml` instead.