#!/usr/bin/env bash
set -euo pipefail

echo "==> Dev container post-create"

# Install Python deps (prefer uv when available)
if command -v uv >/dev/null 2>&1; then
  if [[ -f "uv.lock" ]]; then
    echo "==> Syncing Python deps with uv"
    uv sync
  elif [[ -f "pyproject.toml" ]]; then
    echo "==> Syncing Python project with uv"
    uv sync
  elif [[ -f "requirements.txt" ]]; then
    echo "==> Installing Python requirements with uv"
    uv pip install -r requirements.txt
  fi
elif [[ -f "requirements.txt" ]]; then
  echo "==> Installing Python requirements"
  pip install -r requirements.txt
elif [[ -f "pyproject.toml" ]]; then
  echo "==> Installing Python project (editable)"
  pip install -e ".[dev]" 2>/dev/null || pip install -e .
fi

# Install Node deps when a package manifest appears (repo root and/or apps/desktop)
install_npm_deps() {
  local dir="$1"
  if [[ -f "${dir}/package-lock.json" ]]; then
    echo "==> Installing npm dependencies (ci) in ${dir}"
    (cd "${dir}" && npm ci)
  elif [[ -f "${dir}/package.json" ]]; then
    echo "==> Installing npm dependencies in ${dir}"
    (cd "${dir}" && npm install)
  elif [[ -f "${dir}/pnpm-lock.yaml" ]]; then
    echo "==> Installing pnpm dependencies in ${dir}"
    corepack enable
    (cd "${dir}" && pnpm install --frozen-lockfile)
  elif [[ -f "${dir}/yarn.lock" ]]; then
    echo "==> Installing yarn dependencies in ${dir}"
    corepack enable
    (cd "${dir}" && yarn install --frozen-lockfile)
  fi
}

install_npm_deps "."
install_npm_deps "apps/desktop"

echo "==> Dev container ready"
