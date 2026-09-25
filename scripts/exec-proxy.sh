#!/usr/bin/env bash
# Antigravity Trusted Execution Proxy
# Enforces set -euo pipefail, captures child exit status, streams logs, and writes immutable receipts.

set -euo pipefail

LABEL="check"
if [[ "$#" -gt 1 && "$1" == "--label" ]]; then
  LABEL="$2"
  shift 2
fi

if [[ "$#" -eq 0 ]]; then
  echo "Error: No command specified to exec-proxy.sh" >&2
  echo "Usage: scripts/exec-proxy.sh [--label LABEL] <command...>" >&2
  exit 1
fi

COMMAND_STR="$*"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
RUN_ID="rcpt_$(date +%Y%m%d_%H%M%S)_$RANDOM"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

if ! git -C "${REPO_ROOT}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: Target repository ${REPO_ROOT} is not inside a git repository." >&2
  exit 1
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: Current working directory $(pwd) is not inside a git repository." >&2
  exit 1
fi

CWD_TOP="$(git rev-parse --show-toplevel 2>/dev/null || pwd -P)"
REPO_TOP="$(git -C "${REPO_ROOT}" rev-parse --show-toplevel 2>/dev/null || pwd -P)"
if [[ "${CWD_TOP}" != "${REPO_TOP}" ]]; then
  echo "Error: Working directory mismatch: CWD is '${CWD_TOP}' but proxy repository is '${REPO_TOP}'." >&2
  exit 1
fi

EVIDENCE_DIR="${REPO_ROOT}/.evidence"
LOGS_DIR="${EVIDENCE_DIR}/logs"
RECEIPTS_DIR="${EVIDENCE_DIR}/receipts"
MANIFEST_PATH="${EVIDENCE_DIR}/manifest.v1.json"
LOCK_PATH="${EVIDENCE_DIR}/manifest.lock"

mkdir -p "${LOGS_DIR}" "${RECEIPTS_DIR}"

LOG_PATH="${LOGS_DIR}/${RUN_ID}.log"
RECEIPT_PATH="${RECEIPTS_DIR}/${RUN_ID}.json"

# Calculate current git tree SHA if git is available
GIT_TREE_SHA="unknown"
if git -C "${REPO_ROOT}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  GIT_TREE_SHA=$(git -C "${REPO_ROOT}" write-tree 2>/dev/null || echo "unknown")
fi

# Pre-register check as RUNNING and invalidate GREEN in manifest under lock (F06, F09, P17)
python3 - "${MANIFEST_PATH}" "${LOCK_PATH}" "${LABEL}" "${GIT_TREE_SHA}" "${COMMAND_STR}" "${RUN_ID}" << 'PYEOF'
import sys, os, json, fcntl

manifest_path, lock_path, label, tree_sha, cmd, run_id = sys.argv[1:7]

with open(lock_path, "w") as lf:
    fcntl.flock(lf, fcntl.LOCK_EX)
    try:
        manifest = {
            "schema_version": "manifest.v1",
            "git_tree_sha": tree_sha,
            "policy_disposition": "RED",
            "checks": [],
            "attempt_history": [],
            "open_waivers": []
        }
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest = json.load(f)
            except Exception:
                pass

        manifest["policy_disposition"] = "RED"
        # Record pending attempt
        running_entry = {
            "receipt_id": run_id,
            "label": label,
            "command": cmd,
            "status": "RUNNING",
            "git_tree_sha": tree_sha
        }
        # Mark check as running
        existing = [c for c in manifest.get("checks", []) if c.get("label") != label]
        existing.append(running_entry)
        manifest["checks"] = existing

        tmp_path = manifest_path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, manifest_path)
    finally:
        fcntl.flock(lf, fcntl.LOCK_UN)
PYEOF

# Signal trap to record cancellation if interrupted (F06, P17)
INTERRUPTED=0
cleanup_trap() {
  local sig=$?
  INTERRUPTED=1
  echo "[exec-proxy] Interrupted by signal. Recording cancellation..." >&2
  python3 - "${MANIFEST_PATH}" "${LOCK_PATH}" "${LABEL}" << 'PYEOF'
import sys, os, json, fcntl
manifest_path, lock_path, label = sys.argv[1:4]
with open(lock_path, "w") as lf:
    fcntl.flock(lf, fcntl.LOCK_EX)
    try:
        if os.path.exists(manifest_path):
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            manifest["policy_disposition"] = "RED"
            for c in manifest.get("checks", []):
                if c.get("label") == label and c.get("status") == "RUNNING":
                    c["status"] = "CANCELLED"
                    c["exit_code"] = 130
            tmp_path = manifest_path + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, manifest_path)
    finally:
        fcntl.flock(lf, fcntl.LOCK_UN)
