"""Tests for golden-set eval v2: golden set loader, ground truth extractor, run_eval."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

# ── Golden set loader ─────────────────────────────────────────────────────────


def test_load_golden_questions_base_only() -> None:
    """Unknown language returns only the base set."""
    from agent_ready.evaluator import load_golden_questions

    qs = load_golden_questions("cobol")
    assert len(qs) > 0
    ids = {q["id"] for q in qs}
    assert "base_cmd_001" in ids
    assert "base_saf_001" in ids
    assert "base_arc_001" in ids


def test_load_golden_questions_python_overlay() -> None:
    """Python language includes base + python overlay questions."""
    from agent_ready.evaluator import load_golden_questions

    base_qs = load_golden_questions("cobol")
    py_qs = load_golden_questions("python")

    # Python set is strictly larger
    assert len(py_qs) > len(base_qs)
    # Python-specific question is included
    ids = {q["id"] for q in py_qs}
    assert "py_cmd_001" in ids
    assert "py_adv_001" in ids
    # Base questions still present
    assert "base_cmd_001" in ids


def test_load_golden_questions_javascript_overlay() -> None:
    """JavaScript and TypeScript both load the JS overlay."""
    from agent_ready.evaluator import load_golden_questions

    js_qs = load_golden_questions("javascript")
    ts_qs = load_golden_questions("typescript")

    js_ids = {q["id"] for q in js_qs}
    ts_ids = {q["id"] for q in ts_qs}

    assert "js_cmd_001" in js_ids
    assert "js_cmd_001" in ts_ids  # typescript maps to javascript


def test_load_golden_questions_java_overlay() -> None:
    from agent_ready.evaluator import load_golden_questions

    qs = load_golden_questions("java")
    ids = {q["id"] for q in qs}
    assert "java_cmd_001" in ids


def test_load_golden_questions_go_overlay() -> None:
    from agent_ready.evaluator import load_golden_questions

    qs = load_golden_questions("go")
    ids = {q["id"] for q in qs}
    assert "go_cmd_001" in ids


def test_load_golden_questions_extra_appended() -> None:
    """Extra questions are appended after base+overlay."""
    from agent_ready.evaluator import load_golden_questions

    custom = [{"id": "custom_001", "category": "domain", "prompt": "custom?"}]
    qs = load_golden_questions("python", extra_questions=custom)
    assert qs[-1]["id"] == "custom_001"


def test_golden_questions_have_required_fields() -> None:
    """Every golden question must have id, category, prompt, ground_truth_extraction."""
    from agent_ready.evaluator import load_golden_questions

    for lang in ["python", "javascript", "java", "go", "cobol"]:
        for q in load_golden_questions(lang):
            assert "id" in q, f"Missing 'id' in {q}"
            assert "category" in q, f"Missing 'category' in {q}"
            assert "prompt" in q, f"Missing 'prompt' in {q}"
            assert "ground_truth_extraction" in q, f"Missing extraction in {q['id']}"
            assert "evaluation_criteria" in q, f"Missing criteria in {q['id']}"
            assert "pass_threshold" in q, f"Missing pass_threshold in {q['id']}"


def test_load_custom_questions_missing(tmp_path: Path) -> None:
    """Returns empty list when .agent-ready/custom_questions.json doesn't exist."""
    from agent_ready.evaluator import _load_custom_questions

    result = _load_custom_questions(tmp_path)
    assert result == []


def test_load_custom_questions_present(tmp_path: Path) -> None:
    """Loads custom questions from .agent-ready/custom_questions.json."""
    from agent_ready.evaluator import _load_custom_questions

    custom_dir = tmp_path / ".agent-ready"
    custom_dir.mkdir()
    custom_qs = [{"id": "repo_001", "category": "domain", "prompt": "What does X do?"}]
    (custom_dir / "custom_questions.json").write_text(json.dumps(custom_qs))

    result = _load_custom_questions(tmp_path)
    assert len(result) == 1
    assert result[0]["id"] == "repo_001"


# ── Ground truth extractor ────────────────────────────────────────────────────


def test_static_extract_jsonpath(tmp_path: Path) -> None:
    """Extracts test command from package.json via jsonpath."""
    from agent_ready.ground_truth import extract_ground_truth

    (tmp_path / "package.json").write_text(json.dumps({"scripts": {"test": "jest --coverage"}}))
    q = {
        "id": "test_001",
        "prompt": "test command?",
        "ground_truth_extraction": {
            "method": "static_then_llm",
            "static_sources": [{"file": "package.json", "jsonpath": "scripts.test"}],
            "llm_prompt": "test command?",
        },
        "evaluation_criteria": "...",
    }
    gt = extract_ground_truth(tmp_path, q, {}, "claude-haiku-4-5")
    assert "jest" in gt


