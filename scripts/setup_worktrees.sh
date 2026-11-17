#!/usr/bin/env bash
# Antigravity Cross-Platform setup_worktrees Shim
# Delegates execution directly to scripts/setup_worktrees.py for unified cross-platform behavior.

set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON:-python3}"

SETUP_PY="${SCRIPT_DIR}/setup_worktrees.py"
if [[ ! -f "${SETUP_PY}" ]]; then
  GIT_TOP="$(git rev-parse --show-toplevel 2>/dev/null || true)"
  if [[ -n "${GIT_TOP}" && -f "${GIT_TOP}/scripts/setup_worktrees.py" ]]; then
    SETUP_PY="${GIT_TOP}/scripts/setup_worktrees.py"
  elif [[ -f "${HOME}/.gemini/config/scripts/setup_worktrees.py" ]]; then
    SETUP_PY="${HOME}/.gemini/config/scripts/setup_worktrees.py"
  fi
fi

if [[ ! -f "${SETUP_PY}" ]]; then
  echo "Error: setup_worktrees.py not found in ${SCRIPT_DIR}, repository root, or ~/.gemini/config/scripts." >&2
  exit 1
fi

exec "${PYTHON_BIN}" "${SETUP_PY}" "$@"
