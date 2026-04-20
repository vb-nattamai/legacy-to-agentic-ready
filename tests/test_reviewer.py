from __future__ import annotations

import json

from agent_ready import reviewer

# ── load_context ──────────────────────────────────────────────────────────────


def test_load_context_returns_none_when_file_missing(tmp_path):
    assert reviewer.load_context(tmp_path) is None


def test_load_context_parses_valid_json(tmp_path):
    ctx = {"static": {"project_name": "X"}, "dynamic": {}}
    (tmp_path / "agent-context.json").write_text(json.dumps(ctx))
    assert reviewer.load_context(tmp_path) == ctx


def test_load_context_returns_none_on_malformed_json(tmp_path):
    (tmp_path / "agent-context.json").write_text("{broken")
    assert reviewer.load_context(tmp_path) is None


# ── truncate_diff ─────────────────────────────────────────────────────────────


def test_truncate_diff_leaves_short_diff_unchanged():
    d = "a" * 100
    assert reviewer.truncate_diff(d, max_chars=200) == d


def test_truncate_diff_truncates_at_limit():
    d = "x" * 5000
    result = reviewer.truncate_diff(d, max_chars=1000)
    assert len(result) < 5000
    assert "truncated" in result


def test_truncate_diff_exact_boundary():
    d = "z" * 1000
    assert reviewer.truncate_diff(d, max_chars=1000) == d


# ── build_review_prompt ───────────────────────────────────────────────────────


def test_build_review_prompt_includes_pr_title():
    meta = {"title": "My unique PR", "body": "", "author": "bob", "files": [], "checks": ""}
    assert "My unique PR" in reviewer.build_review_prompt(None, meta, "")


def test_build_review_prompt_without_context_still_works():
    meta = {"title": "T", "body": "B", "author": "a", "files": ["x.py"], "checks": "SUCCESS"}
    prompt = reviewer.build_review_prompt(None, meta, "diff content")
    assert "diff content" in prompt
    assert "x.py" in prompt


def test_build_review_prompt_includes_restricted_paths():
    ctx = {
        "static": {
            "project_name": "App",
            "description": "",
            "primary_language": "Go",
            "frameworks": [],
            "restricted_write_paths": ["go.sum", ".env"],
            "domain_concepts": [],
        },
        "dynamic": {
            "agent_safe_operations": [],
            "agent_forbidden_operations": [],
            "potential_pitfalls": [],
            "architecture_summary": "",
            "test_command": "",
            "build_command": "",
        },
    }
    meta = {"title": "T", "body": "", "author": "a", "files": [], "checks": ""}
    prompt = reviewer.build_review_prompt(ctx, meta, "")
    assert "go.sum" in prompt
    assert ".env" in prompt


# ── parse_review_response ─────────────────────────────────────────────────────


def test_parse_review_response_approve():
    raw = json.dumps({"decision": "APPROVE", "summary": "ok", "issues": [], "body": "LGTM"})
    r = reviewer.parse_review_response(raw)
    assert r["decision"] == "APPROVE"
    assert r["body"] == "LGTM"


def test_parse_review_response_request_changes():
    raw = json.dumps(
        {
            "decision": "REQUEST_CHANGES",
            "summary": "bugs",
            "issues": [{"severity": "BLOCKER", "file": "a.py", "line": "10", "comment": "bad"}],
            "body": "Fix it.",
        }
    )
    r = reviewer.parse_review_response(raw)
    assert r["decision"] == "REQUEST_CHANGES"
    assert len(r["issues"]) == 1


def test_parse_review_response_strips_markdown_fences():
    inner = json.dumps({"decision": "APPROVE", "summary": "ok", "issues": [], "body": "ok"})
    raw = f"```json\n{inner}\n```"
    r = reviewer.parse_review_response(raw)
    assert r["decision"] == "APPROVE"


def test_parse_review_response_fallback_on_invalid_json():
    r = reviewer.parse_review_response("Not JSON at all.")
    assert r["decision"] == "REQUEST_CHANGES"
    assert r["body"] == "Not JSON at all."


def test_parse_review_response_fixes_invalid_decision():
    raw = json.dumps({"decision": "MAYBE", "body": "hmm"})
    r = reviewer.parse_review_response(raw)
    assert r["decision"] == "REQUEST_CHANGES"


def test_parse_review_response_adds_missing_issues_key():
    raw = json.dumps({"decision": "APPROVE", "summary": "ok", "body": "ok"})
    r = reviewer.parse_review_response(raw)
    assert r["issues"] == []


