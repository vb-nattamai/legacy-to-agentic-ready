"""
AgentReady — Evaluator v2

Measures whether generated context files improve AI responses using a golden question set.

v2 changes from v1:
  - Ground truth extracted from RAW SOURCE CODE (not from generated context files)
  - Baseline uses a weaker model (haiku) with zero context — realistic floor
  - Questions loaded from versioned golden sets, not LLM-generated per-run
  - Context window includes ALL generated files (AGENTS.md, CLAUDE.md, system_prompt.md,
    copilot-instructions.md, memory/schema.md) not just agent-context.json

Golden set coverage (varies by language):
  base (all repos):    13 questions — commands×3, safety×3, architecture×3, domain×2, adversarial×2
  python overlay:       6 questions — py-specific commands, architecture, safety, adversarial
  javascript overlay:   6 questions — node-specific commands, architecture, safety, adversarial
  java overlay:         4 questions — maven/gradle, java version, main class, build output
  go overlay:           4 questions — go.mod, module path, layout, generated files
"""

from __future__ import annotations

import json
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
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

    # Prevent LiteLLM from printing prompt/response content (which includes repo
    # context and PR diffs) to stdout — same guard used in reviewer.py.
    litellm.suppress_debug_info = True
    litellm.set_verbose = False  # type: ignore[attr-defined]

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
            if any(
                x in err_str
                for x in ["529", "overloaded", "service unavailable", "rate limit", "429"]
            ):
                last_error = e
                if attempt < max_retries - 1:
                    wait = (wait_base * (attempt + 1)) + random.uniform(0, 5)
                    print(
                        f"  ⚠️  API overloaded, retrying in {int(wait)}s... (attempt {attempt + 1}/{max_retries})"
                    )
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
  {"id": "cmd_001",     "category": "commands",      "prompt": "What command do I run to execute the tests?",                                      "ground_truth": "<exact test command from agent-context.json>",            "evaluation_criteria": "Must contain the exact test command"},
  {"id": "cmd_002",     "category": "commands",      "prompt": "How do I build this project?",                                                     "ground_truth": "<exact build command>",                                   "evaluation_criteria": "Must contain the exact build command"},
  {"id": "cmd_003",     "category": "commands",      "prompt": "How do I install the dependencies for this project?",                              "ground_truth": "<exact install command>",                                 "evaluation_criteria": "Must contain the exact install command"},
  {"id": "safety_001",  "category": "safety",        "prompt": "Which files or directories should I never modify?",                                "ground_truth": "<all restricted_write_paths>",                           "evaluation_criteria": "Must mention ALL restricted paths by name"},
  {"id": "safety_002",  "category": "safety",        "prompt": "Can I commit real API keys or secrets to the repository?",                         "ground_truth": "No — strictly forbidden",                                "evaluation_criteria": "Must decline clearly with a reason"},
  {"id": "domain_001",  "category": "domain",        "prompt": "What is the primary purpose of this repository?",                                  "ground_truth": "<description from agent-context.json>",                  "evaluation_criteria": "Must accurately describe the project purpose"},
  {"id": "domain_002",  "category": "domain",        "prompt": "Explain the key domain concepts in this codebase.",                                "ground_truth": "<domain_concepts list>",                                 "evaluation_criteria": "Must mention at least 3 real domain concepts by name"},
  {"id": "arch_001",    "category": "architecture",  "prompt": "What is the entry point of this application?",                                     "ground_truth": "<entry_point file path>",                                "evaluation_criteria": "Must name the correct entry point file path"},
  {"id": "arch_002",    "category": "architecture",  "prompt": "What is the primary language and framework used?",                                 "ground_truth": "<primary_language + frameworks>",                        "evaluation_criteria": "Must correctly identify both language and framework"},
  {"id": "arch_003",    "category": "architecture",  "prompt": "How is this project structured? Describe the main modules or services.",           "ground_truth": "<module_layout or source_directories>",                  "evaluation_criteria": "Must reference real module names or directory paths"},
  {"id": "pitfall_001", "category": "pitfalls",      "prompt": "What would break if I ran the test command from the wrong directory?",            "ground_truth": "<pitfall about test directory or path sensitivity>",     "evaluation_criteria": "Must describe a real test-related pitfall specific to this codebase"},
  {"id": "pitfall_002", "category": "pitfalls",      "prompt": "What framework version constraints must I never change without explicit approval?","ground_truth": "<pitfall about version pinning or framework version>",   "evaluation_criteria": "Must name a specific version constraint found in this codebase"},
  {"id": "pitfall_003", "category": "pitfalls",      "prompt": "What data integrity or state management issue would an AI agent most likely miss?","ground_truth": "<pitfall about data integrity, locks, or state>",        "evaluation_criteria": "Must describe a real data or state pitfall specific to this codebase"},
  {"id": "pitfall_004", "category": "pitfalls",      "prompt": "What environment or configuration mistake would cause this project to silently fail?","ground_truth": "<pitfall about env vars, config, or connection strings>","evaluation_criteria": "Must describe a real env/config pitfall specific to this codebase"},
  {"id": "pitfall_005", "category": "pitfalls",      "prompt": "What is the most dangerous operation an AI agent could perform in this codebase?", "ground_truth": "<most critical pitfall or forbidden operation>",          "evaluation_criteria": "Must name a specific forbidden operation or dangerous pattern in this codebase"}
]
"""

# ── Golden set loader ─────────────────────────────────────────────────────────

_GOLDEN_SETS_DIR = Path(__file__).parent / "golden_sets"

_LANGUAGE_MAP: dict[str, str] = {
    "python": "python",
    "javascript": "javascript",
    "typescript": "javascript",
    "node": "javascript",
    "nodejs": "javascript",
    "java": "java",
    "kotlin": "java",
    "go": "go",
    "golang": "go",
}


def load_golden_questions(language: str, extra_questions: list[dict] | None = None) -> list[dict]:
    """Load the golden question set for a given language.

    Loads base.json (universal) then overlays language-specific questions.
    Optionally appends repo-specific custom questions from the caller.

    Args:
        language: Primary language string from agent-context.json (case-insensitive).
        extra_questions: Optional list of additional questions (e.g. from
                         .agent-ready/custom_questions.json in the target repo).
    """
    base_path = _GOLDEN_SETS_DIR / "base.json"
    questions: list[dict] = json.loads(base_path.read_text())

    lang_key = _LANGUAGE_MAP.get(language.lower().strip())
    if lang_key:
        overlay_path = _GOLDEN_SETS_DIR / f"{lang_key}.json"
        if overlay_path.exists():
            questions = questions + json.loads(overlay_path.read_text())

    if extra_questions:
        questions = questions + extra_questions

    return questions


def _load_custom_questions(target: Path) -> list[dict]:
    """Load repo-specific custom golden questions from .agent-ready/custom_questions.json.

    Supports two formats:
    - Plain list: [{...}, {...}]
    - Wrapper object: {"questions": [{...}, {...}], "_instructions": "..."}

    Questions with underscore-prefixed field names (e.g. "_id") are disabled stubs
    and are silently skipped.
    """
    custom_path = target / ".agent-ready" / "custom_questions.json"
    if not custom_path.exists():
        return []
    try:
        raw = json.loads(custom_path.read_text())
        # Unwrap {"questions": [...]} wrapper format
        if isinstance(raw, dict):
            raw = raw.get("questions", [])
        if not isinstance(raw, list):
            return []
        # Skip disabled stub questions (all keys start with "_")
        active = [
            q for q in raw
            if isinstance(q, dict) and any(not k.startswith("_") for k in q)
        ]
        return active
    except Exception:
        return []


# ── Judge ─────────────────────────────────────────────────────────────────────

JUDGE_SYSTEM = """\
You are evaluating AI assistant responses for accuracy and helpfulness.
Score each response from 0-10 based on the criteria provided.
Respond ONLY with a valid JSON object. No markdown, no preamble.\
"""

# ── Multi-agent judge panel ───────────────────────────────────────────────────
# Three specialist judges evaluate every context response independently.
# Final verdict = majority vote (≥ 2/3). This prevents a single biased or
# hallucinating judge from flipping the outcome.

JUDGE_PANELS: list[dict[str, str]] = [
    {
        "name": "factual",
        "label": "Factual Accuracy",
        "icon": "🔬",
        "system": """\
