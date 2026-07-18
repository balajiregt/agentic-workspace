#!/usr/bin/env bash
set -euo pipefail

LOCAL_AGENTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${LOCAL_AGENTS_DIR}/.." && pwd)"
PI_MODELS_TARGET="${HOME}/.pi/agent/models.json"
PROFILE="${AGENTIC_PROFILE:-tool-agent}"
AGENT_SCRIPT="agent:${PROFILE}"
MODEL_REF="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["profiles"][sys.argv[2]]["modelRef"])' "${LOCAL_AGENTS_DIR}/config/model-profiles.json" "${PROFILE}" 2>/dev/null || true)"
NPM_PREFIX="$(npm config get prefix 2>/dev/null || true)"
NPM_GLOBAL_BIN="${NPM_PREFIX}/bin"

echo "==> Agentic workspace local agent setup (${PROFILE})"

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

if [[ -x "${NPM_GLOBAL_BIN}/pi" && ":${PATH}:" != *":${NPM_GLOBAL_BIN}:"* ]]; then
  cat <<EOF
==> Pi was found at ${NPM_GLOBAL_BIN}/pi, but that folder is not on PATH.
==> The run script will use it automatically.
==> For direct 'pi' commands, add this to your shell profile:

  export PATH="${NPM_GLOBAL_BIN}:\$PATH"

EOF
fi

python3 "${LOCAL_AGENTS_DIR}/render-pi-models.py" \
  --profile "${PROFILE}" \
  --output "${PI_MODELS_TARGET}"

cat <<EOF

Setup complete.

Run the workspace agent with:

  npm run ${AGENT_SCRIPT}

For Pi file-edit tool-call validation:

  npm run setup:tool-agent
  npm run agent:tool-agent

Or intentionally target another repo:

  /bin/bash ${ROOT_DIR}/local-agents/run-agent.sh /path/to/repo

The first model start may download:

  ${MODEL_REF}
EOF
