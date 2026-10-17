#!/usr/bin/env bash
# Antigravity Release Gate Verifier Shim
# Delegates execution directly to scripts/verify_release_gate.py for unified cross-platform behavior.

set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON:-python3}"

GATE_PY="${SCRIPT_DIR}/verify_release_gate.py"
if [[ ! -f "${GATE_PY}" ]]; then
  GIT_TOP="$(git rev-parse --show-toplevel 2>/dev/null || true)"
  if [[ -n "${GIT_TOP}" && -f "${GIT_TOP}/scripts/verify_release_gate.py" ]]; then
    GATE_PY="${GIT_TOP}/scripts/verify_release_gate.py"
  fi
fi

if [[ ! -f "${GATE_PY}" ]]; then
  echo "Error: verify_release_gate.py not found in ${SCRIPT_DIR} or repository root." >&2
  exit 1
fi

exec "${PYTHON_BIN}" "${GATE_PY}" "$@"
