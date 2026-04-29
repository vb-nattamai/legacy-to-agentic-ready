---
name: run-ci
description: Trigger or simulate the CI pipeline.
---

## When to use this skill

Use this skill when you need to simulate or verify the full CI pipeline locally before pushing changes.

## Steps

1. Install dependencies:
   ```
   pip install -e '.[dev]' 2>/dev/null || pip install -r requirements.txt
   ```
2. Run the test suite:
   ```
   pytest
   ```
3. Confirm all tests pass by reviewing the final summary line output by pytest (e.g. `X passed` with no failures or errors).

## Expected output

A successful run ends with pytest printing a summary such as:

```
========================= X passed in Y.YYs =========================
```

No `FAILED`, `ERROR`, or `WARNING` lines related to test collection or execution should appear.

## Common failures

- **Import error for `app`**: Flask's test client depends on importing `app` from `app.py`. If the symbol has been renamed or the file moved, pytest will fail to collect tests. Restore the `app` symbol in `app.py`.
- **Stale state in `_greetings` list**: The `_greetings` list is module-level state and persists across tests within the same process. If tests are not resetting this list between runs, assertions may fail due to leftover data. Ensure each test that modifies `_greetings` cleans up after itself (e.g. via a fixture that resets the list).
- **Wrong Python version**: This project requires Python `>=3.11`. If you see syntax errors or incompatible feature errors, verify your active Python version with `python --version` and switch to a compatible interpreter.
- **Missing dependencies**: If `pip install -e '.[dev]'` fails and `requirements.txt` is also absent or incomplete, the install step will error out. Verify that `requirements.txt` exists and is up to date, or that `pyproject.toml` contains the correct dependency list.