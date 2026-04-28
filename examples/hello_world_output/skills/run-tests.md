---
name: run-tests
description: Run the full test suite with project-configured settings.
---

## When to use this skill

Use this skill whenever you need to execute the full test suite and verify code coverage for the Flask application.

## Steps

1. Install all dependencies, including dev tools: `pip install -r requirements.txt -r requirements-dev.txt`
2. Run the full test suite with coverage: `pytest -q --cov=app`
3. Confirm success by reviewing the terminal output for a passing summary line (e.g., `N passed`) and a coverage report table showing `app` coverage percentage.

## Expected output

A successful run produces quiet pytest output listing any test results, followed by a `pytest-cov` coverage table similar to:

```
......
Name     Stmts   Miss  Cover
----------------------------
app.py      20      2    90%
----------------------------
TOTAL       20      2    90%

N passed in 0.XXs
```

No failures, errors, or warnings should appear.

## Common failures

- **`ModuleNotFoundError: No module named 'pytest'` or `No module named 'pytest_cov'`**: `requirements-dev.txt` is missing `pytest` and/or `pytest-cov`. Add them to `requirements-dev.txt` and re-run `pip install -r requirements.txt -r requirements-dev.txt`.
- **`ImportError` when importing `app` in tests**: Tests may be conflicting with the Flask app object and module sharing the name `app`. Ensure test files import explicitly (e.g., `from app import app as flask_app`) and that the repo root is on `sys.path`.
- **Environment-dependent test failures for `GREETING`**: `GREETING` is read once at module load time. If a test sets `os.environ["GREETING"]` after import, the change will not take effect. Use `importlib.reload(app)` or set the environment variable before the module is first imported (e.g., via `monkeypatch.setenv` combined with a module reload fixture).
- **Coverage report shows `No data to report`**: The `--cov=app` flag targets the `app` module by name. Confirm `app.py` exists at the repo root and that tests actually import and exercise it.