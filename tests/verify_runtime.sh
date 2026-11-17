#!/usr/bin/env bash
# Automated Conformance and Adversarial Defense Test Suite
# Tests exec-proxy.sh, verify-release-gate.sh, setup_worktrees.sh, and audit_diff.sh
# against whitepaper vulnerabilities (F01–F14) and empirical probes (P01–P22).

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROXY="${REPO_ROOT}/scripts/exec-proxy.sh"
GATE="${REPO_ROOT}/scripts/verify-release-gate.sh"
SETUP_WT="${REPO_ROOT}/scripts/setup_worktrees.sh"
AUDIT_DIFF="${REPO_ROOT}/scripts/audit_diff.sh"

echo "🧪 Starting Antigravity Runtime Conformance & Adversarial Suite..."
PASS_COUNT=0
TOTAL_TESTS=27

# Create isolated test environment for deterministic assertions
TEST_SANDBOX=$(mktemp -d -t agy_test_sandbox_XXXXXX)
trap 'rm -rf "${TEST_SANDBOX}"' EXIT

# Initialize git repository in sandbox
git -C "${TEST_SANDBOX}" init -b main --quiet
git -C "${TEST_SANDBOX}" config user.name "Test Runner"
git -C "${TEST_SANDBOX}" config user.email "test@antigravity.internal"
mkdir -p "${TEST_SANDBOX}/scripts"
cp "${PROXY}" "${TEST_SANDBOX}/scripts/exec-proxy.sh"
cp "${GATE}" "${TEST_SANDBOX}/scripts/verify-release-gate.sh"
cp "${REPO_ROOT}/scripts/exec_proxy.py" "${TEST_SANDBOX}/scripts/exec_proxy.py"
cp "${REPO_ROOT}/scripts/verify_release_gate.py" "${TEST_SANDBOX}/scripts/verify_release_gate.py"
cp "${REPO_ROOT}/scripts/runtime_evidence.py" "${TEST_SANDBOX}/scripts/runtime_evidence.py"
cp "${REPO_ROOT}/scripts/task_ledger.py" "${TEST_SANDBOX}/scripts/task_ledger.py"
cp "${REPO_ROOT}/scripts/setup_worktrees.py" "${TEST_SANDBOX}/scripts/setup_worktrees.py"
cp "${REPO_ROOT}/scripts/audit_diff.py" "${TEST_SANDBOX}/scripts/audit_diff.py"
cp "${SETUP_WT}" "${TEST_SANDBOX}/scripts/setup_worktrees.sh"
cp "${AUDIT_DIFF}" "${TEST_SANDBOX}/scripts/audit_diff.sh"
chmod +x "${TEST_SANDBOX}/scripts/"*

# Add .gitignore ignoring .evidence/ and __pycache__/
cat << 'GIEOF' > "${TEST_SANDBOX}/.gitignore"
.evidence/
__pycache__/
*.py[cod]
GIEOF
echo "console.log('init');" > "${TEST_SANDBOX}/index.js"
git -C "${TEST_SANDBOX}" add .
git -C "${TEST_SANDBOX}" commit -m "chore: initial sandbox state" --quiet

cd "${TEST_SANDBOX}"

SB_PROXY="${TEST_SANDBOX}/scripts/exec-proxy.sh"
SB_GATE="${TEST_SANDBOX}/scripts/verify-release-gate.sh"
SB_LEDGER="${TEST_SANDBOX}/scripts/task_ledger.py"
SB_SETUP_WT="${TEST_SANDBOX}/scripts/setup_worktrees.sh"
SB_AUDIT_DIFF="${TEST_SANDBOX}/scripts/audit_diff.sh"

