---
name: run-tests
description: Run the full test suite with project-configured settings.
---

## When to use this skill

Use this skill whenever you need to execute the full test suite to verify correctness after making changes to the codebase.

## Steps

1. Install dependencies: `pip install -e '.[dev]' 2>/dev/null || pip install -r requirements.txt`
2. Run the test suite: `pytest`
3. Confirm success by checking that all collected tests pass with zero failures or errors reported in the final summary line.

## Expected output

A successful run produces a pytest summary line such as:

```
============================= N passed in X.XXs ==============================
```

All tests in the `tests` directory are collected and executed. No failures, errors, or unexpected warnings should appear.

## Common failures

- **Cross-test state pollution**: The `_greetings` list is module-level global state in `app.py`. Tests that add or mutate greetings without resetting state between runs will affect subsequent tests. Ensure each test isolates state (e.g., by resetting the list in a fixture's teardown).
- **Flask test client not configured**: Tests must obtain the test client via `app.test_client()`. If a test imports `app` and attempts HTTP calls against a localhost server, the server must actually be running — this is not the standard test mode. Use `app.test_client()` instead.
- **Dependency installation fails**: `pip install -e .` may fail because `pyproject.toml` declares a setuptools build backend but lacks a package directory. The install command includes an automatic fallback to `pip install -r requirements.txt`; if the editable install fails, confirm the fallback completed successfully before running tests.
- **Wrong Python version**: This project requires Python `>=3.11`. If tests fail with syntax or compatibility errors, verify your active Python version with `python --version`.