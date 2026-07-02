#!/usr/bin/env bash
set -euo pipefail

PORT="${WORKBENCH_PORT:-8766}"
SESSION="${WORKBENCH_SCREEN_SESSION:-writing-workbench-${PORT}}"

screen -S "${SESSION}" -X quit >/dev/null 2>&1 || true

PIDS="$(lsof -tiTCP:"${PORT}" -sTCP:LISTEN 2>/dev/null || true)"
if [[ -n "${PIDS}" ]]; then
  kill ${PIDS} >/dev/null 2>&1 || true
fi

echo "Workbench stopped for port ${PORT}."
