#!/usr/bin/env bash
# Delegation wrapper: delegates directly to canonical scripts/verify-release-gate.sh
# Eliminates redundant placeholder scripts and guarantees identical gate enforcement.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

CANONICAL_GATE="${REPO_ROOT}/scripts/verify-release-gate.sh"

if [[ -f "${CANONICAL_GATE}" ]]; then
  exec bash "${CANONICAL_GATE}" "$@"
else
  echo '{"decision": "deny", "reason": "Canonical verify-release-gate.sh not found."}' >&2
  exit 1
fi
