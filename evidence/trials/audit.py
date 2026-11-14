#!/usr/bin/env python3
"""Recompute run fairness from Claude Code transcripts for every recorded trial.

For each run and arm: genuine permission denials, and for framework arms whether a
skill's content actually reached the agent. Writes evidence/results/fairness.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import runner  # noqa: E402


def audit(trials_root: Path) -> dict:
    runs = {}
    for run_json in sorted(trials_root.glob("*/run.json")):
        record = json.loads(run_json.read_text())
        arms = {}
        for arm, info in record["arms"].items():
            summary = run_json.parent / f"{arm}-agent.json"
            if not summary.is_file():
                arms[arm] = {"headless": False}
                continue
            session = json.loads(summary.read_text() or "{}").get("session_id")
            blocked = runner.blocked_tool_calls(session) or []
            arms[arm] = {"headless": True, "blockedToolCalls": blocked,
                         "guidanceReceived": runner.guidance_received(Path(info["path"]), session) if arm == "framework" else None}
        runs[record["runId"]] = {"taskId": record["taskId"], "repeat": record["repeat"], "arms": arms}
    return {"schemaVersion": 1, "runs": runs}


def main() -> int:
    result = audit(runner.DEFAULT_OUT)
    out = WORKSPACE / "evidence/results/fairness.json"
    out.write_text(json.dumps(result, indent=2) + "\n")
    for run_id, r in result["runs"].items():
        arms = r["arms"]
        f, b = arms.get("framework", {}), arms.get("baseline", {})
        if f.get("headless") or b.get("headless"):
            print(f"{run_id[:44]:44} guidance={f.get('guidanceReceived')!s:5} blocked b={len(b.get('blockedToolCalls', []))} f={len(f.get('blockedToolCalls', []))}")
    print(f"Wrote {out.relative_to(WORKSPACE)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
