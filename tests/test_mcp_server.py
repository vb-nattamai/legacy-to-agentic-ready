"""Tests for the AgentReady MCP server — helpers and tool logic."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from agent_ready.mcp_server import _check_api_key, _format_score, _models, _resolve

# ── Mock Context ───────────────────────────────────────────────────────────────


class MockContext:
    """Minimal async stand-in for mcp.server.fastmcp.Context."""

    async def info(self, msg: str) -> None:
        pass

    async def report_progress(self, current: int, total: int, msg: str = "") -> None:
        pass


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
    assert (
        "scaffold" in tools["transform"].description.lower()
        or "transform" in tools["transform"].description.lower()
    )


def test_review_pr_tool_has_description() -> None:
    from agent_ready.mcp_server import mcp

    tools = {t.name: t for t in mcp._tool_manager.list_tools()}
    assert "review" in tools["review_pr"].description.lower()


# ── async tool bodies ─────────────────────────────────────────────────────────


def test_score_async_tool(tmp_path: Path) -> None:
    """score tool (async) returns formatted output with score line."""
    from agent_ready.mcp_server import score as mcp_score

    result = asyncio.run(mcp_score(str(tmp_path)))
    assert "/ 100" in result


def test_score_async_tool_with_scaffolding(tmp_path: Path) -> None:
    """score tool returns higher score when files exist."""
    (tmp_path / "AGENTS.md").write_text("# A")
    (tmp_path / "CLAUDE.md").write_text("# C")
    from agent_ready.mcp_server import score as mcp_score

    result = asyncio.run(mcp_score(str(tmp_path)))
    assert "✅ AGENTS.md" in result
    assert "✅ CLAUDE.md" in result


def test_transform_async_tool_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """transform tool calls pipeline and returns score summary."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

    fake_generated = [("AGENTS.md", "written"), ("CLAUDE.md", "written")]
    fake_score = {"score": 80, "max": 100, "rows": [("✅ AGENTS.md", "+10")]}

    with (
        patch("agent_ready.cli._run_llm_pipeline", return_value=fake_generated),
        patch("agent_ready.mcp_server._score_fn", fake_score, create=True),
        patch("agent_ready.cli.score", return_value=fake_score),
    ):
        from agent_ready.mcp_server import transform

        ctx = MockContext()
        result = asyncio.run(transform(ctx, str(tmp_path), provider="anthropic"))

    assert "Transformation complete" in result
    assert "AGENTS.md" in result
    assert "80 / 100" in result


def test_transform_async_tool_dry_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """transform dry_run changes output header."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

    with (
        patch("agent_ready.cli._run_llm_pipeline", return_value=[("AGENTS.md", "written")]),
        patch("agent_ready.cli.score", return_value={"score": 10, "max": 100, "rows": []}),
    ):
        from agent_ready.mcp_server import transform

        ctx = MockContext()
        result = asyncio.run(transform(ctx, str(tmp_path), dry_run=True))

    assert "Dry-run" in result


def test_transform_async_tool_skipped_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """transform shows skip icon for files with non-written status."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

    with (
        patch(
            "agent_ready.cli._run_llm_pipeline",
            return_value=[("AGENTS.md", "skipped")],
        ),
        patch("agent_ready.cli.score", return_value={"score": 0, "max": 100, "rows": []}),
    ):
        from agent_ready.mcp_server import transform

        ctx = MockContext()
        result = asyncio.run(transform(ctx, str(tmp_path)))

    assert "⏭️" in result


def test_evaluate_async_tool_pass(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """evaluate tool returns pass summary when eval passes."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

    fake_result = {
        "passed": True,
        "pass_rate": 0.93,
        "context_score": 9.1,
        "baseline_score": 2.3,
        "category_breakdown": {
            "commands": {"context_avg": 9.1, "pass_rate": 1.0, "question_count": 3}
        },
    }

    with (
        patch("agent_ready.evaluator.run_eval", return_value=fake_result),
        patch("agent_ready.evaluator.save_eval_report", return_value=tmp_path / "AGENTIC_EVAL.md"),
    ):
        from agent_ready.mcp_server import evaluate

        ctx = MockContext()
        result = asyncio.run(evaluate(ctx, str(tmp_path)))

    assert "✅" in result
    assert "93%" in result
    assert "commands" in result


def test_evaluate_async_tool_fail_level(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """evaluate tool appends failure message when below fail_level."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

    fake_result = {
        "passed": False,
        "pass_rate": 0.4,
        "context_score": 4.0,
        "baseline_score": 1.0,
    }

    with (
        patch("agent_ready.evaluator.run_eval", return_value=fake_result),
        patch("agent_ready.evaluator.save_eval_report", return_value=tmp_path / "AGENTIC_EVAL.md"),
    ):
        from agent_ready.mcp_server import evaluate

        ctx = MockContext()
        result = asyncio.run(evaluate(ctx, str(tmp_path), fail_level=0.8))

    assert "❌" in result
    assert "below" in result


def test_review_pr_async_tool_posted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """review_pr tool reports posted when reviewer.run returns posted=True."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

    fake_result = {"decision": "APPROVE", "body": "Looks good!", "posted": True}

    with patch("agent_ready.reviewer.run", return_value=fake_result):
        from agent_ready.mcp_server import review_pr

        ctx = MockContext()
        result = asyncio.run(review_pr(ctx, str(tmp_path), pr_number=42))

    assert "posted to GitHub" in result
    assert "APPROVE" in result
    assert "Looks good!" in result


def test_review_pr_async_tool_dry_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """review_pr dry_run mode does not claim to post."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

    fake_result = {"decision": "REQUEST_CHANGES", "body": "Fix this.", "posted": False}

    with patch("agent_ready.reviewer.run", return_value=fake_result):
        from agent_ready.mcp_server import review_pr

        ctx = MockContext()
        result = asyncio.run(review_pr(ctx, str(tmp_path), pr_number=7, dry_run=True))

    assert "Dry-run" in result
    assert "REQUEST_CHANGES" in result


def test_review_pr_async_tool_not_posted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """review_pr shows warning when posted=False and not dry_run."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

    fake_result = {"decision": "COMMENT", "body": "See notes.", "posted": False}

    with patch("agent_ready.reviewer.run", return_value=fake_result):
        from agent_ready.mcp_server import review_pr

        ctx = MockContext()
        result = asyncio.run(review_pr(ctx, str(tmp_path), pr_number=1, dry_run=False))

    assert "not posted" in result.lower() or "⚠️" in result


def test_main_callable() -> None:
    """main() exists and is callable (doesn't actually start server)."""
    from agent_ready.mcp_server import main

    assert callable(main)
