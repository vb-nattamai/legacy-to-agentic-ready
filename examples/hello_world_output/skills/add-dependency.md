---
name: add-dependency
description: Add a new dependency to the project.
---

## When to use this skill

Use this skill when you need to introduce a new third-party package into the project.

## Steps

1. Add the new package name (and optionally a version pin, e.g. `flask==3.0.0`) as a new line in `requirements.txt`.
   > **Note:** No `requirements.txt` was detected in the file tree during analysis. Confirm the file's location before editing. See *Common failures* below.
2. Install all dependencies (including the newly added one) by running the install command exactly as specified:
   ```
   pip install -r requirements.txt
   ```
3. Verify the dependency is installed and the project still works by running the test command:
   ```
   pytest
   ```

## Expected output

- `pip install -r requirements.txt` completes without errors and reports `Successfully installed <package-name>` (or `Requirement already satisfied` for previously installed packages).
- `pytest` exits with all tests passing and no import errors related to the new or existing packages.

## Common failures

- **`requirements.txt` not found**: The analysis flagged that no `requirements.txt` is visible in the file tree — this repository may be an example output directory rather than the full application source. Locate the actual application source and confirm the path to `requirements.txt` before proceeding.
- **Package version conflict**: If `pip install -r requirements.txt` reports a dependency conflict, review version pins for the new package and any conflicting existing entries in `requirements.txt`, adjust version constraints, and re-run `pip install -r requirements.txt`.
- **`pytest` collection errors after install**: If tests fail to collect due to import errors, confirm the package name is spelled correctly in `requirements.txt` and that the install step completed without errors.
- **Wrong virtual environment active**: If the installed package is not found at runtime, confirm the correct virtual environment is activated before running `pip install -r requirements.txt`.