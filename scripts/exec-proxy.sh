#!/usr/bin/env bash
# Antigravity Trusted Execution Proxy
# Enforces set -euo pipefail, captures child exit status, routes bounded logs, and writes verified receipts.

set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1

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

# Check working tree disk state (F02, P02, P24)
PORCELAIN=$(git -C "${REPO_ROOT}" status --porcelain 2>/dev/null || true)
if [[ -n "${PORCELAIN}" ]]; then
  WORKING_TREE_DIRTY="true"
else
  WORKING_TREE_DIRTY="false"
fi

# Compute true working directory disk state using a transient index
TMP_INDEX=$(mktemp -t agy_proxy_idx_XXXXXX)
cleanup_tmp_index() {
  rm -f "${TMP_INDEX}"
}
trap cleanup_tmp_index EXIT

GIT_INDEX_FILE="${TMP_INDEX}" git -C "${REPO_ROOT}" read-tree HEAD >/dev/null 2>&1 || true
GIT_INDEX_FILE="${TMP_INDEX}" git -C "${REPO_ROOT}" add -A >/dev/null 2>&1 || true
WORKING_TREE_SHA=$(GIT_INDEX_FILE="${TMP_INDEX}" git -C "${REPO_ROOT}" write-tree 2>/dev/null || echo "unknown")
rm -f "${TMP_INDEX}"

# Get repository tree hash
GIT_TREE_SHA=$(git -C "${REPO_ROOT}" write-tree 2>/dev/null || echo "unknown")

# Write initial receipt and preliminary RUNNING check to manifest under lock safely with json.dump
python3 - "${MANIFEST_PATH}" "${LOCK_PATH}" "${LABEL}" "${GIT_TREE_SHA}" "${RUN_ID}" "${COMMAND_STR}" "${WORKING_TREE_SHA}" "${WORKING_TREE_DIRTY}" "${RECEIPT_PATH}" "${TIMESTAMP}" << 'PYEOF'
import sys, os, json, fcntl

manifest_path, lock_path, label, git_tree_sha, run_id, command_str, working_tree_sha, working_tree_dirty, receipt_path, timestamp = sys.argv[1:11]

# Write initial receipt safely
init_receipt = {
    "receipt_id": run_id,
    "timestamp_utc": timestamp,
    "label": label,
    "command": command_str,
    "exit_code": -1,
    "duration_ms": 0,
    "git_tree_sha": git_tree_sha,
    "working_tree_sha": working_tree_sha,
    "working_tree_dirty": (working_tree_dirty.lower() == "true"),
    "log_path": f".evidence/logs/{run_id}.log",
    "metrics": {
        "collected": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0
    },
    "has_warnings": False
}
with open(receipt_path, "w", encoding="utf-8") as rf:
    json.dump(init_receipt, rf, indent=2)
os.chmod(receipt_path, 0o644)

with open(lock_path, "w") as lf:
    fcntl.flock(lf, fcntl.LOCK_EX)
    try:
        manifest = {
            "schema_version": "manifest.v1",
            "git_tree_sha": git_tree_sha,
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

        manifest.setdefault("checks", [])
        manifest.setdefault("attempt_history", [])
        manifest.setdefault("open_waivers", [])

        # Remove existing check for label and replace with RUNNING marker
        manifest["checks"] = [c for c in manifest["checks"] if c.get("label") != label]
        manifest["checks"].append({
            "receipt_id": run_id,
            "label": label,
            "command": command_str,
            "status": "RUNNING",
            "exit_code": -1,
            "git_tree_sha": git_tree_sha,
            "working_tree_sha": working_tree_sha,
            "working_tree_dirty": (working_tree_dirty.lower() == "true"),
            "log_path": f".evidence/logs/{run_id}.log",
            "metrics": {"collected": 0, "passed": 0, "failed": 0, "skipped": 0}
        })
        manifest["git_tree_sha"] = git_tree_sha

        tmp_path = manifest_path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, manifest_path)
    finally:
        fcntl.flock(lf, fcntl.LOCK_UN)
