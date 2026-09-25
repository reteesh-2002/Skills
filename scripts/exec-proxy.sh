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

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EVIDENCE_DIR="${REPO_ROOT}/.evidence"
LOGS_DIR="${EVIDENCE_DIR}/logs"
RECEIPTS_DIR="${EVIDENCE_DIR}/receipts"
MANIFEST_PATH="${EVIDENCE_DIR}/manifest.v1.json"

mkdir -p "${LOGS_DIR}" "${RECEIPTS_DIR}"

LOG_PATH="${LOGS_DIR}/${RUN_ID}.log"
RECEIPT_PATH="${RECEIPTS_DIR}/${RUN_ID}.json"

# Calculate current git tree SHA if git is available
GIT_TREE_SHA="uncommitted"
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  GIT_TREE_SHA=$(git write-tree 2>/dev/null || git rev-parse HEAD 2>/dev/null || echo "uncommitted")
fi

START_MS=$(python3 -c 'import time; print(int(time.time() * 1000))')

# Run the command with pipefail preserved, streaming uncompressed stdout and stderr to the log
set +e
"$@" > >(tee -a "${LOG_PATH}") 2>&1
EXIT_CODE=$?
set -e

END_MS=$(python3 -c 'import time; print(int(time.time() * 1000))')
DURATION_MS=$((END_MS - START_MS))

# Parse framework counts using python helper
python3 - "${COMMAND_STR}" "${EXIT_CODE}" "${DURATION_MS}" "${GIT_TREE_SHA}" "${LOG_PATH}" "${RECEIPT_PATH}" "${MANIFEST_PATH}" "${RUN_ID}" "${LABEL}" << 'PYEOF'
import sys, os, re, json

command_str, exit_code_s, duration_ms_s, git_tree_sha, log_path, receipt_path, manifest_path, run_id, label = sys.argv[1:10]
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

# Node.js built-in test runner
m_node = re.search(r'ℹ\s+tests\s+(\d+)\s+ℹ\s+pass\s+(\d+)\s+ℹ\s+fail\s+(\d+)', log_content)
if m_node:
    collected = int(m_node.group(1))
    passed = int(m_node.group(2))
    failed = int(m_node.group(3))
    m_skip = re.search(r'ℹ\s+skipped\s+(\d+)', log_content)
    if m_skip:
        skipped = int(m_skip.group(1))

# Pytest: e.g. "5 passed, 1 skipped in 0.12s"
m_pytest = re.search(r'(\d+)\s+passed', log_content)
if m_pytest and not m_node:
    passed = int(m_pytest.group(1))
    m_py_fail = re.search(r'(\d+)\s+failed', log_content)
    m_py_skip = re.search(r'(\d+)\s+skipped', log_content)
    if m_py_fail: failed = int(m_py_fail.group(1))
    if m_py_skip: skipped = int(m_py_skip.group(1))
    collected = passed + failed + skipped

# Vitest / Jest: "Tests: 2 passed, 2 total"
m_jest = re.search(r'Tests:\s+.*?(\d+)\s+passed.*?(\d+)\s+total', log_content)
if m_jest and not m_node and not m_pytest:
    passed = int(m_jest.group(1))
    collected = int(m_jest.group(2))
    failed = collected - passed

# Cargo test: "test result: ok. 5 passed; 0 failed; 0 ignored;"
m_cargo = re.search(r'test result:\s+\w+\.\s+(\d+)\s+passed;\s+(\d+)\s+failed;\s+(\d+)\s+ignored', log_content)
if m_cargo:
    passed = int(m_cargo.group(1))
    failed = int(m_cargo.group(2))
    skipped = int(m_cargo.group(3))
    collected = passed + failed + skipped

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
    }
}

with open(receipt_path, "w", encoding="utf-8") as f:
    json.dump(receipt, f, indent=2)

# Update manifest
manifest = {
    "schema_version": "manifest.v1",
    "git_tree_sha": git_tree_sha,
    "policy_disposition": "GREEN" if exit_code == 0 and (collected == 0 or passed == collected) else "RED",
    "checks": [],
    "open_waivers": []
}

if os.path.exists(manifest_path):
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except Exception:
        pass

# Update or append this check
manifest["git_tree_sha"] = git_tree_sha
manifest["checks"] = [c for c in manifest.get("checks", []) if c.get("label") != label]
manifest["checks"].append(receipt)

# Recalculate policy disposition
has_failure = any(c.get("exit_code") != 0 or c.get("metrics", {}).get("failed", 0) > 0 for c in manifest["checks"])
has_skips = any(c.get("metrics", {}).get("skipped", 0) > 0 for c in manifest["checks"])

if has_failure:
    manifest["policy_disposition"] = "RED"
elif has_skips:
    manifest["policy_disposition"] = "AMBER"
else:
    manifest["policy_disposition"] = "GREEN"

with open(manifest_path, "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2)
PYEOF

chmod 644 "${RECEIPT_PATH}"
echo "[exec-proxy] Run ${RUN_ID} complete. Exit: ${EXIT_CODE} (${DURATION_MS}ms). Receipt: ${RECEIPT_PATH}"

exit ${EXIT_CODE}
