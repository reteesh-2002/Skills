#!/usr/bin/env bash
# Automated Conformance and Adversarial Defense Test Suite
# Tests exec-proxy.sh, verify-release-gate.sh, setup_worktrees.sh, and audit_diff.sh
# against whitepaper vulnerabilities (F01–F14) and empirical probes (P01–P22).

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROXY="${REPO_ROOT}/scripts/exec-proxy.sh"
GATE="${REPO_ROOT}/scripts/verify-release-gate.sh"
SETUP_WT="${REPO_ROOT}/adaptive-worker-orchestrator-v2/scripts/setup_worktrees.sh"
AUDIT_DIFF="${REPO_ROOT}/adaptive-worker-orchestrator-v2/scripts/audit_diff.sh"

echo "🧪 Starting Antigravity Runtime Conformance & Adversarial Suite..."
PASS_COUNT=0
TOTAL_TESTS=17

# Create isolated test environment for deterministic assertions
TEST_SANDBOX=$(mktemp -d -t agy_test_sandbox_XXXXXX)
trap 'rm -rf "${TEST_SANDBOX}"' EXIT

# Initialize git repository in sandbox
git -C "${TEST_SANDBOX}" init -b main --quiet
git -C "${TEST_SANDBOX}" config user.name "Test Runner"
git -C "${TEST_SANDBOX}" config user.email "test@antigravity.internal"
mkdir -p "${TEST_SANDBOX}/scripts" "${TEST_SANDBOX}/adaptive-worker-orchestrator-v2/scripts"
cp "${PROXY}" "${TEST_SANDBOX}/scripts/exec-proxy.sh"
cp "${GATE}" "${TEST_SANDBOX}/scripts/verify-release-gate.sh"
cp "${SETUP_WT}" "${TEST_SANDBOX}/adaptive-worker-orchestrator-v2/scripts/setup_worktrees.sh"
cp "${AUDIT_DIFF}" "${TEST_SANDBOX}/adaptive-worker-orchestrator-v2/scripts/audit_diff.sh"
chmod +x "${TEST_SANDBOX}/scripts/"* "${TEST_SANDBOX}/adaptive-worker-orchestrator-v2/scripts/"*

# Add .gitignore ignoring .evidence/
echo ".evidence/" > "${TEST_SANDBOX}/.gitignore"
echo "console.log('init');" > "${TEST_SANDBOX}/index.js"
git -C "${TEST_SANDBOX}" add .
git -C "${TEST_SANDBOX}" commit -m "chore: initial sandbox state" --quiet

cd "${TEST_SANDBOX}"

SB_PROXY="${TEST_SANDBOX}/scripts/exec-proxy.sh"
SB_GATE="${TEST_SANDBOX}/scripts/verify-release-gate.sh"
SB_SETUP_WT="${TEST_SANDBOX}/adaptive-worker-orchestrator-v2/scripts/setup_worktrees.sh"
SB_AUDIT_DIFF="${TEST_SANDBOX}/adaptive-worker-orchestrator-v2/scripts/audit_diff.sh"

# Test 1: Non-zero exit code propagation
echo -n "  [1/17] Testing non-zero exit code capture... "
set +e
"${SB_PROXY}" --label test_fail bash -c "exit 42" >/dev/null 2>&1
CODE=$?
set -e
if [[ ${CODE} -eq 42 ]]; then
  echo "PASS (Captured real exit code 42)"
  PASS_COUNT=$((PASS_COUNT + 1))
else
  echo "FAIL (Expected 42, got ${CODE})"
  exit 1
fi

# Test 2: Pipefail failure detection (P10)
echo -n "  [2/17] Testing child shell pipe failure detection... "
set +e
"${SB_PROXY}" --label test_pipe bash -c "false | cat" >/dev/null 2>&1
CODE=$?
set -e
if [[ ${CODE} -ne 0 ]]; then
  echo "PASS (Caught hidden child pipe failure)"
  PASS_COUNT=$((PASS_COUNT + 1))
