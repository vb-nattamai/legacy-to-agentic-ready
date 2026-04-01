#!/usr/bin/env python3
"""
AgentReady — CLI Transformer v2.0

Transforms any repository into an AI-agent-ready codebase using LLM-first
analysis.  Provider-agnostic via LiteLLM — use any of the built-in presets
or pass any LiteLLM-compatible model string with --model.

Usage:
  agent-ready --target /path/to/repo
  agent-ready --target /path/to/repo --provider openai
  agent-ready --target /path/to/repo --provider groq
  agent-ready --target /path/to/repo --provider ollama
  agent-ready --target /path/to/repo --model ollama/llama3.2
  agent-ready --target /path/to/repo --model groq/llama-3.3-70b-versatile
  agent-ready --target /path/to/repo --only agents
  agent-ready --target /path/to/repo --dry-run
  agent-ready --target /path/to/repo --eval
  agent-ready --target /path/to/repo --eval-only
  agent-ready --target /path/to/repo --eval-only --fail-level 0.8
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
TOOLKIT_ROOT = SCRIPT_DIR.parent.parent

# ── Provider configuration ─────────────────────────────────────────────────
# Built-in presets — each maps the three pipeline phases to concrete LiteLLM
# model strings.  api_key_env=="" means no auth required (e.g. Ollama).
# Any provider supported by LiteLLM can be used directly with --model.

PROVIDERS: dict[str, dict[str, str]] = {
    # ── Cloud: proprietary ─────────────────────────────────────────────
    # Anthropic tier:  Opus (deepest reasoning) / Sonnet (balanced) / Haiku (fast+cheap)
    "anthropic": {
        "analysis":   "claude-opus-4-6",
        "generation": "claude-sonnet-4-6",
        "evaluation": "claude-haiku-4-5-20251001",
        "api_key_env": "ANTHROPIC_API_KEY",
    },
    # OpenAI tier:  gpt-5.4 ≈ Opus (best intelligence, 1M ctx)
    #               gpt-5.4-mini ≈ Sonnet (strong mini, coding + subagents)
    #               gpt-5.4-nano ≈ Haiku (cheapest GPT-5.4-class, high-volume eval)
    "openai": {
        "analysis":   "gpt-5.4",
        "generation": "gpt-5.4-mini",
        "evaluation": "gpt-5.4-nano",
        "api_key_env": "OPENAI_API_KEY",
    },
    # Google tier:  gemini-2.5-pro ≈ Opus-class (most advanced, stable)
    #               gemini-2.5-flash-lite ≈ Haiku (fastest + cheapest in 2.5 family)
    #               Gemini 3.1 Pro exists but is preview-only as of Apr 2026
    "google": {
        "analysis":   "gemini/gemini-2.5-pro",
        "generation": "gemini/gemini-2.5-pro",
        "evaluation": "gemini/gemini-2.5-flash-lite",
        "api_key_env": "GOOGLE_API_KEY",
    },
    # ── Cloud: open-weight / fast inference ───────────────────────────
    # Groq production models (Apr 2026):
    #   llama-3.3-70b-versatile ≈ Sonnet-tier (131K ctx, confirmed production)
    #   llama-3.1-8b-instant ≈ Haiku-tier (fast eval)
    #   Llama 4 Scout is preview-only on Groq; gpt-oss-120b also available production
    "groq": {
        "analysis":   "groq/llama-3.3-70b-versatile",
        "generation": "groq/llama-3.3-70b-versatile",
        "evaluation": "groq/llama-3.1-8b-instant",
        "api_key_env": "GROQ_API_KEY",
    },
    # Mistral: mistral-large ≈ Sonnet-tier; mistral-small ≈ Haiku-tier
    "mistral": {
        "analysis":   "mistral/mistral-large-latest",
        "generation": "mistral/mistral-large-latest",
        "evaluation": "mistral/mistral-small-latest",
        "api_key_env": "MISTRAL_API_KEY",
    },
    # Together AI production models (Apr 2026):
    #   Qwen3.5-397B-A17B ≈ Opus-tier (262K ctx, $0.60/$3.60 per MTok, best available)
    #   Llama-3.3-70B-Turbo ≈ Sonnet-tier (confirmed production, $0.88/$0.88)
    #   Qwen3.5-9B ≈ Haiku-tier (262K ctx, $0.10/$0.15, cheapest capable eval model)
    #   Note: Llama 4 IDs are NOT in Together's production catalog as of Apr 2026
    "together": {
        "analysis":   "together_ai/Qwen/Qwen3.5-397B-A17B",
        "generation": "together_ai/meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "evaluation": "together_ai/Qwen/Qwen3.5-9B",
        "api_key_env": "TOGETHER_API_KEY",
    },
    # ── Local: no API key required ────────────────────────────────────
    # Ollama: llama3.3 (70B) ≈ Sonnet-tier for analysis/generation;
    #         llama3.2 (3B) ≈ Haiku-tier for evaluation.
    # Run: ollama pull llama3.3 && ollama pull llama3.2
    "ollama": {
        "analysis":   "ollama/llama3.3",
        "generation": "ollama/llama3.3",
        "evaluation": "ollama/llama3.2",
        "api_key_env": "",  # local server — no auth
    },
}

# LiteLLM model-prefix → API key env mapping (used by --model auto-detection)
_PREFIX_TO_KEY: dict[str, str] = {
    "anthropic":   "ANTHROPIC_API_KEY",
    "claude":      "ANTHROPIC_API_KEY",
    "openai":      "OPENAI_API_KEY",
    "gpt":         "OPENAI_API_KEY",
    "o1":          "OPENAI_API_KEY",
    "gemini":      "GOOGLE_API_KEY",
    "vertex_ai":   "GOOGLE_APPLICATION_CREDENTIALS",
    "groq":        "GROQ_API_KEY",
    "mistral":     "MISTRAL_API_KEY",
    "together_ai": "TOGETHER_API_KEY",
    "cohere":      "COHERE_API_KEY",
    "ollama":      "",  # local
    "ollama_chat": "",  # local
    "lm_studio":   "",  # local
}


def _resolve_models(provider: str, model: str | None) -> dict[str, str]:
    """Return the model-config dict for a pipeline run.

    If *model* is given (``--model`` flag) it is used for all three phases and
    the API key is inferred from the model-name prefix so users can pass any
    LiteLLM-compatible string without needing a named preset.
    Otherwise the named *provider* preset from ``PROVIDERS`` is returned.

    Supported forms:
        provider/model-name   e.g. "groq/llama-3.3-70b-versatile"
        bare-model-name       e.g. "gpt-4-turbo"  (matched by startswith)
    """
    if model:
        if "/" in model:
            prefix = model.split("/")[0]
            api_key_env = _PREFIX_TO_KEY.get(prefix, f"{prefix.upper()}_API_KEY")
        else:
            # Bare name (e.g. "gpt-4-turbo") — scan known prefixes by startswith
            api_key_env = next(
                (v for k, v in _PREFIX_TO_KEY.items() if model.startswith(k)),
                f"{model.split('-')[0].upper()}_API_KEY",  # best-effort fallback
            )
        return {
            "analysis":   model,
            "generation": model,
            "evaluation": model,
            "api_key_env": api_key_env,
        }
    return PROVIDERS[provider]


# ── Agentic Readiness Scoring ──────────────────────────────────────────────

def score(target_path: Path) -> dict[str, Any]:
    criteria: dict[str, tuple[int, bool]] = {
        "agent-context.json": (10, (target_path / "agent-context.json").exists()),
        "CLAUDE.md":          (10, (target_path / "CLAUDE.md").exists()),
        "AGENTS.md":          (10, (target_path / "AGENTS.md").exists()),
        "system_prompt.md":   (5,  (target_path / "system_prompt.md").exists()),
        "tools/ has files":   (10, any((target_path / "tools").glob("*")) if (target_path / "tools").exists() else False),
    }

    context_file = target_path / "agent-context.json"
    if context_file.exists():
        try:
            ctx = json.loads(context_file.read_text())
            static = ctx.get("static", ctx)
            dynamic = ctx.get("dynamic", {})
            entry_point = static.get("entry_point", "")
            criteria["entry_point exists"]      = (10, bool(entry_point) and (target_path / entry_point).exists())
            criteria["test_command set"]         = (10, bool(static.get("test_command") or dynamic.get("test_command")))
            criteria["restricted_write_paths"]   = (10, len(static.get("restricted_write_paths", [])) > 0)
            criteria["environment_variables"]    = (10, len(static.get("environment_variables", [])) > 0)
            criteria["domain_concepts >= 3"]     = (5,  len(static.get("domain_concepts", [])) >= 3)
        except json.JSONDecodeError:
            pass

    criteria["OpenAPI spec"] = (5, bool(
        list(target_path.glob("**/openapi.yaml")) or
        list(target_path.glob("**/openapi.yml")) or
        list(target_path.glob("**/openapi.json")) or
        list(target_path.glob("**/swagger.yaml")) or
        list(target_path.glob("**/swagger.json"))
    ))
    criteria["CI config exists"] = (5, bool(
        any(target_path.glob(".github/workflows/*.yml")) or
        any(target_path.glob(".gitea/workflows/*.yml")) or
        (target_path / ".travis.yml").exists() or
        (target_path / ".circleci/config.yml").exists() or
        (target_path / "Jenkinsfile").exists()
    ))

    total = 0
    table_rows = []
    for criterion, (points, achieved) in criteria.items():
        if achieved:
            total += points
            table_rows.append((f"✅ {criterion}", f"+{points}"))
        else:
            table_rows.append((f"⬜ {criterion}", "+ 0"))

    return {"score": total, "max": 100, "rows": table_rows}


# ── Pre-commit Hook Management ─────────────────────────────────────────────

def install_hooks(target_path: Path) -> None:
    git_hooks_dir = target_path / ".git" / "hooks"
    hook_path = git_hooks_dir / "pre-commit"
    hook_content = '''#!/bin/sh
# Installed by AgentReady (https://github.com/vb-nattamai/agent-ready)
CHANGED=$(git diff --cached --name-only | grep -E '\\.(py|ts|js|java|go|rs|cs|rb)$')
if [ -z "$CHANGED" ]; then exit 0; fi
TOOLKIT=$(git config --get agentic.toolkit-path)
if [ -z "$TOOLKIT" ]; then
  echo "[agentic-ready] Skipping — agentic.toolkit-path not set."
  exit 0
fi
echo "[agentic-ready] Refreshing agent-context.json..."
python "$TOOLKIT/src/agent_ready/cli.py" --target . --only context --force --quiet
if ! git diff --quiet agent-context.json; then
  git add agent-context.json
fi
'''
    hook_path.parent.mkdir(parents=True, exist_ok=True)
    if hook_path.exists() and "agentic-ready" in hook_path.read_text():
        print(f"⚠️  Pre-commit hook already exists at {hook_path}.")
        return
    hook_path.write_text(hook_content, encoding="utf-8")
    os.chmod(hook_path, 0o755)
    print(f"✅ Pre-commit hook installed in {hook_path}")
    print("Run: git config agentic.toolkit-path /absolute/path/to/agent-ready")


# ── Context Verification ───────────────────────────────────────────────────

def verify(target_path: Path, provider: str = "anthropic") -> None:
    context_file = target_path / "agent-context.json"
    if not context_file.exists():
        print("⚠️  agent-context.json not found.")
        return
    try:
        context_json = json.loads(context_file.read_text())
    except json.JSONDecodeError:
        print("❌ agent-context.json is malformed JSON")
        return

    claude_md = (target_path / "CLAUDE.md").read_text() if (target_path / "CLAUDE.md").exists() else ""

    try:
        import litellm
    except ImportError:
        print("❌ litellm not installed. Run: pip install 'agent-ready[ai]'")
        return

    model = PROVIDERS[provider]["evaluation"]
    prompt = f"""Given the following agent-context.json and CLAUDE.md, answer in valid JSON only:
{{"detected_entry_point": "?", "detected_test_command": "?", "detected_primary_language": "?"}}