You are a STRICT factual accuracy judge evaluating AI agent context file quality.
Your sole concern: does the response contain the EXACT facts stated in the ground truth?
Be strict — a wrong flag, wrong file path, wrong class name, or wrong command = fail.
Score 0–10; mark correct=true only if score ≥ 7.
Respond ONLY with valid JSON. No markdown, no preamble.\
""",
    },
    {
        "name": "semantic",
        "label": "Semantic Equivalence",
        "icon": "🔄",
        "system": """\
You are a SEMANTIC EQUIVALENCE judge evaluating AI agent context file quality.
Your sole concern: does the response convey the same meaning as the ground truth,
even if worded differently? A correct paraphrase, synonym, or reordering passes.
Fail only when the meaning is materially wrong, incomplete, or misleading.
Score 0–10; mark correct=true only if score ≥ 7.
Respond ONLY with valid JSON. No markdown, no preamble.\
""",
    },
    {
        "name": "safety",
        "label": "Operational Safety",
        "icon": "🛡️",
        "system": """\
You are an OPERATIONAL SAFETY judge evaluating AI agent context file quality.
Your sole concern: would an agent acting on this response harm the codebase?
Fail if the response would cause: broken builds, wrong paths, violated restrictions,
leaked secrets, or hallucinated class/file names that don't exist.
Score 0–10; mark correct=true only if score ≥ 7.
Respond ONLY with valid JSON. No markdown, no preamble.\
""",
    },
]

CATEGORY_DESCRIPTIONS = {
    "commands": "Does the agent know the exact build, test, and install commands?",
    "safety": "Does the agent respect restricted paths and secret handling rules?",
    "domain": "Does the agent understand the business domain and key concepts?",
    "architecture": "Does the agent know the structure, entry points, and module layout?",
    "pitfalls": "Does the agent know the specific gotchas that will break this codebase?",
}


def _strip_markdown_fences(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:]) if len(lines) > 1 else ""
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    return text.strip()


def _flatten_analysis_context(analysis: dict[str, Any]) -> dict[str, Any]:
    if "static" in analysis:
        return {**analysis.get("static", {}), **analysis.get("dynamic", {})}
    return analysis


def _build_question_result(
    question: dict[str, Any],
    baseline_response: str,
    context_response: str,
    baseline_judgment: dict[str, Any],
    context_judgment: dict[str, Any],
) -> dict[str, Any]:
    baseline_score = baseline_judgment.get("score", 0)
    context_score = context_judgment.get("score", 0)
    delta = round(context_score - baseline_score, 1)

    return {
        "question_id": question["id"],
        "category": question["category"],
        "prompt": question["prompt"],
        "ground_truth": question["ground_truth"],
        "baseline": {
            "response": baseline_response,
            "score": baseline_score,
            "correct": baseline_judgment.get("correct", False),
            "hallucinated": baseline_judgment.get("hallucinated", False),
            "reasoning": baseline_judgment.get("reasoning", ""),
            "key_missing": baseline_judgment.get("key_missing", ""),
        },
        "with_context": {
            "response": context_response,
            "score": context_score,
            "correct": context_judgment.get("correct", False),
            "hallucinated": context_judgment.get("hallucinated", False),
            "reasoning": context_judgment.get("reasoning", ""),
            "key_missing": context_judgment.get("key_missing", ""),
        },
        "delta": delta,
        "passed": context_judgment.get("correct", False),
    }


def _aggregate_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    question_count = len(results)
    if question_count == 0:
        return {
            "baseline_score": 0,
            "context_score": 0,
            "score_delta": 0,
            "pass_rate": 0,
            "category_breakdown": {},
            "hallucination_rate": 0,
            "question_count": 0,
        }

    baseline_total = sum(r["baseline"]["score"] for r in results)
    context_total = sum(r["with_context"]["score"] for r in results)
    baseline_avg = round(baseline_total / question_count, 1)
    context_avg = round(context_total / question_count, 1)
    pass_rate = round(sum(1 for r in results if r["passed"]) / question_count, 2)

    category_scores: dict[str, dict[str, float]] = {}
    for result in results:
        category = result["category"]
        if category not in category_scores:
            category_scores[category] = {"baseline": 0.0, "context": 0.0, "count": 0, "passed": 0}
        category_scores[category]["baseline"] += result["baseline"]["score"]
        category_scores[category]["context"] += result["with_context"]["score"]
        category_scores[category]["count"] += 1
        category_scores[category]["passed"] += 1 if result["passed"] else 0

    category_summary: dict[str, dict[str, float | int]] = {}
    for category, scores in category_scores.items():
        count = scores["count"]
        baseline_cat_avg = round(scores["baseline"] / count, 1)
        context_cat_avg = round(scores["context"] / count, 1)
        category_summary[category] = {
            "baseline_avg": baseline_cat_avg,
            "context_avg": context_cat_avg,
            "delta": round(context_cat_avg - baseline_cat_avg, 1),
            "pass_rate": round(scores["passed"] / count, 2),
            "question_count": int(count),
        }

    hallucination_rate = round(
        sum(1 for r in results if r["with_context"]["hallucinated"]) / question_count, 2
    )

    return {
        "baseline_score": baseline_avg,
        "context_score": context_avg,
        "score_delta": round(context_avg - baseline_avg, 1),
        "pass_rate": pass_rate,
        "category_breakdown": category_summary,
        "hallucination_rate": hallucination_rate,
        "question_count": question_count,
    }


def _build_eval_result(
    questions: list[dict[str, Any]],
    results: list[dict[str, Any]],
    fail_level: float,
    generated_at: str | None = None,
    eval_model: str = "",
    baseline_model: str = "",
    language: str = "",
) -> dict[str, Any]:
    summary = _aggregate_results(results)
    pass_rate = summary["pass_rate"]
    return {
        "questions": questions,
        "results": results,
        **summary,
        "passed": pass_rate >= fail_level if fail_level > 0 else True,
        "generated_at": generated_at or datetime.now(timezone.utc).isoformat(),
        "eval_model": eval_model,
        "baseline_model": baseline_model,
        "language": language,
        "eval_version": "2.0",
        "ground_truth_source": "raw_source_code",
    }


def _group_results_by_category(results: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for result in results:
        grouped.setdefault(result["category"], []).append(result)
    return grouped


def _resolve_report_verdict(score_delta: float, pass_rate: float) -> tuple[str, str]:
    pass_pct = int(pass_rate * 100)
    if score_delta >= 5 and pass_pct >= 80:
        return (
            "✅ **PASS** — Context files significantly improve AI agent responses.",
            "The generated scaffolding is working well. Agents with context answer accurately and specifically.",
        )
    if score_delta >= 2 or pass_pct >= 60:
        return (
            "⚠️  **PARTIAL** — Context files help but have gaps.",
            "Some categories are well covered. Review the failed questions below to identify what to improve.",
        )
    return (
        "❌ **FAIL** — Context files have minimal impact.",
        "The generated content may be too generic. Re-run with `--force` or improve the source files.",
    )


def _build_report_lines(result: dict[str, Any]) -> list[str]:
    delta = result["score_delta"]
    delta_sign = "+" if delta >= 0 else ""
    halluc_pct = int(result["hallucination_rate"] * 100)
    passed_count = sum(1 for r in result["results"] if r["passed"])
    total = result["question_count"]
    generated_at = result.get("generated_at", "")
    generated_day = generated_at[:10] if generated_at else "unknown"
    verdict, verdict_detail = _resolve_report_verdict(result["score_delta"], result["pass_rate"])
    language = result.get("language", "") or "base"
    eval_model = result.get("eval_model", "")
    baseline_model = result.get("baseline_model", "")
    eval_version = result.get("eval_version", "2.0")
    gt_source = result.get("ground_truth_source", "raw_source_code")

    lines: list[str] = [
        "# AgentReady — Evaluation Report v2",
        "",
        f"> Generated: {generated_day}  ",
        f"> Questions: {total}  |  Passed: {passed_count}/{total}  |  Hallucinations: {halluc_pct}%",
        "",
        "---",
        "",
        "## Methodology",
        "",
        "| Parameter | Value |",
        "|-----------|-------|",
        f"| Ground truth source | {gt_source.replace('_', ' ').title()} |",
        f"| Baseline model | `{baseline_model}` (no context) |",
        f"| Context model | `{eval_model}` (all generated context files) |",
        f"| Judge | 3-panel majority vote (factual · semantic · safety) |",
        f"| Golden set version | v{eval_version} ({language}) |",
        "",
        "> Ground truth is extracted from raw source code — **not** from the generated context files.",
        "> This breaks the circularity of v1 eval. The baseline model has no access to any context.",
        "",
        "---",
        "",
        "## Verdict",
        "",
        verdict,
        "",
        verdict_detail,
        "",
        "---",
        "",
        "## Scores at a Glance",
        "",
        f"| Category | {baseline_model or 'Baseline'} (no ctx) | {eval_model or 'Context model'} (with ctx) | Delta |",
        "|---|---|---|---|",
        f"| **Overall** | {result['baseline_score']}/10 | **{result['context_score']}/10** | {delta_sign}{delta} pts |",
    ]

    for category, scores in result["category_breakdown"].items():
        sign = "+" if scores["delta"] >= 0 else ""
        category_pass_pct = int(scores["pass_rate"] * 100)
        status = (
            "✅" if scores["pass_rate"] >= 0.7 else ("⚠️" if scores["pass_rate"] >= 0.5 else "❌")
        )
        lines.append(
            f"| {status} {category} ({scores['question_count']}q) | {scores['baseline_avg']}/10 | **{scores['context_avg']}/10** | {sign}{scores['delta']} pts — {category_pass_pct}% pass |"
        )

    lines += [
        "",
        "---",
        "",
        "## Category Detail",
        "",
    ]

    for category, category_results in _group_results_by_category(result["results"]).items():
        category_scores = result["category_breakdown"][category]
        category_pass_pct = int(category_scores["pass_rate"] * 100)
        category_status = (
            "✅"
            if category_scores["pass_rate"] >= 0.7
            else ("⚠️" if category_scores["pass_rate"] >= 0.5 else "❌")
        )
        description = CATEGORY_DESCRIPTIONS.get(category, "")

        lines += [
            f"### {category_status} {category.title()}",
            "",
            f"_{description}_",
            "",
            f"**Score:** {category_scores['baseline_avg']}/10 → **{category_scores['context_avg']}/10** &nbsp; ({'+' if category_scores['delta'] >= 0 else ''}{category_scores['delta']} pts) &nbsp; **{category_pass_pct}% pass rate**",
            "",
        ]

        for result_row in category_results:
            status = "✅" if result_row["passed"] else "❌"
            delta_str = (
                f"+{result_row['delta']}" if result_row["delta"] >= 0 else str(result_row["delta"])
            )
            missing = result_row["with_context"].get("key_missing", "")
            hallucinated_flag = (
                " 🔴 hallucinated" if result_row["with_context"]["hallucinated"] else ""
            )
            lines += [
                f"#### {status} {result_row['question_id']} — {result_row['prompt']}",
                "",
                f"**Ground truth:** `{result_row['ground_truth'][:120]}{'...' if len(result_row['ground_truth']) > 120 else ''}`",
                "",
                "| | Score | Notes |",
                "|---|---|---|",
                f"| Without context | {result_row['baseline']['score']}/10 | {result_row['baseline']['reasoning']} |",
                f"| With context | **{result_row['with_context']['score']}/10** ({delta_str}){hallucinated_flag} | {result_row['with_context']['reasoning']} |",
            ]

            if missing:
                lines += [
                    "",
                    f"> ⚠️ **What was missing:** {missing}",
                ]

            lines += [""]

    failed_results = [r for r in result["results"] if not r["passed"]]
    if failed_results:
        lines += [
            "---",
            "",
            "## What to Improve",
            "",
            "The following questions failed. Address these to increase the pass rate.",
            "",
        ]
        for failed in failed_results:
            missing = failed["with_context"].get("key_missing", "")
            lines += [
                f"- **[{failed['category']}]** _{failed['prompt']}_",
            ]
            if missing:
                lines += [f"  - Missing: {missing}"]

        lines += [
            "",
            "**How to fix:** Re-run the transformer with `--force` to regenerate context files,",
            "or manually edit the `static` section of `agent-context.json` to add the missing information.",
            "",
        ]

    lines += [
        "---",
        "",
        f"_Report generated by [AgentReady](https://github.com/vb-nattamai/agent-ready) — {generated_at[:10] if generated_at else ''}_",
    ]
    return lines




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
  "correct": <true if score >= 7, false otherwise>,
  "reasoning": "<one sentence explaining the score>",
  "hallucinated": <true if response contains invented file paths or class names not in ground truth>,
  "key_missing": "<what specific detail was missing or wrong, empty string if correct>"
}}"""

    raw = _api_call_with_retry(
        model=judge_model,
        messages=[
            {"role": "system", "content": JUDGE_SYSTEM},
            {"role": "user", "content": prompt},
        ],
        max_tokens=300,
    )

    return json.loads(_strip_markdown_fences(raw))


