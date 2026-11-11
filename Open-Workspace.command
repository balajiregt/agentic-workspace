#!/bin/zsh
set -eu
ROOT="$(cd -- "$(dirname -- "$0")" && pwd)"
exec /usr/bin/open -a "Visual Studio Code" "$ROOT/agentic-workspace.code-workspace"
