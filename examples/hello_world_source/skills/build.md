---
name: build
description: Build the project artifacts.
---

## When to use this skill

Use this skill when you need to install the project and its dependencies to prepare the environment for running or testing the application.

## Steps

1. Install the project and its dependencies:
   ```
   pip install -e .
   ```
   If the above fails, fall back to:
   ```
   pip install -r requirements.txt
   ```
2. Verify the Flask entry point is importable:
   ```
   python -c "from app import app; print('app loaded')"
   ```
3. Confirm the application starts without error:
   ```
   python app.py
   ```

## Expected output

A successful install via `pip install -e .` will print dependency resolution output ending with:
```
Successfully installed <package-list>
```
The import check will print:
```
app loaded
```
Starting `python app.py` will produce Flask's development server output, e.g.:
```
 * Running on http://127.0.0.1:5000
```

## Common failures

- **`pip install -e .` fails with no `[dev]` extras error**: The project has no `extras_require` dev section; run `pip install -r requirements.txt` instead — this is the authoritative fallback.
- **`python -c "from app import app"` fails with `ModuleNotFoundError: flask`**: Dependencies were not installed successfully; re-run the install step and confirm `flask>=2.3` is present in the environment (`pip show flask`).
- **`python app.py` fails with `Address already in use`**: Another process is occupying the default Flask port; stop the conflicting process or set `FLASK_RUN_PORT` to a free port before retrying.
- **Wrong Python version**: This project requires Python `>=3.11`; confirm your active interpreter with `python --version` and switch to a compliant version if needed.