agent-context.json:
{json.dumps(context_json, indent=2)}

CLAUDE.md:
{claude_md}"""

    try:
        response = litellm.completion(
            model=model,
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        llm_answers = json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"⚠️  Verification failed: {e}")
        return

    static = context_json.get("static", context_json)
    results = [
        ("entry_point",      static.get("entry_point", "<unknown>"),      llm_answers.get("detected_entry_point", "<unknown>")),
        ("test_command",     static.get("test_command", "<unknown>"),      llm_answers.get("detected_test_command", "<unknown>")),
        ("primary_language", static.get("primary_language", "<unknown>"),  llm_answers.get("detected_primary_language", "<unknown>")),
    ]

    print()
    print("┌─────────────────────┬──────────────────────┬──────────────────────┬────────┐")
    print("│ Field               │ agent-context.json   │ LLM understood       │ Match  │")
    print("├─────────────────────┼──────────────────────┼──────────────────────┼────────┤")
    matched = 0
    for field, actual, understood in results:
        match = "✅" if str(actual).lower() in str(understood).lower() or str(understood).lower() in str(actual).lower() else "❌"
        if "✅" in match:
            matched += 1
        print(f"│ {field:<19} │ {str(actual)[:20]:<20} │ {str(understood)[:20]:<20} │ {match:<6} │")
    print("└─────────────────────┴──────────────────────┴──────────────────────┴────────┘")
    print(f"Verification score: {matched}/3")
    if matched < 2:
        sys.exit(1)


# ── LLM Pipeline ──────────────────────────────────────────────────────────

def _run_llm_pipeline(
    target: Path,
    models: dict[str, str],
    provider_label: str,
    only: str | None,
    dry_run: bool,
    force: bool,
    quiet: bool,
) -> list[tuple[str, str]]:
    api_key_env = models["api_key_env"]
    if api_key_env:  # empty string → local provider, no auth needed
        if not os.environ.get(api_key_env):
            print(f"❌ {api_key_env} environment variable is not set.")
            print(f"   Required for provider '{provider_label}'")
            sys.exit(1)

    try:
        from agent_ready import analyser, generator
    except ImportError as exc:
        print(f"❌ Missing dependency: {exc}")
        print("   Run: pip install 'agent-ready[ai]'")
        sys.exit(1)

    if not quiet:
        print(f"\n🤖 LLM-first mode active  [{provider_label} / {models['analysis']}]")
        print("─" * 50)

    analysis = analyser.run(
        target=target,
        analysis_model=models["analysis"],
        quiet=quiet,
    )

    if not quiet:
        print(f"\n✍️  Generating files with {models['generation']}...")

    gen = generator.LLMGenerator(
        target=target,
        analysis=analysis,
        generation_model=models["generation"],
        dry_run=dry_run,
        force=force,
        quiet=quiet,
    )

    if only:
        return gen.generate_only(only)
    return gen.generate_all()


# ── Eval Pipeline ──────────────────────────────────────────────────────────

def _run_eval_pipeline(
    target: Path,
    models: dict[str, str],
    fail_level: float = 0.0,
    quiet: bool = False,
) -> dict[str, Any]:
    api_key_env = models["api_key_env"]
    if api_key_env and not os.environ.get(api_key_env):
        print(f"❌ {api_key_env} environment variable is not set.")
        sys.exit(1)

    try:
        from agent_ready import evaluator
    except ImportError as exc:
        print(f"❌ Missing dependency: {exc}")
        print("   Run: pip install 'agent-ready[ai]'")
        sys.exit(1)

    try:
        result = evaluator.run_eval(
            target=target,
            eval_model=models["evaluation"],
            judge_model=models["evaluation"],
            fail_level=fail_level,
            quiet=quiet,
        )
        report_path = evaluator.save_eval_report(target, result)
        if not quiet:
            print(f"\n  📄 Full report saved: {report_path.relative_to(target)}")
        if fail_level > 0 and not result["passed"]:
            print(f"\n❌ Eval failed: pass rate {int(result['pass_rate'] * 100)}% is below threshold {int(fail_level * 100)}%")
            sys.exit(1)
        return result
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)


# ── CLI ────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Transform any repository into an AI-agent-ready codebase.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  agent-ready --target /path/to/repo
  agent-ready --target /path/to/repo --provider openai
  agent-ready --target /path/to/repo --provider google
  agent-ready --target /path/to/repo --only agents
  agent-ready --target /path/to/repo --dry-run
  agent-ready --target /path/to/repo --eval
  agent-ready --target /path/to/repo --eval-only
  agent-ready --target /path/to/repo --eval-only --fail-level 0.8

Supported provider presets:
  anthropic  Opus (analysis) + Sonnet (generation) + Haiku (eval)                [ANTHROPIC_API_KEY]
  openai     gpt-5.4 (analysis) + gpt-5.4-mini (generation) + gpt-5.4-nano (eval) [OPENAI_API_KEY]
  google     gemini-2.5-pro (analysis+generation) + gemini-2.5-flash-lite (eval)  [GOOGLE_API_KEY]
  groq       llama-3.3-70B (analysis+generation) + llama-3.1-8b-instant (eval)   [GROQ_API_KEY]
  mistral    mistral-large-latest (analysis+gen) + mistral-small-latest (eval)    [MISTRAL_API_KEY]
  together   Qwen3.5-397B (analysis) + Llama-3.3-70B (gen) + Qwen3.5-9B (eval)   [TOGETHER_API_KEY]
  ollama     llama3.3 70B (analysis+gen) + llama3.2 (eval) — local, no API key

Or bypass presets entirely with any LiteLLM model string:
  --model ollama/mistral
  --model groq/mixtral-8x7b-32768
  --model bedrock/anthropic.claude-3-5-sonnet-20241022-v2:0
        """,
    )
    parser.add_argument("--target", "-t", required=True, help="Target repository path")
    parser.add_argument(
        "--provider",
        choices=list(PROVIDERS),
        default="anthropic",
        help="LLM provider preset (default: anthropic). Ignored when --model is given.",
    )
    parser.add_argument(
        "--model",
        metavar="MODEL",
        help=(
            "Any LiteLLM-compatible model string, e.g. 'ollama/llama3.2' or "
            "'groq/llama-3.3-70b-versatile'.  Overrides --provider and uses this "
            "single model for all three pipeline phases."
        ),
    )
    parser.add_argument(
        "--only", choices=["agents", "tools", "context", "memory"],
        help="Generate only a specific category",
    )
    parser.add_argument("--dry-run",        action="store_true", help="Preview without writing files")
    parser.add_argument("--force",          action="store_true", help="Overwrite existing files")
    parser.add_argument("--quiet",          action="store_true", help="Suppress non-essential output")
    parser.add_argument("--install-hooks",  action="store_true", help="Install pre-commit hook")
    parser.add_argument("--verify",         action="store_true", help="Verify generated context with LLM")
    parser.add_argument(
        "--eval", action="store_true",
        help="After transformation, evaluate whether context files improve AI responses.",
    )
    parser.add_argument(
        "--eval-only", action="store_true",
        help="Skip transformation, run evaluation only against existing context files.",
    )
    parser.add_argument(
        "--fail-level", type=float, default=0.0, metavar="0.0-1.0",
        help="Exit 1 if eval pass rate is below this threshold. Use as CI gate.",
    )

    args = parser.parse_args()
    target = Path(args.target).resolve()

    if not target.is_dir():
        print(f"❌ Directory not found: {target}")
        sys.exit(1)

    if args.install_hooks:
        install_hooks(target)
        return

    if args.verify:
        verify(target, provider=args.provider)
        return

    models = _resolve_models(args.provider, getattr(args, "model", None))
    provider_label = getattr(args, "model", None) or args.provider

    # ── Eval-only path ────────────────────────────────────────────────────
    if args.eval_only:
        if not args.quiet:
            print()
            print("╔══════════════════════════════════════════════╗")
            print("║   🧪 AgentReady Evaluator v2.0              ║")
            print("╚══════════════════════════════════════════════╝")
            print()
        _run_eval_pipeline(target=target, models=models, fail_level=args.fail_level, quiet=args.quiet)
        return

    # ── Transformation ────────────────────────────────────────────────────
    if not args.quiet:
        print()
        print("╔══════════════════════════════════════════════╗")
        print("║   🤖 AgentReady Transformer v2.0 (LLM)     ║")
        print("╚══════════════════════════════════════════════╝")
        print()

    generated = _run_llm_pipeline(
        target=target,
        models=models,
        provider_label=provider_label,
        only=args.only,
        dry_run=args.dry_run,
        force=args.force,
        quiet=args.quiet,
    )

    # ── Scoring + summary ─────────────────────────────────────────────────
    readiness = score(target)

    if not args.quiet:
        print()
        print("─" * 50)
        mode_str = "[DRY RUN] " if args.dry_run else ""
        print(f"✅ {mode_str}Transformation Complete")
        print("─" * 50)
        print()
        print("  Generated Files:")
        for filepath, status in generated:
            print(f"    {status[:2]} {filepath}")
        print()
        print("──────────────────────────────────────────────")
        print(f"  AGENTIC READINESS SCORE: {readiness['score']} / {readiness['max']}")
        print("──────────────────────────────────────────────")
        for criterion, points in readiness["rows"]:
            print(f"  {criterion:<42} {points:>4}")
        if readiness["score"] < 100:
            print()
            print("  💡 To improve your score:")
            if not any(target.glob("**/openapi.{yaml,json,yml}")):
                print("     - Add an OpenAPI spec (openapi.yaml)")
        print("──────────────────────────────────────────────")
        print()

    # ── Optional eval after transformation ───────────────────────────────
    if args.eval and not args.dry_run:
        _run_eval_pipeline(target=target, models=models, fail_level=args.fail_level, quiet=args.quiet)


if __name__ == "__main__":
    main()