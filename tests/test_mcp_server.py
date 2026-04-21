"""Tests for the AgentReady MCP server — helpers and tool logic."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from agent_ready.mcp_server import _check_api_key, _format_score, _models, _resolve


# ── _resolve ──────────────────────────────────────────────────────────────────


def test_resolve_returns_absolute_path(tmp_path: Path) -> None:
    result = _resolve(str(tmp_path))
    assert result == tmp_path.resolve()
    assert result.is_absolute()


def test_resolve_raises_on_missing_dir(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="not found"):
        _resolve(str(tmp_path / "does_not_exist"))


def test_resolve_raises_on_file_not_dir(tmp_path: Path) -> None:
    f = tmp_path / "file.txt"
    f.write_text("x")
    with pytest.raises(ValueError, match="not found"):
        _resolve(str(f))


def test_resolve_expands_home() -> None:
    home = Path.home()
    result = _resolve("~")
    assert result == home


# ── _format_score ─────────────────────────────────────────────────────────────


def test_format_score_perfect() -> None:
    result = {
        "score": 100,
        "max": 100,
        "rows": [("✅ agent-context.json", "+10"), ("✅ CLAUDE.md", "+10")],
    }
    output = _format_score(result)
    assert "100 / 100" in output
    assert "agent-context.json" in output
    assert "+10" in output


def test_format_score_partial() -> None:
    result = {
        "score": 80,
        "max": 100,
        "rows": [("✅ agent-context.json", "+10"), ("⬜ tools/ has files", "+ 0")],
    }
    output = _format_score(result)
    assert "80 / 100" in output
    assert "⬜ tools/ has files" in output
    assert "+ 0" in output


def test_format_score_zero() -> None:
    result = {"score": 0, "max": 100, "rows": []}
    output = _format_score(result)
    assert "0 / 100" in output


# ── _models ───────────────────────────────────────────────────────────────────


def test_models_returns_dict_with_required_keys() -> None:
    m = _models("anthropic")
    assert "analysis" in m
    assert "generation" in m
    assert "evaluation" in m
    assert "api_key_env" in m


def test_models_anthropic_uses_correct_env_var() -> None:
    m = _models("anthropic")
    assert m["api_key_env"] == "ANTHROPIC_API_KEY"


def test_models_ollama_has_no_api_key() -> None:
    m = _models("ollama")
    assert m["api_key_env"] == ""


def test_models_openai_uses_correct_env_var() -> None:
    m = _models("openai")
    assert m["api_key_env"] == "OPENAI_API_KEY"


# ── _check_api_key ────────────────────────────────────────────────────────────


def test_check_api_key_passes_when_env_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    _check_api_key({"api_key_env": "ANTHROPIC_API_KEY"})  # should not raise


def test_check_api_key_raises_when_env_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        _check_api_key({"api_key_env": "ANTHROPIC_API_KEY"})


def test_check_api_key_passes_for_local_provider() -> None:
    # ollama has empty api_key_env — should never raise regardless of env
    _check_api_key({"api_key_env": ""})


# ── score tool (synchronous inner logic) ──────────────────────────────────────


def test_score_tool_integration(tmp_path: Path) -> None:
    """score tool returns formatted string with score line."""
    # Create minimal scaffolding so score isn't 0
    (tmp_path / "AGENTS.md").write_text("# AGENTS")
    (tmp_path / "CLAUDE.md").write_text("# CLAUDE")
    (tmp_path / "agent-context.json").write_text(
        '{"static":{"entry_point":"","test_command":"pytest",'
        '"restricted_write_paths":["a"],"environment_variables":["B"],'
        '"domain_concepts":["x","y","z"]}}'
    )
    from agent_ready.cli import score as _score

    result = _score(tmp_path)
    output = _format_score(result)
    assert "/ 100" in output
    assert "AGENTS.md" in output


# ── mcp_server module structure ───────────────────────────────────────────────


def test_mcp_server_has_four_tools() -> None:
    from agent_ready.mcp_server import mcp

    tools = mcp._tool_manager.list_tools()
    names = {t.name for t in tools}
    assert names == {"transform", "score", "evaluate", "review_pr"}


def test_mcp_server_name() -> None:
    from agent_ready.mcp_server import mcp

    assert mcp.name == "agent-ready"


def test_transform_tool_has_description() -> None:
    from agent_ready.mcp_server import mcp

    tools = {t.name: t for t in mcp._tool_manager.list_tools()}
    assert "scaffold" in tools["transform"].description.lower() or \
           "transform" in tools["transform"].description.lower()


def test_review_pr_tool_has_description() -> None:
    from agent_ready.mcp_server import mcp

    tools = {t.name: t for t in mcp._tool_manager.list_tools()}
    assert "review" in tools["review_pr"].description.lower()
