#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOST="${WORKBENCH_HOST:-0.0.0.0}"
PORT="${WORKBENCH_PORT:-8766}"
ENGINE="${WORKBENCH_ENGINE:-deepseek}"
SESSION="${WORKBENCH_SCREEN_SESSION:-writing-workbench-${PORT}}"
LOG="${ROOT}/.cache/writing/inline_editor_server_lan.log"
PYTHON_BIN="${WORKBENCH_PYTHON:-}"

if [[ -z "${PYTHON_BIN}" ]]; then
  if [[ -x "${ROOT}/.venv-local-vlm/bin/python" ]]; then
    PYTHON_BIN="${ROOT}/.venv-local-vlm/bin/python"
  elif [[ -x "${ROOT}/.venv/bin/python" ]]; then
    PYTHON_BIN="${ROOT}/.venv/bin/python"
  else
    PYTHON_BIN="$(command -v python3)"
  fi
fi

mkdir -p "$(dirname "${LOG}")"

if ! command -v screen >/dev/null 2>&1; then
  echo "screen not found; run the server in a terminal instead." >&2
  exit 1
fi

screen -S "${SESSION}" -X quit >/dev/null 2>&1 || true
screen -dmS "${SESSION}" bash -lc "cd '${ROOT}' && '${PYTHON_BIN}' tools/inline_editor_server.py --host '${HOST}' --port '${PORT}' --engine '${ENGINE}' >> '${LOG}' 2>&1"

sleep 1

if ! lsof -nP -iTCP:"${PORT}" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Workbench failed to start. Last log lines:" >&2
  tail -40 "${LOG}" >&2 || true
  exit 1
fi

LAN_IP="$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || true)"
echo "Workbench running in screen session: ${SESSION}"
echo "Python: ${PYTHON_BIN}"
echo "Local: http://127.0.0.1:${PORT}/v2/"
if [[ -n "${LAN_IP}" ]]; then
  echo "LAN:   http://${LAN_IP}:${PORT}/v2/"
else
  echo "LAN IP not detected. Check System Settings > Wi-Fi for this Mac's IP."
fi
echo "Log:   ${LOG}"
