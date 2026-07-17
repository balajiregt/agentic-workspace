#!/usr/bin/env bash
set -euo pipefail

LOCAL_AGENTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${LOCAL_AGENTS_DIR}/.." && pwd)"
TARGET_REPO="${1:-${ROOT_DIR}/projects/microservices/xyz-service}"
PROFILE="${AGENTIC_PROFILE:-8gb}"
PROFILE_JSON="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["profiles"][sys.argv[2]][sys.argv[3]])' "${LOCAL_AGENTS_DIR}/config/model-profiles.json" "${PROFILE}" modelRef 2>/dev/null || true)"

if [[ -z "${PROFILE_JSON}" ]]; then
  echo "Unknown AGENTIC_PROFILE '${PROFILE}'. Available: low-memory, 8gb, 16gb" >&2
  exit 1
fi

MODEL_REF="${AGENTIC_MODEL_REF:-${PROFILE_JSON}}"
PORT="${AGENTIC_LLAMA_PORT:-$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["profiles"][sys.argv[2]]["port"])' "${LOCAL_AGENTS_DIR}/config/model-profiles.json" "${PROFILE}")}"
CONTEXT_WINDOW="${AGENTIC_CONTEXT_WINDOW:-$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["profiles"][sys.argv[2]]["contextWindow"])' "${LOCAL_AGENTS_DIR}/config/model-profiles.json" "${PROFILE}")}"
MAX_TOKENS="${AGENTIC_MAX_TOKENS:-$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["profiles"][sys.argv[2]]["maxTokens"])' "${LOCAL_AGENTS_DIR}/config/model-profiles.json" "${PROFILE}")}"
BASE_URL="http://localhost:${PORT}"
LOG_FILE="${TMPDIR:-/tmp}/agentic-workspace-llama-${PORT}.log"
PI_MODELS_TARGET="${HOME}/.pi/agent/models.json"

if [[ ! -d "${TARGET_REPO}" ]]; then
  echo "Target repo does not exist: ${TARGET_REPO}" >&2
  exit 1
fi

if command -v llama-server >/dev/null 2>&1; then
  LLAMA_SERVER_CMD=(llama-server -hf "${MODEL_REF}" --alias local-model --port "${PORT}")
elif command -v llama >/dev/null 2>&1; then
  LLAMA_SERVER_CMD=(llama serve -hf "${MODEL_REF}" --alias local-model --port "${PORT}")
else
  echo "llama.cpp is not installed. Run: npm run setup:8gb" >&2
  exit 1
fi

if ! command -v pi >/dev/null 2>&1; then
  echo "Pi coding agent is not installed. Run: npm run setup:8gb" >&2
  exit 1
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

if server_running; then
  echo "==> Reusing llama.cpp server at ${BASE_URL}"
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

Suggested prompt:
Use the Jira context in ${ROOT_DIR}/contexts/current/service-context.yml.
Follow repository_topology before deciding where tests or deployment changes belong.
Update service code, OpenAPI, tests, and deployment impact only as required by the context.

EOF

cd "${TARGET_REPO}"
pi
