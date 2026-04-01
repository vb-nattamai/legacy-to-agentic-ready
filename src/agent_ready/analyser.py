"""
AgentReady — LLM Analyser (Phase 1 + Phase 2)

Phase 1: Collect — mechanical file reading, no reasoning.
Phase 2: Analyse — LLM reads the actual code and produces a structured
         JSON understanding of the repository.

Uses LiteLLM — works with Anthropic, OpenAI, and Google providers.
"""

from __future__ import annotations

import json
import random
import time
from pathlib import Path
from typing import Any

# ── Constants ─────────────────────────────────────────────────────────────────

SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "env",
    ".tox", ".mypy_cache", ".pytest_cache", "dist", "build", "target",
    ".next", ".nuxt", "out", "coverage", ".idea", ".vscode",
    ".gradle", ".sass-cache", "tmp", "temp",
}

# AgentReady-generated files — never feed back to Opus as source code
SKIP_AGENT_FILES = {
    "AGENTS.md",
    "CLAUDE.md",
    "agent-context.json",
    "system_prompt.md",
    "mcp.json",
    "AGENTIC_EVAL.md",
    "AGENTIC_READINESS.md",
}

SKIP_AGENT_DIRS = {
    "memory",
    "tools",
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

MAX_SOURCE_FILES = 40
MAX_FILE_KB = 80

ANALYSIS_SCHEMA = """
{
  "project_name": "string",
  "description": "string — what this project does in 1-2 sentences",
  "primary_language": "string — the single dominant language",
  "secondary_languages": ["string"],
  "frameworks": ["string — only frameworks actually found in dependency files"],
  "build_system": "maven|gradle|npm|yarn|pip|go|cargo|make|bundler|unknown",
  "entry_point": "string — main entry point path relative to repo root, must exist in file tree",
  "test_command": "string — exact command to run tests",
  "build_command": "string — exact command to build",
  "install_command": "string — exact command to install dependencies",
  "run_command": "string — exact command to run the application",
  "architecture_summary": "string — 2-3 sentences on the system architecture",
  "domain_concepts": [
    {"term": "string — from actual code", "definition": "string — what it means in this codebase"}
  ],
  "restricted_write_paths": ["string — paths agents must NEVER modify"],
  "environment_variables": ["string — env var names found in the code"],
  "key_components": [
    {"name": "string", "path": "string — must exist in file tree", "responsibility": "string"}
  ],
  "agent_safe_operations": ["string — specific safe operations in THIS codebase"],
  "agent_forbidden_operations": ["string — specific forbidden operations in THIS codebase"],
  "test_framework": "string",
  "test_directory": "string",
  "source_directories": ["string"],
  "module_layout": {"module-name": "path"},
  "naming_convention": "snake_case|camelCase|PascalCase|kebab-case",
  "structure_type": "monorepo|single-package|multi-module",
  "has_ci": true,
  "has_openapi": false,
  "potential_pitfalls": ["string — specific gotchas an AI agent will hit"]
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
    if not quiet:
        print("  📂 Collecting repository files...")

    file_tree: list[str] = []
    source_files: dict[str, str] = {}
    config_files: dict[str, str] = {}
    ci_files: dict[str, str] = {}
    readme: str | None = None
    has_openapi = False

    for path in sorted(target.rglob("*")):
        if any(skip in path.parts for skip in SKIP_DIRS):
            continue
        if path.is_file():
            file_tree.append(str(path.relative_to(target)))

    for name in ["README.md", "README.rst", "README.txt", "README"]:
        p = target / name
        if p.exists():
            readme = p.read_text(errors="ignore")[:6000]
            break

    for name in CONFIG_FILES:
        p = target / name
        if p.exists():
            config_files[name] = p.read_text(errors="ignore")[:3000]

    for ci_dir in [".github/workflows", ".gitea/workflows", ".circleci", ".gitlab"]:
        ci_path = target / ci_dir
        if ci_path.is_dir():
            for f in ci_path.iterdir():
                if f.is_file():
                    ci_files[str(f.relative_to(target))] = f.read_text(errors="ignore")[:2000]

    for pattern in OPENAPI_PATTERNS:
        if list(target.rglob(pattern)):
            has_openapi = True
            break

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
            # Never feed AgentReady's own output back to the analysis model
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

def _llm_call(model: str, system: str, prompt: str, max_tokens: int = 4096) -> str:
    """Single LiteLLM call with retry logic for overloaded errors."""
    try:
        import litellm
        import litellm.exceptions
    except ImportError:
        raise ImportError("litellm not installed. Run: pip install 'agent-ready[ai]'")

    last_error = None
    for attempt in range(3):
        try:
            response = litellm.completion(
                model=model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            # Handle overloaded / service unavailable errors across all providers
            err_str = str(e).lower()
            if any(x in err_str for x in ["529", "overloaded", "service unavailable", "rate limit", "429"]):
                last_error = e
                if attempt < 2:
                    wait = (30 * (attempt + 1)) + random.uniform(0, 5)
                    print(f"  ⚠️  API overloaded, retrying in {int(wait)}s... (attempt {attempt + 1}/3)")
                    time.sleep(wait)
                else:
                    raise last_error
            else:
                raise
    raise last_error


def analyse(
    repo: dict[str, Any],
    analysis_model: str,
    quiet: bool = False,
) -> dict[str, Any]:
    if not quiet:
        print(f"  🧠 Running deep code analysis with {analysis_model}...")
        print("     (this takes ~30–60 seconds)")

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
    raw = _llm_call(model=analysis_model, system=ANALYSIS_SYSTEM, prompt=prompt, max_tokens=4096)

    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:])
    if raw.endswith("```"):
        raw = raw.rsplit("```", 1)[0]

    analysis = json.loads(raw.strip())
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


def run(
    target: Path,
    analysis_model: str,
    quiet: bool = False,
) -> dict[str, Any]:
    """Run Phase 1 (collect) then Phase 2 (LLM analysis) and return analysis."""
    repo = collect(target, quiet=quiet)
    return analyse(repo, analysis_model=analysis_model, quiet=quiet)