"""
AgentReady MCP Server

Exposes agent-ready capabilities as MCP tools so Claude Code, VS Code,
and any MCP-compatible client can call them directly — no CLI required.

Tools:
  transform   — full pipeline: analyse repo → generate scaffolding → score
  score       — instant 100-pt readiness check (no LLM, local only)
  evaluate    — 15-question three-judge eval panel (proves context quality)
  review_pr   — post an APPROVE / REQUEST_CHANGES review on a PR

Usage:
  # Start the server (stdio transport, works with any MCP host)
  python -m agent_ready.mcp_server

  # Or via the installed command:
  agent-ready-mcp

Configure in mcp.json:
  {
    "mcpServers": {
      "agent-ready": {
        "command": "python",
        "args": ["-m", "agent_ready.mcp_server"],
        "env": { "ANTHROPIC_API_KEY": "${ANTHROPIC_API_KEY}" }
      }
    }
  }
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import Context, FastMCP

mcp = FastMCP(
    name="agent-ready",
    instructions=(
        "AgentReady transforms legacy repositories into AI-agent-ready codebases. "
        "Use 'transform' to generate scaffolding, 'score' to check readiness, "
        "'evaluate' to measure quality with a three-judge panel, and 'review_pr' "
        "to review a pull request grounded in the repo's agent-context.json."
    ),
)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _resolve(target: str) -> Path:
    p = Path(target).expanduser().resolve()
    if not p.is_dir():
        raise ValueError(f"Target directory not found: {p}")
    return p


def _models(provider: str) -> dict[str, str]:
    from agent_ready.cli import _resolve_models

    return _resolve_models(provider, None)


def _check_api_key(models: dict[str, str]) -> None:
    env_var = models.get("api_key_env", "")
    if env_var and not os.environ.get(env_var):
        raise RuntimeError(
            f"{env_var} environment variable is not set. Set it before calling this tool."
        )


def _format_score(result: dict[str, Any]) -> str:
    lines = [f"AGENTIC READINESS SCORE: {result['score']} / {result['max']}", ""]
    for criterion, points in result["rows"]:
        lines.append(f"  {criterion:<42} {points:>4}")
    return "\n".join(lines)


# ── Tools ─────────────────────────────────────────────────────────────────────


@mcp.tool(
    description=(
        "Transform a repository into an AI-agent-ready codebase. "
        "Runs the full pipeline: collect → analyse → generate scaffolding files "
        "(AGENTS.md, CLAUDE.md, system_prompt.md, agent-context.json, mcp.json, "
        "memory/schema.md). Returns the agentic readiness score when done."
    )
)
async def transform(
    ctx: Context,
    target: str,
    provider: str = "anthropic",
    only: str | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> str:
    """
    Args:
        target:   Absolute path to the repository to transform.
        provider: LLM provider — anthropic (default), openai, google, groq,
                  mistral, together, ollama.
        only:     Limit to one file type: agents, tools, context, or memory.
        force:    Overwrite existing generated files.
        dry_run:  Preview what would be generated without writing any files.
    """
    target_path = _resolve(target)
    models = _models(provider)
    _check_api_key(models)

    await ctx.info(f"Starting transform: {target_path.name} [{provider}]")

    from agent_ready.cli import _run_llm_pipeline
    from agent_ready.cli import score as _score

    await ctx.report_progress(0, 3, "Analysing repository…")
    generated = _run_llm_pipeline(
        target=target_path,
        models=models,
        provider_label=provider,
        only=only,
        dry_run=dry_run,
        force=force,
        quiet=True,
    )

    await ctx.report_progress(2, 3, "Scoring…")
    readiness = _score(target_path)

    await ctx.report_progress(3, 3, "Done")

    lines = ["✅ Transformation complete", ""]
    if dry_run:
        lines[0] = "🔍 Dry-run preview (no files written)"
    lines.append("Generated files:")
    for fname, status in generated:
        icon = "✅" if status in ("written", "ok") else "⏭️ "
        lines.append(f"  {icon}  {fname}")
    lines.append("")
    lines.append(_format_score(readiness))
    return "\n".join(lines)


@mcp.tool(
    description=(
        "Return the 100-point agentic readiness score for a repository. "
        "Checks for all scaffolding files locally — no LLM call, instant result."
    )
)
async def score(target: str) -> str:
    """
    Args:
        target: Absolute path to the repository to score.
    """
    from agent_ready.cli import score as _score

    target_path = _resolve(target)
    result = _score(target_path)
    return _format_score(result)


@mcp.tool(
    description=(
        "Run the AgentReady evaluation framework: generates 15 repo-specific questions, "
        "asks them with and without context files, and judges responses using a "
        "three-specialist panel (Factual Accuracy, Semantic Equivalence, Operational Safety). "
        "Returns per-question verdicts, scores, and a summary verdict. "
        "Takes 2–3 minutes — requires scaffolding files to already exist."
    )
)
async def evaluate(
    ctx: Context,
    target: str,
    provider: str = "anthropic",
    fail_level: float = 0.0,
) -> str:
    """
    Args:
        target:     Absolute path to the repository to evaluate.
        provider:   LLM provider for evaluation (default: anthropic).
        fail_level: Float 0.0–1.0. Returns an error if pass rate is below this.
    """
    target_path = _resolve(target)
    models = _models(provider)
    _check_api_key(models)

    await ctx.info(f"Running eval: {target_path.name} [{provider}] — this takes ~2–3 min")
    await ctx.report_progress(0, 4, "Generating questions…")

    from agent_ready import evaluator as _eval

    result = _eval.run_eval(
        target=target_path,
        eval_model=models["evaluation"],
        judge_model=models["evaluation"],
        fail_level=0.0,  # we handle fail_level ourselves below
        quiet=True,
    )

    await ctx.report_progress(4, 4, "Done")

    report_path = _eval.save_eval_report(target_path, result)

    lines = [
        f"{'✅' if result['passed'] else '❌'} Eval complete: {target_path.name}",
        f"Pass rate: {int(result['pass_rate'] * 100)}%  |  "
        f"Context score: {result.get('avg_context_score', 0):.1f}/10  |  "
        f"Baseline: {result.get('avg_baseline_score', 0):.1f}/10",
        f"Report saved: {report_path}",
    ]

    if fail_level > 0 and result["pass_rate"] < fail_level:
        lines.append(
            f"\n❌ Pass rate {int(result['pass_rate'] * 100)}% is below "
            f"threshold {int(fail_level * 100)}%"
        )

    # Per-category summary
    if "by_category" in result:
        lines.append("\nResults by category:")
        for cat, cat_result in result["by_category"].items():
            passed = cat_result.get("passed", 0)
            total = cat_result.get("total", 0)
            lines.append(f"  {cat:<14} {passed}/{total}")

    return "\n".join(lines)


@mcp.tool(
    description=(
        "Review a GitHub pull request grounded in agent-context.json. "
        "Posts an APPROVE or REQUEST_CHANGES review with file-specific comments. "
        "The review understands your architecture, restricted paths, domain concepts, "
        "and known pitfalls before reading a single line of diff."
    )
)
async def review_pr(
    ctx: Context,
    target: str,
    pr_number: int,
    provider: str = "anthropic",
    dry_run: bool = False,
) -> str:
    """
    Args:
        target:    Absolute path to the repository containing the PR.
        pr_number: GitHub PR number to review.
        provider:  LLM provider (default: anthropic).
        dry_run:   Return the review text without posting it to GitHub.
    """
    target_path = _resolve(target)
    models = _models(provider)
    _check_api_key(models)

    await ctx.info(f"Reviewing PR #{pr_number} in {target_path.name}…")

    from agent_ready import reviewer

    result = reviewer.run(
        target=target_path,
        pr_number=pr_number,
        model=models["generation"],
        quiet=True,
    )

    decision = result.get("decision", "COMMENT")
    body = result.get("body", "")

    if not dry_run and result.get("posted"):
        posted_note = "✅ Review posted to GitHub"
    elif dry_run:
        posted_note = "🔍 Dry-run — review NOT posted"
    else:
        posted_note = "⚠️  Review was not posted (check GitHub auth)"

    return f"{posted_note}\nDecision: {decision}\n\n{body}"


# ── Entry point ───────────────────────────────────────────────────────────────


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
