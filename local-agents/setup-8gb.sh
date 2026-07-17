#!/usr/bin/env bash
set -euo pipefail

LOCAL_AGENTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${LOCAL_AGENTS_DIR}/.." && pwd)"
PI_MODELS_SOURCE="${LOCAL_AGENTS_DIR}/config/pi-models-8gb.json"
PI_MODELS_TARGET="${HOME}/.pi/agent/models.json"

echo "==> Agentic workspace 8 GB setup"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This setup script is intended for macOS." >&2
  exit 1
fi

if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew is required. Install it from https://brew.sh, then rerun this script." >&2
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "npm is required. Install Node.js first, then rerun this script." >&2
  exit 1
fi

if ! command -v llama-server >/dev/null 2>&1 && ! command -v llama >/dev/null 2>&1; then
  echo "==> Installing llama.cpp"
  brew install llama.cpp
else
  echo "==> llama.cpp already installed"
fi

if ! command -v pi >/dev/null 2>&1; then
  echo "==> Installing Pi coding agent"
  npm install -g @earendil-works/pi-coding-agent
else
  echo "==> Pi coding agent already installed"
fi

mkdir -p "$(dirname "${PI_MODELS_TARGET}")"
cp "${PI_MODELS_SOURCE}" "${PI_MODELS_TARGET}"
echo "==> Wrote Pi model config to ${PI_MODELS_TARGET}"

cat <<EOF

Setup complete.

Run the sample workspace agent with:

  npm run agent:8gb

Or from any repo:

  /bin/bash ${ROOT_DIR}/local-agents/run-agent.sh /path/to/repo

The first model start may download:

  Qwen/Qwen2.5-Coder-3B-Instruct-GGUF:Q4_K_M
EOF
