---
name: run-ci
description: Trigger or simulate the CI pipeline.
---

## When to use this skill

Use this skill when you need to simulate or trigger the CI pipeline locally to verify that dependencies install and tests pass.

## Steps

1. Install dependencies: `pip install -r requirements.txt`
2. Run the test suite: `pytest`
3. Confirm all tests pass with no errors by reviewing the pytest output summary at the end of the run.

## Expected output

A successful run produces a pytest summary line indicating all collected tests passed (e.g., `X passed in Xs`), with no errors or failures reported. The dependency installation step should complete without package resolution errors.

## Common failures

- **`requirements.txt` not found**: The analysis notes that no `requirements.txt` is visible in the file tree. This file may be absent or located at an unverified path. Check the repository root and consult project documentation before running the install command.
- **No tests collected by pytest**: The test directory is not determinable from source. Locate the test files manually and confirm pytest can discover them, or check for a `pytest.ini`, `setup.cfg`, or `pyproject.toml` that configures the test path.
- **Import errors during test run**: Application source files are noted as potentially absent from this repository (this may be an example output directory). Verify that the actual Flask application code is present before running CI.

## Notes

The analysis flags that this repository may contain only AgentReady-generated artifacts and not the actual Flask application source code. Confirm that application source files and `requirements.txt` are present before attempting to run the CI pipeline.