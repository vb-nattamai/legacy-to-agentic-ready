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


def test_collect_caps_source_files_at_max_source_files(tmp_path: Path) -> None:
    for idx in range(analyser.MAX_SOURCE_FILES + 5):
        _write(tmp_path / "src" / f"file_{idx:03}.py", "x = 1\n")

    collected = analyser.collect(tmp_path, quiet=True)
    source_files = collected["source_files"]

    assert len(source_files) == analyser.MAX_SOURCE_FILES
    assert "src/file_000.py" in source_files
    assert f"src/file_{analyser.MAX_SOURCE_FILES + 1:03}.py" not in source_files
