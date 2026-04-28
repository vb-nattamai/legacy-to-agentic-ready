```markdown
---
name: add-dependency
description: Add a new dependency to the project.
---

## When to use this skill

Use this skill whenever a new third-party package needs to be added to the project and made available to all contributors.

## Steps

1. Add the new package name (with an optional version pin, e.g. `requests==2.31.0`) to `requirements.txt` on its own line. If the package is only needed for development or testing, add it to `requirements-dev.txt` instead.
2. Install all dependencies to sync your local environment: `pip install -r requirements.txt -r requirements-dev.txt`
3. Verify the package is importable and the test suite still passes: `pytest -q --cov=app`

## Expected output

The install step prints each package being collected and ends with `Successfully installed <package-name>`. The test step outputs a passing test summary such as:

```
..........                                                     [100%]
---------- coverage: platform ... -----------
TOTAL    95%
10 passed in 0.42s
```

## Common failures

- **Package not found / install error**: The package name may be misspelled or not available on PyPI. Double-check the name on https://pypi.org and correct it in `requirements.txt` before re-running the install command.
- **Import errors in tests after install**: `app.py` is a single-file module at the repo root and imports resolve from there. Ensure the new package is imported correctly in `app.py` (e.g. `import requests`) rather than using a subpackage path that assumes a package structure.
- **`pytest-cov` or `pytest` missing**: If `requirements-dev.txt` is empty or incomplete, `pytest -q --cov=app` will fail. Confirm that `pytest` and `pytest-cov` are listed in `requirements-dev.txt` and re-run `pip install -r requirements.txt -r requirements-dev.txt`.
- **Version conflict**: A pinned version may conflict with an existing dependency. Run `pip install -r requirements.txt -r requirements-dev.txt` again after relaxing or adjusting the version specifier, then re-run the test command to confirm compatibility.
```