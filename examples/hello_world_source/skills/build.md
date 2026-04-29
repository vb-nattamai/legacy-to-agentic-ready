---
name: build
description: Build the project artifacts.
---

## When to use this skill

Use this skill when you need to install project dependencies and prepare the environment to run or develop the application.

## Steps

1. Install dependencies by running: `pip install -e '.[dev]' 2>/dev/null || pip install -r requirements.txt`
2. Verify the entry point is accessible: confirm `app.py` exists at the repository root.
3. Confirm the build succeeded by running the application: `python app.py`

## Expected output

A successful run of the install step will produce pip output showing packages being installed (or "already satisfied" messages for cached packages), ending with no errors. Running `python app.py` will start the Flask development server, typically printing output such as:

```
 * Running on http://127.0.0.1:5000
```

with no import errors or tracebacks.

## Common failures

- **`pip install -e '.[dev]'` fails with "No such file or directory" or build backend error**: `pyproject.toml` declares a setuptools build backend but there is no `setup.cfg` or package directory, so editable install may fail. The command automatically falls back to `pip install -r requirements.txt` — confirm that fallback completed without errors.
- **Wrong Python version**: This project requires Python `>=3.11`. If the install or run step fails with syntax errors or version-related messages, verify your active Python version with `python --version` and switch to a compatible interpreter.
- **`ModuleNotFoundError` for `flask`**: The install step did not complete successfully. Re-run `pip install -r requirements.txt` directly and inspect the output for errors.
- **`app.py` not found**: You are not running the command from the repository root. Change to the repository root directory before running any build or run commands.