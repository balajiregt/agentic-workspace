#!/usr/bin/env python3
"""Build or serve a local Graphify view without requiring a global install."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import venv
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


WORKSPACE = Path(__file__).resolve().parents[1]
DEFAULT_VENV = WORKSPACE / "artifacts/tools/graphify-venv"
DEFAULT_OUTPUT = WORKSPACE / "graphify-out"
GRAPHIFY_VERSION = "0.9.33"


def run(command: list[str], cwd: Path = WORKSPACE) -> None:
    print("+ " + " ".join(command))
    subprocess.run(command, cwd=cwd, check=True)


def venv_bin(venv_dir: Path, name: str) -> Path:
    return venv_dir / ("Scripts" if sys.platform == "win32" else "bin") / name


def ensure_graphify(venv_dir: Path) -> Path:
    graphify_bin = os.environ.get("GRAPHIFY_BIN")
    if graphify_bin:
        graphify = Path(graphify_bin)
        if graphify.exists():
            return graphify
    graphify = venv_bin(venv_dir, "graphify")
    if graphify.exists():
        return graphify
    venv_dir.parent.mkdir(parents=True, exist_ok=True)
    venv.EnvBuilder(with_pip=True).create(venv_dir)
    python = venv_bin(venv_dir, "python")
    run([str(python), "-m", "pip", "install", "--upgrade", "pip"])
    run([str(python), "-m", "pip", "install", f"graphifyy=={GRAPHIFY_VERSION}"])
    return graphify


def build(venv_dir: Path) -> None:
    graphify = ensure_graphify(venv_dir)
    run([str(graphify), "extract", ".", "--code-only", "--out", "."])
    run([str(graphify), "cluster-only", ".", "--no-label"])


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        pass


def serve(host: str, port: int, output_dir: Path) -> None:
    if not (output_dir / "graph.html").is_file():
        raise SystemExit("Missing graphify-out/graph.html. Run `npm run graphify:build` first.")
    handler = lambda *args, **kwargs: QuietHandler(*args, directory=str(output_dir), **kwargs)
    server = ThreadingHTTPServer((host, port), handler)
    display_host = "127.0.0.1" if host == "0.0.0.0" else host
    print(f"Serving Graphify view at http://{display_host}:{port}/graph.html")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["setup", "build", "serve"])
    parser.add_argument("--venv", default=str(DEFAULT_VENV))
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8767)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    venv_dir = Path(args.venv).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    if args.command == "setup":
        ensure_graphify(venv_dir)
    elif args.command == "build":
        build(venv_dir)
    elif args.command == "serve":
        serve(args.host, args.port, output_dir)


if __name__ == "__main__":
    main()
