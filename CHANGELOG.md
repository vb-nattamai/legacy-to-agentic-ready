# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.7.0] — 2026-04-22

### Added

- add runtime_version to analysis schema + complete README rewrite

---
## [2.6.3] — 2026-04-21


### Fixed

- ruff lint and format violations (f-string placeholder, duplicate dict key)

### Changed

- docs: update README and agent files to reflect v2 eval, 12 generated files, MCP server

---
## [2.6.2] — 2026-04-21


### Fixed

- reduce hallucination false positives to reach industry-standard rates

---
## [2.6.1] — 2026-04-21

### Added

- (templates): production-ready template and generator improvements
- (eval): golden-set v2 — break circular ground truth, haiku baseline
- (mcp): add real MCP server with transform, score, evaluate, review_pr tools
- (eval): add standalone eval workflow for target repos

### Fixed

- float formatting and dead code cleanup
- (analyser): eliminate hallucination root cause — filter AgentReady tooling from LLM input
- (evaluator): _load_custom_questions handles wrapper format and disabled stubs
- (generator): restore generate_mcp_json accidentally deleted in template edit
- (score): brace-glob tip bug, add tools/refresh_context.py, reach 100/100
- (pr-template): remove non-existent files from PR body; add agent scaffolding
- (security): expression injection in dev utility workflows
- (eval): wire _multi_judge_response into run_eval — panel was dead code
- (ci): coverage >50%, CodeQL CWE-312, remaining ${{ }} in run: block
- (lint): remove unused call import in test_reviewer.py
- (security): bash arrays for cmd building, regex allowlist, missing run: label
- (security): harden workflows against injection and suppress litellm logging

### Changed

- docs: fix workflow names, add security model, ci/codeql sections, contributing checklist
- style: ruff format evaluator.py
- chore: resolve merge conflicts with main (2.5.2)

---
## [2.6.0] — 2026-04-17

### Added

- `reusable-eval.yml` — new reusable workflow that runs eval-only against any target repo; posts `AGENTIC_EVAL.md` to the step summary and uploads it as a 30-day artifact
- `eval-workflow.yml` template — installed into target repos as `.github/workflows/agentic-ready-eval.yml`; triggers on `workflow_dispatch` and on `push` to `main` when scaffolding files change

### Changed

- `install-workflow.yml` template — `eval` now defaults to `true`; transformation runs include evaluation by default
- `install-to-target-repo.yml` — installer now also pushes `agentic-ready-eval.yml` into target repos (5 files total)

---

## [2.5.2] — 2026-04-17

### Added

- (installer): also push pr-review-workflow.yml to target repos

### Fixed

- address PR review agent feedback

---
## [2.5.1] — 2026-04-16

### Added

- (reviewer): add LLM-powered PR review agent

### Fixed

- (reviewer): address security review feedback
- (analyser): use relative path parts for SKIP_DIRS check
- replace em dash with ASCII hyphen in workflow names and format Python files
- remove --llm flag from context-drift-detector workflow

### Changed

- ci: add codeql and dependabot
- refactor: split evaluator into testable helper functions
- test: add deterministic coverage for analyser and generator
- docs: align automation and secret handling guidance
- ci: add repo validation workflow for tests and lint

---
## [2.5.0] — 2026-04-16

### Added

- **PR Review Agent**: `reviewer.py` module + `--review-pr <n>` CLI flag — AI-powered code review grounded in `agent-context.json`; posts APPROVE/REQUEST_CHANGES directly to GitHub
- `pr-review-workflow.yml` template — installed into target repos, runs on every pull request
- `.github/workflows/pr-review.yml` — AgentReady's own self-review workflow

### Fixed

- `analyser.py`: use relative path parts for SKIP_DIRS/SKIP_AGENT_DIRS checks — previously files under `/tmp` (Linux CI) were all silently skipped due to "tmp" appearing in absolute path parts
- `context-drift-detector.yml`: replace em dash (U+2014) with ASCII hyphen in workflow `name:` field — fixes "workflow file issue" ghost failures on every push in target repos
- CI: remove `--llm` flag from context-drift-detector workflow — LLM is now the default, flag was removed from CLI in v2.4.4 but not from the workflow

### Changed

- `context-drift-detector-workflow.yml` template: remove redundant `setuptools wheel build` from pip install; use shared `DRIFT_PR_TEMPLATE.md` instead of inline heredoc; sync git commit message to use ASCII hyphen

---
## [2.4.4] — 2026-04-04


### Fixed

- remove --llm flag from context-drift-detector — LLM is now default

---
## [2.4.3] — 2026-04-03


