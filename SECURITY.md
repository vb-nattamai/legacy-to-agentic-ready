# Security Policy

## Supported Versions

AgentReady is actively maintained on `main` and the latest published release.
Older releases may not receive security fixes.

| Version | Supported |
|---|---|
| Latest release / `main` | ✅ |
| Earlier releases | ❌ |

## Reporting a Vulnerability

Please report suspected vulnerabilities privately by opening a GitHub Security Advisory for this repository:

1. Go to `https://github.com/vb-nattamai/agent-ready/security/advisories`
2. Click **Report a vulnerability**
3. Include impact, reproduction steps, and suggested mitigations if known

If you cannot use advisories, open a private maintainer contact request via a GitHub issue and avoid posting exploit details publicly.

## Important Project-Specific Notes

- This project automates repository changes through workflows that can create branches and pull requests.
- Some workflows use privileged credentials (for example `INSTALL_TOKEN` and provider API keys).
- Treat these credentials as sensitive and rotate/restrict them with least privilege.
- Redact all secrets, tokens, and API keys from logs, screenshots, issue reports, and pull requests.
