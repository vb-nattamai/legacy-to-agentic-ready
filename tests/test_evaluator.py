from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from agent_ready import evaluator


def _sample_question() -> dict[str, str]:
    return {
        "id": "cmd_001",
        "category": "commands",
        "prompt": "How do I run tests?",
        "ground_truth": "pytest -q",
        "evaluation_criteria": "Must contain pytest -q",
    }


def test_strip_markdown_fences() -> None:
    raw = "```json\n{\"ok\": true}\n```"
    assert evaluator._strip_markdown_fences(raw) == '{"ok": true}'


def test_flatten_analysis_context_merges_static_dynamic() -> None:
    analysis = {
        "static": {"test_command": "pytest", "entry_point": "app.py"},
        "dynamic": {"test_command": "pytest -q", "build_system": "pip"},
    }

    flattened = evaluator._flatten_analysis_context(analysis)

    assert flattened["entry_point"] == "app.py"
    assert flattened["build_system"] == "pip"
    assert flattened["test_command"] == "pytest -q"


def test_build_question_result_maps_scores_and_delta() -> None:
    question = _sample_question()
    result = evaluator._build_question_result(
        question=question,
        baseline_response="maybe use unittest",
        context_response="Use pytest -q",
        baseline_judgment={"score": 3, "correct": False, "hallucinated": False, "reasoning": "wrong cmd", "key_missing": "pytest"},
        context_judgment={"score": 9, "correct": True, "hallucinated": False, "reasoning": "exact", "key_missing": ""},
    )

    assert result["question_id"] == "cmd_001"
    assert result["delta"] == 6
    assert result["passed"] is True
    assert result["baseline"]["score"] == 3
    assert result["with_context"]["score"] == 9


def test_aggregate_results_computes_summary_and_categories() -> None:
    q1 = evaluator._build_question_result(
        question=_sample_question(),
        baseline_response="baseline 1",
        context_response="context 1",
        baseline_judgment={"score": 4, "correct": False, "hallucinated": False, "reasoning": "", "key_missing": ""},
        context_judgment={"score": 8, "correct": True, "hallucinated": False, "reasoning": "", "key_missing": ""},
    )
    q2 = evaluator._build_question_result(
        question={
            "id": "safety_001",
            "category": "safety",
            "prompt": "Should I commit secrets?",
            "ground_truth": "No",
            "evaluation_criteria": "Must refuse",
        },
        baseline_response="maybe",
        context_response="no",
        baseline_judgment={"score": 2, "correct": False, "hallucinated": False, "reasoning": "", "key_missing": ""},
        context_judgment={"score": 6, "correct": False, "hallucinated": True, "reasoning": "", "key_missing": "clear refusal"},
    )

    summary = evaluator._aggregate_results([q1, q2])

    assert summary["baseline_score"] == 3.0
    assert summary["context_score"] == 7.0
    assert summary["score_delta"] == 4.0
    assert summary["pass_rate"] == 0.5
    assert summary["hallucination_rate"] == 0.5
    assert summary["question_count"] == 2
    assert summary["category_breakdown"]["commands"]["context_avg"] == 8.0
    assert summary["category_breakdown"]["safety"]["pass_rate"] == 0.0


def test_build_eval_result_applies_fail_level_threshold() -> None:
    result_row = evaluator._build_question_result(
        question=_sample_question(),
        baseline_response="baseline",
        context_response="context",
        baseline_judgment={"score": 2, "correct": False, "hallucinated": False, "reasoning": "", "key_missing": ""},
        context_judgment={"score": 8, "correct": True, "hallucinated": False, "reasoning": "", "key_missing": ""},
    )
    result = evaluator._build_eval_result(
        questions=[_sample_question()],
        results=[result_row],
        fail_level=0.8,
        generated_at="2026-01-01T00:00:00+00:00",
    )

    assert result["pass_rate"] == 1.0
    assert result["passed"] is True
    assert result["generated_at"] == "2026-01-01T00:00:00+00:00"


def test_resolve_report_verdict_thresholds() -> None:
    assert evaluator._resolve_report_verdict(5.0, 0.8)[0].startswith("✅")
    assert evaluator._resolve_report_verdict(2.0, 0.4)[0].startswith("⚠️")
    assert evaluator._resolve_report_verdict(1.0, 0.4)[0].startswith("❌")


def test_build_report_lines_includes_improvement_section_on_failures() -> None:
    failed_row = evaluator._build_question_result(
        question={
            "id": "pitfall_001",
            "category": "pitfalls",
            "prompt": "What can break?",
            "ground_truth": "Do not change workflow scopes",
            "evaluation_criteria": "Must mention scopes",
        },
        baseline_response="unknown",
        context_response="unknown",
        baseline_judgment={"score": 1, "correct": False, "hallucinated": False, "reasoning": "wrong", "key_missing": "scopes"},
        context_judgment={"score": 5, "correct": False, "hallucinated": False, "reasoning": "still incomplete", "key_missing": "exact scopes"},
    )
    eval_result = evaluator._build_eval_result(
        questions=[],
        results=[failed_row],
        fail_level=0.5,
        generated_at="2026-01-01T00:00:00+00:00",
    )

    lines = evaluator._build_report_lines(eval_result)
    report = "\n".join(lines)

    assert "## What to Improve" in report
    assert "[pitfalls]" in report
    assert "Missing: exact scopes" in report
