---
name: add-dependency
description: Add a new dependency to the project.
---

## When to use this skill

Use this skill whenever a new third-party package needs to be added to the project as a runtime dependency.

## Steps

1. Open `pyproject.toml` and add the new package (with an appropriate version constraint) to the `dependencies` list under the `[project]` section — this is the authoritative source for project dependencies. Do **not** edit `requirements.txt` for project dependencies.
2. Install the updated dependencies by running:
   ```
   pip install -e .
   ```
3. Verify the dependency is importable and the existing test suite still passes by running:
   ```
   pytest
   ```

## Expected output

- `pip install -e .` completes without errors and reports the new package as installed.
- `pytest` exits with all tests passing and no import errors related to the new or existing packages.
- The `[project]` `dependencies` list in `pyproject.toml` contains the newly added entry (e.g. `"requests>=2.31"`).

## Common failures

- **`pip install -e .` fails with a resolver conflict**: The version constraint you specified is incompatible with an already-installed package. Loosen or adjust the version specifier in `pyproject.toml` and retry.
- **`pytest` fails with `ModuleNotFoundError`**: The install step did not complete successfully or was run in the wrong virtual environment. Confirm you are in the correct environment (`which python`) and re-run `pip install -e .`.
- **Dependency appears installed but is not reflected in `pyproject.toml`**: You may have run `pip install <package>` directly without editing `pyproject.toml`. Add the package to the `dependencies` list in `pyproject.toml` manually to make the change permanent and reproducible.
- **`pip install -e .[dev]` is used instead**: The project has no `extras_require` `dev` section in `pyproject.toml`, so this command will fail. Use `pip install -e .` or fall back to `pip install -r requirements.txt`.