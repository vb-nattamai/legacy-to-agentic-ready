# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
