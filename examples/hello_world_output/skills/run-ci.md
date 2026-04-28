```markdown
---
name: run-ci
description: Trigger or simulate the CI pipeline.
---

## When to use this skill

Use this skill when you need to locally reproduce or verify the full CI pipeline before pushing changes or diagnosing a CI failure.

## Steps

1. Install all dependencies: `pip install -r requirements.txt -r requirements-dev.txt`
2. Run the test suite with coverage: `pytest -q --cov=app`
3. Confirm success by checking that all tests pass with no errors and a coverage report is printed to stdout.

## Expected output

A successful run looks like:

```
..........                                                        [100%]
10 passed in 0.42s

---------- coverage: platform linux, python 3.x ----------
Name      Stmts   Miss  Cover
-----------------------------
app.py       25      0   100%
```

All tests report `passed`, zero failures or errors, and a coverage table for `app` is displayed.

## Common failures

- **`ModuleNotFoundError: No module named 'pytest'` or `No module named 'pytest_cov'`**: `requirements-dev.txt` is missing `pytest` and/or `pytest-cov`. Add them to `requirements-dev.txt` and re-run the install command.
- **`ImportError` or confusion importing `app` in tests**: The app module is a single file (`app.py`) at the repo root, not a package. Ensure tests import directly from `app` (e.g., `from app import app`) and that the working directory is the repo root when running `pytest`.
- **Unexpected behavior from `GREETING` environment variable**: `GREETING` is read once at module load time. If you changed the environment variable after the process started, restart the process or set the variable before invoking `pytest` (e.g., `GREETING=Hello pytest -q --cov=app`).
- **Dependency conflicts or stale environment**: Delete and recreate your virtual environment, then re-run `pip install -r requirements.txt -r requirements-dev.txt` from a clean state.
```