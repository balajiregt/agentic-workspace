#!/usr/bin/env bash
set -euo pipefail

LOCAL_AGENTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${LOCAL_AGENTS_DIR}/.." && pwd)"
TARGET_REPO="${1:-${ROOT_DIR}}"
PROFILE="${AGENTIC_PROFILE:-8gb}"
PROFILE_JSON="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["profiles"][sys.argv[2]][sys.argv[3]])' "${LOCAL_AGENTS_DIR}/config/model-profiles.json" "${PROFILE}" modelRef 2>/dev/null || true)"

if [[ -z "${PROFILE_JSON}" ]]; then
  echo "Unknown AGENTIC_PROFILE '${PROFILE}'. Available: low-memory, 8gb, tool-agent, 16gb" >&2
  exit 1
fi

MODEL_REF="${AGENTIC_MODEL_REF:-${PROFILE_JSON}}"
PORT="${AGENTIC_LLAMA_PORT:-$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["profiles"][sys.argv[2]]["port"])' "${LOCAL_AGENTS_DIR}/config/model-profiles.json" "${PROFILE}")}"
CONTEXT_WINDOW="${AGENTIC_CONTEXT_WINDOW:-$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["profiles"][sys.argv[2]]["contextWindow"])' "${LOCAL_AGENTS_DIR}/config/model-profiles.json" "${PROFILE}")}"
MAX_TOKENS="${AGENTIC_MAX_TOKENS:-$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["profiles"][sys.argv[2]]["maxTokens"])' "${LOCAL_AGENTS_DIR}/config/model-profiles.json" "${PROFILE}")}"
PARALLEL_SLOTS="${AGENTIC_PARALLEL_SLOTS:-1}"
LLAMA_TOOLS="${AGENTIC_LLAMA_TOOLS:-all}"
REQUIRE_TOOL_CALLS="${AGENTIC_REQUIRE_TOOL_CALLS:-1}"
BASE_URL="http://localhost:${PORT}"
LOG_FILE="${TMPDIR:-/tmp}/agentic-workspace-llama-${PORT}.log"
PI_MODELS_TARGET="${HOME}/.pi/agent/models.json"
PI_SKILL_PATH="${ROOT_DIR}/skills/microservice-change"
PI_PROMPTS_PATH="${ROOT_DIR}/docs/prompts"
PI_ARGS=(--approve --tools read,bash,edit,write,grep,find,ls)
NPM_PREFIX="$(npm config get prefix 2>/dev/null || true)"
NPM_GLOBAL_BIN="${NPM_PREFIX}/bin"
PI_BIN="$(command -v pi 2>/dev/null || true)"

if [[ -z "${PI_BIN}" && -x "${NPM_GLOBAL_BIN}/pi" ]]; then
  PI_BIN="${NPM_GLOBAL_BIN}/pi"
fi

if [[ ! -d "${TARGET_REPO}" ]]; then
  echo "Target repo does not exist: ${TARGET_REPO}" >&2
  exit 1
fi

if command -v llama-server >/dev/null 2>&1; then
  LLAMA_SERVER_CMD=(llama-server -hf "${MODEL_REF}" --alias local-model --port "${PORT}" --ctx-size "${CONTEXT_WINDOW}" --parallel "${PARALLEL_SLOTS}" --metrics --tools "${LLAMA_TOOLS}")
elif command -v llama >/dev/null 2>&1; then
  LLAMA_SERVER_CMD=(llama serve -hf "${MODEL_REF}" --alias local-model --port "${PORT}" --ctx-size "${CONTEXT_WINDOW}" --parallel "${PARALLEL_SLOTS}" --metrics --tools "${LLAMA_TOOLS}")
else
  echo "llama.cpp is not installed. Run: npm run setup:8gb" >&2
  exit 1
fi

if [[ -z "${PI_BIN}" ]]; then
  echo "Pi coding agent is not installed. Run: npm run setup:8gb" >&2
  if [[ -n "${NPM_GLOBAL_BIN}" ]]; then
    echo "Expected Pi at: ${NPM_GLOBAL_BIN}/pi" >&2
    echo "If setup already installed Pi, add npm's global bin to PATH:" >&2
    echo "  export PATH=\"${NPM_GLOBAL_BIN}:\$PATH\"" >&2
  fi
  exit 1
fi

if [[ -f "${ROOT_DIR}/AGENTS.md" ]]; then
  PI_ARGS+=(--append-system-prompt "${ROOT_DIR}/AGENTS.md")
fi