def test_static_extract_file_exists(tmp_path: Path) -> None:
    """Returns fixed string when a file exists (lockfile detection)."""
    from agent_ready.ground_truth import extract_ground_truth

    (tmp_path / "yarn.lock").write_text("# yarn lock")
    q = {
        "id": "test_002",
        "prompt": "package manager?",
        "ground_truth_extraction": {
            "method": "static_then_llm",
            "static_sources": [{"file": "yarn.lock", "exists": "yarn"}],
            "llm_prompt": "package manager?",
        },
        "evaluation_criteria": "...",
    }
    gt = extract_ground_truth(tmp_path, q, {}, "claude-haiku-4-5")
    assert gt == "yarn"


def test_static_extract_grep(tmp_path: Path) -> None:
    """Finds matching line via grep pattern."""
    from agent_ready.ground_truth import extract_ground_truth

    (tmp_path / "Makefile").write_text("test:\n\tpytest tests/\n\nbuild:\n\tpip install .")
    q = {
        "id": "test_003",
        "prompt": "test target?",
        "ground_truth_extraction": {
            "method": "static_then_llm",
            "static_sources": [{"file": "Makefile", "pattern": "^test:"}],
            "llm_prompt": "test target?",
        },
        "evaluation_criteria": "...",
    }
    gt = extract_ground_truth(tmp_path, q, {}, "claude-haiku-4-5")
    assert "test:" in gt


def test_static_extract_read(tmp_path: Path) -> None:
    """Returns full file content when read=True."""
    from agent_ready.ground_truth import extract_ground_truth

    (tmp_path / ".python-version").write_text("3.11.4")
    q = {
        "id": "test_004",
        "prompt": "python version?",
        "ground_truth_extraction": {
            "method": "static_then_llm",
            "static_sources": [{"file": ".python-version", "read": True}],
            "llm_prompt": "python version?",
        },
        "evaluation_criteria": "...",
    }
    gt = extract_ground_truth(tmp_path, q, {}, "claude-haiku-4-5")
    assert "3.11" in gt


def test_static_extract_missing_falls_back_to_llm(tmp_path: Path) -> None:
    """When static sources fail, calls LLM extractor."""
    from agent_ready.ground_truth import extract_ground_truth

    source_files = {"README.md": "Run tests with: pytest tests/"}
    q = {
        "id": "test_005",
        "prompt": "test command?",
        "ground_truth_extraction": {
            "method": "static_then_llm",
            "static_sources": [{"file": "nonexistent.json", "jsonpath": "scripts.test"}],
            "llm_prompt": "What command runs the tests?",
        },
        "evaluation_criteria": "...",
    }

    with patch("agent_ready.ground_truth._llm_extract", return_value="pytest tests/") as mock_llm:
        gt = extract_ground_truth(tmp_path, q, source_files, "claude-haiku-4-5")

    mock_llm.assert_called_once()
    assert gt == "pytest tests/"


def test_extract_all_returns_dict(tmp_path: Path) -> None:
    """extract_all returns a dict keyed by question id."""
    from agent_ready.ground_truth import extract_all

    (tmp_path / "package.json").write_text(json.dumps({"scripts": {"test": "npm test"}}))
    questions = [
        {
            "id": "q1",
            "prompt": "test?",
            "ground_truth_extraction": {
                "method": "static_then_llm",
                "static_sources": [{"file": "package.json", "jsonpath": "scripts.test"}],
                "llm_prompt": "test?",
            },
            "evaluation_criteria": "...",
        }
    ]
    result = extract_all(tmp_path, questions, {}, "claude-haiku-4-5", quiet=True)
    assert "q1" in result
    assert "npm test" in result["q1"]


# ── run_eval v2 integration ───────────────────────────────────────────────────


def test_resolve_baseline_model_default() -> None:
    """Default baseline for anthropic model is haiku."""
    from agent_ready.evaluator import _resolve_baseline_model

    result = _resolve_baseline_model("claude-opus-4-6", None)
    assert "haiku" in result


def test_resolve_baseline_model_explicit() -> None:
    """Explicit baseline_model overrides default."""
    from agent_ready.evaluator import _resolve_baseline_model

    result = _resolve_baseline_model("claude-opus-4-6", "gpt-4o-mini")
    assert result == "gpt-4o-mini"


