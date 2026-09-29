#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEACHER_DIR="${ROOT}/services/teacher"
DESKTOP_DIR="${ROOT}/apps/desktop"

if ! command -v uv >/dev/null 2>&1; then
  echo "error: uv is required but not found in PATH" >&2
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "error: npm is required but not found in PATH" >&2
  exit 1
fi

echo "==> Teacher: uv sync"
(cd "${TEACHER_DIR}" && uv sync)

echo "==> Teacher: uv run pytest"
(cd "${TEACHER_DIR}" && uv run pytest)

echo "==> Desktop: npm install"
(cd "${DESKTOP_DIR}" && npm install)

echo "==> Desktop: npm test"
(cd "${DESKTOP_DIR}" && npm test)

echo "==> Desktop: npm run typecheck"
(cd "${DESKTOP_DIR}" && npm run typecheck)

echo "==> Desktop: npm run build"
(cd "${DESKTOP_DIR}" && npm run build)

# electron-vite only passes --no-sandbox when NO_SANDBOX=1 (ELECTRON_DISABLE_SANDBOX
# alone is not enough here: chrome-sandbox exists but is not root-owned/setuid).
export NO_SANDBOX="${NO_SANDBOX:-1}"

display_is_live() {
  local d="$1"
  [[ -S "/tmp/.X11-unix/X${d#:}" ]] || return 1
  if command -v xdpyinfo >/dev/null 2>&1; then
    xdpyinfo -display "$d" >/dev/null 2>&1
  else
    return 0
  fi
}

# Cursor/IDE often exports DISPLAY=:0 even when desktop-lite VNC is on :1.
resolve_display() {
  local candidate
  for candidate in ${DISPLAY:-} :1 :0; do
    [[ -n "${candidate}" ]] || continue
    if display_is_live "${candidate}"; then
      echo "${candidate}"
      return 0
    fi
  done
  return 1
}

if RESOLVED_DISPLAY="$(resolve_display)"; then
  if [[ "${DISPLAY:-}" != "${RESOLVED_DISPLAY}" ]]; then
    echo "==> DISPLAY=${DISPLAY:-<unset>} is not a live X server; using ${RESOLVED_DISPLAY}"
  fi
  export DISPLAY="${RESOLVED_DISPLAY}"
  echo "==> Desktop: npm run dev (DISPLAY=${DISPLAY}, NO_SANDBOX=${NO_SANDBOX})"
  echo "    Open noVNC on port 6080 (password: vscode) to see the window."
  (cd "${DESKTOP_DIR}" && npm run dev)
else
  if ! command -v xvfb-run >/dev/null 2>&1; then
    echo "error: no live X display and xvfb-run is not available" >&2
    echo "  Start desktop-lite / open port 6080, or set DISPLAY to a working server." >&2
    exit 1
  fi
  echo "==> Desktop: npm run dev:xvfb (no live DISPLAY, NO_SANDBOX=${NO_SANDBOX})"
  (cd "${DESKTOP_DIR}" && npm run dev:xvfb)
fi
