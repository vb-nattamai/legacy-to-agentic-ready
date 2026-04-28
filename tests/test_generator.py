from __future__ import annotations

import ast
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from agent_ready import generator
from agent_ready.generator import (
    _is_rest_api,
    build_codeowners,
    build_custom_questions_starter,
    build_dependabot_yml,
    build_openapi_stub,
    build_refresh_context_script,
)


def _analysis_payload() -> dict[str, object]:
    return {
        "project_name": "agent-ready",
        "description": "Transforms repos into agent-ready scaffolding.",
        "primary_language": "Python",
        "frameworks": ["pytest"],
        "entry_point": "src/agent_ready/cli.py",
        "test_command": "pytest -q",
        "restricted_write_paths": [".github/workflows/release.yml"],
        "environment_variables": ["OPENAI_API_KEY"],
        "domain_concepts": [{"term": "Scaffold", "definition": "Generated context files"}],
        "secondary_languages": [],
        "build_system": "pip",
        "build_command": "python -m build",
        "install_command": "pip install -e .",
        "run_command": "agent-ready --target .",
        "test_framework": "pytest",
        "test_directory": "tests",
        "source_directories": ["src/agent_ready"],
        "module_layout": {"agent_ready": "src/agent_ready"},
        "architecture_summary": "CLI orchestrates analyse/generate/eval phases.",
        "key_components": [
            {"name": "cli", "path": "src/agent_ready/cli.py", "responsibility": "entry"}
        ],
        "agent_safe_operations": ["edit docs"],
        "agent_forbidden_operations": ["commit secrets"],
        "potential_pitfalls": ["Do not overwrite static context"],
        "naming_convention": "snake_case",
        "structure_type": "single-package",
        "has_ci": True,
        "has_openapi": False,
    }


def test_build_agent_context_preserves_existing_static() -> None:
    analysis = _analysis_payload()
    existing_static = {
        "project_name": "custom-name",
        "description": "manual description",
        "primary_language": "Python",
        "frameworks": ["manual-framework"],
        "entry_point": "custom_entry.py",
        "test_command": "custom-test",
        "restricted_write_paths": ["manual/path"],
        "environment_variables": ["MANUAL_ENV"],
        "domain_concepts": ["Manual: concept"],
    }

    rendered = generator.build_agent_context(analysis, existing_static=existing_static)
    parsed = json.loads(rendered)

    assert parsed["static"] == existing_static
    assert parsed["dynamic"]["build_system"] == "pip"
    assert parsed["dynamic"]["run_command"] == "agent-ready --target ."
    assert parsed["dynamic"]["has_ci"] is True
    assert parsed["dynamic"]["has_openapi"] is False
    assert datetime.fromisoformat(parsed["dynamic"]["last_scanned"])


def test_generate_only_context_updates_dynamic_without_clobbering_static(tmp_path: Path) -> None:
    existing_context = {
        "static": {
            "project_name": "keep-me",
            "description": "human-edited",
            "primary_language": "Python",
            "frameworks": ["manual-framework"],
            "entry_point": "manual.py",
            "test_command": "manual-test",
            "restricted_write_paths": ["manual/path"],
            "environment_variables": ["MANUAL_ENV"],
            "domain_concepts": ["Manual: concept"],
        },
        "dynamic": {
            "last_scanned": "2020-01-01T00:00:00+00:00",
            "build_system": "unknown",
        },
    }
    (tmp_path / "agent-context.json").write_text(json.dumps(existing_context), encoding="utf-8")

    gen = generator.LLMGenerator(
        target=tmp_path,
        analysis=_analysis_payload(),
        generation_model="unused-for-context-only",
        quiet=True,
    )
    generated = gen.generate_only("context")
    updated = json.loads((tmp_path / "agent-context.json").read_text(encoding="utf-8"))

    assert updated["static"] == existing_context["static"]
    assert updated["dynamic"]["build_system"] == "pip"
    assert updated["dynamic"]["last_scanned"] != existing_context["dynamic"]["last_scanned"]
    assert any(
        path == "agent-context.json" and status.startswith("🔄") for path, status in generated
    )


# ── build_refresh_context_script ─────────────────────────────────────────────


def test_refresh_context_script_is_valid_python() -> None:
    script = build_refresh_context_script(_analysis_payload())
    ast.parse(script)  # raises SyntaxError if invalid


def test_refresh_context_script_contains_project_name() -> None:
    script = build_refresh_context_script({"project_name": "my-cool-api"})
    assert "my-cool-api" in script


def test_refresh_context_script_contains_cli_invocation() -> None:
    script = build_refresh_context_script(_analysis_payload())
    assert "agent_ready.cli" in script
    assert "--only" in script
    assert "context" in script


