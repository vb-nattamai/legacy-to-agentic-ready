---
name: build
description: Build the project artifacts.
---

## When to use this skill

Use this skill when you need to install the project and its dependencies to prepare it for development or execution.

## Steps

1. Install the project and its dependencies by running: `pip install -e '.[dev]' 2>/dev/null || pip install -r requirements.txt`
2. Verify the entry point is accessible: confirm `app.py` exists at the repository root.
3. Validate the build succeeded by running the application: `python app.py`

## Expected output

A successful build produces no error output from the install command, with all dependencies resolved and installed into the active Python environment. Running `python app.py` should start the Flask development server without import errors or missing-module exceptions.

## Common failures

- **Missing Python version**: This project requires Python `>=3.11` (verified from `pyproject.toml`). If the install fails with syntax or compatibility errors, confirm your active Python version meets this requirement before retrying.
- **`requirements.txt` not found**: The fallback install path (`pip install -r requirements.txt`) will fail if this file does not exist. If `pip install -e '.[dev]'` also fails, check that `pyproject.toml` or `setup.py` is present and well-formed at the repository root.
- **Editable install fails**: If `pip install -e .` raises an error about missing `setup.py` or `pyproject.toml` build backend, verify those files are intact and that `pip` is up to date (`pip install --upgrade pip`).
- **`app` symbol not found at runtime**: Flask's test client and other tooling must be able to import `app` from `app.py`. Do not rename that symbol; if you see `ImportError` referencing `app`, confirm the `app` Flask instance is defined at module level in `app.py`.