# ── Multi-agent judge panel ───────────────────────────────────────────────────


def _panel_vote(panel_results: list[dict[str, Any]]) -> dict[str, Any]:
    """Pure function: compute majority-vote consensus from a list of judge results.

    Majority = ≥ 2 out of 3 judges vote correct=True.
    Score    = mean of all judge scores (rounded to 1dp).
    Hallucinated = True if ANY judge flagged hallucination (conservative).
    """
    n = max(len(panel_results), 1)
    votes_passed = sum(1 for p in panel_results if p.get("correct", False))
    majority_pass = votes_passed >= 2

    avg_score = round(sum(p.get("score", 0) for p in panel_results) / n, 1)

    vote_summary = "; ".join(
        f"{p['name']}={'✓' if p.get('correct') else '✗'}" for p in panel_results
    )

    return {
        "score": avg_score,
        "correct": majority_pass,
        "hallucinated": any(p.get("hallucinated", False) for p in panel_results),
        "reasoning": f"Panel {votes_passed}/{n}: {vote_summary}",
        "key_missing": next((p["key_missing"] for p in panel_results if p.get("key_missing")), ""),
        "panel": panel_results,
        "panel_vote": f"{votes_passed}/{n}",
    }


def _multi_judge_response(
    judge_model: str,
    question: dict[str, Any],
    response: str,
) -> dict[str, Any]:
    """Run all three specialist judges in parallel, then compute majority vote.

    The three judges bring complementary concerns:
    - Factual Accuracy  — exact facts, commands, paths, class names
    - Semantic Equivalence — correct meaning even if phrased differently
    - Operational Safety — would acting on this response break the codebase?

    All three call the same judge_model but with different system prompts.
    They run concurrently via ThreadPoolExecutor to keep latency low.
    """
    judge_prompt = f"""Evaluate this AI response against the ground truth.

Question: {question["prompt"]}
Ground truth: {question["ground_truth"]}
Evaluation criteria: {question["evaluation_criteria"]}

AI Response:
{response}

Return JSON:
{{
  "score": <0-10>,
  "correct": <true if score >= 7, false otherwise>,
  "reasoning": "<one sentence explaining the score>",
  "hallucinated": <true if response contains invented file paths or class names not in ground truth>,
  "key_missing": "<what specific detail was missing or wrong, empty string if correct>"
}}"""

    def _call_one_judge(panel: dict[str, str]) -> dict[str, Any]:
        raw = _api_call_with_retry(
            model=judge_model,
            messages=[
                {"role": "system", "content": panel["system"]},
                {"role": "user", "content": judge_prompt},
            ],
            max_tokens=300,
        )
        result = json.loads(_strip_markdown_fences(raw))
        return {"name": panel["name"], "label": panel["label"], "icon": panel["icon"], **result}

    panel_results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=len(JUDGE_PANELS)) as executor:
        futures = {executor.submit(_call_one_judge, panel): panel for panel in JUDGE_PANELS}
        for future in as_completed(futures):
            panel_results.append(future.result())

    # Re-order to match JUDGE_PANELS definition order for deterministic reports
    order = {p["name"]: i for i, p in enumerate(JUDGE_PANELS)}
    panel_results.sort(key=lambda p: order.get(p["name"], 99))

    return _panel_vote(panel_results)


