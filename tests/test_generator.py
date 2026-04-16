from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from agent_ready import generator


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