else
  echo "FAIL (Pipe failure was swallowed)"
  exit 1
fi

# Test 3: Real Node spec test metric capture (P16 / F07)
echo -n "  [3/17] Testing Node.js spec test metric parsing (P16)... "
set +e
"${SB_PROXY}" --label test_node_sanity node -e 'const test = require("node:test"); const assert = require("node:assert"); test("sanity", () => { assert.strictEqual(1, 1); });' >/dev/null 2>&1
CODE=$?
set -e
RCPT_FILE=$(ls -t "${TEST_SANDBOX}/.evidence/receipts/"*.json | head -n 1)
COLLECTED=$(python3 -c "import json; r=json.load(open('${RCPT_FILE}')); print(r['metrics']['collected'])")
PASSED=$(python3 -c "import json; r=json.load(open('${RCPT_FILE}')); print(r['metrics']['passed'])")

if [[ ${CODE} -eq 0 && ${COLLECTED} -eq 1 && ${PASSED} -eq 1 ]]; then
  echo "PASS (Correctly extracted: collected=1, passed=1 despite intervening suites line)"
  PASS_COUNT=$((PASS_COUNT + 1))
else
  echo "FAIL (Expected 1 collected/passed, got collected=${COLLECTED}, passed=${PASSED})"
  exit 1
fi

# Test 4: Release gate approval on clean verified state
echo -n "  [4/17] Testing release gate approval on clean verified tree... "
# Clean evidence dir and run a clean verified test check
rm -rf "${TEST_SANDBOX}/.evidence"
"${SB_PROXY}" --label test_node_sanity node -e 'const test = require("node:test"); const assert = require("node:assert"); test("sanity", () => { assert.strictEqual(1, 1); });' >/dev/null 2>&1
set +e
OUTPUT=$("${SB_GATE}" 2>&1)
CODE=$?
set -e
if [[ ${CODE} -eq 0 ]]; then
  echo "PASS (Gate passed clean verified tree)"
  PASS_COUNT=$((PASS_COUNT + 1))
else
  echo "FAIL (Gate rejected valid evidence: ${OUTPUT})"
  exit 1
fi

# Test 5: P01 - Zero tests on test-labeled check blocked by release gate (F01)
echo -n "  [5/17] Testing P01 zero-test test-labeled check rejection... "
"${SB_PROXY}" --label test_fake_zero true >/dev/null 2>&1
set +e
OUTPUT=$("${SB_GATE}" 2>&1)
CODE=$?
set -e
if [[ ${CODE} -ne 0 ]] && echo "${OUTPUT}" | grep -q "Zero-inventory false green"; then
  echo "PASS (Gate blocked zero-inventory test check)"
  PASS_COUNT=$((PASS_COUNT + 1))
else
  echo "FAIL (Gate allowed zero-test check: ${OUTPUT})"
  exit 1
fi

# Test 6: P02 - Unstaged working tree changes blocked by release gate (F02)
echo -n "  [6/17] Testing P02 unstaged working tree modification rejection... "
# Reset manifest to clean state first
"${SB_PROXY}" --label test_node_sanity node -e 'const test = require("node:test"); const assert = require("node:assert"); test("sanity", () => { assert.strictEqual(1, 1); });' >/dev/null 2>&1
echo "tamper" >> "${TEST_SANDBOX}/index.js"
set +e
OUTPUT=$("${SB_GATE}" 2>&1)
CODE=$?
set -e
git -C "${TEST_SANDBOX}" checkout -- index.js
if [[ ${CODE} -ne 0 ]] && echo "${OUTPUT}" | grep -q "Working directory is dirty"; then
  echo "PASS (Gate blocked unstaged file modification)"
  PASS_COUNT=$((PASS_COUNT + 1))
else
  echo "FAIL (Gate allowed unstaged modification: ${OUTPUT})"
  exit 1
fi

