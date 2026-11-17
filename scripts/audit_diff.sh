#!/usr/bin/env bash
# Antigravity Cross-Platform audit_diff Shim
# Delegates execution directly to scripts/audit_diff.py for unified cross-platform behavior.

set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON:-python3}"

AUDIT_PY="${SCRIPT_DIR}/audit_diff.py"
if [[ ! -f "${AUDIT_PY}" ]]; then
  GIT_TOP="$(git rev-parse --show-toplevel 2>/dev/null || true)"
  if [[ -n "${GIT_TOP}" && -f "${GIT_TOP}/scripts/audit_diff.py" ]]; then
    AUDIT_PY="${GIT_TOP}/scripts/audit_diff.py"
  elif [[ -f "${HOME}/.gemini/config/scripts/audit_diff.py" ]]; then
    AUDIT_PY="${HOME}/.gemini/config/scripts/audit_diff.py"
  fi
fi

if [[ ! -f "${AUDIT_PY}" ]]; then
  echo "Error: audit_diff.py not found in ${SCRIPT_DIR}, repository root, or ~/.gemini/config/scripts." >&2
  exit 1
fi

exec "${PYTHON_BIN}" "${AUDIT_PY}" "$@"
