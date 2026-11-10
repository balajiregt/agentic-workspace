#!/bin/zsh
set -eu
ROOT="$(cd -- "$(dirname -- "$0")" && pwd)"
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
if ! command -v node >/dev/null 2>&1; then
  printf 'Node.js 20 or newer is required. Install Node, then reopen this launcher.\n'
  exit 1
fi
exec node "$ROOT/products/agent-tools/agent-dashboard/scripts/manage.mjs" stop