# Test 7: P04 - Mixed snapshot rejection (F02b)
echo -n "  [7/17] Testing P04 mixed-snapshot / stale check rejection... "
# Commit a new file to advance tree
echo "export const b = 2;" > "${TEST_SANDBOX}/b.js"
git -C "${TEST_SANDBOX}" add b.js
git -C "${TEST_SANDBOX}" commit -m "add b" --quiet
# Run non-test check on new tree without re-running test
"${SB_PROXY}" --label lint_clean true >/dev/null 2>&1
set +e
OUTPUT=$("${SB_GATE}" 2>&1)
CODE=$?
set -e
if [[ ${CODE} -ne 0 ]] && echo "${OUTPUT}" | grep -q "Mixed snapshot detected"; then
  echo "PASS (Gate blocked mixed snapshot evidence)"
  PASS_COUNT=$((PASS_COUNT + 1))
else
  echo "FAIL (Gate allowed mixed snapshot: ${OUTPUT})"
  exit 1
fi

# Test 8: P05 - Handwritten manifest missing physical receipts/logs (F03)
echo -n "  [8/17] Testing P05 missing physical receipt/log rejection... "
CUR_TREE=$(git -C "${TEST_SANDBOX}" write-tree)
cat << MEOF > "${TEST_SANDBOX}/.evidence/manifest.v1.json"
{
  "schema_version": "manifest.v1",
  "git_tree_sha": "${CUR_TREE}",
  "policy_disposition": "GREEN",
  "checks": [
    {
      "receipt_id": "rcpt_forged_nonexistent",
      "label": "fake_check",
      "command": "true",
      "exit_code": 0,
      "git_tree_sha": "${CUR_TREE}",
      "metrics": {"collected": 0, "passed": 0, "failed": 0, "skipped": 0}
    }
  ]
}
MEOF
set +e
OUTPUT=$("${SB_GATE}" 2>&1)
CODE=$?
set -e
if [[ ${CODE} -ne 0 ]] && echo "${OUTPUT}" | grep -q "Physical receipt file not found"; then
  echo "PASS (Gate blocked forged manifest with missing receipts)"
  PASS_COUNT=$((PASS_COUNT + 1))
else
  echo "FAIL (Gate allowed forged manifest: ${OUTPUT})"
  exit 1
fi

# Test 9: P06 & P09 - Unknown tree SHA rejection (F05)
echo -n "  [9/17] Testing P06 & P09 invalid or unknown tree SHA rejection... "
cat << MEOF > "${TEST_SANDBOX}/.evidence/manifest.v1.json"
{
  "schema_version": "manifest.v1",
  "git_tree_sha": "unknown",
  "policy_disposition": "GREEN",
  "checks": []
}
MEOF
set +e
OUTPUT=$("${SB_GATE}" 2>&1)
CODE=$?
set -e
if [[ ${CODE} -ne 0 ]] && echo "${OUTPUT}" | grep -q "invalid or uninitialized git_tree_sha"; then
  echo "PASS (Gate rejected unknown tree SHA)"
  PASS_COUNT=$((PASS_COUNT + 1))
else
  echo "FAIL (Gate allowed unknown tree SHA: ${OUTPUT})"
  exit 1
fi

# Test 10: P07 - Invalid policy disposition rejection (F11)
echo -n "  [10/17] Testing P07 invalid disposition 'BANANA' rejection... "
cat << MEOF > "${TEST_SANDBOX}/.evidence/manifest.v1.json"
{
  "schema_version": "manifest.v1",
  "git_tree_sha": "${CUR_TREE}",
  "policy_disposition": "BANANA",
  "checks": []
}
MEOF
set +e
OUTPUT=$("${SB_GATE}" 2>&1)
CODE=$?
set -e
if [[ ${CODE} -ne 0 ]] && echo "${OUTPUT}" | grep -q "Invalid policy disposition 'BANANA'"; then
  echo "PASS (Gate rejected BANANA disposition)"
  PASS_COUNT=$((PASS_COUNT + 1))