# Test 1: Non-zero exit code propagation
echo -n "  [1/26] Testing non-zero exit code capture... "
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
echo -n "  [2/26] Testing child shell pipe failure detection... "
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
echo -n "  [3/26] Testing Node.js spec test metric parsing (P16)... "
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
echo -n "  [4/26] Testing release gate approval on clean verified tree... "
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
echo -n "  [5/26] Testing P01 zero-test test-labeled check rejection... "
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
echo -n "  [6/26] Testing P02 unstaged working tree modification rejection... "
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
echo -n "  [7/26] Testing P04 mixed-snapshot / stale check rejection... "
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
echo -n "  [8/26] Testing P05 missing physical receipt/log rejection... "
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
echo -n "  [9/26] Testing P06 & P09 invalid or unknown tree SHA rejection... "
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
echo -n "  [10/26] Testing P07 invalid disposition 'BANANA' rejection... "
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
echo -n "  [11/26] Testing P08 unstructured waiver ['self-approved'] rejection... "
mkdir -p "${TEST_SANDBOX}/.evidence/receipts"
cat << REOF > "${TEST_SANDBOX}/.evidence/receipts/dummy.json"
{
  "receipt_id": "dummy",
  "command": "true",
  "exit_code": 0,
  "git_tree_sha": "${CUR_TREE}",
  "metrics": {
    "collected": 0,
    "passed": 0,
    "failed": 0,
    "skipped": 0
  }
}
REOF
cat << MEOF > "${TEST_SANDBOX}/.evidence/manifest.v1.json"
{
  "schema_version": "manifest.v1",
  "git_tree_sha": "${CUR_TREE}",
  "policy_disposition": "AMBER",
  "checks": [
    {
      "receipt_id": "dummy",
      "label": "dummy",
      "command": "true",
      "git_tree_sha": "${CUR_TREE}",
      "exit_code": 0,
      "metrics": {
        "collected": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0
      }
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
echo -n "  [12/26] Testing P12 retry laundering prevention & AMBER classification... "
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
echo -n "  [13/26] Testing P18 concurrent manifest writes with flock... "
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
echo -n "  [14/26] Testing P19 dirty worktree rescue before cleanup... "
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
echo -n "  [15/26] Testing P20 audit_diff out-of-scope symlink rejection... "
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
echo -n "  [16/26] Testing P21 audit_diff path prefix boundary defense... "
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
echo -n "  [17/26] Testing P22 audit_diff untracked placeholder detection... "
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

# Test 18: P23 - Worktree preservation on failed rescue commit
echo -n "  [18/26] Testing P23 worktree preservation when rescue commit fails... "
"${SB_SETUP_WT}" main worker_fail_probe >/dev/null 2>&1
FAIL_WT="${TEST_SANDBOX}/.git/.orch-worktrees/worker_fail_probe"
echo "uncommitted critical" > "${FAIL_WT}/critical.txt"
FAIL_GITDIR=$(git -C "${FAIL_WT}" rev-parse --git-dir)
touch "${FAIL_GITDIR}/index.lock"
set +e
CLEANUP_OUT=$("${SB_SETUP_WT}" cleanup 2>&1)
CLEANUP_CODE=$?
set -e
rm -f "${FAIL_GITDIR}/index.lock"
if [[ ${CLEANUP_CODE} -ne 0 && -d "${FAIL_WT}" ]]; then
  echo "PASS (Preserved dirty worktree and aborted cleanup on commit failure)"
  PASS_COUNT=$((PASS_COUNT + 1))
  "${SB_SETUP_WT}" cleanup >/dev/null 2>&1 || true
else
  echo "FAIL (Deleted worktree despite failed rescue commit: ${CLEANUP_OUT})"
  exit 1
fi

# Test 19: P24 - Unstaged modification test run rejected by release gate
echo -n "  [19/26] Testing P24 unstaged working tree test run rejected by gate... "
rm -rf "${TEST_SANDBOX}/.evidence"
echo "console.log('unstaged');" >> "${TEST_SANDBOX}/index.js"
"${SB_PROXY}" --label test_dirty_node node -e 'console.log("ℹ tests 1\nℹ pass 1\nℹ fail 0");' >/dev/null 2>&1
git -C "${TEST_SANDBOX}" checkout -- index.js
set +e
GATE_DIRTY_OUT=$("${SB_GATE}" 2>&1)
GATE_DIRTY_CODE=$?
set -e
if [[ ${GATE_DIRTY_CODE} -ne 0 ]] && echo "${GATE_DIRTY_OUT}" | grep -q "dirty working tree"; then
  echo "PASS (Gate rejected test run executed against unstaged code)"
  PASS_COUNT=$((PASS_COUNT + 1))
else
  echo "FAIL (Gate allowed test run against unstaged code: ${GATE_DIRTY_OUT})"
  exit 1
fi

# Test 20: P25 - Empty receipt {} and invalid waiver date rejection
echo -n "  [20/26] Testing P25 empty receipt {} and invalid waiver date rejection... "
rm -rf "${TEST_SANDBOX}/.evidence"
"${SB_PROXY}" --label test_clean node -e 'console.log("ℹ tests 1\nℹ pass 1\nℹ fail 0");' >/dev/null 2>&1
RCPT_FILE=$(ls -t "${TEST_SANDBOX}/.evidence/receipts/"*.json | head -n 1)
echo "{}" > "${RCPT_FILE}"
set +e
GATE_CORRUPT_OUT=$("${SB_GATE}" 2>&1)
GATE_CORRUPT_CODE=$?
set -e
if [[ ${GATE_CORRUPT_CODE} -ne 0 ]] && echo "${GATE_CORRUPT_OUT}" | grep -q "missing mandatory field"; then
  echo "PASS (Gate rejected corrupt receipt {})"
  PASS_COUNT=$((PASS_COUNT + 1))
else
  echo "FAIL (Gate accepted corrupt receipt {}: ${GATE_CORRUPT_OUT})"
  exit 1
fi

# Test 21: P26 - Antigravity protojson hook protocol compliance
echo -n "  [21/26] Testing P26 Antigravity protojson hook protocol compliance... "
HOOK_PAYLOAD='{"toolCall": {"name": "run_command", "args": {"CommandLine": "git push origin main"}}}'
set +e
HOOK_OUT=$(echo "${HOOK_PAYLOAD}" | "${SB_GATE}" --pre-tool 2>/dev/null)
set -e
DECISION=$(python3 -c "import json, sys; d=json.loads(sys.argv[1]); print(d.get('decision'))" "${HOOK_OUT}" 2>/dev/null || echo "invalid")
if [[ "${DECISION}" == "deny" ]]; then
  echo "PASS (Hook output strict JSON denial without evidence)"
  PASS_COUNT=$((PASS_COUNT + 1))
else
  echo "FAIL (Hook failed protocol compliance: ${HOOK_OUT})"
  exit 1
fi

# Test 22: P27 - Git option variants command matcher in hook mode
echo -n "  [22/26] Testing P27 git option variants hook matching... "
rm -rf "${TEST_SANDBOX}/.evidence"
HOOK_PAYLOAD_C='{"toolCall": {"name": "run_command", "args": {"CommandLine": "git -C . push origin main"}}}'
set +e
HOOK_OUT_C=$(echo "${HOOK_PAYLOAD_C}" | "${SB_GATE}" --pre-tool 2>/dev/null)
set -e
DEC_C=$(python3 -c "import json, sys; d=json.loads(sys.argv[1]); print(d.get('decision'))" "${HOOK_OUT_C}" 2>/dev/null || echo "invalid")

# Test non-release git command (commit with push in message)
HOOK_PAYLOAD_COMMIT='{"toolCall": {"name": "run_command", "args": {"CommandLine": "git commit -m \"push something\""}}}'
set +e
HOOK_OUT_COMMIT=$(echo "${HOOK_PAYLOAD_COMMIT}" | "${SB_GATE}" --pre-tool 2>/dev/null)
set -e
DEC_COMMIT=$(python3 -c "import json, sys; d=json.loads(sys.argv[1]); print(d.get('decision'))" "${HOOK_OUT_COMMIT}" 2>/dev/null || echo "invalid")

if [[ "${DEC_C}" == "deny" && "${DEC_COMMIT}" == "allow" ]]; then
  echo "PASS (git -C . push denied without evidence, git commit -m 'push' allowed)"
  PASS_COUNT=$((PASS_COUNT + 1))
else
  echo "FAIL (Expected deny and allow, got '${DEC_C}' and '${DEC_COMMIT}')"
  exit 1
fi

# Test 23: P28 - Physical receipt field tampering detection
echo -n "  [23/26] Testing P28 physical receipt field tampering detection... "
rm -rf "${TEST_SANDBOX}/.evidence"
"${SB_PROXY}" --label test_tamper node -e 'console.log("ℹ tests 1\nℹ pass 1\nℹ fail 0");' >/dev/null 2>&1
RCPT_FILE=$(ls -t "${TEST_SANDBOX}/.evidence/receipts/"*.json | head -n 1)
# Tamper receipt to report 999 failed tests
python3 -c "
import json, sys
f = sys.argv[1]
d = json.load(open(f))
d['metrics']['failed'] = 999
json.dump(d, open(f, 'w'))
" "${RCPT_FILE}"
set +e
GATE_TAMPER_OUT=$("${SB_GATE}" 2>&1)
GATE_TAMPER_CODE=$?
set -e
if [[ ${GATE_TAMPER_CODE} -ne 0 ]] && echo "${GATE_TAMPER_OUT}" | grep -qE "Test metric mismatch|failed tests"; then
  echo "PASS (Gate detected tampered receipt with 999 failures)"
  PASS_COUNT=$((PASS_COUNT + 1))
else
  echo "FAIL (Gate accepted tampered receipt: ${GATE_TAMPER_OUT})"
  exit 1
fi

# Test 24: P29 - TDD Red-Green cycle snapshot isolation (not flaky retry)
echo -n "  [24/26] Testing P29 TDD Red-Green cycle snapshot isolation... "
rm -rf "${TEST_SANDBOX}/.evidence"
# 1. TDD Red phase: test fails on current snapshot
set +e
"${SB_PROXY}" --label tdd_unit bash -c "exit 1" >/dev/null 2>&1
set -e
# 2. Implementation: commit fix creating new snapshot
echo "console.log('tdd fix applied');" >> "${TEST_SANDBOX}/index.js"
git -C "${TEST_SANDBOX}" add index.js
git -C "${TEST_SANDBOX}" commit -m "fix: apply tdd fix" --quiet
# 3. TDD Green phase: test passes on new snapshot
"${SB_PROXY}" --label tdd_unit node -e 'console.log("ℹ tests 1\nℹ pass 1\nℹ fail 0");' >/dev/null 2>&1
DISP=$(python3 -c "import json; m=json.load(open('${TEST_SANDBOX}/.evidence/manifest.v1.json')); print(m['policy_disposition'])")
FLAKY_FLAG=$(python3 -c "import json; m=json.load(open('${TEST_SANDBOX}/.evidence/manifest.v1.json')); print(m['checks'][-1].get('flaky_retry', False))")
if [[ "${DISP}" == "GREEN" && "${FLAKY_FLAG}" == "False" ]]; then
  echo "PASS (TDD Red-Green progression classified as GREEN, not flaky retry)"
  PASS_COUNT=$((PASS_COUNT + 1))
else
  echo "FAIL (TDD run falsely flagged as flaky retry: disposition=${DISP}, flaky=${FLAKY_FLAG})"
  exit 1
fi

# Test 25: P30 - Date-only waiver ('YYYY-MM-DD') expiry parsing
echo -n "  [25/26] Testing P30 date-only waiver expiry parsing... "
CUR_TREE=$(git -C "${TEST_SANDBOX}" write-tree)
RCPT_ID="rcpt_date_only_waiver_test"
cat << REOF > "${TEST_SANDBOX}/.evidence/receipts/${RCPT_ID}.json"
{
  "receipt_id": "${RCPT_ID}",
  "timestamp_utc": "2026-09-27T00:00:00Z",
  "label": "warn_check",
  "command": "node -e 'console.warn(1)'",
  "exit_code": 0,
  "duration_ms": 10,
  "git_tree_sha": "${CUR_TREE}",
  "working_tree_sha": "${CUR_TREE}",
  "working_tree_dirty": false,
  "metrics": { "collected": 0, "passed": 0, "failed": 0, "skipped": 0 }
}
REOF
cat << MEOF > "${TEST_SANDBOX}/.evidence/manifest.v1.json"
{
  "schema_version": "manifest.v1",
  "git_tree_sha": "${CUR_TREE}",
  "policy_disposition": "AMBER",
  "checks": [
    {
      "receipt_id": "${RCPT_ID}",
      "label": "warn_check",
      "command": "node -e 'console.warn(1)'",
      "git_tree_sha": "${CUR_TREE}",
      "working_tree_sha": "${CUR_TREE}",
      "working_tree_dirty": false,
      "exit_code": 0,
      "metrics": { "collected": 0, "passed": 0, "failed": 0, "skipped": 0 }
    }
  ],
  "open_waivers": [
    {
      "author": "team-lead",
      "reason": "approved for release",
      "expires_at": "2099-01-01"
    }
  ]
}
MEOF
set +e
DATE_GATE_OUT=$("${SB_GATE}" 2>&1)
DATE_GATE_CODE=$?
set -e
if [[ ${DATE_GATE_CODE} -eq 0 ]] && echo "${DATE_GATE_OUT}" | grep -q "RELEASE GATE PASS"; then
  echo "PASS (Date-only waiver '2099-01-01' evaluated successfully without error)"
  PASS_COUNT=$((PASS_COUNT + 1))
else
  echo "FAIL (Date-only waiver crashed or was rejected: ${DATE_GATE_OUT})"
  exit 1
fi

# Test 26: P31 - Bounded log capture and compact model output policy (Release B / O-01–O-05)
echo -n "  [26/26] Testing P31 bounded log capture and compact output formatting... "
rm -rf "${TEST_SANDBOX}/.evidence"
set +e
COMPACT_OUT=$("${SB_PROXY}" --label noisy_check bash -c "for i in {1..50}; do echo \"noisy debug line \$i\"; done; exit 1" 2>&1)
COMPACT_CODE=$?
set -e
if [[ ${COMPACT_CODE} -ne 0 ]] && echo "${COMPACT_OUT}" | grep -q "Failure Excerpt" && echo "${COMPACT_OUT}" | grep -q "Full Log:"; then
  LOG_PATH_FOUND=$(echo "${COMPACT_OUT}" | grep -oE "\.evidence/logs/rcpt_[^ ]+\.log" | head -n 1)
  if [[ -f "${TEST_SANDBOX}/${LOG_PATH_FOUND}" ]] && grep -q "noisy debug line 1" "${TEST_SANDBOX}/${LOG_PATH_FOUND}"; then
    echo "PASS (Raw log captured to disk, compact excerpt returned on failure)"
    PASS_COUNT=$((PASS_COUNT + 1))
  else
    echo "FAIL (Raw log file not properly written or missing: ${LOG_PATH_FOUND})"
    exit 1
  fi
else
  echo "FAIL (Expected Failure Excerpt and Full Log reference: ${COMPACT_OUT})"
  exit 1
fi

# Test 27: P32 - Canonical live task ledger tracking & rendering (Release B / T-01–T-06)
echo -n "  [27/27] Testing P32 canonical live task ledger tracking & rendering... "
python3 "${SB_LEDGER}" init "Release B Ledger Conformance" >/dev/null 2>&1
python3 "${SB_LEDGER}" add --id T1 --title "Core Contract" --owner "Coordinator" >/dev/null 2>&1
python3 "${SB_LEDGER}" update --id T1 --status Running --detail "Implementing" >/dev/null 2>&1
mkdir -p "${TEST_SANDBOX}/.evidence/receipts"
cat << REOF > "${TEST_SANDBOX}/.evidence/receipts/rcpt_sample.json"
{
  "receipt_id": "rcpt_sample",
  "exit_code": 0,
  "git_tree_sha": "${CUR_TREE}",
  "metrics": { "collected": 1, "passed": 1, "failed": 0, "skipped": 0 }
}
REOF
python3 "${SB_LEDGER}" update --id T1 --status Done --detail "Completed" --evidence "rcpt_sample" >/dev/null 2>&1
LEDGER_MD=$(python3 "${SB_LEDGER}" status 2>/dev/null)
if echo "${LEDGER_MD}" | grep -q "1 of 1 tasks complete" && echo "${LEDGER_MD}" | grep -q "Core Contract" && echo "${LEDGER_MD}" | grep -q "Done"; then
  echo "PASS (Task ledger initialized, updated, and rendered markdown accurately)"
  PASS_COUNT=$((PASS_COUNT + 1))
else
  echo "FAIL (Task ledger failed state tracking or rendering: ${LEDGER_MD})"
  exit 1
fi

echo ""
echo "🎉 Conformance & Adversarial Suite: ${PASS_COUNT}/${TOTAL_TESTS} tests passed cleanly."
echo "# tests ${TOTAL_TESTS}"
echo "# pass ${PASS_COUNT}"
echo "# fail $((TOTAL_TESTS - PASS_COUNT))"
exit 0
