---
name: build
description: Build the project artifacts.
---

## When to use this skill

Use this skill when you need to install dependencies and prepare the project for running or testing.

## Steps

1. Install all dependencies: `pip install -r requirements.txt -r requirements-dev.txt`
2. Verify the entry point is present and the Flask app is importable: `python -c "import app; print(app.app)"`
3. Confirm the app starts without errors: `python app.py`

## Expected output

Step 1 should complete with pip printing `Successfully installed ...` or `Requirement already satisfied` for all packages listed in both requirements files, ending with no errors.

Step 2 should print the Flask app object, e.g. `<Flask 'app'>`, confirming the module loads correctly.

Step 3 should show Flask's development server output, e.g.:
```
 * Running on http://127.0.0.1:5000
 * Debug mode: ...
```

## Common failures

- **`requirements-dev.txt` not found**: Ensure the file exists and contains at least `pytest` and `pytest-cov`. Create it if missing before re-running the install command.
- **`ModuleNotFoundError` during import**: A package listed in `requirements.txt` or `requirements-dev.txt` failed to install — check pip output for errors and re-run `pip install -r requirements.txt -r requirements-dev.txt`.
- **Flask app object naming conflict**: Because the module and the Flask instance are both named `app`, importing in tests may behave unexpectedly. Reference the Flask instance explicitly as `app.app` when needed.
- **`GREETING` environment variable ignored**: If `GREETING` is set after the process starts, it will have no effect because it is read once at module load time — set the variable in the environment before launching `python app.py`.