def test_resolve_baseline_model_openai() -> None:
    from agent_ready.evaluator import _resolve_baseline_model

    result = _resolve_baseline_model("gpt-5.4", None)
    assert "mini" in result or "nano" in result or "gpt" in result


def test_run_eval_v2_result_has_new_fields(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """run_eval v2 result includes eval_version, baseline_model, ground_truth_source."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

    fake_context = tmp_path / "agent-context.json"
    fake_context.write_text(json.dumps({"primary_language": "python", "static": {}, "dynamic": {}}))
    (tmp_path / "AGENTS.md").write_text("# Agents")
    (tmp_path / "CLAUDE.md").write_text("# Claude")

    fake_questions = [
        {
            "id": "base_cmd_001",
            "category": "commands",
            "difficulty": "medium",
            "prompt": "What is the test command?",
            "pass_threshold": 7.5,
            "ground_truth_extraction": {
                "method": "static_then_llm",
                "static_sources": [],
                "llm_prompt": "test command?",
            },
            "evaluation_criteria": "Must contain test command.",
            "ground_truth": "pytest tests/",
        }
    ]

    fake_judgment = {
        "score": 9,
        "correct": True,
        "reasoning": "correct",
        "hallucinated": False,
        "key_missing": "",
    }
    fake_panel = {
        "score": 9.0,
        "correct": True,
        "reasoning": "correct",
        "hallucinated": False,
        "key_missing": "",
        "panel_vote": "3/3",
        "panel": [],
    }

    with (
        patch("agent_ready.evaluator.load_golden_questions", return_value=fake_questions),
        patch(
            "agent_ready.ground_truth.extract_all", return_value={"base_cmd_001": "pytest tests/"}
        ),
        patch(
            "agent_ready.analyser.collect",
            return_value={"source_files": {}, "primary_language": "python"},
        ),
        patch("agent_ready.evaluator._ask", return_value="pytest tests/ -v"),
        patch("agent_ready.evaluator._judge_response", return_value=fake_judgment),
        patch("agent_ready.evaluator._multi_judge_response", return_value=fake_panel),
    ):
        from agent_ready.evaluator import run_eval

        result = run_eval(
            target=tmp_path,
            eval_model="claude-opus-4-6",
            judge_model="claude-opus-4-6",
            baseline_model="claude-haiku-4-5",
            quiet=True,
        )

    assert result["eval_version"] == "2.0"
    assert result["baseline_model"] == "claude-haiku-4-5"
    assert result["ground_truth_source"] == "raw_source_code"
    assert result["language"] == "python"
    assert result["question_count"] == 1


def test_run_eval_v2_report_has_methodology(tmp_path: Path) -> None:
    """save_eval_report v2 includes Methodology section."""
    from agent_ready.evaluator import save_eval_report

    fake_result = {
        "results": [
            {
                "question_id": "base_cmd_001",
                "category": "commands",
                "prompt": "test?",
                "passed": True,
                "delta": 7.0,
                "ground_truth": "pytest",
                "baseline": {
                    "score": 2,
                    "reasoning": "ok",
                    "hallucinated": False,
                    "key_missing": "",
                },
                "with_context": {
                    "score": 9,
                    "reasoning": "great",
                    "hallucinated": False,
                    "key_missing": "",
                    "panel_vote": "3/3",
                    "panel": [],
                },
            }
        ],
        "questions": [],
        "baseline_score": 2.0,
        "context_score": 9.0,
        "score_delta": 7.0,
        "pass_rate": 1.0,
        "hallucination_rate": 0.0,
        "question_count": 1,
        "category_breakdown": {
            "commands": {
                "baseline_avg": 2.0,
                "context_avg": 9.0,
                "delta": 7.0,
                "pass_rate": 1.0,
                "question_count": 1,
            }
        },
        "passed": True,
        "generated_at": "2026-04-21T08:00:00Z",
        "eval_model": "claude-opus-4-6",
        "baseline_model": "claude-haiku-4-5",
        "language": "python",
        "eval_version": "2.0",
        "ground_truth_source": "raw_source_code",
    }

    report_path = save_eval_report(tmp_path, fake_result)
    content = report_path.read_text()

    assert "Evaluation Report v2" in content
    assert "Methodology" in content
    assert "raw_source_code" in content or "Raw Source Code" in content
    assert "claude-haiku-4-5" in content
    assert "claude-opus-4-6" in content
    assert content.endswith("\n")