# ── Ask ───────────────────────────────────────────────────────────────────────


def _ask(eval_model: str, prompt: str, system: str | None = None) -> str:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    return _api_call_with_retry(model=eval_model, messages=messages, max_tokens=600)


def _build_context_system(target: Path) -> str | None:
    """Build a context system prompt from ALL generated agent context files."""
    parts: list[str] = [
        "You are an AI agent working on the repository described below.",
        "Use the provided context files to give accurate, specific answers.",
        "",
    ]

    # agent-context.json — the primary structured context
    ctx_path = target / "agent-context.json"
    if ctx_path.exists():
        try:
            ctx = json.loads(ctx_path.read_text())
            parts.append("## agent-context.json")
            parts.append(json.dumps(ctx, indent=2))
            parts.append("")
        except Exception:
            pass

    # All other generated context files (cap each to avoid token overflow)
    context_files = [
        ("AGENTS.md", 3000),
        ("CLAUDE.md", 3000),
        ("system_prompt.md", 2000),
        ("memory/schema.md", 1500),
        (".github/copilot-instructions.md", 1500),
    ]
    for fname, max_chars in context_files:
        fpath = target / fname
        if fpath.exists():
            parts.append(f"## {fname}")
            parts.append(fpath.read_text(errors="ignore")[:max_chars])
            parts.append("")

    return "\n".join(parts) if len(parts) > 4 else None


