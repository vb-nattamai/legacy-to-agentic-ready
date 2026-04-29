from __future__ import annotations

import ast
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from unittest.mock import patch

from agent_ready import generator
from agent_ready.generator import (
    _is_rest_api,
    build_codeowners,
    build_cursorrules,
    build_custom_questions_starter,
    build_dependabot_yml,
    build_openapi_stub,
    build_refresh_context_script,
    detect_hooks,
    detect_skills,
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


def test_codeowners_includes_new_artifacts() -> None:
    out = build_codeowners({})
    for entry in (".cursorrules", "skills/", "hooks/"):
        assert entry in out, f"Missing {entry} in CODEOWNERS"


# ── build_cursorrules ─────────────────────────────────────────────────────────


def test_build_cursorrules_uses_analysis_data() -> None:
    analysis = _analysis_payload()
    out = build_cursorrules(analysis)
    assert "agent-ready" in out
    assert "Python" in out
    assert "pytest -q" in out
    assert "pip install -e ." in out


def test_build_cursorrules_missing_commands_use_fallback() -> None:
    out = build_cursorrules({"project_name": "empty-repo"})
    assert "Not determinable from source" in out


def test_build_cursorrules_todo_verify_uses_fallback() -> None:
    out = build_cursorrules({"test_command": "TODO: verify", "project_name": "x"})
    assert "Not determinable from source" in out


def test_build_cursorrules_includes_restricted_paths() -> None:
    out = build_cursorrules({"restricted_write_paths": [".github/workflows/release.yml"]})
    assert ".github/workflows/release.yml" in out


def test_build_cursorrules_includes_domain_concepts() -> None:
    out = build_cursorrules(
        {"domain_concepts": [{"term": "Scaffold", "definition": "Generated context files"}]}
    )
    assert "Scaffold" in out


def test_build_cursorrules_is_idempotent() -> None:
    analysis = _analysis_payload()
    assert build_cursorrules(analysis) == build_cursorrules(analysis)


# ── detect_skills ─────────────────────────────────────────────────────────────


def test_detect_skills_always_includes_run_tests_and_build() -> None:
    skills = detect_skills({})
    assert "run-tests" in skills
    assert "build" in skills


def test_detect_skills_linter_adds_lint_skill() -> None:
    skills = detect_skills({"frameworks": ["ruff"]})
    assert "lint" in skills


def test_detect_skills_eslint_adds_lint_skill() -> None:
    skills = detect_skills({"frameworks": ["eslint", "react"]})
    assert "lint" in skills


def test_detect_skills_docker_in_frameworks_adds_start_local() -> None:
    skills = detect_skills({"frameworks": ["docker", "fastapi"]})
    assert "start-local" in skills


def test_detect_skills_has_ci_adds_run_ci() -> None:
    skills = detect_skills({"has_ci": True})
    assert "run-ci" in skills


def test_detect_skills_has_openapi_adds_generate_api_docs() -> None:
    skills = detect_skills({"has_openapi": True})
    assert "generate-api-docs" in skills


def test_detect_skills_pip_build_system_adds_add_dependency() -> None:
    skills = detect_skills({"build_system": "pip"})
    assert "add-dependency" in skills


def test_detect_skills_alembic_adds_run_migrations() -> None:
    skills = detect_skills({"frameworks": ["alembic", "sqlalchemy"]})
    assert "run-migrations" in skills


def test_detect_skills_no_duplicates() -> None:
    skills = detect_skills({"frameworks": ["ruff", "ruff"]})
    assert skills.count("lint") == 1


def test_detect_skills_empty_analysis_returns_minimum() -> None:
    skills = detect_skills({})
    assert skills == ["run-tests", "build"]


# ── detect_hooks ──────────────────────────────────────────────────────────────


def test_detect_hooks_always_includes_session_start_and_pre_tool_call() -> None:
    hooks = detect_hooks({})
    assert "session-start" in hooks
    assert "pre-tool-call" in hooks


def test_detect_hooks_test_command_adds_post_test() -> None:
    hooks = detect_hooks({"test_command": "pytest -q"})
    assert "post-test" in hooks


def test_detect_hooks_todo_test_command_excludes_post_test() -> None:
    hooks = detect_hooks({"test_command": "TODO: verify"})
    assert "post-test" not in hooks


def test_detect_hooks_no_test_excludes_post_test() -> None:
    hooks = detect_hooks({})
    assert "post-test" not in hooks


def test_detect_hooks_linter_adds_pre_commit() -> None:
    hooks = detect_hooks({"frameworks": ["ruff"]})
    assert "pre-commit" in hooks


def test_detect_hooks_no_linter_excludes_pre_commit() -> None:
    hooks = detect_hooks({"frameworks": ["pytest"]})
    assert "pre-commit" not in hooks


# ── generate_skill_file / generate_hook_file (mock _call) ────────────────────


def test_generate_skill_file_calls_llm_with_skill_name() -> None:
    with patch("agent_ready.generator._call", return_value="skill content") as mock_call:
        result = generator.generate_skill_file("test-model", "run-tests", _analysis_payload())
    assert result == "skill content"
    mock_call.assert_called_once()
    prompt_arg = mock_call.call_args[0][1]
    assert "run-tests" in prompt_arg


def test_generate_hook_file_calls_llm_with_hook_name() -> None:
    with patch("agent_ready.generator._call", return_value="hook content") as mock_call:
        result = generator.generate_hook_file("test-model", "session-start", _analysis_payload())
    assert result == "hook content"
    mock_call.assert_called_once()
    prompt_arg = mock_call.call_args[0][1]
    assert "session-start" in prompt_arg


def test_llm_generator_skills_writes_files(tmp_path: Path) -> None:
    with patch("agent_ready.generator._call", return_value="# skill"):
        gen = generator.LLMGenerator(
            target=tmp_path,
            analysis=_analysis_payload(),
            generation_model="test-model",
            quiet=True,
        )
        gen._skills()
    skills_dir = tmp_path / "skills"
    assert skills_dir.is_dir()
    assert (skills_dir / "run-tests.md").exists()
    assert (skills_dir / "build.md").exists()


def test_llm_generator_hooks_writes_files(tmp_path: Path) -> None:
    with patch("agent_ready.generator._call", return_value="# hook"):
        gen = generator.LLMGenerator(
            target=tmp_path,
            analysis=_analysis_payload(),
            generation_model="test-model",
            quiet=True,
        )
        gen._hooks()
    hooks_dir = tmp_path / "hooks"
    assert hooks_dir.is_dir()
    assert (hooks_dir / "session-start.md").exists()
    assert (hooks_dir / "pre-tool-call.md").exists()


def test_llm_generator_cursorrules_writes_file(tmp_path: Path) -> None:
    gen = generator.LLMGenerator(
        target=tmp_path,
        analysis=_analysis_payload(),
        generation_model="unused",
        quiet=True,
    )
    gen._cursorrules()
    assert (tmp_path / ".cursorrules").exists()
    content = (tmp_path / ".cursorrules").read_text()
    assert "agent-ready" in content


# ── edge case / hardening tests ───────────────────────────────────────────────


def test_build_cursorrules_empty_analysis_no_silent_blanks() -> None:
    """build_cursorrules must not silently produce empty sections."""
    result = build_cursorrules({})
    assert "Not determinable from source" in result


def test_build_cursorrules_missing_restricted_paths_uses_fallback() -> None:
    """Restricted paths section uses explicit fallback when field is absent."""
    result = build_cursorrules({"project_name": "x"})
    assert "Not determinable from source" in result


def test_build_cursorrules_missing_domain_concepts_uses_fallback() -> None:
    """Domain concepts section uses explicit fallback when field is absent."""
    result = build_cursorrules({})
    assert "Not determinable from source" in result


def test_detect_skills_unexpected_field_types_does_not_crash() -> None:
    """detect_skills must not crash when analysis fields have unexpected types."""
    analysis = {
        "test_command": None,
        "build_system": 42,
        "frameworks": None,
        "file_tree": None,
        "config_files": None,
    }
    result = detect_skills(analysis)
    assert "run-tests" in result
    assert "build" in result


def test_detect_skills_docker_in_file_tree_adds_start_local() -> None:
    """Docker detection via file_tree."""
    result = detect_skills({"file_tree": ["Dockerfile", "src/main.py"]})
    assert "start-local" in result


def test_detect_skills_docker_compose_in_config_files_adds_start_local() -> None:
    """Docker detection via config_files dict keys."""
    result = detect_skills({"config_files": {"docker-compose.yml": "version: '3'"}})
    assert "start-local" in result


def test_skills_generation_failure_does_not_crash_pipeline(tmp_path: Path) -> None:
    """A single skill LLM failure must not crash the pipeline."""
    call_results = [Exception("LLM timeout"), "# build skill content"]

    def side_effect(*args: object, **kwargs: object) -> str:
        result = call_results.pop(0)
        if isinstance(result, Exception):
            raise result
        return str(result)

    with patch("agent_ready.generator._call", side_effect=side_effect):
        gen = generator.LLMGenerator(
            target=tmp_path,
            analysis=_analysis_payload(),
            generation_model="test-model",
            quiet=True,
        )
        gen._skills()  # must not raise

    paths = [p for p, _ in gen.generated]
    # build.md succeeded; run-tests.md was skipped with a warning entry
    assert "skills/build.md" in paths
    assert any("run-tests" in p for p in paths)


def test_hooks_generation_failure_does_not_crash_pipeline(tmp_path: Path) -> None:
    """A single hook LLM failure must not crash the pipeline."""
    call_results = [Exception("LLM timeout"), "# pre-tool-call content"]

    def side_effect(*args: object, **kwargs: object) -> str:
        result = call_results.pop(0)
        if isinstance(result, Exception):
            raise result
        return str(result)

    with patch("agent_ready.generator._call", side_effect=side_effect):
        gen = generator.LLMGenerator(
            target=tmp_path,
            analysis=_analysis_payload(),
            generation_model="test-model",
            quiet=True,
        )
        gen._hooks()  # must not raise

    paths = [p for p, _ in gen.generated]
    assert "hooks/pre-tool-call.md" in paths


def test_generate_hook_file_references_agent_context_when_present() -> None:
    """Hook prompt notes agent-context.json is available when in generated_files."""
    with patch("agent_ready.generator._call", return_value="hook") as mock_call:
        generator.generate_hook_file(
            "model", "session-start", {}, generated_files={"agent-context.json"}
        )
    prompt = mock_call.call_args[0][1]
    assert "Load current state from agent-context.json" in prompt


def test_generate_hook_file_warns_when_agent_context_missing() -> None:
    """Hook prompt warns agent-context.json is not generated when absent."""
    with patch("agent_ready.generator._call", return_value="hook") as mock_call:
        generator.generate_hook_file("model", "session-start", {}, generated_files=set())
    prompt = mock_call.call_args[0][1]
    assert "not yet generated" in prompt


# ── Cost tracking tests ───────────────────────────────────────────────────────


def test_cost_calculation_opus() -> None:
    from agent_ready.generator import _calculate_cost

    cost = _calculate_cost("claude-opus-4-6", 1_000_000, 1_000_000)
    assert cost == 90.0  # $15 input + $75 output per million tokens


def test_cost_calculation_unknown_model_is_zero() -> None:
    from agent_ready.generator import _calculate_cost

    assert _calculate_cost("unknown-model", 1_000_000, 1_000_000) == 0.0


def test_reset_usage_clears_totals() -> None:
    from agent_ready.generator import _usage_totals, get_usage_report, reset_usage

    _usage_totals["calls"] = 99
    _usage_totals["input_tokens"] = 5000
    reset_usage()
    report = get_usage_report()
    assert report["calls"] == 0
    assert report["input_tokens"] == 0
    assert report["estimated_cost_usd"] == 0.0


def test_safety_grounding_rules_include_no_secrets_rule() -> None:
    """_GROUNDING_RULES must include the secrets not_found instruction."""
    from agent_ready.generator import _GROUNDING_RULES

    assert "secrets_present" in _GROUNDING_RULES
    assert "No secrets handling mechanism is configured" in _GROUNDING_RULES


def test_safety_grounding_rules_include_no_destructive_ops_rule() -> None:
    """_GROUNDING_RULES must include the no irreversible operations instruction."""
    from agent_ready.generator import _GROUNDING_RULES

    assert "No irreversible operations are present" in _GROUNDING_RULES
    assert "cost_report.json" in _GROUNDING_RULES


def test_domain_grounding_rules_exclude_health_endpoints() -> None:
    """_GROUNDING_RULES must explicitly exclude /health as a domain concept."""
    from agent_ready.generator import _GROUNDING_RULES

    assert "/health" in _GROUNDING_RULES
    assert "infrastructure" in _GROUNDING_RULES


def test_domain_grounding_rules_include_service_identity() -> None:
    """_GROUNDING_RULES must mention Service Identity extraction from root endpoint."""
    from agent_ready.generator import _GROUNDING_RULES

    assert "Service Identity" in _GROUNDING_RULES


# ── Spec 12: multi-provider pricing and cost report ───────────────────────────


def test_openai_model_pricing() -> None:
    """gpt-5.4-mini cost is calculated correctly."""
    from agent_ready.generator import _calculate_cost

    assert _calculate_cost("gpt-5.4-mini", 1_000_000, 1_000_000) == 0.75


def test_groq_model_pricing() -> None:
    """llama-3.3-70b-versatile cost is calculated correctly (bare name and prefixed)."""
    from agent_ready.generator import _calculate_cost

    assert round(_calculate_cost("llama-3.3-70b-versatile", 1_000_000, 1_000_000), 2) == 1.38
    # Also works with LiteLLM prefix
    assert round(_calculate_cost("groq/llama-3.3-70b-versatile", 1_000_000, 1_000_000), 2) == 1.38


def test_unknown_model_pricing_is_zero() -> None:
    """Unknown model returns zero cost without crashing."""
    from agent_ready.generator import _calculate_cost

    assert _calculate_cost("unknown-model-xyz", 1_000_000, 1_000_000) == 0.0


def test_cost_report_includes_provider() -> None:
    """get_usage_report must include the provider field."""
    from agent_ready.generator import get_usage_report, reset_usage

    reset_usage()
    report = get_usage_report(provider="openai")
    assert report["provider"] == "openai"


def test_cost_report_provider_defaults_to_unknown() -> None:
    """get_usage_report defaults provider to unknown when not specified."""
    from agent_ready.generator import get_usage_report, reset_usage

    reset_usage()
    report = get_usage_report()
    assert "provider" in report
    assert report["provider"] == "unknown"