else
  echo "FAIL (Gate accepted BANANA disposition: ${OUTPUT})"
  exit 1
fi

# Test 11: P08 - Unstructured string waiver rejection (F11)
echo -n "  [11/17] Testing P08 unstructured waiver ['self-approved'] rejection... "
mkdir -p "${TEST_SANDBOX}/.evidence/receipts"
echo '{"receipt_id": "dummy"}' > "${TEST_SANDBOX}/.evidence/receipts/dummy.json"
cat << MEOF > "${TEST_SANDBOX}/.evidence/manifest.v1.json"
{
  "schema_version": "manifest.v1",
  "git_tree_sha": "${CUR_TREE}",
  "policy_disposition": "AMBER",
  "checks": [
    {
      "receipt_id": "dummy",
      "label": "dummy",
      "git_tree_sha": "${CUR_TREE}",
      "exit_code": 0
    }
  ],
  "open_waivers": ["self-approved"]
}
MEOF
set +e
OUTPUT=$("${SB_GATE}" 2>&1)
CODE=$?
set -e
if [[ ${CODE} -ne 0 ]] && echo "${OUTPUT}" | grep -q "Invalid waiver format"; then
  echo "PASS (Gate rejected unstructured string waiver)"
  PASS_COUNT=$((PASS_COUNT + 1))
else
  echo "FAIL (Gate allowed unstructured waiver: ${OUTPUT})"
  exit 1
fi

# Test 12: P12 - Retry laundering prevention & flaky retry AMBER classification (F08)
echo -n "  [12/17] Testing P12 retry laundering prevention & AMBER classification... "
# Run failing check first
set +e
"${SB_PROXY}" --label flaky_test bash -c "exit 1" >/dev/null 2>&1
# Rerun same label with passing command
"${SB_PROXY}" --label flaky_test bash -c "exit 0" >/dev/null 2>&1
set -e
DISP=$(python3 -c "import json; m=json.load(open('${TEST_SANDBOX}/.evidence/manifest.v1.json')); print(m['policy_disposition'])")
HIST_LEN=$(python3 -c "import json; m=json.load(open('${TEST_SANDBOX}/.evidence/manifest.v1.json')); print(len(m.get('attempt_history', [])))")
FLAKY_FLAG=$(python3 -c "import json; m=json.load(open('${TEST_SANDBOX}/.evidence/manifest.v1.json')); print(m['checks'][-1].get('flaky_retry', False))")

if [[ "${DISP}" == "AMBER" && "${FLAKY_FLAG}" == "True" && ${HIST_LEN} -ge 2 ]]; then
  echo "PASS (Retried pass preserved in attempt_history and flagged as AMBER)"
  PASS_COUNT=$((PASS_COUNT + 1))
else
  echo "FAIL (Expected AMBER and flaky_retry=True, got disposition=${DISP}, flaky=${FLAKY_FLAG}, hist=${HIST_LEN})"
  exit 1
fi

# Test 13: P18 - High concurrency race defense (F09)
echo -n "  [13/17] Testing P18 concurrent manifest writes with flock... "
pids=()
for i in {1..6}; do
  "${SB_PROXY}" --label "concurrent_worker_${i}" true >/dev/null 2>&1 &
  pids+=($!)
done
for pid in "${pids[@]}"; do
  wait "$pid"
done

CHECK_COUNT=$(python3 -c "import json; m=json.load(open('${TEST_SANDBOX}/.evidence/manifest.v1.json')); print(len([c for c in m['checks'] if 'concurrent_worker_' in c.get('label', '')]))")
if [[ ${CHECK_COUNT} -eq 6 ]]; then
  echo "PASS (All 6 concurrent checks recorded without lost updates)"
  PASS_COUNT=$((PASS_COUNT + 1))
else
  echo "FAIL (Expected 6 concurrent checks, found ${CHECK_COUNT})"
  exit 1