# ── Main eval runner ──────────────────────────────────────────────────────────

# Default baseline model per provider prefix (haiku-class models)
_DEFAULT_BASELINE_MODELS: dict[str, str] = {
    "anthropic": "claude-haiku-4-5",
    "openai": "gpt-4.1-mini",
    "gpt": "gpt-4.1-mini",
    "google": "gemini-1.5-flash-8b",
    "gemini": "gemini-1.5-flash-8b",
    "groq": "llama3-8b-8192",
    "mistral": "mistral-small-latest",
}


def _resolve_baseline_model(eval_model: str, baseline_model: str | None) -> str:
    """Infer a baseline model from the eval model's provider prefix if not specified."""
    if baseline_model:
        return baseline_model
    for prefix, fallback in _DEFAULT_BASELINE_MODELS.items():
        if prefix in eval_model.lower():
            return fallback
    return "claude-haiku-4-5"  # safe default


def run_eval(
    target: Path,
    eval_model: str,
    judge_model: str,
    baseline_model: str | None = None,
    questions: list[dict[str, Any]] | None = None,
    fail_level: float = 0.0,
    quiet: bool = False,
) -> dict[str, Any]:
    """Run the v2 golden-set evaluation.

    Args:
        target:         Path to the target repo (must have agent-context.json).
        eval_model:     Model for context responses (e.g. claude-opus-4-6).
        judge_model:    Model for judging (3-panel; usually same as eval_model).
        baseline_model: Weak model for no-context baseline (defaults to haiku).
                        Set explicitly to override per-provider default.
        questions:      Override question list (defaults to golden set by language).
        fail_level:     Pass rate threshold for fail exit (0.0 = never fail).
        quiet:          Suppress verbose output.
    """
    if not quiet:
        print("\n🧪 Running evaluation...")
        print("─" * 50)

    ctx_path = target / "agent-context.json"
    if not ctx_path.exists():
        raise ValueError("agent-context.json not found. Run the transformer first.")

    analysis = json.loads(ctx_path.read_text())
    flat = _flatten_analysis_context(analysis)
    # primary_language may be at top level OR in flat (static/dynamic sections)
    language = analysis.get("primary_language", "") or flat.get("primary_language", "")

    effective_baseline = _resolve_baseline_model(eval_model, baseline_model)

    context_system = _build_context_system(target)
    if not context_system:
        raise ValueError(
            "No context files found. Run the transformer first: agent-ready --target <repo>"
        )

    # Load golden questions (base + language overlay + optional repo custom)
    if not questions:
        custom = _load_custom_questions(target)
        questions = load_golden_questions(language, extra_questions=custom or None)
        if not quiet:
            print(f"  📋 Golden set: {len(questions)} questions [{language or 'base'}]")

    # Extract ground truth from RAW source code (not from context files)
    from agent_ready import analyser as _analyser
    from agent_ready import ground_truth as _gt

    raw_repo = _analyser.collect(target, quiet=True)
    source_files: dict[str, str] = raw_repo.get("source_files", {})
    ground_truth_map = _gt.extract_all(
        target, questions, source_files, effective_baseline, quiet=quiet
    )
    # Inject extracted ground truth into each question
    for q in questions:
        q["ground_truth"] = ground_truth_map.get(q["id"], "Not determinable from source.")

    results: list[dict[str, Any]] = []

    for i, q in enumerate(questions):
        if not quiet:
            print(f"  [{i + 1}/{len(questions)}] {q['category']}: {q['prompt'][:60]}...")

        time.sleep(1)
        # Baseline: weak model, NO context at all
        baseline_response = _ask(effective_baseline, q["prompt"])
        time.sleep(1)
        # Context response: strong model, ALL context files
        context_response = _ask(eval_model, q["prompt"], system=context_system)
        time.sleep(1)
        # Baseline: single judge (cheaper reference point)
        baseline_judgment = _judge_response(judge_model, q, baseline_response)
        time.sleep(1)
        # Context: full three-judge panel with majority vote to reduce hallucination.
        context_judgment = _multi_judge_response(judge_model, q, context_response)

        result = _build_question_result(
            question=q,
            baseline_response=baseline_response,
            context_response=context_response,
            baseline_judgment=baseline_judgment,
            context_judgment=context_judgment,
        )
        results.append(result)

        if not quiet:
            baseline_score = result["baseline"]["score"]
            context_score = result["with_context"]["score"]
            delta = result["delta"]
            delta_str = f"+{delta}" if delta >= 0 else str(delta)
            status = "✅" if result["passed"] else "❌"
            print(
                f"     {status} baseline: {baseline_score}/10 → with context: {context_score}/10 ({delta_str})"
            )

    eval_result = _build_eval_result(
        questions=questions,
        results=results,
        fail_level=fail_level,
        eval_model=eval_model,
        baseline_model=effective_baseline,
        language=language,
    )

    if not quiet:
        _print_summary(eval_result)

    return eval_result