PYEOF
  exit 130
}
trap cleanup_trap INT TERM

# If command is invoked as bash -c "...", enforce pipefail (P10)
CMD_TO_RUN=("$@")
if [[ "${1:-}" == "bash" && "${2:-}" == "-c" ]]; then
  CMD_TO_RUN=("bash" "-c" "set -o pipefail; ${3:-}")
fi

START_MS=$(python3 -c 'import time; print(int(time.time() * 1000))')

# Run the command with pipefail preserved and stream to log via pipe (F06, P14)
set +e
set -o pipefail
"${CMD_TO_RUN[@]}" 2>&1 | tee -a "${LOG_PATH}"
PIPE_STATUSES=("${PIPESTATUS[@]}")
CMD_EXIT="${PIPE_STATUSES[0]}"
SINK_EXIT="${PIPE_STATUSES[1]:-0}"
set -e

# If the sink failed, fail immediately (P14)
if [[ ${SINK_EXIT} -ne 0 ]]; then
  echo "❌ [exec-proxy]: Log sink failed with exit code ${SINK_EXIT}" >&2
  EXIT_CODE=${SINK_EXIT}
else
  EXIT_CODE=${CMD_EXIT}
fi

# Ensure log file exists
touch "${LOG_PATH}"

END_MS=$(python3 -c 'import time; print(int(time.time() * 1000))')
DURATION_MS=$((END_MS - START_MS))

# Disable interrupt trap before final atomic update
trap - INT TERM

# Parse framework counts and update manifest under lock (F07, F08, F09, P16, P18)
python3 - "${COMMAND_STR}" "${EXIT_CODE}" "${DURATION_MS}" "${GIT_TREE_SHA}" "${LOG_PATH}" "${RECEIPT_PATH}" "${MANIFEST_PATH}" "${LOCK_PATH}" "${RUN_ID}" "${LABEL}" << 'PYEOF'
import sys, os, re, json, fcntl

command_str, exit_code_s, duration_ms_s, git_tree_sha, log_path, receipt_path, manifest_path, lock_path, run_id, label = sys.argv[1:11]
exit_code = int(exit_code_s)
duration_ms = int(duration_ms_s)

log_content = ""
if os.path.exists(log_path):
    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
        log_content = f.read()

# Default counts
collected = 0
passed = 0
failed = 0
skipped = 0
has_deprecation_warning = False

# Node.js built-in test runner (F07 / P16: handles intervening lines like 'ℹ suites' or 'ℹ cancelled')
if "ℹ tests" in log_content:
    m_tests = re.search(r'ℹ\s+tests\s+(\d+)', log_content)
    m_pass = re.search(r'ℹ\s+pass\s+(\d+)', log_content)
    m_fail = re.search(r'ℹ\s+fail\s+(\d+)', log_content)
    m_skip = re.search(r'ℹ\s+skipped\s+(\d+)', log_content)
    if m_tests: collected = int(m_tests.group(1))
    if m_pass: passed = int(m_pass.group(1))
    if m_fail: failed = int(m_fail.group(1))
    if m_skip: skipped = int(m_skip.group(1))
elif "# tests" in log_content: # TAP format from node/tap
    m_tests = re.search(r'#\s+tests\s+(\d+)', log_content)
    m_pass = re.search(r'#\s+pass\s+(\d+)', log_content)
    m_fail = re.search(r'#\s+fail\s+(\d+)', log_content)
    if m_tests: collected = int(m_tests.group(1))
    if m_pass: passed = int(m_pass.group(1))
    if m_fail: failed = int(m_fail.group(1))
elif "passed" in log_content and ("failed" in log_content or "passed in" in log_content or "test session starts" in log_content):
    # Pytest format
    m_pass = re.search(r'(\d+)\s+passed', log_content)
    m_fail = re.search(r'(\d+)\s+failed', log_content)
    m_skip = re.search(r'(\d+)\s+skipped', log_content)
    if m_pass: passed = int(m_pass.group(1))
    if m_fail: failed = int(m_fail.group(1))
    if m_skip: skipped = int(m_skip.group(1))
    collected = passed + failed + skipped