### Fixed

- correct install path and add --llm to context drift detector

### Changed

- docs: update README with food-delivery benchmark, 15-question eval, new report format
- chore: remove static template files — replaced by LLM generation

---
## [2.4.2] — 2026-04-02


### Fixed

- replace llm flag with provider in install-workflow.yml template

---
## [2.4.1] — 2026-04-02


### Fixed

- align workflows with LiteLLM multi-provider — replace llm flag with provider, fix install paths

---
## [2.4.0] — 2026-04-02

### Added

- expand eval to 15 questions, 5 pitfall categories, readable report format

### Changed

- docs: update all docs and templates for provider-agnostic litellm refactor

---
## [2.3.8] — 2026-04-01


### Fixed

- skip AgentReady-generated files during analysis to prevent hallucinations on re-runs

---
## [2.3.7] — 2026-04-01


### Fixed

- use heredoc for drift PR body to fix YAML syntax error on line 92

---
## [2.3.6] — 2026-04-01


### Fixed

- update drift PR template to include potential pitfalls verification

---
## [2.3.5] — 2026-04-01


### Fixed

- add --llm to context drift detector, inline PR body in template

---
## [2.3.4] — 2026-04-01


### Fixed

- update context-drift-detector template to reference renamed workflow

### Changed

- docs: rewrite automation.md for v2.0 — LLM mode, eval framework, labeled-only trigger universal prompt for v2.0 — LLM-first, no templates, pitfalls emphasis

---
## [2.3.3] — 2026-04-01


### Fixed

- add eval and fail_level to install-workflow.yml template

---
## [2.3.2] — 2026-04-01


### Fixed

- update installer to use renamed context-drift-detector-workflow.yml template

---
## [2.3.1] — 2026-04-01


### Fixed

- replace misleading improvement% with absolute score delta in evaluator

---
## [2.3.0] — 2026-04-01

### Added

- strengthen pitfalls prompts in generator, add Kotlin to mcp runtime map

### Changed

- chore: remove obsolete workflow files and update README for clarity and context

---
## [2.2.0] — 2026-03-31

### Added

- add workflow to validate INSTALL_TOKEN permissions

---
## [2.1.3] — 2026-03-31


### Fixed

- update generation model from claude-haiku-4-5-20251001 to claude-sonnet-4-6

### Performance

- switch generation model from Sonnet to Haiku for reliability and speed

---
## [2.1.2] — 2026-03-31


### Fixed

- update generation model to claude-haiku-4-5-20251001

---
## [2.1.1] — 2026-03-31


### Fixed

- remove root templates, rename drift detector template, update cli/generator/evaluator with retry logic and eval framework

---
## [2.1.0] — 2026-03-31

### Added

- implement AgentReady installation workflow and remove deprecated issue trigger

### Changed

- test: add push permission check workflow for INSTALL_TOKEN validation
- refactor: update AgentReady documentation for clarity and versioning

---
## [2.0.7] — 2026-03-27


### Fixed

- catch APIStatusError 529 instead of non-existent OverloadedError
- add retry logic for overloaded Anthropic API in analyser
- use INSTALL_TOKEN directly for pushing to target repository
- use INSTALL_TOKEN env var explicitly for cross-repo push
- set PYTHONPATH for agent-ready CLI execution in transformer workflow
- specify repository and token for agent-ready checkout in transformer workflow
- add debug step to list workspace contents in reusable transformer workflow
- run cli.py via absolute GITHUB_WORKSPACE path, install anthropic directly
- add confirmation message for agent_ready installation in transformer workflow
- update command to use module syntax for agent-ready CLI
- update AI dependency installation to use specific version of anthropic
- use realpath for agent-ready installation path in transformer workflow

---
## [2.0.6] — 2026-03-27


### Fixed

- catch APIStatusError 529 instead of non-existent OverloadedError
- add retry logic for overloaded Anthropic API in analyser
- use INSTALL_TOKEN directly for pushing to target repository
- use INSTALL_TOKEN env var explicitly for cross-repo push
- set PYTHONPATH for agent-ready CLI execution in transformer workflow
- specify repository and token for agent-ready checkout in transformer workflow
- add debug step to list workspace contents in reusable transformer workflow
- run cli.py via absolute GITHUB_WORKSPACE path, install anthropic directly
- add confirmation message for agent_ready installation in transformer workflow
- update command to use module syntax for agent-ready CLI
- update AI dependency installation to use specific version of anthropic
- use realpath for agent-ready installation path in transformer workflow

---
## [2.0.5] — 2026-03-27


### Fixed