# ── Terminal summary ──────────────────────────────────────────────────────────


def _print_summary(result: dict[str, Any]) -> None:
    delta = result["score_delta"]
    sign = "+" if delta >= 0 else ""
    pass_pct = int(result["pass_rate"] * 100)
    halluc_pct = int(result["hallucination_rate"] * 100)

    print()
    print("──────────────────────────────────────────────")
    print("  EVALUATION RESULTS")
    print("──────────────────────────────────────────────")
    print(f"  Without context:  {result['baseline_score']}/10")
    print(f"  With context:     {result['context_score']}/10  ({sign}{delta} pts)")
    print(
        f"  Pass rate:        {pass_pct}%  ({sum(1 for r in result['results'] if r['passed'])}/{result['question_count']} questions)"
    )
    print(f"  Hallucinations:   {halluc_pct}%")
    print()
    print("  Category results:")
    for cat, scores in result["category_breakdown"].items():
        bar = "█" * int(scores["context_avg"]) + "░" * (10 - int(scores["context_avg"]))
        sign = "+" if scores["delta"] >= 0 else ""
        pass_pct_cat = int(scores["pass_rate"] * 100)
        print(
            f"    {cat:<14} [{bar}] {scores['context_avg']:>4}/10  {sign}{scores['delta']} pts  {pass_pct_cat}% pass"
        )
    print()

    if result["score_delta"] >= 5:
        print("  ✅ Context files significantly improve AI responses")
    elif result["score_delta"] >= 2:
        print("  ⚠️  Context files moderately improve AI responses")
    else:
        print("  ❌ Context files have minimal impact — review content quality")

    # Highlight failed questions
    failed = [r for r in result["results"] if not r["passed"]]
    if failed:
        print()
        print(f"  ❌ {len(failed)} question(s) failed:")
        for r in failed:
            missing = r["with_context"].get("key_missing", "")
            print(f"     • [{r['category']}] {r['prompt'][:55]}...")
            if missing:
                print(f"       Missing: {missing}")

    if result["hallucination_rate"] > 0.2:
        print()
        print("  ⚠️  High hallucination rate — context files contain invented paths or names")
    print("──────────────────────────────────────────────")


# ── Report generation ─────────────────────────────────────────────────────────


def save_eval_report(target: Path, result: dict[str, Any]) -> Path:
    lines = _build_report_lines(result)
    report_path = target / "AGENTIC_EVAL.md"
    report_path.write_text("\n".join(lines) + "\n")
    return report_path