elif "Tests:" in log_content:
    # Vitest / Jest: "Tests: 2 passed, 2 total"
    m_jest = re.search(r'Tests:\s+.*?(\d+)\s+passed.*?(\d+)\s+total', log_content)
    if m_jest:
        passed = int(m_jest.group(1))
        collected = int(m_jest.group(2))
        failed = collected - passed
elif "test result:" in log_content:
    # Cargo test: "test result: ok. 5 passed; 0 failed; 0 ignored;"
    m_cargo = re.search(r'test result:\s+\w+\.\s+(\d+)\s+passed;\s+(\d+)\s+failed;\s+(\d+)\s+ignored', log_content)
    if m_cargo:
        passed = int(m_cargo.group(1))
        failed = int(m_cargo.group(2))
        skipped = int(m_cargo.group(3))
        collected = passed + failed + skipped

# Check for deprecation warnings (F08, P13)
if "DeprecationWarning" in log_content or "ExperimentalWarning" in log_content:
    has_deprecation_warning = True

# Build receipt
receipt = {
    "receipt_id": run_id,
    "label": label,
    "command": command_str,
    "exit_code": exit_code,
    "duration_ms": duration_ms,
    "git_tree_sha": git_tree_sha,
    "log_path": os.path.relpath(log_path, os.path.dirname(manifest_path)),
    "metrics": {
        "collected": collected,
        "passed": passed,
        "failed": failed,
        "skipped": skipped
    },
    "has_warnings": has_deprecation_warning
}

# Write receipt file atomically
tmp_receipt = receipt_path + ".tmp"
with open(tmp_receipt, "w", encoding="utf-8") as f:
    json.dump(receipt, f, indent=2)
    f.flush()
    os.fsync(f.fileno())
os.replace(tmp_receipt, receipt_path)
os.chmod(receipt_path, 0o644)

# Update manifest under exclusive lock (F08, F09, P12, P18)
with open(lock_path, "w") as lf:
    fcntl.flock(lf, fcntl.LOCK_EX)
    try:
        manifest = {
            "schema_version": "manifest.v1",
            "git_tree_sha": git_tree_sha,
            "policy_disposition": "GREEN" if exit_code == 0 and (collected == 0 or passed == collected) else "RED",
            "checks": [],
            "attempt_history": [],
            "open_waivers": []
        }

        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest = json.load(f)
            except Exception:
                pass

        manifest.setdefault("checks", [])
        manifest.setdefault("attempt_history", [])
        manifest.setdefault("open_waivers", [])

        # F08 / P12: Record to immutable attempt history
        manifest["attempt_history"].append(receipt)

        # Check if there were prior failed attempts for this label
        prior_failed_attempts = [
            a for a in manifest["attempt_history"]
            if a.get("label") == label and (a.get("exit_code") != 0 or a.get("metrics", {}).get("failed", 0) > 0)
        ]

        if prior_failed_attempts and exit_code == 0 and failed == 0:
            receipt["flaky_retry"] = True
            receipt["prior_failures_count"] = len(prior_failed_attempts)

        # Update checks array for this label
        manifest["checks"] = [c for c in manifest["checks"] if c.get("label") != label]
        manifest["checks"].append(receipt)
        manifest["git_tree_sha"] = git_tree_sha

        # Calculate policy disposition
        has_failure = any(c.get("exit_code") != 0 or c.get("metrics", {}).get("failed", 0) > 0 for c in manifest["checks"])
        has_skips = any(c.get("metrics", {}).get("skipped", 0) > 0 for c in manifest["checks"])
        has_flaky = any(c.get("flaky_retry", False) for c in manifest["checks"])
        has_warnings = any(c.get("has_warnings", False) for c in manifest["checks"])

        if has_failure:
            manifest["policy_disposition"] = "RED"
        elif has_skips or has_flaky or has_warnings:
            # F08 / P12: Retried pass or warning results in AMBER disposition
            manifest["policy_disposition"] = "AMBER"
        else:
            manifest["policy_disposition"] = "GREEN"

        tmp_manifest = manifest_path + ".tmp"
        with open(tmp_manifest, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_manifest, manifest_path)
    finally:
        fcntl.flock(lf, fcntl.LOCK_UN)
PYEOF

echo "[exec-proxy] Run ${RUN_ID} complete. Exit: ${EXIT_CODE} (${DURATION_MS}ms). Receipt: ${RECEIPT_PATH}"

exit ${EXIT_CODE}
