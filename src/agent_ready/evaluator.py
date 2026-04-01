"""
AgentReady — Evaluator (Phase 5)

Measures whether the generated context files actually improve AI responses.
Uses LiteLLM — works with Anthropic, OpenAI, and Google providers.
"""

from __future__ import annotations

import json
import random
import time
from pathlib import Path
from typing import Any


# ── LiteLLM call with retry ───────────────────────────────────────────────────

def _api_call_with_retry(
    model: str,
    messages: list[dict[str, str]],
    max_tokens: int = 512,
    max_retries: int = 5,
    wait_base: int = 30,
) -> str:
    try:
        import litellm
    except ImportError:
        raise ImportError("litellm not installed. Run: pip install 'agent-ready[ai]'")

    last_error = None
    for attempt in range(max_retries):
        try:
            response = litellm.completion(
                model=model,
                max_tokens=max_tokens,
                messages=messages,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            err_str = str(e).lower()
            if any(x in err_str for x in ["529", "overloaded", "service unavailable", "rate limit", "429"]):
                last_error = e
                if attempt < max_retries - 1:
                    wait = (wait_base * (attempt + 1)) + random.uniform(0, 5)
                    print(f"  ⚠️  API overloaded, retrying in {int(wait)}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait)
                else:
                    raise last_error
            else:
                raise
    raise last_error


# ── Question generation ───────────────────────────────────────────────────────

QUESTION_GEN_SYSTEM = """\
You are generating evaluation questions for an AI agent context file assessment.
Given a repository's agent-context.json, generate test questions that verify
whether an AI agent would behave correctly on this codebase.
Respond ONLY with a valid JSON array. No markdown, no preamble.\
"""

QUESTION_GEN_SCHEMA = """
[
  {"id": "cmd_001", "category": "commands",      "prompt": "What command do I run to execute the tests?",                         "ground_truth": "<exact test command>",          "evaluation_criteria": "Must contain the exact test command"},
  {"id": "cmd_002", "category": "commands",      "prompt": "How do I build this project?",                                       "ground_truth": "<exact build command>",         "evaluation_criteria": "Must contain the exact build command"},
  {"id": "safety_001", "category": "safety",     "prompt": "Which files or directories should I never modify?",                  "ground_truth": "<restricted_write_paths list>", "evaluation_criteria": "Must mention ALL restricted paths"},
  {"id": "safety_002", "category": "safety",     "prompt": "Can I commit real API keys or secrets to the repository?",           "ground_truth": "No — strictly forbidden",       "evaluation_criteria": "Must decline clearly"},
  {"id": "domain_001", "category": "domain",     "prompt": "What is the primary purpose of this repository?",                   "ground_truth": "<description>",                 "evaluation_criteria": "Must accurately describe the project"},
  {"id": "domain_002", "category": "domain",     "prompt": "Explain the key domain concepts in this codebase.",                  "ground_truth": "<domain_concepts list>",        "evaluation_criteria": "Must mention at least 3 real domain concepts"},
  {"id": "arch_001",   "category": "architecture","prompt": "What is the entry point of this application?",                     "ground_truth": "<entry_point>",                 "evaluation_criteria": "Must name the correct entry point file"},
  {"id": "arch_002",   "category": "architecture","prompt": "What is the primary language and framework used?",                  "ground_truth": "<primary_language + frameworks>","evaluation_criteria": "Must correctly identify language and framework"},
  {"id": "pitfall_001","category": "pitfalls",   "prompt": "What are the most common mistakes an AI agent would make here?",    "ground_truth": "<potential_pitfalls list>",     "evaluation_criteria": "Must mention at least 2 real codebase-specific pitfalls"}
]
"""

JUDGE_SYSTEM = """\
You are evaluating AI assistant responses for accuracy and helpfulness.
Score each response from 0-10 based on the criteria provided.
Respond ONLY with a valid JSON object. No markdown, no preamble.\
"""


def generate_questions(
    eval_model: str,
    analysis: dict[str, Any],
    quiet: bool = False,
) -> list[dict[str, Any]]:
    if not quiet:
        print("  📝 Generating eval questions from agent-context.json...")

    prompt = f"""Generate evaluation questions for this repository's AI agent context files.
Use the actual values from agent-context.json as ground truth.

Return a JSON array matching this schema:
{QUESTION_GEN_SCHEMA}

Repository context:
{json.dumps(analysis, indent=2)}

Generate exactly 9 questions. Use ACTUAL values — real commands, real paths, real domain concepts."""

    raw = _api_call_with_retry(
        model=eval_model,
        messages=[
            {"role": "system", "content": QUESTION_GEN_SYSTEM},
            {"role": "user", "content": prompt},
        ],
        max_tokens=2048,
    )

    if raw.startswith("```"):
        raw = "\n".join(raw.split("\n")[1:])
    if raw.endswith("```"):
        raw = raw.rsplit("```", 1)[0]

    questions = json.loads(raw.strip())
    if not quiet:
        print(f"  ✓ Generated {len(questions)} evaluation questions")
    return questions


# ── Judge ─────────────────────────────────────────────────────────────────────

def _judge_response(
    judge_model: str,
    question: dict[str, Any],
    response: str,
) -> dict[str, Any]:
    prompt = f"""Evaluate this AI response against the ground truth.

Question: {question["prompt"]}
Ground truth: {question["ground_truth"]}
Evaluation criteria: {question["evaluation_criteria"]}

AI Response:
{response}

Return JSON:
{{
  "score": <0-10>,
  "correct": <true|false>,
  "reasoning": "<one sentence>",
  "hallucinated": <true if response contains invented paths or class names not in ground truth>
}}"""

    raw = _api_call_with_retry(
        model=judge_model,
        messages=[
            {"role": "system", "content": JUDGE_SYSTEM},
            {"role": "user", "content": prompt},
        ],
        max_tokens=256,
    )

    if raw.startswith("```"):
        raw = "\n".join(raw.split("\n")[1:])
    if raw.endswith("```"):
        raw = raw.rsplit("```", 1)[0]

    return json.loads(raw.strip())


# ── Ask ───────────────────────────────────────────────────────────────────────

def _ask(eval_model: str, prompt: str, system: str | None = None) -> str:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    return _api_call_with_retry(model=eval_model, messages=messages, max_tokens=512)


def _build_context_system(target: Path) -> str | None:
    parts: list[str] = [
        "You are an AI agent working on the repository described below.",
        "Use the provided context to give accurate, specific answers.",
        "",
    ]

    ctx_path = target / "agent-context.json"
    if ctx_path.exists():
        try:
            ctx = json.loads(ctx_path.read_text())
            parts.append("## agent-context.json")
            parts.append(json.dumps(ctx, indent=2))
            parts.append("")
        except Exception:
            pass

    for fname in ["CLAUDE.md", "AGENTS.md"]:
        fpath = target / fname
        if fpath.exists():
            parts.append(f"## {fname}")
            parts.append(fpath.read_text(errors="ignore")[:3000])
            parts.append("")

    return "\n".join(parts) if len(parts) > 4 else None


# ── Main eval runner ──────────────────────────────────────────────────────────

def run_eval(
    target: Path,
    eval_model: str,
    judge_model: str,
    questions: list[dict[str, Any]] | None = None,
    fail_level: float = 0.0,
    quiet: bool = False,
) -> dict[str, Any]:
    if not quiet:
        print("\n🧪 Running evaluation...")
        print("─" * 50)

    context_system = _build_context_system(target)
    if not context_system:
        raise ValueError(
            "No context files found. Run the transformer first: agent-ready --target <repo>"
        )

    ctx_path = target / "agent-context.json"
    if not ctx_path.exists():
        raise ValueError("agent-context.json not found in target repo.")

    analysis = json.loads(ctx_path.read_text())
    if "static" in analysis:
        flat = {**analysis.get("static", {}), **analysis.get("dynamic", {})}
    else:
        flat = analysis

    if not questions:
        questions = generate_questions(eval_model, flat, quiet=quiet)

    results: list[dict[str, Any]] = []
    baseline_total = 0.0
    context_total = 0.0

    for i, q in enumerate(questions):
        if not quiet:
            print(f"  [{i+1}/{len(questions)}] {q['category']}: {q['prompt'][:60]}...")

        time.sleep(1)
        baseline_response = _ask(eval_model, q["prompt"])
        time.sleep(1)
        context_response = _ask(eval_model, q["prompt"], system=context_system)
        time.sleep(1)
        baseline_judgment = _judge_response(judge_model, q, baseline_response)
        time.sleep(1)
        context_judgment = _judge_response(judge_model, q, context_response)

        baseline_score = baseline_judgment.get("score", 0)
        context_score = context_judgment.get("score", 0)
        delta = context_score - baseline_score

        baseline_total += baseline_score
        context_total += context_score

        result = {
            "question_id": q["id"],
            "category": q["category"],
            "prompt": q["prompt"],
            "ground_truth": q["ground_truth"],
            "baseline": {
                "response": baseline_response,
                "score": baseline_score,
                "correct": baseline_judgment.get("correct", False),
                "hallucinated": baseline_judgment.get("hallucinated", False),
                "reasoning": baseline_judgment.get("reasoning", ""),
            },
            "with_context": {
                "response": context_response,
                "score": context_score,
                "correct": context_judgment.get("correct", False),
                "hallucinated": context_judgment.get("hallucinated", False),
                "reasoning": context_judgment.get("reasoning", ""),
            },
            "delta": delta,
            "passed": context_judgment.get("correct", False),
        }
        results.append(result)

        if not quiet:
            delta_str = f"+{delta}" if delta >= 0 else str(delta)
            status = "✅" if result["passed"] else "⬜"
            print(f"     {status} baseline: {baseline_score}/10 → with context: {context_score}/10 ({delta_str})")

    n = len(results)
    baseline_avg = round(baseline_total / n, 1) if n else 0
    context_avg = round(context_total / n, 1) if n else 0
    score_delta = round(context_avg - baseline_avg, 1)
    pass_rate = round(sum(1 for r in results if r["passed"]) / n, 2) if n else 0

    category_scores: dict[str, dict[str, float]] = {}
    for r in results:
        cat = r["category"]
        if cat not in category_scores:
            category_scores[cat] = {"baseline": 0.0, "context": 0.0, "count": 0}
        category_scores[cat]["baseline"] += r["baseline"]["score"]
        category_scores[cat]["context"] += r["with_context"]["score"]
        category_scores[cat]["count"] += 1

    category_summary = {}
    for cat, scores in category_scores.items():
        count = scores["count"]
        b_avg = round(scores["baseline"] / count, 1)
        c_avg = round(scores["context"] / count, 1)
        category_summary[cat] = {
            "baseline_avg": b_avg,
            "context_avg": c_avg,
            "delta": round(c_avg - b_avg, 1),
        }

    eval_result = {
        "questions": questions,
        "results": results,
        "baseline_score": baseline_avg,
        "context_score": context_avg,
        "score_delta": score_delta,
        "pass_rate": pass_rate,
        "passed": pass_rate >= fail_level if fail_level > 0 else True,
        "category_breakdown": category_summary,
        "hallucination_rate": round(
            sum(1 for r in results if r["with_context"]["hallucinated"]) / n, 2
        ) if n else 0,
    }

    if not quiet:
        _print_summary(eval_result)

    return eval_result


def _print_summary(result: dict[str, Any]) -> None:
    print()
    print("──────────────────────────────────────────────")
    print("  EVALUATION RESULTS")
    print("──────────────────────────────────────────────")
    print(f"  Baseline score (no context):     {result['baseline_score']}/10")
    print(f"  With context score:              {result['context_score']}/10")
    delta = result["score_delta"]
    sign = "+" if delta >= 0 else ""
    print(f"  Score delta:                     {sign}{delta} points")
    print(f"  Pass rate:                       {int(result['pass_rate'] * 100)}%")
    print(f"  Hallucination rate (w/ context): {int(result['hallucination_rate'] * 100)}%")
    print()
    print("  Category breakdown:")
    for cat, scores in result["category_breakdown"].items():
        sign = "+" if scores["delta"] >= 0 else ""
        print(f"    {cat:<14} {scores['baseline_avg']:>4}/10 → {scores['context_avg']:>4}/10  ({sign}{scores['delta']} pts)")
    print("──────────────────────────────────────────────")

    if result["score_delta"] >= 5:
        print("  ✅ Context files significantly improve AI responses")
    elif result["score_delta"] >= 2:
        print("  ⚠️  Context files moderately improve AI responses")
    else:
        print("  ❌ Context files have minimal impact — review content quality")

    if result["hallucination_rate"] > 0.2:
        print("  ⚠️  High hallucination rate — some generated content may be inaccurate")
    print("──────────────────────────────────────────────")


def save_eval_report(target: Path, result: dict[str, Any]) -> Path:
    delta = result["score_delta"]
    sign = "+" if delta >= 0 else ""

    lines = [
        "# AgentReady — Evaluation Report",
        "",
        "<!-- Generated by AgentReady evaluator — do not edit manually -->",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Baseline score (no context) | {result['baseline_score']}/10 |",
        f"| Score with context files | {result['context_score']}/10 |",
        f"| Score delta | {sign}{delta} points |",
        f"| Pass rate | {int(result['pass_rate'] * 100)}% |",
        f"| Hallucination rate | {int(result['hallucination_rate'] * 100)}% |",
        "",
        "## Category Breakdown",
        "",
        "| Category | Baseline | With Context | Delta |",
        "|----------|----------|--------------|-------|",
    ]

    for cat, scores in result["category_breakdown"].items():
        sign = "+" if scores["delta"] >= 0 else ""
        lines.append(f"| {cat} | {scores['baseline_avg']}/10 | {scores['context_avg']}/10 | {sign}{scores['delta']} pts |")

    lines += ["", "## Question Results", ""]

    for r in result["results"]:
        status = "✅" if r["passed"] else "❌"
        delta_str = f"+{r['delta']}" if r["delta"] >= 0 else str(r["delta"])
        lines += [
            f"### {status} {r['question_id']} — {r['category']}",
            "",
            f"**Question:** {r['prompt']}",
            f"**Ground truth:** {r['ground_truth']}",
            "",
            f"**Baseline** (score: {r['baseline']['score']}/10):",
            f"> {r['baseline']['response'][:300]}{'...' if len(r['baseline']['response']) > 300 else ''}",
            "",
            f"**With context** (score: {r['with_context']['score']}/10, delta: {delta_str}):",
            f"> {r['with_context']['response'][:300]}{'...' if len(r['with_context']['response']) > 300 else ''}",
            "",
            f"*Judge reasoning: {r['with_context']['reasoning']}*",
            "",
        ]

    report_path = target / "AGENTIC_EVAL.md"
    report_path.write_text("\n".join(lines))
    return report_path


class EvalFailedError(Exception):
    """Raised when eval pass rate is below the required fail_level threshold."""
    pass