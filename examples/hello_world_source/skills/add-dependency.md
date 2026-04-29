---
name: add-dependency
description: Add a new dependency to the project.
---

## When to use this skill

Use this skill when you need to introduce a new third-party package into the project and ensure it is properly recorded and validated.

## Steps

1. Install the new package and record it: `pip install <package-name>` then add the package (with a pinned or minimum version) to `requirements.txt`.
2. Reinstall the project in editable mode to confirm the full dependency set resolves cleanly: detected as likely: `pip install -e .` — verify before use. If that fails, fall back to `pip install -r requirements.txt`.
3. Run the test suite to confirm no existing functionality is broken: `pytest`

## Expected output

- `pip install <package-name>` completes without errors and prints `Successfully installed <package-name>-<version>`.
- The package name and version specifier appear as a new line in `requirements.txt`.
- `pytest` exits with all tests passing and no collection errors.

## Common failures

- **Dependency conflict**: If `pip install` reports incompatible version constraints, inspect the conflicting packages listed in the error, adjust the version specifier in `requirements.txt`, and re-run the install command.
- **Package not found on PyPI**: Verify the exact package name on PyPI; a typo will produce a `No matching distribution found` error. Correct the name and retry.
- **Tests fail after adding the dependency**: The new package may introduce behaviour that conflicts with module-level state (e.g. the `_greetings` list) or changes response headers that existing tests assert on. Isolate the failure with `pytest -v`, review the diff, and either pin an older compatible version or update the affected tests.
- **`pip install -e .` not available**: If `pyproject.toml` or `setup.py` is absent or malformed, fall back to `pip install -r requirements.txt` and ensure `requirements.txt` is the authoritative dependency file.