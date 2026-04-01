"""
AgentReady — LLM Analyser (Phase 1 + Phase 2)

Phase 1: Collect — mechanical file reading, no reasoning.
Phase 2: Analyse — Claude Opus reads the actual code and produces a
         structured JSON understanding of the repository.

This module is only used when --llm is passed to the CLI.
The existing static RepoAnalyzer in cli.py is unaffected.
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import anthropic

# ── Models ────────────────────────────────────────────────────────────────────

ANALYSIS_MODEL = "claude-opus-4-6"

# ── Constants ─────────────────────────────────────────────────────────────────

SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "env",
    ".tox", ".mypy_cache", ".pytest_cache", "dist", "build", "target",
    ".next", ".nuxt", "out", "coverage", ".idea", ".vscode",
    ".gradle", ".sass-cache", "tmp", "temp",
}

# AgentReady-generated files — skip these during analysis so Opus never reads
# its own previous output as source code, which causes hallucinations.
SKIP_AGENT_FILES = {
    "AGENTS.md",
    "CLAUDE.md",
    "agent-context.json",
    "system_prompt.md",
    "mcp.json",
    "AGENTIC_EVAL.md",
    "AGENTIC_READINESS.md",
}

# AgentReady-generated directories — skip entirely
SKIP_AGENT_DIRS = {
    "memory",  # memory/schema.md
    "tools",   # generated tool scaffolds
}

SOURCE_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".mjs",
    ".java", ".go", ".rs", ".cs", ".rb", ".kt",
    ".swift", ".cpp", ".c", ".h", ".php",
}

CONFIG_FILES = [
    "package.json", "pom.xml", "build.gradle", "build.gradle.kts",
    "go.mod", "Cargo.toml", "pyproject.toml", "requirements.txt",
    "setup.py", "setup.cfg", "Makefile", "Gemfile",
    ".env.example", ".env.sample", "docker-compose.yml", "Dockerfile",
]

OPENAPI_PATTERNS = [
    "openapi.yaml", "openapi.yml", "openapi.json",
    "swagger.yaml", "swagger.yml", "swagger.json",
]

# Max source files to pass to LLM (cost/token control)
MAX_SOURCE_FILES = 40
MAX_FILE_KB = 80

# ── Analysis JSON schema (sent to the LLM as a reference) ─────────────────────

ANALYSIS_SCHEMA = """
{
  "project_name": "string",
  "description": "string — what this project does in 1-2 sentences, derived from README and code",
  "primary_language": "string — the single dominant language",
  "secondary_languages": ["string"],
  "frameworks": ["string — only frameworks actually found in dependency files or imports"],
  "build_system": "maven|gradle|npm|yarn|pip|go|cargo|make|bundler|unknown",
  "entry_point": "string — the main entry point file path relative to repo root, must exist in file tree",
  "test_command": "string — exact command to run tests, verified against build config",
  "build_command": "string — exact command to build the project",
  "install_command": "string — exact command to install dependencies",
  "run_command": "string — exact command to run the application",
  "architecture_summary": "string — 2-3 sentences on the system architecture and key design decisions",
  "domain_concepts": [
    {
      "term": "string — class name, method name, or domain term found in the actual code",
      "definition": "string — what this means in the context of this specific codebase"
    }
  ],
  "restricted_write_paths": [
    "string — paths agents must NEVER modify: db migrations, generated code, lock files, secrets"
  ],
  "environment_variables": [
    "string — env var names found by scanning os.getenv / System.getenv / process.env / .env.example"
  ],
  "key_components": [
    {
      "name": "string — class, module, or file name",
      "path": "string — path relative to repo root, must exist in file tree",
      "responsibility": "string — one sentence describing what this component does"
    }
  ],
  "agent_safe_operations": [
    "string — specific operations an AI agent is safely permitted to do in THIS codebase"
  ],
  "agent_forbidden_operations": [
    "string — specific operations an AI agent must never perform in THIS codebase"
  ],
  "test_framework": "string — e.g. pytest, JUnit, Jest, go test, RSpec",
  "test_directory": "string — path to the primary test directory",
  "source_directories": ["string — primary source directories"],
  "module_layout": {"module-name": "path — relative to repo root"},
  "naming_convention": "snake_case|camelCase|PascalCase|kebab-case",
  "structure_type": "monorepo|single-package|multi-module",
  "has_ci": true,
  "has_openapi": false,
  "potential_pitfalls": [
    "string — specific gotchas an AI agent will hit if it doesn't know them"
  ]
}
"""

ANALYSIS_SYSTEM = """\
You are a senior software architect performing a deep analysis of a codebase.
Your output drives the generation of AI agent scaffolding files.
Respond ONLY with a single valid JSON object matching the schema provided.
No markdown fences, no preamble, no explanation — raw JSON only.
All file paths must be relative to the repo root and must actually appear in the file tree.
Mark any value you cannot confirm with "TODO: verify" rather than guessing.\
"""


# ── Phase 1: Collect ──────────────────────────────────────────────────────────

def collect(target: Path, quiet: bool = False) -> dict[str, Any]:
    """
    Mechanically read repository files. No reasoning here — just collection.

    Returns a dict with:
      file_tree    — list of relative paths (up to 300)
      readme       — content of README if present
      config_files — dict of config file name → content
      ci_files     — dict of CI file path → content
      source_files — dict of source file path → content (production code only)
      has_openapi  — bool
    """
    if not quiet:
        print("  📂 Collecting repository files...")

    file_tree: list[str] = []
    source_files: dict[str, str] = {}
    config_files: dict[str, str] = {}
    ci_files: dict[str, str] = {}
    readme: str | None = None
    has_openapi = False

    # Walk the full tree for the file list
    for path in sorted(target.rglob("*")):
        if any(skip in path.parts for skip in SKIP_DIRS):
            continue
        if path.is_file():
            file_tree.append(str(path.relative_to(target)))

    # README
    for name in ["README.md", "README.rst", "README.txt", "README"]:
        p = target / name
        if p.exists():
            readme = p.read_text(errors="ignore")[:6000]
            break

    # Config files
    for name in CONFIG_FILES:
        p = target / name
        if p.exists():
            config_files[name] = p.read_text(errors="ignore")[:3000]

    # CI files
    for ci_dir in [".github/workflows", ".gitea/workflows", ".circleci", ".gitlab"]:
        ci_path = target / ci_dir
        if ci_path.is_dir():
            for f in ci_path.iterdir():
                if f.is_file():
                    ci_files[str(f.relative_to(target))] = f.read_text(errors="ignore")[:2000]

    # OpenAPI
    for pattern in OPENAPI_PATTERNS:
        if list(target.rglob(pattern)):
            has_openapi = True
            break

    # Source files — production code only, skip test directories and agent files
    test_markers = {"test", "tests", "spec", "__tests__", "fixtures", "mocks"}
    collected = 0
    for ext in SOURCE_EXTENSIONS:
        if collected >= MAX_SOURCE_FILES:
            break
        for f in sorted(target.rglob(f"*{ext}")):
            if collected >= MAX_SOURCE_FILES:
                break
            if any(skip in f.parts for skip in SKIP_DIRS):
                continue
            if any(marker in f.parts for marker in test_markers):
                continue
            # Skip AgentReady-generated files — prevents Opus reading its own
            # previous output as source code, which causes hallucinations
            if f.name in SKIP_AGENT_FILES:
                continue
            if any(skip in f.parts for skip in SKIP_AGENT_DIRS):
                continue
            if f.stat().st_size / 1024 > MAX_FILE_KB:
                continue
            try:
                source_files[str(f.relative_to(target))] = f.read_text(errors="ignore")[:3000]
                collected += 1
            except Exception:
                pass

    if not quiet:
        print(f"  📁 {len(file_tree)} files in tree")
        print(f"  📄 {len(source_files)} source files collected")

    return {
        "file_tree": file_tree[:300],
        "readme": readme,
        "config_files": config_files,
        "ci_files": ci_files,
        "source_files": source_files,
        "has_openapi": has_openapi,
    }


# ── Phase 2: LLM Analysis ─────────────────────────────────────────────────────

def analyse(
    client: anthropic.Anthropic,
    repo: dict[str, Any],
    quiet: bool = False,
) -> dict[str, Any]:
    """
    Phase 2: Claude Opus reads the actual code and produces structured
    understanding. This is the intelligence pass — all reasoning happens here.

    Returns the parsed analysis JSON dict.
    """
    if not quiet:
        print(f"  🧠 Running deep code analysis with {ANALYSIS_MODEL}...")
        print("     (this takes ~30–60 seconds)")

    # Build the prompt — assemble all collected content
    parts: list[str] = [
        f"Analyse this repository and return JSON matching this schema:\n{ANALYSIS_SCHEMA}\n"
    ]

    if repo["readme"]:
        parts.append(f"## README\n{repo['readme']}")

    if repo["config_files"]:
        parts.append("## Config & Build Files")
        for name, content in repo["config_files"].items():
            parts.append(f"### {name}\n```\n{content}\n```")

    parts.append("## Complete File Tree\n" + "\n".join(repo["file_tree"]))

    if repo["ci_files"]:
        parts.append("## CI Configuration")
        for name, content in repo["ci_files"].items():
            parts.append(f"### {name}\n```\n{content}\n```")

    if repo["source_files"]:
        parts.append("## Production Source Files")
        for path, content in repo["source_files"].items():
            parts.append(f"### {path}\n```\n{content}\n```")

    prompt = "\n\n".join(parts)

    last_error = None
    for attempt in range(3):
        try:
            response = client.messages.create(
                model=ANALYSIS_MODEL,
                max_tokens=4096,
                system=ANALYSIS_SYSTEM,
                messages=[{"role": "user", "content": prompt}],
            )
            break
        except anthropic.APIStatusError as e:
            if e.status_code != 529:
                raise
            last_error = e
            if attempt < 2:
                wait = 30 * (attempt + 1)
                if not quiet:
                    print(f"  ⚠️  API overloaded, retrying in {wait}s... (attempt {attempt + 1}/3)")
                time.sleep(wait)
            else:
                raise last_error

    raw = response.content[0].text.strip()

    # Strip accidental markdown fences
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:])
    if raw.endswith("```"):
        raw = raw.rsplit("```", 1)[0]

    analysis = json.loads(raw.strip())

    # Stamp has_openapi from static detection if LLM missed it
    analysis.setdefault("has_openapi", repo["has_openapi"])

    if not quiet:
        print(f"  ✓ Language: {analysis.get('primary_language', '?')}")
        print(f"  ✓ Frameworks: {', '.join(analysis.get('frameworks', [])) or 'none'}")
        print(f"  ✓ Entry point: {analysis.get('entry_point', '?')}")
        print(f"  ✓ Domain concepts: {len(analysis.get('domain_concepts', []))}")
        print(f"  ✓ Env vars found: {len(analysis.get('environment_variables', []))}")
        print(f"  ✓ Restricted paths: {len(analysis.get('restricted_write_paths', []))}")
        print(f"  ✓ Potential pitfalls: {len(analysis.get('potential_pitfalls', []))}")

    return analysis


# ── Convenience: run both phases ──────────────────────────────────────────────

def run(
    target: Path,
    client: anthropic.Anthropic,
    quiet: bool = False,
) -> dict[str, Any]:
    """Run Phase 1 (collect) then Phase 2 (LLM analysis) and return analysis."""
    repo = collect(target, quiet=quiet)
    return analyse(client, repo, quiet=quiet)