PYEOF

cleanup_trap() {
  echo "⚠️ [exec-proxy]: Process interrupted. Updating manifest to CANCELLED..." >&2
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

# Run the command with pipefail preserved
# Compact output policy routes full raw log to file while providing concise summaries
set +e
set -o pipefail
if [[ "${VERBOSE_STREAM:-0}" == "1" ]]; then
  "${CMD_TO_RUN[@]}" 2>&1 | tee -a "${LOG_PATH}"
  PIPE_STATUSES=("${PIPESTATUS[@]}")
  CMD_EXIT="${PIPE_STATUSES[0]}"
  SINK_EXIT="${PIPE_STATUSES[1]:-0}"
else
  "${CMD_TO_RUN[@]}" > "${LOG_PATH}" 2>&1
  CMD_EXIT=$?
  SINK_EXIT=0
fi
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

# Parse framework counts, update manifest, and invoke runtime_evidence engine (F07, F08, F09, P16, P18)
METRICS_JSON=$(python3 - "${COMMAND_STR}" "${EXIT_CODE}" "${DURATION_MS}" "${GIT_TREE_SHA}" "${LOG_PATH}" "${RECEIPT_PATH}" "${MANIFEST_PATH}" "${LOCK_PATH}" "${RUN_ID}" "${LABEL}" "${WORKING_TREE_SHA}" "${WORKING_TREE_DIRTY}" "${SCRIPT_DIR}" << 'PYEOF'
import sys, os, re, json, fcntl

command_str, exit_code_s, duration_ms_s, git_tree_sha, log_path, receipt_path, manifest_path, lock_path, run_id, label, working_tree_sha, working_tree_dirty, script_dir = sys.argv[1:14]
exit_code = int(exit_code_s)
duration_ms = int(duration_ms_s)

sys.path.insert(0, script_dir)
import runtime_evidence

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

# Heuristic parser for test frameworks
if re.search(r'\d+\s+(?:passed|failed|error(?:ed)?|skipped)\b', log_content) and re.search(r'in \d+\.?\d*s', log_content):
    # Pytest: "1 passed in 0.05s", "1 passed, 1 skipped in 0.01s", "2 failed in 0.3s"
    m_pass = re.search(r'(\d+)\s+passed', log_content)
    m_fail = re.search(r'(\d+)\s+(?:failed|error(?:ed)?)', log_content)
    m_skip = re.search(r'(\d+)\s+skipped', log_content)
    if m_pass and m_pass.group(1): passed = int(m_pass.group(1))
    if m_fail and m_fail.group(1): failed = int(m_fail.group(1))
    if m_skip and m_skip.group(1): skipped = int(m_skip.group(1))
    collected = passed + failed + skipped
elif "# tests" in log_content or "ℹ tests" in log_content or "✔" in log_content or "ℹ pass" in log_content:
    # Node.js TAP: "# tests 1", "# pass 1", "# fail 0", or modern spec reporter "ℹ tests 1"
    m_tests = re.search(r'(?:#|ℹ)\s+tests\s+(\d+)', log_content)
    m_pass = re.search(r'(?:#|ℹ)\s+pass(?:ed)?\s+(\d+)', log_content)
    m_fail = re.search(r'(?:#|ℹ)\s+fail(?:ed)?\s+(\d+)', log_content)
    m_skip = re.search(r'(?:#|ℹ)\s+(?:cancelled|skipped)\s+(\d+)', log_content)

    if m_tests and m_tests.group(1): collected = int(m_tests.group(1))
    if m_pass and m_pass.group(1): passed = int(m_pass.group(1))
    if m_fail and m_fail.group(1): failed = int(m_fail.group(1))
    if m_skip and m_skip.group(1): skipped = int(m_skip.group(1))

    # Fallback: if collected is still 0, scan for checkmarks/crosses
    if collected == 0:
        pass_matches = len(re.findall(r'✔\s+.+', log_content))
        fail_matches = len(re.findall(r'✖\s+.+', log_content))
        if pass_matches > 0 or fail_matches > 0:
            passed = pass_matches
            failed = fail_matches
            collected = passed + failed
elif "Tests:" in log_content:
    # Jest/Vitest: "Tests:       1 passed, 1 total"
    m_jest = re.search(r'Tests:\s+(\d+)\s+passed,\s+(\d+)\s+total', log_content)
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
elif "Ran " in log_content and (" tests in " in log_content or " test in " in log_content):
    # Python unittest: "Ran 16 tests in 0.004s" or "Ran 1 test in 0.001s"
    m_ran = re.search(r'Ran\s+(\d+)\s+tests?\s+in', log_content)
    m_fail = re.search(r'FAILED\s*\(.*?failures=(\d+)', log_content)
    m_err  = re.search(r'FAILED\s*\(.*?errors=(\d+)', log_content)
    m_skip = re.search(r'skipped=(\d+)', log_content)
    if m_ran:
        collected = int(m_ran.group(1))
        failed    = (int(m_fail.group(1)) if m_fail else 0) + (int(m_err.group(1)) if m_err else 0)
        skipped   = int(m_skip.group(1)) if m_skip else 0
        passed    = collected - failed - skipped

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
    "working_tree_sha": working_tree_sha,
    "working_tree_dirty": (working_tree_dirty.lower() == "true"),
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

        # Flaky retry check using centralized runtime_evidence logic
        curr_tree = git_tree_sha
        curr_wt_sha = receipt.get("working_tree_sha", "")

        if runtime_evidence.is_flaky_retry(manifest["attempt_history"], receipt, curr_tree, curr_wt_sha):
            receipt["flaky_retry"] = True
            receipt["prior_failures_count"] = 1

        # Update checks array for this label
        manifest["checks"] = [c for c in manifest["checks"] if c.get("label") != label]
        manifest["checks"].append(receipt)
        manifest["git_tree_sha"] = git_tree_sha

        # Calculate policy disposition via shared runtime_evidence engine
        manifest["policy_disposition"] = runtime_evidence.calculate_policy_disposition(manifest["checks"])

        tmp_manifest = manifest_path + ".tmp"
        with open(tmp_manifest, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_manifest, manifest_path)
    finally:
        fcntl.flock(lf, fcntl.LOCK_UN)

# Emit parsed metrics for compact summary formatting
print(json.dumps({"collected": collected, "passed": passed, "failed": failed, "skipped": skipped}))
PYEOF
)

# Output summary based on outcome and output policy (Release B / Task T3)
if [[ "${EXIT_CODE}" -eq 0 ]]; then
  PARSED_COLL=$(echo "${METRICS_JSON}" | python3 -c "import json, sys; print(json.load(sys.stdin).get('collected', 0))" 2>/dev/null || echo "0")
  PARSED_PASS=$(echo "${METRICS_JSON}" | python3 -c "import json, sys; print(json.load(sys.stdin).get('passed', 0))" 2>/dev/null || echo "0")
  if [[ "${PARSED_COLL}" -gt 0 ]]; then
    echo "[exec-proxy] ✓ Check '${LABEL}' passed (${DURATION_MS}ms, tests: ${PARSED_PASS}/${PARSED_COLL})."
  else
    echo "[exec-proxy] ✓ Check '${LABEL}' passed (${DURATION_MS}ms)."
  fi
  echo "[exec-proxy] Receipt: ${RECEIPT_PATH}"
  echo "[exec-proxy] Log: ${LOG_PATH}"
else
  echo "❌ [exec-proxy] Check '${LABEL}' failed with exit code ${EXIT_CODE} (${DURATION_MS}ms)." >&2
  echo "[exec-proxy] Failure Excerpt (last 20 lines of ${LOG_PATH}):" >&2
  tail -n 20 "${LOG_PATH}" >&2 || true
  echo "[exec-proxy] Full Log: ${LOG_PATH}" >&2
  echo "[exec-proxy] Receipt: ${RECEIPT_PATH}" >&2
fi

exit ${EXIT_CODE}
