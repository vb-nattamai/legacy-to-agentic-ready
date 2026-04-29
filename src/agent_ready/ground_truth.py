"""Ground truth extraction from raw source code (not from generated context files).

This module breaks the circularity in the v1 eval: instead of having the LLM fill
ground truth from the context files it just generated, we extract ground truth by
reading the raw source files — static parsing where possible, haiku LLM call on raw
code as fallback. The context files are never consulted here.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from agent_ready.generator import _usage_totals

# ── Static extractors ─────────────────────────────────────────────────────────


def _read_file(target: Path, filename: str) -> str | None:
    """Read a file from the target repo, return content or None."""
    p = target / filename
    if p.exists():
        try:
            return p.read_text(errors="ignore")[:4000]
        except Exception:
            return None
    return None


def _jsonpath_get(data: dict, dotpath: str) -> str | None:
    """Traverse a dict by dot-separated keys (e.g. 'scripts.test')."""
    parts = dotpath.split(".")
    current: Any = data
    for part in parts:
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    if current is None:
        return None
    if isinstance(current, dict):
        return json.dumps(current, indent=2)
    return str(current)


def _extract_static(target: Path, source: dict[str, Any]) -> str | None:
    """Try one static source definition and return its value or None."""
    filename = source.get("file")
    if not filename:
        return None

    content = _read_file(target, filename)

    # exists: return a fixed string if the file exists
    if "exists" in source:
        return source["exists"] if content is not None else None

    if content is None:
        return None

    # read: return full file content
    if source.get("read"):
        return content.strip()

    # jsonpath: parse JSON/JSONC and traverse
    if "jsonpath" in source and filename.endswith(".json"):
        try:
            data = json.loads(content)
            return _jsonpath_get(data, source["jsonpath"])
        except Exception:
            return None

    # grep: return first matching line
    if "grep" in source:
        pattern = source["grep"]
        for line in content.splitlines():
            if re.search(pattern, line, re.IGNORECASE):
                return line.strip()
        return None

    # pattern: return first line matching regex (anchored patterns like ^test:)
    if "pattern" in source:
        for line in content.splitlines():
            if re.match(source["pattern"], line.strip()):
                return line.strip()
        return None

    # toml_path: basic TOML section/key lookup (no full TOML parser required)
    if "toml_path" in source:
        return _toml_get(content, source["toml_path"])

    # makefile_cmd: extract the command body for a Makefile target (not the label)
    if "makefile_cmd" in source:
        return _extract_makefile_command(content, source["makefile_cmd"])

    # exists_section: return a value when a TOML section header like [tool.ruff] is present
    if "exists_section" in source:
        section_header = f"[{source['exists_section']}]"
        for line in content.splitlines():
            if line.strip() == section_header:
                return source.get("value", source["exists_section"].split(".")[-1])
        return None

    return None


def _toml_get(content: str, dotpath: str) -> str | None:
    """Very basic TOML key extraction — handles [section] headers and key=value."""
    parts = dotpath.split(".")
    if not parts:
        return None

    # Build section header to look for, e.g. "tool.pytest.ini_options" -> [tool.pytest.ini_options]
    section = ".".join(parts[:-1])
    key = parts[-1]

    in_section = section == ""
    for line in content.splitlines():
        stripped = line.strip()
        # Section header detection
        if stripped.startswith("[") and stripped.endswith("]"):
            header = stripped[1:-1].strip()
            in_section = header == section
            continue
        if in_section and stripped.startswith(key):
            # Match "key = value" or "key=value"
            m = re.match(rf"^{re.escape(key)}\s*=\s*(.+)", stripped)
            if m:
                return m.group(1).strip().strip('"').strip("'")
    return None


def _glob_match(target: Path, pattern: str) -> str | None:
    """Return the first match of a glob pattern relative to target, or None."""
    matches = list(target.glob(pattern))
    return str(matches[0].relative_to(target)) if matches else None


def _extract_makefile_command(content: str, target: str) -> str | None:
    """Extract the command body for a given Makefile target (not the label itself).

    Example Makefile:
        test:
            pytest

    _extract_makefile_command(content, "test") -> "pytest"
    """
    lines = content.splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Match "test:" or "test: dep1 dep2"
        if stripped == f"{target}:" or stripped.startswith(f"{target}:"):
            # Find the next line that is a tab-indented command body
            for j in range(i + 1, len(lines)):
                cmd_line = lines[j]
                if cmd_line.startswith("\t") or cmd_line.startswith("    "):
                    return cmd_line.strip()
                # Stop if we hit a non-blank, non-comment line that isn't indented
                if cmd_line.strip() and not cmd_line.startswith("#"):
                    break
    return None


def _extract_dependency_source(file_contents: dict[str, str]) -> dict[str, str | None]:
    """Return the authoritative dependency management file and its content.

    pyproject.toml with a [project] dependencies section takes priority over
    requirements.txt, which may be present as a convenience file only.
    """
    pyproject = file_contents.get("pyproject.toml", "")
    if "[project]" in pyproject and "dependencies" in pyproject:
        return {
            "file": "pyproject.toml",
            "content": pyproject,
            "note": "pyproject.toml [project].dependencies is authoritative",
        }
    reqs = file_contents.get("requirements.txt", "")
    if reqs:
        return {
            "file": "requirements.txt",
            "content": reqs,
            "note": "requirements.txt is the dependency source",
        }
    return {"file": None, "content": "", "note": "No dependency file found"}


def _extract_linting_tools(pyproject_content: str) -> dict[str, str]:
    """Extract linting and formatting tools from pyproject.toml."""
    tools: dict[str, str] = {}

    if "[tool.ruff]" in pyproject_content:
        tools["linter"] = "ruff"
        tools["formatter"] = "ruff format"
        for line in pyproject_content.splitlines():
            if "line-length" in line and "=" in line:
                tools["line_length"] = line.split("=")[-1].strip()
            if line.strip().startswith("select") and "=" in line:
                tools["rules"] = line.split("=")[-1].strip()

    if "[tool.mypy]" in pyproject_content:
        tools["type_checker"] = "mypy"

    if not tools:
        tools["note"] = "No linting tools configured"

    return tools


# ── LLM extractor ─────────────────────────────────────────────────────────────

_GROUND_TRUTH_SYSTEM = (
    "You are a precise code analyst. Answer questions about source code based ONLY "
    "on what is present in the provided files. If you cannot determine the answer "
    "from the files, say 'Not determinable from source'. Do not hallucinate or guess. "
    "Be concise — 1-3 sentences maximum."
)

_MAX_SOURCE_CHARS = 20_000  # cap total context sent to haiku


def _llm_extract(
    source_files: dict[str, str],
    llm_prompt: str,
    baseline_model: str,
) -> str:
    """Ask the baseline (haiku) model to extract ground truth from raw source code."""
    import litellm  # lazy import — not needed for static-only questions

    # Build a compact source context (skip generated/binary files)
    parts: list[str] = []
    total = 0
    skip_extensions = {".png", ".jpg", ".gif", ".ico", ".woff", ".woff2", ".ttf", ".pdf"}
    skip_patterns = {
        "AGENTIC_EVAL.md",
        "agent-context.json",
        "AGENTS.md",
        "CLAUDE.md",
        "system_prompt.md",
        "mcp.json",
        "memory/schema.md",
        ".github/copilot-instructions.md",
    }

    for path, content in sorted(source_files.items()):
        if any(path.endswith(ext) for ext in skip_extensions):
            continue
        if any(skip in path for skip in skip_patterns):
            continue
        if total >= _MAX_SOURCE_CHARS:
            break
        snippet = content[:2000]
        parts.append(f"=== {path} ===\n{snippet}")
        total += len(snippet)

    if not parts:
        return "No source files available."

    source_context = "\n\n".join(parts)

    messages = [
        {"role": "system", "content": _GROUND_TRUTH_SYSTEM},
        {
            "role": "user",
            "content": (f"Source files:\n\n{source_context}\n\nQuestion: {llm_prompt}"),
        },
    ]
    try:
        resp = litellm.completion(
            model=baseline_model,
            messages=messages,
            max_tokens=300,
            temperature=0,
        )
        if hasattr(resp, "usage") and resp.usage is not None:
            if baseline_model not in _usage_totals["by_model"]:
                _usage_totals["by_model"][baseline_model] = {"input": 0, "output": 0}
            in_toks = (
                getattr(resp.usage, "input_tokens", None)
                or getattr(resp.usage, "prompt_tokens", 0)
                or 0
            )
            out_toks = (
                getattr(resp.usage, "output_tokens", None)
                or getattr(resp.usage, "completion_tokens", 0)
                or 0
            )
            _usage_totals["input_tokens"] += in_toks
            _usage_totals["output_tokens"] += out_toks
            _usage_totals["calls"] += 1
            _usage_totals["by_model"][baseline_model]["input"] += in_toks
            _usage_totals["by_model"][baseline_model]["output"] += out_toks
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"Extraction failed: {e}"


# ── Public API ─────────────────────────────────────────────────────────────────


def extract_ground_truth(
    target: Path,
    question: dict[str, Any],
    source_files: dict[str, str],
    baseline_model: str,
) -> str:
    """
    Extract ground truth for one question from raw source code.

    Args:
        target:        Path to the target repository root.
        question:      A golden-set question dict with 'ground_truth_extraction' key.
        source_files:  Raw source file contents {relative_path: content} from analyser.collect().
        baseline_model: Model ID to use for LLM extraction fallback (e.g. claude-haiku-4-5).

    Returns:
        A ground truth string derived from source code, never from generated context files.
    """
    extraction = question.get("ground_truth_extraction", {})
    method = extraction.get("method", "llm")
    llm_prompt = extraction.get("llm_prompt", question.get("prompt", ""))

    if method == "static_then_llm":
        # Try static sources in order; fall back to LLM if none succeed
        for source in extraction.get("static_sources", []):
            # Handle glob sources
            if "glob" in source:
                result = _glob_match(target, source["glob"])
                if result:
                    return result
            else:
                result = _extract_static(target, source)
                if result:
                    return result
        # All static sources exhausted — use LLM on raw code
        return _llm_extract(source_files, llm_prompt, baseline_model)

    elif method == "static":
        for source in extraction.get("static_sources", []):
            if "glob" in source:
                result = _glob_match(target, source["glob"])
                if result:
                    return result
            else:
                result = _extract_static(target, source)
                if result:
                    return result
        return "Not determinable from static analysis."

    else:  # method == "llm" or default
        return _llm_extract(source_files, llm_prompt, baseline_model)


def extract_all(
    target: Path,
    questions: list[dict[str, Any]],
    source_files: dict[str, str],
    baseline_model: str,
    quiet: bool = False,
) -> dict[str, str]:
    """
    Extract ground truth for all questions. Returns {question_id: ground_truth}.

    Ground truth is always derived from raw source files — never from
    agent-context.json, AGENTS.md, CLAUDE.md, or any other generated file.
    """
    if not quiet:
        print(f"  🔍 Extracting ground truth from source code ({len(questions)} questions)...")

    results: dict[str, str] = {}
    for q in questions:
        qid = q["id"]
        gt = extract_ground_truth(target, q, source_files, baseline_model)
        results[qid] = gt
        if not quiet and gt and len(gt) < 120:
            print(f"     {qid}: {gt}")

    return results
