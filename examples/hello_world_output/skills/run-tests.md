---
name: run-tests
description: Run the full test suite with project-configured settings.
---

## When to use this skill

Use this skill when you need to execute the full test suite to verify correctness of changes made to the codebase.

## Steps

1. Install dependencies using the exact install command from the project configuration:
   ```
   pip install -r requirements.txt
   ```
   > **Caution:** No `requirements.txt` is confirmed present in the file tree. If this file is missing, dependency installation will fail. See Common Failures below.

2. Run the test suite using the project-configured test command:
   ```
   pytest
   ```

3. Review the output to confirm all tests pass — look for a summary line indicating zero failures and zero errors.

## Expected output

A successful run produces a pytest summary showing all collected tests passing, with no FAILED or ERROR entries. The final summary line will indicate the number of tests passed (e.g., `X passed in Y.XXs`).

## Common failures

- **`requirements.txt` not found**: The analysis notes that no `requirements.txt` is confirmed visible in the repository file tree. This repository appears to be an example output directory, not the actual Flask application source. Locate the correct source repository and run this skill there.

- **No tests collected**: The test directory could not be verified from the analysis input. If pytest reports `no tests ran` or `collected 0 items`, confirm the location of test files manually and pass the correct path to `pytest` — the test directory is not determinable from source.

- **Import errors or missing modules**: If pytest fails due to missing dependencies, the application source files may not be present — this is flagged as a known pitfall. Verify you are operating on the full application repository, not just the AgentReady-generated artifacts directory.

- **Entry point or application not found**: The application entry point is not determinable from source. If tests require a running application context, consult the project's own documentation to identify the correct entry point before running tests.