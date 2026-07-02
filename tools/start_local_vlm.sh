#!/usr/bin/env zsh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="${ROOT_DIR}/.venv-local-vlm"
MODEL="${LOCAL_VLM_MODEL:-mlx-community/Qwen3-VL-4B-Instruct-3bit}"
HOST="${LOCAL_VLM_HOST:-127.0.0.1}"
PORT="${LOCAL_VLM_PORT:-8010}"

if [[ ! -x "${VENV_DIR}/bin/vllm-mlx" ]]; then
  echo "Missing ${VENV_DIR}/bin/vllm-mlx. Create .venv-local-vlm and install vllm-mlx first." >&2
  exit 1
fi

exec "${VENV_DIR}/bin/vllm-mlx" serve "${MODEL}" --host "${HOST}" --port "${PORT}"
