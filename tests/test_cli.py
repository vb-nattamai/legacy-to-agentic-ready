"""Basic smoke tests for agent_ready.cli.

Run with:
    python3 -m pytest tests/ -v
or after pip install:
    pytest
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import agent_ready  # noqa: E402
from agent_ready.cli import PROVIDERS, _resolve_models, score  # noqa: E402

# ── Package metadata ───────────────────────────────────────────────────────


def test_version_format():
    parts = agent_ready.__version__.split(".")
    assert len(parts) == 3
    assert all(p.isdigit() for p in parts)


# ── Provider configuration ─────────────────────────────────────────────────

REQUIRED_KEYS = {"analysis", "generation", "evaluation", "api_key_env"}


def test_providers_have_required_keys():
    for name, config in PROVIDERS.items():
        assert REQUIRED_KEYS <= config.keys(), (
            f"Provider '{name}' missing: {REQUIRED_KEYS - config.keys()}"
        )


def test_all_providers_present():
    """Verify the full provider roster is present."""
    expected = {"anthropic", "openai", "google", "groq", "mistral", "together", "ollama"}
    assert expected <= set(PROVIDERS), f"Missing providers: {expected - set(PROVIDERS)}"


def test_anthropic_models():
    assert "opus" in PROVIDERS["anthropic"]["analysis"].lower()
    assert "sonnet" in PROVIDERS["anthropic"]["generation"].lower()
    assert "haiku" in PROVIDERS["anthropic"]["evaluation"].lower()


def test_openai_models():
    assert "gpt" in PROVIDERS["openai"]["analysis"].lower()
    assert "mini" in PROVIDERS["openai"]["generation"].lower()
    assert "nano" in PROVIDERS["openai"]["evaluation"].lower()


def test_google_models():
    assert "gemini" in PROVIDERS["google"]["analysis"].lower()
    assert "lite" in PROVIDERS["google"]["evaluation"].lower()


def test_groq_models():
    assert "llama" in PROVIDERS["groq"]["analysis"].lower()
    assert "llama" in PROVIDERS["groq"]["evaluation"].lower()


def test_mistral_models():
    assert "mistral" in PROVIDERS["mistral"]["analysis"].lower()
    assert "mistral" in PROVIDERS["mistral"]["evaluation"].lower()


def test_together_models():
    assert "qwen" in PROVIDERS["together"]["analysis"].lower()
    assert "llama" in PROVIDERS["together"]["generation"].lower()
    assert "qwen" in PROVIDERS["together"]["evaluation"].lower()


def test_ollama_no_api_key():
    """Ollama is a local provider -- api_key_env must be empty."""
    assert PROVIDERS["ollama"]["api_key_env"] == ""


def test_cloud_providers_have_api_key_env():
    """Every cloud provider must declare a non-empty api_key_env."""
    cloud = {"anthropic", "openai", "google", "groq", "mistral", "together"}
    for name in cloud:
        assert PROVIDERS[name]["api_key_env"], f"Provider '{name}' has empty api_key_env"


# ── _resolve_models ────────────────────────────────────────────────────────


def test_resolve_models_preset():
    """No --model: returns the named provider preset unchanged."""
    result = _resolve_models("anthropic", None)
    assert result is PROVIDERS["anthropic"]


def test_resolve_models_custom_ollama():
    """--model ollama/... should produce empty api_key_env (local provider)."""
    result = _resolve_models("anthropic", "ollama/llama3.2")
    assert result["analysis"] == "ollama/llama3.2"
    assert result["generation"] == "ollama/llama3.2"
    assert result["evaluation"] == "ollama/llama3.2"
    assert result["api_key_env"] == ""


def test_resolve_models_custom_groq():
    """--model groq/... should resolve to GROQ_API_KEY."""
    result = _resolve_models("anthropic", "groq/mixtral-8x7b-32768")
    assert result["analysis"] == "groq/mixtral-8x7b-32768"
    assert result["api_key_env"] == "GROQ_API_KEY"


def test_resolve_models_custom_openai_prefix():
    """--model gpt-... (no slash) prefix maps to OPENAI_API_KEY."""
    result = _resolve_models("anthropic", "gpt-4-turbo")
    assert result["api_key_env"] == "OPENAI_API_KEY"


def test_resolve_models_custom_unknown_prefix():
    """Unknown prefixes fall back to PREFIX_API_KEY."""
    result = _resolve_models("anthropic", "bedrock/anthropic.claude-3-5-sonnet")
    assert result["analysis"] == "bedrock/anthropic.claude-3-5-sonnet"
    assert result["api_key_env"] == "BEDROCK_API_KEY"


def test_resolve_models_all_phases_same():
    """--model always maps all three phases to the same model string."""
    m = "mistral/mistral-large-latest"
    result = _resolve_models("openai", m)
    assert result["analysis"] == result["generation"] == result["evaluation"] == m


# ── Scoring ────────────────────────────────────────────────────────────────


def test_score_returns_dict(tmp_path):
    result = score(tmp_path)
    assert "score" in result
    assert "max" in result
    assert "rows" in result
    assert isinstance(result["score"], int)
    assert result["score"] <= result["max"]


def test_score_zero_on_empty_dir(tmp_path):
    assert score(tmp_path)["score"] == 0


def test_score_max_is_100(tmp_path):
    assert score(tmp_path)["max"] == 100


def test_score_improves_with_agent_context(tmp_path):
    base = score(tmp_path)
    context = {
        "static": {
            "project_name": "test-project",
            "primary_language": "Python",
            "entry_point": "main.py",
            "test_command": "pytest",
            "restricted_write_paths": [".env"],
            "environment_variables": ["DATABASE_URL"],
            "domain_concepts": ["Order: a customer order", "Item: a menu item", "Driver: a driver"],
        },
        "dynamic": {"last_scanned": "2026-01-01T00:00:00Z"},
    }
    (tmp_path / "agent-context.json").write_text(json.dumps(context))
    (tmp_path / "main.py").write_text("# entry point")
    assert score(tmp_path)["score"] > base["score"]


def test_score_with_all_files(tmp_path):
    context = {
        "static": {
            "project_name": "full-project",
            "primary_language": "Python",
            "entry_point": "main.py",
            "test_command": "pytest",
            "restricted_write_paths": [".env"],
            "environment_variables": ["DATABASE_URL"],
            "domain_concepts": ["A: a", "B: b", "C: c"],
        },
        "dynamic": {"last_scanned": "2026-01-01T00:00:00Z"},
    }
    (tmp_path / "agent-context.json").write_text(json.dumps(context))
    (tmp_path / "main.py").write_text("# entry")
    (tmp_path / "CLAUDE.md").write_text("# Claude")
    (tmp_path / "AGENTS.md").write_text("# Agents")
    (tmp_path / "system_prompt.md").write_text("# System")
    tools = tmp_path / "tools"
    tools.mkdir()
    (tools / "example.py").write_text("# tool")
    (tmp_path / "openapi.yaml").write_text("openapi: 3.0.0")
    gh = tmp_path / ".github" / "workflows"
    gh.mkdir(parents=True)
    (gh / "ci.yml").write_text("name: CI")

    assert score(tmp_path)["score"] >= 90
