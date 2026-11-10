#!/usr/bin/env python3
"""Build and serve the QA dashboard, test graph, and optional Graphify view."""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

from context_paths import API_RESOLVED, UI_RESOLVED


WORKSPACE = Path(__file__).resolve().parents[2]


def run(command: list[str]) -> None:
    print("+ " + " ".join(command))
    subprocess.run(command, cwd=WORKSPACE, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dashboard-port", type=int, default=8765)
    parser.add_argument("--test-port", type=int, default=8766)
    parser.add_argument("--graphify-port", type=int, default=8767)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--skip-graphify-build", action="store_true")
    parser.add_argument("--api-context", type=Path, default=API_RESOLVED)
    parser.add_argument("--ui-context", type=Path, default=UI_RESOLVED)
    args = parser.parse_args()

    for selected, default, script in [
        (args.api_context, API_RESOLVED, "resolve_context.py"),
        (args.ui_context, UI_RESOLVED, "resolve_ui_context.py"),
    ]:
        if not (WORKSPACE / selected).is_file():
            if selected != default:
                parser.error(f"Selected resolved context does not exist: {selected}")
            run(["python3", f"tooling/scripts/{script}"])
    context_args = ["--api-context", str(args.api_context), "--ui-context", str(args.ui_context)]
    run(["python3", "tooling/scripts/build_test_graph.py", *context_args])
    if not args.skip_graphify_build:
        run(["python3", "tooling/scripts/graphify_local.py", "build"])
    run(["python3", "tooling/scripts/build_qa_dashboard.py", *context_args])

    processes = [
        subprocess.Popen(
            [
                "python3",
                "tooling/scripts/build_qa_dashboard.py",
                "--serve",
                "--host",
                args.host,
                "--port",
                str(args.dashboard_port),
                *context_args,
            ],
            cwd=WORKSPACE,
        ),
        subprocess.Popen(
            [
                "python3",
                "tooling/scripts/build_test_graph.py",
                "--serve",
                "--host",
                args.host,
                "--port",
                str(args.test_port),
                *context_args,
            ],
            cwd=WORKSPACE,
        ),
        subprocess.Popen(
            [
                "python3",
                "tooling/scripts/graphify_local.py",
                "serve",
                "--host",
                args.host,
                "--port",
                str(args.graphify_port),
            ],
            cwd=WORKSPACE,
        ),
    ]
    print("")
    display_host = "127.0.0.1" if args.host == "0.0.0.0" else args.host
    print(f"QA dashboard:      http://{display_host}:{args.dashboard_port}/")
    print(f"Test-impact graph: http://{display_host}:{args.test_port}/")
    print(f"Graphify graph:    http://{display_host}:{args.graphify_port}/graph.html")
    print("Press Ctrl+C to stop dashboard and graph servers.")
    try:
        while all(process.poll() is None for process in processes):
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
        for process in processes:
            try:
                process.wait(timeout=5)
            except KeyboardInterrupt:
                process.kill()
            except subprocess.TimeoutExpired:
                process.kill()
    if any(process.returncode not in (0, -15, None) for process in processes):
        sys.exit(1)


if __name__ == "__main__":
    main()