def test_generate_only_context_also_writes_refresh_script(tmp_path: Path) -> None:
    gen = generator.LLMGenerator(
        target=tmp_path,
        analysis=_analysis_payload(),
        generation_model="unused",
        quiet=True,
    )
    generated = gen.generate_only("context")
    paths = [p for p, _ in generated]
    assert "tools/refresh_context.py" in paths
    assert (tmp_path / "tools" / "refresh_context.py").exists()


# ── build_dependabot_yml ──────────────────────────────────────────────────────


def test_dependabot_pip_ecosystem() -> None:
    out = build_dependabot_yml({"build_system": "pip", "primary_language": "python"})
    assert "package-ecosystem: pip" in out
    assert "github-actions" in out


def test_dependabot_npm_ecosystem() -> None:
    out = build_dependabot_yml({"build_system": "npm", "primary_language": "javascript"})
    assert "package-ecosystem: npm" in out


def test_dependabot_unknown_falls_back_to_pip() -> None:
    out = build_dependabot_yml({"build_system": "unknown", "primary_language": "cobol"})
    assert "package-ecosystem: pip" in out


def test_dependabot_always_includes_github_actions() -> None:
    for build_sys in ("pip", "npm", "maven", "go"):
        out = build_dependabot_yml({"build_system": build_sys})
        assert "github-actions" in out, f"Missing github-actions for {build_sys}"


# ── build_custom_questions_starter ───────────────────────────────────────────


def test_custom_questions_starter_is_valid_json() -> None:
    out = build_custom_questions_starter(_analysis_payload())
    parsed = json.loads(out)
    assert "questions" in parsed
    assert len(parsed["questions"]) >= 1


def test_custom_questions_starter_questions_are_prefixed() -> None:
    """All question fields should use underscore prefix — disabled by default."""
    out = build_custom_questions_starter(_analysis_payload())
    parsed = json.loads(out)
    for q in parsed["questions"]:
        for key in q:
            if key != "_comment":
                assert key.startswith("_"), f"Field {key!r} should be prefixed with '_'"


def test_custom_questions_starter_contains_project_name() -> None:
    out = build_custom_questions_starter({"project_name": "my-service", "primary_language": "go"})
    assert "my-service" in out


# ── build_openapi_stub / _is_rest_api ─────────────────────────────────────────


def test_is_rest_api_detects_flask() -> None:
    assert _is_rest_api({"frameworks": ["flask"]})


def test_is_rest_api_detects_express() -> None:
    assert _is_rest_api({"frameworks": ["express"]})


def test_is_rest_api_false_for_cli_tool() -> None:
    assert not _is_rest_api({"frameworks": ["click", "typer"]})


def test_is_rest_api_false_for_no_frameworks() -> None:
    assert not _is_rest_api({})


def test_openapi_stub_is_valid_yaml() -> None:
    import yaml

    out = build_openapi_stub(
        {"project_name": "test-api", "frameworks": ["fastapi"], "primary_language": "python"}
    )
    # strip the comment header before parsing
    body = "\n".join(line for line in out.splitlines() if not line.startswith("#"))
    parsed = yaml.safe_load(body)
    assert parsed["openapi"] == "3.1.0"
    assert "/health" in parsed["paths"]


def test_openapi_stub_only_generated_for_rest_api(tmp_path: Path) -> None:
    analysis = _analysis_payload()
    analysis["frameworks"] = ["click"]  # not a REST framework
    analysis["has_openapi"] = False

    gen = generator.LLMGenerator(
        target=tmp_path, analysis=analysis, generation_model="unused", quiet=True
    )
    # only test the openapi-specific method — avoids LLM calls
    gen._openapi_stub()
    paths = [p for p, _ in gen.generated]
    assert "openapi.yaml" not in paths


def test_openapi_stub_skipped_when_already_has_openapi(tmp_path: Path) -> None:
    analysis = _analysis_payload()
    analysis["frameworks"] = ["flask"]
    analysis["has_openapi"] = True  # already exists

    gen = generator.LLMGenerator(
        target=tmp_path, analysis=analysis, generation_model="unused", quiet=True
    )
    gen._openapi_stub()
    paths = [p for p, _ in gen.generated]
    assert "openapi.yaml" not in paths


# ── build_codeowners ──────────────────────────────────────────────────────────


def test_codeowners_includes_key_generated_files() -> None:
    out = build_codeowners({})
    for filename in (
        "agent-context.json",
        "AGENTS.md",
        "CLAUDE.md",
        "memory/",
        ".github/workflows/",
    ):
        assert filename in out, f"Missing {filename} in CODEOWNERS"


def test_codeowners_includes_restricted_paths() -> None:
    out = build_codeowners({"restricted_write_paths": [".github/workflows", "src/migrations"]})
    assert "src/migrations/" in out


def test_codeowners_is_not_empty() -> None:
    out = build_codeowners(_analysis_payload())
    assert len(out.strip()) > 0
