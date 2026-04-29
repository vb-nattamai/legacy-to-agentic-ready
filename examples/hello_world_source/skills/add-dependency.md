---
name: add-dependency
description: Add a new dependency to the project.
---

## When to use this skill

Use this skill whenever a new third-party package needs to be added as a project dependency.

## Steps

1. Open `pyproject.toml` and add the new package (with any required version constraint) to the `dependencies` list under the `[project]` section — this is the authoritative source for project dependencies. Do **not** edit `requirements.txt` for project dependencies.
2. Install the updated dependencies by running: `pip install -e '.[dev]' 2>/dev/null || pip install -r requirements.txt`
3. Verify the dependency is importable and the test suite still passes by running: `pytest`

## Expected output

- `pyproject.toml` `[project].dependencies` list contains the new package entry (e.g. `"requests>=2.31"`).
- The install command completes without errors and the package is available in the active environment.
- `pytest` exits with no failures.

## Common failures

- **`pip install -e .` fails with no package directory found**: `pyproject.toml` declares a setuptools build backend but there is no `setup.cfg` or package directory; the install command includes a `requirements.txt` fallback (`pip install -e '.[dev]' 2>/dev/null || pip install -r requirements.txt`) which should handle this automatically.
- **Version conflict with existing dependencies**: Check the existing constraint `flask>=2.3` in `pyproject.toml` and ensure the new package's requirements are compatible; resolve by adjusting version specifiers and re-running the install command.
- **`pytest` failures after adding the dependency**: The new package may have introduced a side effect or the dependency itself may be incompatible with Python `>=3.11` (the required version per `pyproject.toml`); remove the addition, verify compatibility, and retry.