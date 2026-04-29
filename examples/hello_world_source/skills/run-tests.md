---
name: run-tests
description: Run the full test suite with project-configured settings.
---

## When to use this skill

Use this skill whenever you need to verify that all tests pass after making changes to the codebase.

## Steps

1. Install project dependencies: `pip install -e .`
2. Run the full test suite: `pytest`
3. Confirm success by reviewing the summary line printed at the end of the pytest output.

## Expected output

A successful run produces a pytest summary line such as:

```
collected N items

tests/... PASSED
...
N passed in X.XXs
```

All collected test items should show `PASSED` with no `FAILED`, `ERROR`, or `WARNING` lines related to test results.

## Common failures

- **Import error on `app.py`**: The `app` variable in `app.py` is the Flask application object; if it has been renamed, the test client instantiation in tests will fail. Restore the variable name to `app` or update test references accordingly.
- **Accumulated state across tests**: The `_greetings` list is module-level mutable state. If tests call `/greet/<name>` and share the same app instance, greetings accumulate across test functions and assertions may fail. Re-create the Flask test client per test function, or reset `_greetings` in a fixture between tests.
- **Missing dependencies**: If `pytest` or `flask` are not found, run `pip install -e .` from the repository root to install all declared dependencies from `pyproject.toml`.
- **Wrong Python version**: This project requires Python `>=3.11`. If tests fail with syntax or compatibility errors, verify the active interpreter with `python --version` and switch to a supported version.