def test_build_review_prompt_exercises_all_context_branches():
    """Cover description, frameworks, arch_summary, forbidden_ops, domain_concepts, pitfalls."""
    ctx = {
        "static": {
            "project_name": "FoodApp",
            "description": "A food delivery platform",
            "primary_language": "Go",
            "frameworks": ["Gin", "GORM"],
            "restricted_write_paths": ["go.sum"],
            "domain_concepts": ["Order", "Driver", "Restaurant"],
        },
        "dynamic": {
            "agent_safe_operations": [],
            "agent_forbidden_operations": ["Drop tables", "DELETE without WHERE"],
            "potential_pitfalls": ["Race condition on orders", "N+1 queries"],
            "architecture_summary": "Event-driven microservices",
            "test_command": "go test ./...",
            "build_command": "go build",
        },
    }
    meta = {"title": "T", "body": "", "author": "", "files": [], "checks": ""}
    prompt = reviewer.build_review_prompt(ctx, meta, "")
    assert "A food delivery platform" in prompt
    assert "Gin" in prompt
    assert "Event-driven microservices" in prompt
    assert "Drop tables" in prompt
    assert "Order" in prompt
    assert "Race condition on orders" in prompt


# ── fetch_pr_diff ─────────────────────────────────────────────────────────────


def test_fetch_pr_diff_returns_stdout_on_success(tmp_path):
    from unittest.mock import MagicMock, patch

    mock = MagicMock()
    mock.stdout = "diff --git a/foo.py b/foo.py\n+new line"
    with patch("subprocess.run", return_value=mock):
        result = reviewer.fetch_pr_diff(42, tmp_path)
    assert result == mock.stdout


def test_fetch_pr_diff_returns_empty_string_on_error(tmp_path):
    from unittest.mock import patch

    with patch("subprocess.run", side_effect=Exception("gh not found")):
        result = reviewer.fetch_pr_diff(42, tmp_path)
    assert result == ""


# ── fetch_pr_metadata ─────────────────────────────────────────────────────────


def test_fetch_pr_metadata_parses_response(tmp_path):
    from unittest.mock import MagicMock, patch

    payload = {
        "title": "My PR",
        "body": "description",
        "author": {"login": "alice"},
        "files": [{"path": "src/main.py"}, {"path": "tests/test_main.py"}],
        "statusCheckRollup": [{"state": "SUCCESS"}],
    }
    mock = MagicMock()
    mock.stdout = json.dumps(payload)
    with patch("subprocess.run", return_value=mock):
        meta = reviewer.fetch_pr_metadata(1, tmp_path)
    assert meta["title"] == "My PR"
    assert meta["author"] == "alice"
    assert meta["files"] == ["src/main.py", "tests/test_main.py"]
    assert meta["checks"] == "SUCCESS"


def test_fetch_pr_metadata_returns_empty_dict_on_error(tmp_path):
    from unittest.mock import patch

    with patch("subprocess.run", side_effect=Exception("fail")):
        meta = reviewer.fetch_pr_metadata(1, tmp_path)
    assert meta == {"title": "", "body": "", "author": "", "files": [], "checks": ""}


def test_fetch_pr_metadata_handles_string_author(tmp_path):
    from unittest.mock import MagicMock, patch

    payload = {
        "title": "T",
        "body": "",
        "author": "plain-string-author",
        "files": [],
        "statusCheckRollup": [],
    }
    mock = MagicMock()
    mock.stdout = json.dumps(payload)
    with patch("subprocess.run", return_value=mock):
        meta = reviewer.fetch_pr_metadata(1, tmp_path)
    assert meta["author"] == "plain-string-author"
    assert meta["checks"] == ""


# ── post_review ───────────────────────────────────────────────────────────────


def test_post_review_returns_true_on_success(tmp_path):
    from unittest.mock import MagicMock, patch

    with patch("subprocess.run", return_value=MagicMock()):
        result = reviewer.post_review(1, "APPROVE", "LGTM", tmp_path)
    assert result is True


def test_post_review_returns_false_on_exception(tmp_path):
    from unittest.mock import patch

    with patch("subprocess.run", side_effect=Exception("fail")):
        result = reviewer.post_review(1, "APPROVE", "LGTM", tmp_path)
    assert result is False


def test_post_review_uses_approve_flag(tmp_path):
    from unittest.mock import MagicMock, patch

    with patch("subprocess.run", return_value=MagicMock()) as mock_run:
        reviewer.post_review(1, "APPROVE", "Looks good", tmp_path)
    cmd = mock_run.call_args[0][0]
    assert "--approve" in cmd
    assert "--request-changes" not in cmd


