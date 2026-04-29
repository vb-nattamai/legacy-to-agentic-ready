---
name: build
description: Build the project artifacts.
---

## When to use this skill

Use this skill when you need to install project dependencies and prepare the environment for running or testing the Flask application.

## Steps

1. Install project dependencies by running: `pip install -r requirements.txt`
2. Verify the installation completed without errors by checking that all packages were successfully installed.
3. Confirm success by running: `pip list` to validate that dependencies are present in the environment.

## Expected output

A successful run produces output showing each package being downloaded and installed, ending with a line similar to:

```
Successfully installed <package-name>==<version> ...
```

No error messages or dependency conflict warnings should appear.

## Common failures

- **Missing requirements.txt**: No `requirements.txt` is confirmed present in the repository file tree. If the file is absent, the build command will fail with `ERROR: Could not open requirements file`. Locate or recreate the requirements file before proceeding — dependency information must be inferred from documentation as noted in the project analysis.
- **Dependency conflicts**: If conflicting package versions are detected during install, resolve them by reviewing the requirements file and aligning version pins, or use a fresh virtual environment to isolate the installation.
- **Application source files not present**: The repository is identified as an example output directory containing AgentReady-generated artifacts only, not the actual Flask application code. If source files are missing, the build environment may install successfully but the application will not be runnable. Verify you are working in the correct repository before proceeding.