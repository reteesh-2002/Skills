#!/usr/bin/env bash
# Antigravity Trusted Execution Proxy Shim
# Delegates execution directly to scripts/exec_proxy.py for unified cross-platform behavior.

set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON:-python3}"

PROXY_PY="${SCRIPT_DIR}/exec_proxy.py"
if [[ ! -f "${PROXY_PY}" ]]; then
  GIT_TOP="$(git rev-parse --show-toplevel 2>/dev/null || true)"
  if [[ -n "${GIT_TOP}" && -f "${GIT_TOP}/scripts/exec_proxy.py" ]]; then
    PROXY_PY="${GIT_TOP}/scripts/exec_proxy.py"
  fi
fi

if [[ ! -f "${PROXY_PY}" ]]; then
  echo "Error: exec_proxy.py not found in ${SCRIPT_DIR} or repository root." >&2
  exit 1
fi

exec "${PYTHON_BIN}" "${PROXY_PY}" "$@"
