#!/usr/bin/env python3
"""
Refresh agent-context.json for hello_world.

Run this script from the repo root whenever the codebase changes significantly
(new modules, entry-point changes, new environment variables, etc.) to keep the
AI agent context up to date.

Usage:
    python tools/refresh_context.py [--provider PROVIDER] [--dry-run]

Requirements:
    pip install agent-ready[ai]
    export ANTHROPIC_API_KEY=...   # or whichever provider you use
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
DEFAULT_PROVIDER = "anthropic"


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh agent-context.json")
    parser.add_argument(
        "--provider",
        default=DEFAULT_PROVIDER,
        help=f"LLM provider (default: {DEFAULT_PROVIDER})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without writing files",
    )
    args = parser.parse_args()

    cmd = [
        sys.executable, "-m", "agent_ready.cli",
        "--target", str(REPO_ROOT),
        "--provider", args.provider,
        "--only", "context",
    ]
    if args.dry_run:
        cmd.append("--dry-run")

    print(f"🔄 Refreshing agent-context.json for hello_world...")
    print(f"   Provider : {args.provider}")
    print(f"   Target   : {REPO_ROOT}")
    if args.dry_run:
        print("   Mode     : dry-run (no files written)")
    print()

    result = subprocess.run(cmd, cwd=REPO_ROOT)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
