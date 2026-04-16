"""
AgentReady - PR Reviewer

Reviews pull requests using LLM reasoning grounded in the repo's
agent-context.json. Provider-agnostic via LiteLLM.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

# ── Pure helpers ──────────────────────────────────────────────────────────────


def load_context(target: Path) -> dict[str, Any] | None:
    """Read agent-context.json from target; return None if missing or malformed."""
    ctx_file = target / "agent-context.json"
    if not ctx_file.exists():
        return None
    try:
        return json.loads(ctx_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def truncate_diff(diff: str, max_chars: int = 12000) -> str:
    """Return diff truncated to max_chars with a suffix when trimmed."""
    if len(diff) <= max_chars:
        return diff
    suffix = "\n... truncated ..."
    return diff[:max_chars] + suffix


def build_review_prompt(context: dict | None, pr_metadata: dict, diff: str) -> str:
    """Construct the LLM review prompt from context and PR metadata."""
    lines: list[str] = []

    lines.append("You are an expert code reviewer. Review the following pull request.")
    lines.append("")
    lines.append("Respond ONLY with a valid JSON object — no markdown, no preamble — with keys:")
    lines.append('  "decision": "APPROVE" or "REQUEST_CHANGES"')
    lines.append('  "summary": one-sentence summary')
    lines.append('  "issues": list of {severity, file, line, comment} (empty list if none)')
    lines.append('  "body": full markdown review body')
    lines.append("")

    if context is not None:
        static = context.get("static", {})
        dynamic = context.get("dynamic", {})

        project_name = static.get("project_name", "")
        description = static.get("description", "")
        primary_language = static.get("primary_language", "")
        frameworks = static.get("frameworks", [])
        restricted = static.get("restricted_write_paths", [])
        domain_concepts = static.get("domain_concepts", [])

        arch_summary = dynamic.get("architecture_summary", "")
        forbidden_ops = dynamic.get("agent_forbidden_operations", [])
        pitfalls = dynamic.get("potential_pitfalls", [])

        lines.append("## Repository Context (agent-context.json)")
        if project_name:
            lines.append(f"Project: {project_name}")
        if description:
            lines.append(f"Description: {description}")
        if primary_language:
            lines.append(f"Language: {primary_language}")
        if frameworks:
            lines.append(f"Frameworks: {', '.join(frameworks)}")
        if arch_summary:
            lines.append(f"Architecture: {arch_summary}")
        if restricted:
            lines.append(f"Restricted write paths (must not be modified): {', '.join(restricted)}")
        if forbidden_ops:
            lines.append(f"Forbidden operations: {'; '.join(forbidden_ops)}")
        if domain_concepts:
            lines.append(f"Domain concepts: {', '.join(str(c) for c in domain_concepts)}")
        if pitfalls:
            lines.append("Known pitfalls:")
            for p in pitfalls:
                lines.append(f"  - {p}")
        lines.append("")

    lines.append("## Pull Request")
    lines.append(f"Title: {pr_metadata.get('title', '')}")
    author = pr_metadata.get("author", "")
    if author:
        lines.append(f"Author: {author}")
    body = pr_metadata.get("body", "")
    if body:
        lines.append(f"Description: {body}")
    files = pr_metadata.get("files", [])
    if files:
        lines.append(f"Files changed: {', '.join(files)}")
    checks = pr_metadata.get("checks", "")
    if checks:
        lines.append(f"CI status: {checks}")
    lines.append("")

    lines.append("## Diff")
    lines.append(diff if diff else "(no diff)")
    lines.append("")

    lines.append("Respond ONLY with a JSON object. No markdown fences, no extra text.")

    return "\n".join(lines)


def parse_review_response(response: str) -> dict[str, Any]:
    """Parse LLM JSON response; fallback to REQUEST_CHANGES on failure."""
    text = response.strip()

    # Strip markdown fences
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()

    try:
        result = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return {
            "decision": "REQUEST_CHANGES",
            "summary": "Could not parse LLM response.",
            "issues": [],
            "body": response,
        }

    # Ensure valid decision
    if result.get("decision") not in ("APPROVE", "REQUEST_CHANGES"):
        result["decision"] = "REQUEST_CHANGES"

    # Ensure issues key exists
    if "issues" not in result:
        result["issues"] = []

    return result


# ── IO functions (subprocess / gh CLI) ────────────────────────────────────────


def fetch_pr_metadata(pr_number: int, cwd: Path) -> dict[str, Any]:
    """Fetch PR metadata via gh CLI."""
    try:
        result = subprocess.run(
            [
                "gh",
                "pr",
                "view",
                str(pr_number),
                "--json",
                "title,body,author,files,statusCheckRollup",
            ],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        raw = json.loads(result.stdout)
        files = [f.get("path", "") for f in raw.get("files", [])]
        checks_list = raw.get("statusCheckRollup", [])
        checks = checks_list[0].get("state", "") if checks_list else ""
        author_obj = raw.get("author", {})
        author = author_obj.get("login", "") if isinstance(author_obj, dict) else str(author_obj)
        return {
            "title": raw.get("title", ""),
            "body": raw.get("body", ""),
            "author": author,
            "files": files,
            "checks": checks,
        }
    except Exception:
        return {"title": "", "body": "", "author": "", "files": [], "checks": ""}


def fetch_pr_diff(pr_number: int, cwd: Path) -> str:
    """Fetch PR diff via gh CLI; return empty string on failure."""
    try:
        result = subprocess.run(
            ["gh", "pr", "diff", str(pr_number)],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout
    except Exception:
        return ""


def post_review(pr_number: int, decision: str, body: str, cwd: Path) -> bool:
    """Post a review via gh CLI; return True on success."""
    flag = "--approve" if decision == "APPROVE" else "--request-changes"
    try:
        subprocess.run(
            ["gh", "pr", "review", str(pr_number), flag, "--body", body],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        return True
    except Exception:
        return False


# ── Main entry point ──────────────────────────────────────────────────────────


def run(target: Path, pr_number: int, model: str, quiet: bool = False) -> dict[str, Any]:
    """Orchestrate PR review: load context → fetch → prompt → LLM → parse."""
    try:
        import litellm

        from agent_ready.generator import _call
    except ImportError:
        raise ImportError("litellm not installed. Run: pip install 'agent-ready[ai]'")

    # Prevent LiteLLM from printing prompt/response content to stdout.
    # Prompts include the PR diff which may contain credential-like strings.
    litellm.suppress_debug_info = True
    litellm.set_verbose = False  # type: ignore[attr-defined]

    if not quiet:
        print(f"  🔍 Reviewing PR #{pr_number}...")

    context = load_context(target)
    metadata = fetch_pr_metadata(pr_number, target)
    diff = fetch_pr_diff(pr_number, target)
    diff = truncate_diff(diff)

    prompt = build_review_prompt(context, metadata, diff)

    if not quiet:
        print(f"  🤖 Calling {model}...")

    raw = _call(model=model, prompt=prompt, max_tokens=4000)
    review = parse_review_response(raw)

    if not quiet:
        icon = "✅" if review["decision"] == "APPROVE" else "🔴"
        print(f"  {icon} Decision: {review['decision']}")

    return review