def test_post_review_uses_request_changes_flag(tmp_path):
    from unittest.mock import MagicMock, patch

    with patch("subprocess.run", return_value=MagicMock()) as mock_run:
        reviewer.post_review(1, "REQUEST_CHANGES", "Fix it", tmp_path)
    cmd = mock_run.call_args[0][0]
    assert "--request-changes" in cmd
    assert "--approve" not in cmd


def test_post_review_subprocess_uses_list_not_shell(tmp_path):
    """Ensure no shell=True — guards against command injection."""
    from unittest.mock import MagicMock, patch

    with patch("subprocess.run", return_value=MagicMock()) as mock_run:
        reviewer.post_review(1, "APPROVE", "ok", tmp_path)
    _, kwargs = mock_run.call_args
    assert kwargs.get("shell", False) is False


# ── run() ─────────────────────────────────────────────────────────────────────


def test_run_returns_approve_review(tmp_path):
    """Full run() with all external calls mocked — no LLM, no gh CLI."""
    from unittest.mock import MagicMock, patch

    approve_json = '{"decision": "APPROVE", "summary": "LGTM", "issues": [], "body": "Approved."}'

    mock_litellm = MagicMock()
    with (
        patch.dict("sys.modules", {"litellm": mock_litellm}),
        patch(
            "agent_ready.reviewer.fetch_pr_metadata",
            return_value={
                "title": "Add caching",
                "body": "Adds Redis",
                "author": "dev",
                "files": ["cache.py"],
                "checks": "SUCCESS",
            },
        ),
        patch("agent_ready.reviewer.fetch_pr_diff", return_value="+import redis"),
        patch("agent_ready.generator._call", return_value=approve_json),
    ):
        result = reviewer.run(tmp_path, 7, "test-model", quiet=True)

    assert result["decision"] == "APPROVE"
    assert result["issues"] == []
    assert result["body"] == "Approved."


def test_run_returns_request_changes_review(tmp_path):
    """run() propagates REQUEST_CHANGES verdict correctly."""
    from unittest.mock import MagicMock, patch

    rc_json = (
        '{"decision": "REQUEST_CHANGES", "summary": "Bug found", '
        '"issues": [{"severity": "BLOCKER", "file": "a.py", "line": "5", "comment": "null deref"}], '
        '"body": "Please fix."}'
    )
    mock_litellm = MagicMock()
    with (
        patch.dict("sys.modules", {"litellm": mock_litellm}),
        patch(
            "agent_ready.reviewer.fetch_pr_metadata",
            return_value={
                "title": "Bad change",
                "body": "",
                "author": "dev",
                "files": ["a.py"],
                "checks": "FAILURE",
            },
        ),
        patch("agent_ready.reviewer.fetch_pr_diff", return_value="-safe_call()\n+unsafe()"),
        patch("agent_ready.generator._call", return_value=rc_json),
    ):
        result = reviewer.run(tmp_path, 3, "test-model", quiet=True)

    assert result["decision"] == "REQUEST_CHANGES"
    assert len(result["issues"]) == 1


def test_run_raises_without_litellm(tmp_path):
    """run() gives a clear error when litellm is not installed."""
    import sys
    from unittest.mock import patch

    saved = sys.modules.pop("litellm", None)
    try:
        with patch.dict("sys.modules", {"litellm": None}):
            try:
                reviewer.run(tmp_path, 1, "test-model", quiet=True)
                assert False, "should have raised"
            except (ImportError, TypeError):
                pass
    finally:
        if saved is not None:
            sys.modules["litellm"] = saved


def test_run_verbose_output(tmp_path, capsys):
    """run() with quiet=False exercises the progress print statements."""
    from unittest.mock import MagicMock, patch

    approve_json = '{"decision": "APPROVE", "summary": "ok", "issues": [], "body": "ok"}'
    mock_litellm = MagicMock()
    with (
        patch.dict("sys.modules", {"litellm": mock_litellm}),
        patch(
            "agent_ready.reviewer.fetch_pr_metadata",
            return_value={
                "title": "T",
                "body": "",
                "author": "a",
                "files": [],
                "checks": "",
            },
        ),
        patch("agent_ready.reviewer.fetch_pr_diff", return_value=""),
        patch("agent_ready.generator._call", return_value=approve_json),
    ):
        result = reviewer.run(tmp_path, 1, "test-model", quiet=False)

    captured = capsys.readouterr()
    assert "Reviewing PR" in captured.out
    assert "APPROVE" in captured.out
    assert result["decision"] == "APPROVE"
