from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from agent_ready import analyser


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_collect_skips_ignored_and_generated_content(tmp_path: Path) -> None:
    _write(tmp_path / "src" / "app.py", "print('ok')\n")
    _write(tmp_path / "tests" / "test_app.py", "def test_noop():\n    assert True\n")
    _write(tmp_path / "memory" / "state.py", "print('generated')\n")
    _write(tmp_path / "tools" / "example_tool.py", "print('generated')\n")
    _write(tmp_path / "node_modules" / "pkg" / "index.js", "console.log('skip')\n")
    _write(tmp_path / ".git" / "hooks" / "pre-commit", "echo skip\n")
    _write(tmp_path / "AGENTS.md", "# generated\n")
    _write(
        tmp_path / "src" / "large.py",
        "x" * ((analyser.MAX_FILE_KB * 1024) + 10),
    )
    _write(tmp_path / "openapi.yaml", "openapi: 3.0.0\n")

    collected = analyser.collect(tmp_path, quiet=True)

    assert "src/app.py" in collected["source_files"]
    assert "tests/test_app.py" not in collected["source_files"]
    assert "memory/state.py" not in collected["source_files"]
    assert "tools/example_tool.py" not in collected["source_files"]
    assert "src/large.py" not in collected["source_files"]
    assert collected["has_openapi"] is True


def test_collect_excludes_agent_ready_workflows_from_ci_files(tmp_path: Path) -> None:
    """AgentReady's own workflow files must NOT appear in ci_files sent to the LLM."""
    _write(tmp_path / "src" / "app.py", "print('app')\n")
    _write(tmp_path / ".github" / "workflows" / "agentic-ready.yml", "name: Agentic Ready\n")
    _write(tmp_path / ".github" / "workflows" / "agentic-ready-eval.yml", "name: Eval\n")
    _write(tmp_path / ".github" / "workflows" / "context-drift-detector.yml", "name: Drift\n")
    _write(tmp_path / ".github" / "workflows" / "pr-review.yml", "name: PR Review\n")
    _write(tmp_path / ".github" / "workflows" / "ci.yml", "name: CI\non: [push]\n")

    collected = analyser.collect(tmp_path, quiet=True)

    ci_filenames = {Path(k).name for k in collected["ci_files"]}
    # The app's own CI should be kept
    assert "ci.yml" in ci_filenames, "App's own CI workflow should be included"
    # All agent-ready workflows must be excluded
    for skipped in (
        "agentic-ready.yml",
        "agentic-ready-eval.yml",
        "context-drift-detector.yml",
        "pr-review.yml",
    ):
        assert skipped not in ci_filenames, f"{skipped} should be filtered out of ci_files"


def test_collect_excludes_agent_ready_files_from_file_tree(tmp_path: Path) -> None:
    """AgentReady generated files and its workflows must not appear in file_tree."""
    _write(tmp_path / "src" / "app.py", "print('app')\n")
    _write(tmp_path / "AGENTS.md", "# generated\n")
    _write(tmp_path / "CLAUDE.md", "# generated\n")
    _write(tmp_path / "agent-context.json", "{}\n")
    _write(tmp_path / "mcp.json", "{}\n")
    _write(tmp_path / "AGENTIC_EVAL.md", "# eval\n")
    _write(tmp_path / ".github" / "workflows" / "agentic-ready.yml", "name: AR\n")
    _write(tmp_path / ".agent-ready" / "custom_questions.json", "{}\n")

    collected = analyser.collect(tmp_path, quiet=True)
    tree = collected["file_tree"]

    assert "src/app.py" in tree
    for excluded in (
        "AGENTS.md",
        "CLAUDE.md",
        "agent-context.json",
        "mcp.json",
        "AGENTIC_EVAL.md",
        ".github/workflows/agentic-ready.yml",
    ):
        assert excluded not in tree, f"{excluded} should be excluded from file_tree"


def test_collect_excludes_agent_ready_dirs_from_file_tree(tmp_path: Path) -> None:
    """The .agent-ready dir should not appear in the file tree."""
    _write(tmp_path / "src" / "app.py", "print('app')\n")
    _write(tmp_path / ".agent-ready" / "custom_questions.json", "{}\n")
    _write(tmp_path / "memory" / "schema.md", "# schema\n")
    _write(tmp_path / "tools" / "refresh_context.py", "# refresh\n")

    collected = analyser.collect(tmp_path, quiet=True)
    tree = collected["file_tree"]

    assert "src/app.py" in tree
    assert not any(".agent-ready" in p for p in tree)
    assert not any(p.startswith("memory/") for p in tree)
    assert not any(p.startswith("tools/") for p in tree)

    for idx in range(analyser.MAX_SOURCE_FILES + 5):
        _write(tmp_path / "src" / f"file_{idx:03}.py", "x = 1\n")

    collected = analyser.collect(tmp_path, quiet=True)
    source_files = collected["source_files"]

    assert len(source_files) == analyser.MAX_SOURCE_FILES
    assert "src/file_000.py" in source_files
    assert f"src/file_{analyser.MAX_SOURCE_FILES + 1:03}.py" not in source_files
