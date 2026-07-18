#!/usr/bin/env python3
"""Run the weekly no-model paper-response refresh and deterministic screen."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> int:
    started = datetime.now(timezone.utc).isoformat()
    run([
        sys.executable,
        "scripts/paper_response_evidence.py",
        "refresh",
        "--browser-resolve",
        "auto",
    ])
    run([sys.executable, "scripts/screen_paper_response_matches.py"])
    print(json.dumps({
        "status": "ok",
        "started_at": started,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "model_calls": 0,
        "steps": ["public_endpoint_refresh", "deterministic_suggestion_change_screen"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