fi

# Test 14: P19 - Worker worktree dirty cleanup rescue (F04)
echo -n "  [14/17] Testing P19 dirty worktree rescue before cleanup... "
"${SB_SETUP_WT}" main worker_probe >/dev/null 2>&1
WT_PATH="${TEST_SANDBOX}/.git/.orch-worktrees/worker_probe"
echo "uncommitted valuable work" > "${WT_PATH}/critical_work.txt"
"${SB_SETUP_WT}" cleanup >/dev/null 2>&1
RESCUE_BRANCH=$(git -C "${TEST_SANDBOX}" branch --list 'orch/rescue-worker_probe*' | head -n 1 | tr -d ' *')

if [[ -n "${RESCUE_BRANCH}" ]]; then
  echo "PASS (Uncommitted changes preserved in ${RESCUE_BRANCH})"
  PASS_COUNT=$((PASS_COUNT + 1))
else
  echo "FAIL (No rescue branch found for uncommitted work)"
  exit 1
fi

# Test 15: P20 - audit_diff symlink sandbox escape defense (F12)
echo -n "  [15/17] Testing P20 audit_diff out-of-scope symlink rejection... "
ln -s /etc/passwd "${TEST_SANDBOX}/malicious_link"
set +e
OUTPUT=$("${SB_AUDIT_DIFF}" "${TEST_SANDBOX}" main "index.js" 2>&1)
CODE=$?
set -e
rm -f "${TEST_SANDBOX}/malicious_link"
if [[ ${CODE} -ne 0 ]] && echo "${OUTPUT}" | grep -q "OUT-OF-SCOPE-SYMLINK"; then
  echo "PASS (Blocked out-of-scope symlink escape)"
  PASS_COUNT=$((PASS_COUNT + 1))
else
  echo "FAIL (Allowed out-of-scope symlink: ${OUTPUT})"
  exit 1
fi

# Test 16: P21 - audit_diff prefix match boundary defense (F12)
echo -n "  [16/17] Testing P21 audit_diff path prefix boundary defense... "
mkdir -p "${TEST_SANDBOX}/src-evil"
echo "malicious" > "${TEST_SANDBOX}/src-evil/bad.js"
set +e
OUTPUT=$("${SB_AUDIT_DIFF}" "${TEST_SANDBOX}" main "src" 2>&1)
CODE=$?
set -e
rm -rf "${TEST_SANDBOX}/src-evil"
if [[ ${CODE} -ne 0 ]] && echo "${OUTPUT}" | grep -q "OUT-OF-SCOPE"; then
  echo "PASS (Correctly rejected src-evil when allowed prefix is src)"
  PASS_COUNT=$((PASS_COUNT + 1))
else
  echo "FAIL (Allowed src-evil prefix match: ${OUTPUT})"
  exit 1
fi

# Test 17: P22 - audit_diff untracked placeholder detection (F13)
echo -n "  [17/17] Testing P22 audit_diff untracked placeholder detection... "
echo "// TODO: implement secret backdoor" > "${TEST_SANDBOX}/untracked_component.js"
set +e
OUTPUT=$(FAIL_ON_PLACEHOLDERS=1 "${SB_AUDIT_DIFF}" "${TEST_SANDBOX}" main "untracked_component.js" 2>&1)
CODE=$?
set -e
rm -f "${TEST_SANDBOX}/untracked_component.js"
if [[ ${CODE} -ne 0 ]] && echo "${OUTPUT}" | grep -q "PLACEHOLDERS detected"; then
  echo "PASS (Detected placeholders in untracked files)"
  PASS_COUNT=$((PASS_COUNT + 1))
else
  echo "FAIL (Failed to catch untracked placeholder: ${OUTPUT})"
  exit 1
fi

echo ""
echo "🎉 Conformance & Adversarial Suite: ${PASS_COUNT}/${TOTAL_TESTS} tests passed cleanly."
exit 0
