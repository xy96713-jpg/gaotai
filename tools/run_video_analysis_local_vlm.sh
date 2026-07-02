#!/usr/bin/env zsh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
API_BASE="${VIDEO_ANALYSIS_API_BASE:-http://127.0.0.1:8010/v1}"
MODEL="${VIDEO_ANALYSIS_MODEL:-mlx-community/Qwen3-VL-4B-Instruct-3bit}"
PYTHON_BIN="${VIDEO_ANALYSIS_PYTHON:-${ROOT_DIR}/.venv-local-vlm/bin/python}"

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <video-url> [extra args...]" >&2
  exit 1
fi

export VIDEO_ANALYSIS_MODEL="${MODEL}"

exec "${PYTHON_BIN}" "${ROOT_DIR}/tools/youtube_video_notes.py" \
  --analysis-backend mlx-vlm-local \
  --extract-frames \
  --frame-interval-seconds "${VIDEO_ANALYSIS_FRAME_INTERVAL_SECONDS:-60}" \
  --max-frames "${VIDEO_ANALYSIS_MAX_FRAMES:-4}" \
  "$@"
