---
name: run-tests
description: Run the full test suite with project-configured settings.
---

## When to use this skill

Use this skill whenever you need to execute the full test suite to verify correctness after making changes to the codebase.

## Steps

1. Install dependencies: `pip install -e .` (detected as likely — verify before use; alternatively `pip install -r requirements.txt`)
2. Run the test suite from the repository root: `pytest`
3. Confirm all tests pass by reviewing the summary line printed at the end of pytest output.

## Expected output

A successful run ends with a pytest summary line such as:

```
===== N passed in X.XXs =====
```

No failures, errors, or warnings that halt execution. All test files in the `tests/` directory are collected and run.

## Common failures

- **Stale `_greetings` list state between test runs**: The `_greetings` list is module-level state in `app.py` and persists across requests within a process. If tests do not reset this list between runs, assertions may fail due to leftover entries from prior tests. Add a fixture or teardown step that clears `_greetings` before each test.
- **Import error on `app`**: Flask's test client depends on importing `app` from `app.py`. If that symbol is renamed or the file is moved, test discovery will break. Restore the `app` symbol in `app.py` to fix.
- **Wrong Python version**: This project requires Python `>=3.11`. Running under an older interpreter may cause syntax or compatibility errors. Confirm your active Python version with `python --version` and switch to a `>=3.11` interpreter if needed.
- **Missing dependencies**: If `pytest` or Flask are not installed, the test run will fail immediately with an import error. Re-run the install command to restore the environment.