if [[ -d "${PI_SKILL_PATH}" ]]; then
  PI_ARGS+=(--skill "${PI_SKILL_PATH}")
fi

if [[ -d "${PI_PROMPTS_PATH}" ]]; then
  PI_ARGS+=(--prompt-template "${PI_PROMPTS_PATH}")
fi

python3 "${LOCAL_AGENTS_DIR}/render-pi-models.py" \
  --profile "${PROFILE}" \
  --output "${PI_MODELS_TARGET}" \
  --model-ref "${MODEL_REF}" \
  --port "${PORT}" \
  --context-window "${CONTEXT_WINDOW}" \
  --max-tokens "${MAX_TOKENS}" >/dev/null

server_running() {
  curl -fsS "${BASE_URL}/v1/models" >/dev/null 2>&1
}

server_context_window() {
  curl -fsS "${BASE_URL}/v1/models" 2>/dev/null \
    | python3 -c 'import json,sys; data=json.load(sys.stdin); print(data.get("data",[{}])[0].get("meta",{}).get("n_ctx",""))' 2>/dev/null \
    || true
}

if server_running; then
  echo "==> Reusing llama.cpp server at ${BASE_URL}"
  ACTUAL_CONTEXT_WINDOW="$(server_context_window)"
  if [[ -n "${ACTUAL_CONTEXT_WINDOW}" && "${ACTUAL_CONTEXT_WINDOW}" != "${CONTEXT_WINDOW}" && "${AGENTIC_ALLOW_SERVER_MISMATCH:-0}" != "1" ]]; then
    cat <<EOF >&2
Existing llama.cpp server context does not match this run.

Requested context window: ${CONTEXT_WINDOW}
Running server context:  ${ACTUAL_CONTEXT_WINDOW}

Stop the existing agent/server terminal with Ctrl+C, or run:

  lsof -nP -iTCP:${PORT} -sTCP:LISTEN
  kill <PID>

Then rerun this command.
EOF
    exit 1
  fi
  echo "==> Existing server context window: ${ACTUAL_CONTEXT_WINDOW:-unknown}"
  STARTED_SERVER=0
else
  echo "==> Starting llama.cpp on ${BASE_URL}"
  echo "==> Logs: ${LOG_FILE}"
  "${LLAMA_SERVER_CMD[@]}" >"${LOG_FILE}" 2>&1 &
  LLAMA_PID="$!"
  STARTED_SERVER=1

  for _ in $(seq 1 90); do
    if server_running; then
      break
    fi
    if ! kill -0 "${LLAMA_PID}" >/dev/null 2>&1; then
      echo "llama.cpp exited early. Recent logs:" >&2
      tail -80 "${LOG_FILE}" >&2 || true
      exit 1
    fi
    sleep 1
  done

  if ! server_running; then
    echo "Timed out waiting for llama.cpp at ${BASE_URL}. Recent logs:" >&2
    tail -80 "${LOG_FILE}" >&2 || true
    exit 1
  fi
fi

if ! python3 "${LOCAL_AGENTS_DIR}/check-tool-calls.py" --base-url "${BASE_URL}" --model local-model; then
  cat <<EOF

WARNING: The current local model/server did not return structured tool_calls.
Pi may print JSON such as {"name":"edit",...} instead of executing file tools.
This profile is still useful for context/token experiments, but do not treat it
as a validated editing-agent profile until:

  npm run agent:doctor

prints TOOL_CALL_CHECK=PASS for the selected model/server.

EOF
  if [[ "${REQUIRE_TOOL_CALLS}" == "1" ]]; then
    exit 1
  fi
fi

cleanup() {
  if [[ "${STARTED_SERVER}" == "1" ]]; then
    echo "==> Stopping llama.cpp"
    kill "${LLAMA_PID}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

cat <<EOF
==> Starting Pi in ${TARGET_REPO}
Profile: ${PROFILE}
Model: ${MODEL_REF}
Context window: ${CONTEXT_WINDOW}
Max output tokens: ${MAX_TOKENS}
Parallel slots: ${PARALLEL_SLOTS}
llama.cpp tools: ${LLAMA_TOOLS}
Pi binary: ${PI_BIN}
Pi options: ${PI_ARGS[*]}
Metrics dashboard:
  npm run metrics:8gb
  open http://localhost:8765

Suggested prompt:
For the existing customer risk API test, add one assertion that riskCategory is not empty.
Use AGENTS.md and contexts/current/service-context.yml before editing.
Do not create, rename, or append to unrelated test files.

EOF

cd "${TARGET_REPO}"
"${PI_BIN}" "${PI_ARGS[@]}"
