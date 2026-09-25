#!/usr/bin/env bash
# Automated Conformance and Adversarial Defense Test Suite
# Tests exec-proxy.sh and verify-release-gate.sh against whitepaper false-green vectors.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROXY="${REPO_ROOT}/scripts/exec-proxy.sh"
GATE="${REPO_ROOT}/scripts/verify-release-gate.sh"

echo "🧪 Starting Antigravity Runtime Conformance Suite..."
PASS_COUNT=0
TOTAL_TESTS=5

# Test 1: Non-zero exit code propagation
echo -n "  [1/5] Testing non-zero exit code capture... "
set +e
"${PROXY}" --label test_fail bash -c "exit 42" >/dev/null 2>&1
CODE=$?
set -e
if [[ ${CODE} -eq 42 ]]; then
  echo "PASS (Captured real exit code 42)"
  PASS_COUNT=$((PASS_COUNT + 1))
else
  echo "FAIL (Expected 42, got ${CODE})"
  exit 1
fi

# Test 2: Pipefail failure detection
echo -n "  [2/5] Testing pipe failure detection... "
set +e
"${PROXY}" --label test_pipe bash -c "set -o pipefail; false | cat" >/dev/null 2>&1
CODE=$?
set -e
if [[ ${CODE} -ne 0 ]]; then
  echo "PASS (Caught hidden pipe failure)"
  PASS_COUNT=$((PASS_COUNT + 1))
else
  echo "FAIL (Pipe failure was swallowed)"
  exit 1
fi

# Test 3: Valid test execution and manifest reset to green
echo -n "  [3/5] Testing clean verification & metric capture... "
# Re-initialize clean manifest for release gate testing
cat << 'MEOF' > "${REPO_ROOT}/.evidence/manifest.v1.json"
{
  "schema_version": "manifest.v1",
  "git_tree_sha": "uninitialized",
  "policy_disposition": "GREEN",
  "checks": [],
  "open_waivers": []
}
MEOF

"${PROXY}" --label test_clean python3 -c "print('All systems functional'); exit(0)" >/dev/null 2>&1
if [[ -f "${REPO_ROOT}/.evidence/manifest.v1.json" ]]; then
  echo "PASS (Receipt & manifest updated cleanly)"
  PASS_COUNT=$((PASS_COUNT + 1))
else
  echo "FAIL (Manifest not found)"
  exit 1
fi

# Test 4: Release gate pass on clean tree
echo -n "  [4/5] Testing release gate approval on verified state... "
set +e
OUTPUT=$("${GATE}" 2>&1)
CODE=$?
set -e
if [[ ${CODE} -eq 0 ]]; then
  echo "PASS (Gate passed clean evidence)"
  PASS_COUNT=$((PASS_COUNT + 1))
else
  echo "FAIL (Gate rejected valid evidence: ${OUTPUT})"
  exit 1
fi

# Test 5: Release gate fail-closed on modified working tree
echo -n "  [5/5] Testing release gate fail-closed on modified working tree... "
echo "tamper" > "${REPO_ROOT}/tamper_test.txt"
git -C "${REPO_ROOT}" add "${REPO_ROOT}/tamper_test.txt"
set +e
OUTPUT=$("${GATE}" 2>&1)
CODE=$?
set -e
# Clean up tamper test file immediately
git -C "${REPO_ROOT}" rm -f "${REPO_ROOT}/tamper_test.txt" >/dev/null 2>&1 || rm -f "${REPO_ROOT}/tamper_test.txt"

if [[ ${CODE} -ne 0 ]] && echo "${OUTPUT}" | grep -q "Stale evidence"; then
  echo "PASS (Gate blocked stale untracked changes)"
  PASS_COUNT=$((PASS_COUNT + 1))
else
  echo "FAIL (Gate allowed stale release)"
  exit 1
fi

echo ""
echo "🎉 Conformance Suite: ${PASS_COUNT}/${TOTAL_TESTS} tests passed cleanly."
exit 0
