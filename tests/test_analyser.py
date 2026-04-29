from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from agent_ready import analyser
from agent_ready.analyser import extract_verified_facts


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


# ── extract_verified_facts ─────────────────────────────────────────────────


def _make_repo(**overrides) -> dict:
    base = {"file_tree": [], "readme": "", "config_files": {}, "ci_files": {}, "source_files": {}}
    base.update(overrides)
    return base


def test_verified_facts_test_command_from_pyproject():
    repo = _make_repo(config_files={"pyproject.toml": "[tool.pytest.ini_options]\naddopts = '-q'"})
    facts = extract_verified_facts(repo)
    assert facts["test_command"]["value"] == "pytest"
    assert facts["test_command"]["confidence"] == "high"
    assert "pyproject.toml" in facts["test_command"]["source"]


def test_verified_facts_test_command_from_requirements():
    repo = _make_repo(config_files={"requirements.txt": "flask\npytest\n"})
    facts = extract_verified_facts(repo)
    # no pytest in config => not_found (requirements.txt is not a command source)
    assert facts["test_command"]["confidence"] == "not_found"


def test_verified_facts_install_command_pip_requirements():
    repo = _make_repo(config_files={"requirements.txt": "flask\n"})
    facts = extract_verified_facts(repo)
    assert facts["install_command"]["value"] == "pip install -r requirements.txt"
    assert facts["install_command"]["confidence"] == "high"


def test_verified_facts_install_command_npm():
    repo = _make_repo(config_files={"package.json": '{"name": "app"}'})
    facts = extract_verified_facts(repo)
    assert facts["install_command"]["value"] == "npm install"
    assert facts["install_command"]["confidence"] == "inferred"


def test_verified_facts_entry_point_from_file_tree():
    repo = _make_repo(file_tree=["app.py", "requirements.txt"])
    facts = extract_verified_facts(repo)
    assert facts["entry_point"]["value"] == "app.py"
    assert facts["entry_point"]["confidence"] == "high"


def test_verified_facts_entry_point_from_main_block():
    repo = _make_repo(source_files={"myapp.py": 'if __name__ == "__main__":\n    main()'})
    facts = extract_verified_facts(repo)
    assert facts["entry_point"]["value"] == "myapp.py"
    assert facts["entry_point"]["confidence"] == "high"


def test_verified_facts_python_version_from_pyproject():
    repo = _make_repo(config_files={"pyproject.toml": '[project]\nrequires-python = ">=3.11"'})
    facts = extract_verified_facts(repo)
    assert facts["python_version"]["value"] == ">=3.11"
    assert facts["python_version"]["confidence"] == "high"


def test_verified_facts_not_found_when_missing():
    repo = _make_repo()
    facts = extract_verified_facts(repo)
    assert facts["test_command"]["confidence"] == "not_found"
    assert facts["install_command"]["confidence"] == "not_found"
    assert facts["entry_point"]["confidence"] == "not_found"
    assert facts["python_version"]["confidence"] == "not_found"


def test_verified_facts_restricted_paths_from_gitignore():
    gitignore = "dist/\nbuild/\n*.egg-info\n__pycache__/\n"
    repo = _make_repo(config_files={".gitignore": gitignore})
    facts = extract_verified_facts(repo)
    assert facts["restricted_paths"]["confidence"] == "inferred"
    assert any("dist" in v for v in facts["restricted_paths"]["value"])


def test_extract_verified_facts_detects_ruff_from_pyproject():
    """ruff is detected from [tool.ruff] section in pyproject.toml."""
    pyproject = (
        "[tool.ruff]\nline-length = 88\ntarget-version = 'py311'\n\n"
        '[tool.ruff.lint]\nselect = ["E", "F", "I"]\n'
    )
    repo = _make_repo(config_files={"pyproject.toml": pyproject})
    facts = extract_verified_facts(repo)
    assert facts["linter"]["value"] == "ruff"
    assert facts["linter"]["confidence"] == "high"
    assert facts["linter"]["details"]["lint_command"] == "ruff check ."
    assert facts["linter"]["details"]["format_command"] == "ruff format ."


def test_extract_verified_facts_no_linter_when_none_configured():
    """Returns not_found when no linting tools are configured."""
    repo = _make_repo(source_files={"app.py": "print('hello')"})
    facts = extract_verified_facts(repo)
    assert facts["linter"]["confidence"] == "not_found"
    assert facts["linter"]["value"] is None


def test_extract_verified_facts_pyproject_deps_take_priority():
    """pyproject.toml [project].dependencies takes priority over requirements.txt."""
    pyproject = "[project]\nname = 'hello_world'\ndependencies = [\n    \"flask>=2.3\",\n]\n"
    repo = _make_repo(
        config_files={
            "pyproject.toml": pyproject,
            "requirements.txt": "flask>=2.3\npytest>=7.0\n",
        }
    )
    facts = extract_verified_facts(repo)
    assert facts["dependency_manager"]["value"] == "pyproject.toml"
    assert facts["dependency_manager"]["confidence"] == "high"
    assert "pyproject.toml" in facts["dependency_manager"]["details"]["add_dependency_procedure"]
    assert "flask>=2.3" in facts["dependency_manager"]["details"]["dependencies"]


def test_extract_verified_facts_falls_back_to_requirements_txt():
    """requirements.txt is used when pyproject.toml has no [project] section."""
    repo = _make_repo(
        config_files={
            "pyproject.toml": "[build-system]\nrequires = ['setuptools']\n",
            "requirements.txt": "flask>=2.3\n",
        }
    )
    facts = extract_verified_facts(repo)
    assert facts["dependency_manager"]["value"] == "requirements.txt"


def test_extract_verified_facts_do_not_warns_about_requirements():
    """When pyproject.toml is authoritative, do_not warns against requirements.txt."""
    pyproject = "[project]\nname = 'x'\ndependencies = [\"flask>=2.3\"]\n"
    repo = _make_repo(config_files={"pyproject.toml": pyproject})
    facts = extract_verified_facts(repo)
    assert "requirements.txt" in facts["dependency_manager"]["details"]["do_not"]
