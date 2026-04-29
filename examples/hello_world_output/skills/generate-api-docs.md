---
name: generate-api-docs
description: Generate or update API documentation from the OpenAPI spec.
---

## When to use this skill

Use this skill when you need to generate or refresh API documentation from the repository's OpenAPI specification.

## Steps

1. Install dependencies using the exact command from the analysis: `pip install -r requirements.txt`
2. Locate the OpenAPI spec file in the repository — the entry point and spec file path are not determinable from source; inspect the repository file tree to find the spec (e.g. a `.yaml`, `.json`, or `.yml` file describing the API).
3. Run the documentation generation tool against the located OpenAPI spec. Command not determinable from source — check your project's documentation.
4. Validate the output by running the test suite: `pytest`

## Expected output

A successful run produces generated API documentation artifacts (format and output directory not determinable from source) with no errors reported during generation, and the `pytest` test suite exits with no failures.

## Common failures

- **`requirements.txt` not found**: The analysis notes that no `requirements.txt` is visible in the file tree — this repository may be an example output directory rather than the full application source. Verify you are working in the correct repository root before running install commands.
- **OpenAPI spec not found**: The spec file path is not determinable from source. Search the repository manually for `.yaml`, `.json`, or `.yml` files and confirm the correct spec path before running the documentation generator.
- **Entry point unknown**: The application entry point is listed as `TODO: verify` in the analysis. Inspect the repository to identify the correct entry point before attempting to run or reference the application.
- **Missing application source files**: The analysis explicitly flags that application source files may not be present — if the generator requires live application introspection, this will fail. Confirm the full source is available.