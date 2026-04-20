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
    raw = '```json\n{"ok": true}\n```'
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


def test_flatten_analysis_context_returns_flat_dict_unchanged() -> None:
    flat = {"test_command": "pytest", "build_system": "pip"}
    assert evaluator._flatten_analysis_context(flat) == flat


def test_aggregate_results_returns_zeros_for_empty_list() -> None:
    summary = evaluator._aggregate_results([])
    assert summary["baseline_score"] == 0
    assert summary["context_score"] == 0
    assert summary["pass_rate"] == 0
    assert summary["category_breakdown"] == {}


def test_build_question_result_maps_scores_and_delta() -> None:
    question = _sample_question()
    result = evaluator._build_question_result(
        question=question,
        baseline_response="maybe use unittest",
        context_response="Use pytest -q",
        baseline_judgment={
            "score": 3,
            "correct": False,
            "hallucinated": False,
            "reasoning": "wrong cmd",
            "key_missing": "pytest",
        },
        context_judgment={
            "score": 9,
            "correct": True,
            "hallucinated": False,
            "reasoning": "exact",
            "key_missing": "",
        },
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
        baseline_judgment={
            "score": 4,
            "correct": False,
            "hallucinated": False,
            "reasoning": "",
            "key_missing": "",
        },
        context_judgment={
            "score": 8,
            "correct": True,
            "hallucinated": False,
            "reasoning": "",
            "key_missing": "",
        },
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
        baseline_judgment={
            "score": 2,
            "correct": False,
            "hallucinated": False,
            "reasoning": "",
            "key_missing": "",
        },
        context_judgment={
            "score": 6,
            "correct": False,
            "hallucinated": True,
            "reasoning": "",
            "key_missing": "clear refusal",
        },
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
        baseline_judgment={
            "score": 2,
            "correct": False,
            "hallucinated": False,
            "reasoning": "",
            "key_missing": "",
        },
        context_judgment={
            "score": 8,
            "correct": True,
            "hallucinated": False,
            "reasoning": "",
            "key_missing": "",
        },
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
        baseline_judgment={
            "score": 1,
            "correct": False,
            "hallucinated": False,
            "reasoning": "wrong",
            "key_missing": "scopes",
        },
        context_judgment={
            "score": 5,
            "correct": False,
            "hallucinated": False,
            "reasoning": "still incomplete",
            "key_missing": "exact scopes",
        },
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


# ── Multi-agent judge panel tests ─────────────────────────────────────────────


def _make_judge_result(
    name: str, correct: bool, score: int, hallucinated: bool = False, key_missing: str = ""
) -> dict:
    return {
        "name": name,
        "correct": correct,
        "score": score,
        "hallucinated": hallucinated,
        "key_missing": key_missing,
    }


def test_panel_vote_unanimous_pass() -> None:
    results = [
        _make_judge_result("factual", True, 9),
        _make_judge_result("semantic", True, 8),
        _make_judge_result("safety", True, 8),
    ]
    verdict = evaluator._panel_vote(results)
    assert verdict["correct"] is True
    assert verdict["panel_vote"] == "3/3"
    assert verdict["hallucinated"] is False
    assert verdict["score"] == 8.3


def test_panel_vote_unanimous_fail() -> None:
    results = [
        _make_judge_result("factual", False, 3),
        _make_judge_result("semantic", False, 4),
        _make_judge_result("safety", False, 2),
    ]
    verdict = evaluator._panel_vote(results)
    assert verdict["correct"] is False
    assert verdict["panel_vote"] == "0/3"


def test_panel_vote_majority_pass_two_out_of_three() -> None:
    results = [
        _make_judge_result("factual", True, 8),
        _make_judge_result("semantic", True, 7),
        _make_judge_result("safety", False, 4),
    ]
    verdict = evaluator._panel_vote(results)
    assert verdict["correct"] is True
    assert verdict["panel_vote"] == "2/3"


def test_panel_vote_majority_fail_one_out_of_three() -> None:
    results = [
        _make_judge_result("factual", True, 8),
        _make_judge_result("semantic", False, 5),
        _make_judge_result("safety", False, 3),
    ]
    verdict = evaluator._panel_vote(results)
    assert verdict["correct"] is False
    assert verdict["panel_vote"] == "1/3"


def test_panel_vote_hallucination_any_judge_flags() -> None:
    """Conservative: any judge flagging hallucination sets the flag."""
    results = [
        _make_judge_result("factual", True, 9, hallucinated=False),
        _make_judge_result("semantic", True, 8, hallucinated=True),
        _make_judge_result("safety", True, 7, hallucinated=False),
    ]
    verdict = evaluator._panel_vote(results)
    assert verdict["hallucinated"] is True
    assert verdict["correct"] is True  # still passes on votes


def test_panel_vote_key_missing_from_first_failing_judge() -> None:
    results = [
        _make_judge_result("factual", False, 4, key_missing="wrong flag"),
        _make_judge_result("semantic", True, 7, key_missing=""),
        _make_judge_result("safety", False, 3, key_missing="broken path"),
    ]
    verdict = evaluator._panel_vote(results)
    assert verdict["key_missing"] == "wrong flag"


def test_panel_vote_reasoning_contains_vote_summary() -> None:
    results = [
        _make_judge_result("factual", True, 9),
        _make_judge_result("semantic", False, 4),
        _make_judge_result("safety", True, 8),
    ]
    verdict = evaluator._panel_vote(results)
    assert "2/3" in verdict["reasoning"]
    assert "factual=✓" in verdict["reasoning"]
    assert "semantic=✗" in verdict["reasoning"]


def test_panel_vote_empty_list_does_not_crash() -> None:
    """Edge case: empty list should not divide by zero."""
    verdict = evaluator._panel_vote([])
    assert verdict["correct"] is False
    assert verdict["score"] == 0.0


def test_multi_judge_response_uses_three_judges(monkeypatch) -> None:
    """Verify _multi_judge_response calls the judge for each panel member."""
    call_count = {"n": 0}

    def fake_api_call(model, messages, max_tokens):
        call_count["n"] += 1
        return '{"score": 8, "correct": true, "reasoning": "good", "hallucinated": false, "key_missing": ""}'

    monkeypatch.setattr(evaluator, "_api_call_with_retry", fake_api_call)

    question = _sample_question()
    result = evaluator._multi_judge_response("anthropic/claude-3-haiku", question, "pytest -q")

    assert call_count["n"] == 3  # one per judge panel
    assert result["panel_vote"] == "3/3"
    assert result["correct"] is True


def test_multi_judge_response_result_sorted_by_panel_order(monkeypatch) -> None:
    """Results must be sorted to match JUDGE_PANELS order regardless of completion order."""
    panel_names = [p["name"] for p in evaluator.JUDGE_PANELS]

    def fake_api_call(model, messages, max_tokens):
        return '{"score": 7, "correct": true, "reasoning": "ok", "hallucinated": false, "key_missing": ""}'

    monkeypatch.setattr(evaluator, "_api_call_with_retry", fake_api_call)

    result = evaluator._multi_judge_response(
        "anthropic/claude-3-haiku", _sample_question(), "pytest -q"
    )
    returned_names = [p["name"] for p in result["panel"]]
    assert returned_names == panel_names


def test_judge_panels_constant_has_three_entries() -> None:
    assert len(evaluator.JUDGE_PANELS) == 3
    for panel in evaluator.JUDGE_PANELS:
        assert "name" in panel
        assert "label" in panel
        assert "icon" in panel
        assert "system" in panel