- use INSTALL_TOKEN directly for pushing to target repository
- use INSTALL_TOKEN env var explicitly for cross-repo push
- set PYTHONPATH for agent-ready CLI execution in transformer workflow
- specify repository and token for agent-ready checkout in transformer workflow
- add debug step to list workspace contents in reusable transformer workflow
- run cli.py via absolute GITHUB_WORKSPACE path, install anthropic directly
- add confirmation message for agent_ready installation in transformer workflow
- update command to use module syntax for agent-ready CLI
- update AI dependency installation to use specific version of anthropic
- use realpath for agent-ready installation path in transformer workflow

---
## [2.0.4] — 2026-03-27


### Fixed

- set PYTHONPATH for agent-ready CLI execution in transformer workflow
- specify repository and token for agent-ready checkout in transformer workflow
- add debug step to list workspace contents in reusable transformer workflow
- run cli.py via absolute GITHUB_WORKSPACE path, install anthropic directly
- add confirmation message for agent_ready installation in transformer workflow
- update command to use module syntax for agent-ready CLI
- update AI dependency installation to use specific version of anthropic
- use realpath for agent-ready installation path in transformer workflow

---
## [2.0.3] — 2026-03-26


### Fixed

- simplify Python package installation step in reusable transformer workflow

---
## [2.0.2] — 2026-03-26


### Fixed

- remove unnecessary directory change in Python setup step

---
## [2.0.1] — 2026-03-26


### Fixed

- remove pip caching from Python setup in reusable transformer workflow

---
## [2.0.0] — 2026-03-26

### Added

- LLM-first transformation pipeline

---
## [1.3.0] — 2026-03-26

### Added

- generate OpenAI and Gemini agent entry points from templates
- add OpenAI and Gemini agent entry point templates

### Fixed

- update platform references and enhance discovery instructions for agent generation
- always generate system_prompt.md and print readiness score after file generation
- only generate tool templates and agent-context.json for detected languages; add LLM verification option

### Changed

- docs: clarify intention and LLM usage for production-ready context
- docs: add version/license badges, pip install, and CLI usage to README
- chore: archive notice — superseded by agent-ready repo
- docs: clarify and simplify context-refresh workflow header for users

---
## [1.2.2] — 2026-03-26


### Fixed

- bundle templates as package data so pip-installed runs generate all files

### Changed

- ci: fix 6 workflow issues — install toolkit, exclude checkout, guard PR creation

---
## [1.2.1] — 2026-03-26


### Fixed

- install agent-ready package in transformer workflow

### Changed

- ci: use modern setuptools build backend (setuptools.build_meta)
- ci: use non-editable install for toolkit to avoid editable pyproject backend failures
- ci: upgrade packaging toolchain before editable install to fix BackendUnavailable

---
## [1.2.0] — 2026-03-25

### Added

- automatically create agentic-ready issue when installing to target repo

### Changed

- refactor: industry-standard Python package structure + fix all legacy branding

---
## [1.1.2] — 2026-03-25


### Fixed

- context-refresh ignores last_scanned timestamp to prevent false-positive drift PRs

---
## [1.1.1] — 2026-03-25


### Fixed

- context-refresh now reusable via workflow_call, install-to-repo pushes both workflows, README clarifies LLM usage and workflow purposes

### Changed

- docs: add Workflows section describing all 5 workflows + update repo structure tree

---
## [1.1.0] — 2026-03-25

### Added

#### Features
- **Agentic Readiness Transformer Agent Definition** — Complete 5-phase specification for using the transformer tool itself as an agent
  - Phase 1: Repository audit checklist
  - Phase 2: Universal core files generation
  - Phase 3: Platform-specific agent files (Claude, OpenAI, Gemini, VS Code)
  - Phase 4: AGENTIC_READINESS.md with scoring
  - Phase 5: Validation checklist with security constraints

#### CLI Enhancements
- `--install-hooks` — Pre-commit hook installer for automatic dynamic context refresh
- `--verify` — LLM-based context verification with Claude Haiku (validates entry_point, test_command, language)
- `--quiet` — Suppress banner (CI-friendly mode)
- `--verbose` — Detailed logging during transformation

#### GitHub Actions Workflows
- **issue-trigger.yml** — Trigger transformations from issues with `[agentic-ready]` title/label
- **reusable-transformer.yml** — Callable workflow for integration into any pipeline
- **context-refresh.yml** — Weekly scheduled refresh (Monday 09:00 UTC) with drift detection
- **test-dry-run.yml** — Manual testing workflow for previewing changes without writing files

#### Security
- Collaborator authentication checks in workflows (GitHub & Gitea)
- Role-based access control for transformation triggers
- Validation of restricted_write_paths across all generated files

#### Data Structure
- **Static/Dynamic Split** in agent-context.json
  - Static section: `repo_name`, `primary_language`, `frameworks`, `entry_point`, `restricted_write_paths`, `environment_variables`
  - Dynamic section: `last_scanned`, `module_layout`, `domain_concepts`, `agent_capabilities` (auto-refreshed)
- **AGENTIC_READINESS.md** — New audit report with platform compatibility matrix

#### Scoring System
- **100-Point Readiness Score** with 12 criteria:
  - Core files (agent-context.json, CLAUDE.md, AGENTS.md): 30 points
  - Executable files and commands (entry_point, test_command, build_command): 30 points
  - Constraints and safety (restricted_write_paths, environment_variables): 20 points
  - Domain knowledge (domain_concepts, OpenAPI spec, CI config): 20 points
- Actionable recommendations for improvement
- Output after every transformation

#### Documentation
- Comprehensive README with:
  - 7 major improvements documented with examples
  - CLI reference with all flags
  - GitHub Actions dry-run instructions
  - Environment variable configuration guide
  - Platform compatibility matrix
  - "Keeping context fresh" section (3 strategies)
  - "Verify your context" section with CI gate examples
- CHANGELOG.md (this file)

### Changed

#### YAML Fixes
- Fixed multiline string handling in issue-trigger.yml workflows (both GitHub and Gitea)
- Converted to heredoc pattern with `$(cat <<'EOF')` for proper YAML parsing

#### Platform Coverage
- Updated all platform-specific agents to propagate constraints
- Enhanced system_prompt.md with full domain glossary
- Improved tool definition templates for Python, TypeScript, Java, Go

#### Pre-commit Hook
- Automatic dynamic section refresh on source file changes
- Configurable via `git config agentic.toolkit-path`
- Safe handling: static section never overwritten

### Fixed

- YAML syntax error on line 121 of issue-trigger.yml (multiline string handling)
- Context staleness issue through pre-commit hooks and weekly CI refresh
- Tool parity across platforms (all tools now available on all platforms)
- Memory schema missing from initial generation (now included by default)

### Documentation

- Added "Keeping context fresh" section with 3 strategies
- Added "Verify your context" section with CI gate instructions
- Added "🎯 CLI Reference" quick lookup table
- Added "🤖 Using the Transformer as an AI Agent" guide
- Added "🎯 Recent Improvements (v1.1.0)" section with detailed feature breakdown
- Enhanced automation section with security details

---

## [1.0.0] — 2026-03-10

### Added

Initial release with core functionality:

#### Core Features
- Automatic repository analysis (language, framework, build system detection)
- Multi-platform agent scaffolding (Claude, OpenAI, Gemini, Any LLM)
- Static context generation:
  - `AGENTS.md` — Agent instruction file with safe/forbidden operations
  - `CLAUDE.md` — Claude Code context with module layout
  - `system_prompt.md` — Universal system prompt for any LLM
  - `agent-context.json` — Machine-readable repo map
  - `mcp.json` — MCP server configuration
  - Tool scaffolds (`tools/<capability>_tool.*`)
  - Memory schema (`memory/schema.md`)

#### Language Support
- Python (Flask, Django, FastAPI, scripts)
- TypeScript / JavaScript (React, Next.js, Express, Node.js)
- Java (Spring Boot, Maven, Gradle)
- Go (Gin, Echo, stdlib)
- Rust (Cargo)
- C# / .NET (ASP.NET)
- Ruby (Rails, gems)
- Generic fallback templates

#### CLI
- `--target` — Specify target repository path
- `--only` — Selective generation (agents, tools, context, memory)
- `--dry-run` — Preview without writing files
- `--force` — Overwrite existing files
- `--provider` — Specify LLM provider (anthropic, openai)

#### Automation
- GitHub Actions integration
- Gitea Actions support
- Reusable workflow patterns
- Issue-based triggers

#### Documentation
- Comprehensive README with examples
- Multiple usage modes and examples
- Contributing guidelines
- MIT License

---

## Version History

| Version | Date | Major Changes |
|---------|------|---------------|
| 1.1.0 | 2026-03-25 | 7 improvements: security, freshness, quality, structure, scoring, CLI enhancements, documentation |
| 1.0.0 | 2026-03-10 | Initial release with core scaffolding and automation |

---

[1.1.0]: https://github.com/vb-nattamai/agent-ready/releases/tag/v1.1.0
[1.0.0]: https://github.com/vb-nattamai/agent-ready/releases/tag/v1.0.0
