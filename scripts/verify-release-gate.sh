#!/usr/bin/env bash
# Antigravity Release Gate Verifier
# Deterministically evaluates evidence manifests against current git tree to block unverified releases.

set -euo pipefail

PRE_TOOL_CMD=""
PRE_TOOL_INPUT=""

if [[ "$#" -gt 0 && "$1" == "--pre-tool" ]]; then
  if [[ "$#" -gt 1 ]]; then
    PRE_TOOL_CMD="$2"
  elif ! [ -t 0 ]; then
    PRE_TOOL_INPUT=$(cat)
    PRE_TOOL_CMD=$(python3 -c "import sys, json
try:
    data = json.loads(sys.argv[1]) if sys.argv[1] else {}
    print(data.get('tool_input', {}).get('CommandLine', '') or data.get('command', ''))
except Exception:
    print('')" "${PRE_TOOL_INPUT}" 2>/dev/null || echo "")
  fi
  # If pre-tool command doesn't attempt release/push, allow immediately
  if [[ -n "${PRE_TOOL_CMD}" ]] && ! echo "${PRE_TOOL_CMD}" | grep -qE 'git\s+(-[a-zA-Z0-9_\-\.]+\s+)*push|gh\s+pr\s+create|npm\s+publish'; then
    if ! [ -t 0 ] && [[ -n "${PRE_TOOL_INPUT}" ]]; then
      echo '{"decision": "allow"}'
    fi
    exit 0
  fi
fi

fail_gate() {
  local reason="$1"
  echo "❌ [RELEASE GATE BLOCKED]: ${reason}" >&2
  if [[ -n "${PRE_TOOL_INPUT}" ]]; then
    echo "{\"decision\": \"deny\", \"reason\": \"${reason}\"}"
  fi
  exit 1
}

# 1. Enforce git repository presence and CWD alignment (F05, P09)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

if ! git -C "${REPO_ROOT}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  fail_gate "Target directory ${REPO_ROOT} is not inside a git repository."
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  fail_gate "Current working directory $(pwd) is not inside a git repository."
fi

CWD_TOP="$(git rev-parse --show-toplevel 2>/dev/null || pwd -P)"
REPO_TOP="$(git -C "${REPO_ROOT}" rev-parse --show-toplevel 2>/dev/null || pwd -P)"
if [[ "${CWD_TOP}" != "${REPO_TOP}" ]]; then
  fail_gate "Working directory mismatch: CWD is '${CWD_TOP}' but script repository is '${REPO_TOP}'."
fi

MANIFEST_PATH="${REPO_ROOT}/.evidence/manifest.v1.json"

# 2. Check uncommitted or untracked changes in working directory (F02)
PORCELAIN=$(git -C "${REPO_ROOT}" status --porcelain 2>/dev/null || true)
if [[ -n "${PORCELAIN}" ]]; then
  fail_gate "Working directory is dirty (uncommitted or untracked changes present). Stash, commit, or clean working tree before release. Changes:\n${PORCELAIN}"
fi

if [[ ! -f "${MANIFEST_PATH}" ]]; then
  fail_gate "Evidence manifest not found at ${MANIFEST_PATH}. Run verification via scripts/exec-proxy.sh first."
fi

# Evaluate manifest using python policy reducer
python3 - "${MANIFEST_PATH}" "${REPO_ROOT}" << 'PYEOF'
import sys, os, subprocess, json, datetime

manifest_path = sys.argv[1]
repo_root = sys.argv[2]
evidence_dir = os.path.dirname(manifest_path)

try:
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
except Exception as e:
    print(f"❌ [RELEASE GATE BLOCKED]: Invalid JSON in manifest: {e}", file=sys.stderr)
    sys.exit(1)

# 1. Schema check (F11)
if manifest.get("schema_version") != "manifest.v1":
    print("❌ [RELEASE GATE BLOCKED]: Unsupported schema_version in manifest", file=sys.stderr)
    sys.exit(1)

disposition = manifest.get("policy_disposition", "RED")
if disposition not in ("GREEN", "AMBER"):
    print(f"❌ [RELEASE GATE BLOCKED]: Invalid policy disposition '{disposition}'. Must be GREEN or AMBER.", file=sys.stderr)
    sys.exit(1)

# 2. Git Tree Freshness & Unknown Tree Rejection (F02, F05)
try:
    current_tree = subprocess.check_output(["git", "-C", repo_root, "write-tree"], stderr=subprocess.DEVNULL).decode().strip()
except Exception:
    current_tree = "unknown"

manifest_tree = manifest.get("git_tree_sha", "")

if not current_tree or current_tree in ("unknown", "uninitialized"):
    print("❌ [RELEASE GATE BLOCKED]: Current git tree cannot be determined.", file=sys.stderr)
    sys.exit(1)

if not manifest_tree or manifest_tree in ("unknown", "uninitialized"):
    print(f"❌ [RELEASE GATE BLOCKED]: Manifest contains invalid or uninitialized git_tree_sha: '{manifest_tree}'", file=sys.stderr)
    sys.exit(1)

if current_tree != manifest_tree:
    print(f"❌ [RELEASE GATE BLOCKED]: Stale evidence. Working tree changed since tests ran.", file=sys.stderr)
    print(f"   Tested tree:  {manifest_tree}", file=sys.stderr)
    print(f"   Current tree: {current_tree}", file=sys.stderr)
    print(f"   Action: Re-run verification suite via scripts/exec-proxy.sh before releasing.", file=sys.stderr)
    sys.exit(1)

# 3. Check inventory
checks = manifest.get("checks", [])
if not checks:
    print("❌ [RELEASE GATE BLOCKED]: Manifest contains 0 verification checks.", file=sys.stderr)
    sys.exit(1)

# 4. Check results, False-green defense & Physical evidence verification (F01, F02b, F03, F06)
total_collected_tests = 0
has_test_checks = False

for c in checks:
    label = c.get("label", "unknown")
    cmd = c.get("command", "unknown")
    exit_code = c.get("exit_code", -1)
    metrics = c.get("metrics", {})
    collected = metrics.get("collected", 0)
    passed = metrics.get("passed", 0)
    failed = metrics.get("failed", 0)
    check_tree = c.get("git_tree_sha", "")
    receipt_id = c.get("receipt_id")
    log_rel = c.get("log_path")

    # F03: Physical receipt existence verification
    if not receipt_id:
        print(f"❌ [RELEASE GATE BLOCKED]: Check '{label}' missing receipt_id.", file=sys.stderr)
        sys.exit(1)
    receipt_file = os.path.join(evidence_dir, "receipts", f"{receipt_id}.json")
    if not os.path.exists(receipt_file):
        print(f"❌ [RELEASE GATE BLOCKED]: Physical receipt file not found: {receipt_file}", file=sys.stderr)
        sys.exit(1)

    # F03: Physical log existence verification
    if log_rel:
        log_file = os.path.normpath(os.path.join(evidence_dir, log_rel))
        if not os.path.exists(log_file):
            print(f"❌ [RELEASE GATE BLOCKED]: Execution log file not found: {log_file}", file=sys.stderr)
            sys.exit(1)

    # F02b: Mixed snapshot defense (every check must match current tree)
    if not check_tree or check_tree in ("unknown", "uninitialized"):
        print(f"❌ [RELEASE GATE BLOCKED]: Check '{label}' has invalid git_tree_sha '{check_tree}'.", file=sys.stderr)
        sys.exit(1)
    if check_tree != current_tree:
        print(f"❌ [RELEASE GATE BLOCKED]: Mixed snapshot detected. Check '{label}' was tested against tree {check_tree[:8]}, but current tree is {current_tree[:8]}.", file=sys.stderr)
        sys.exit(1)

    # Exit code & failure verification
    if exit_code != 0:
        print(f"❌ [RELEASE GATE BLOCKED]: Check '{label}' ('{cmd}') failed with exit code {exit_code}.", file=sys.stderr)
        sys.exit(1)

    if failed > 0:
        print(f"❌ [RELEASE GATE BLOCKED]: Check '{label}' reported {failed} failed tests.", file=sys.stderr)
        sys.exit(1)

    if collected > 0 and passed != collected:
        print(f"❌ [RELEASE GATE BLOCKED]: False-green trap in '{label}'. Passed ({passed}) != Collected ({collected}).", file=sys.stderr)
        sys.exit(1)

    # F01: Test-labeled checks must collect > 0 tests
    is_test_check = ("test" in label.lower()) or ("test" in cmd.lower()) or ("pytest" in cmd.lower()) or ("vitest" in cmd.lower()) or ("jest" in cmd.lower())
    if is_test_check:
        has_test_checks = True
        total_collected_tests += collected
        if collected == 0:
            print(f"❌ [RELEASE GATE BLOCKED]: Test check '{label}' recorded 0 collected tests (Zero-inventory false green).", file=sys.stderr)
            sys.exit(1)

if has_test_checks and total_collected_tests == 0:
    print("❌ [RELEASE GATE BLOCKED]: Test checks were executed but total collected tests is 0.", file=sys.stderr)
    sys.exit(1)

# 5. Policy disposition & Strict waiver objects (F11)
disposition = manifest.get("policy_disposition", "RED")
if disposition not in ("GREEN", "AMBER"):
    print(f"❌ [RELEASE GATE BLOCKED]: Invalid policy disposition '{disposition}'. Must be GREEN or AMBER.", file=sys.stderr)
    sys.exit(1)

if disposition == "RED":
    print("❌ [RELEASE GATE BLOCKED]: Manifest policy disposition is RED.", file=sys.stderr)
    sys.exit(1)

if disposition == "AMBER":
    waivers = manifest.get("open_waivers", [])
    if not waivers:
        print("❌ [RELEASE GATE BLOCKED]: Manifest policy is AMBER but no authorized waiver is registered.", file=sys.stderr)
        sys.exit(1)

    for w in waivers:
        if not isinstance(w, dict):
            print("❌ [RELEASE GATE BLOCKED]: Invalid waiver format. Must be a structured object with author, reason, and expires_at.", file=sys.stderr)
            sys.exit(1)
        author = w.get("author")
        reason = w.get("reason")
        expires_at = w.get("expires_at")
        if not author or not reason or not expires_at:
            print("❌ [RELEASE GATE BLOCKED]: Incomplete waiver object. Missing author, reason, or expires_at.", file=sys.stderr)
            sys.exit(1)

        try:
            exp = datetime.datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            now = datetime.datetime.now(datetime.timezone.utc)
            if exp < now:
                print(f"❌ [RELEASE GATE BLOCKED]: Waiver by '{author}' expired on {expires_at}.", file=sys.stderr)
                sys.exit(1)
        except Exception:
            try:
                exp = datetime.datetime.strptime(expires_at, "%Y-%m-%d").replace(tzinfo=datetime.timezone.utc)
                now = datetime.datetime.now(datetime.timezone.utc)
                if exp < now:
                    print(f"❌ [RELEASE GATE BLOCKED]: Waiver by '{author}' expired on {expires_at}.", file=sys.stderr)
                    sys.exit(1)
            except Exception:
                pass

# Success
print(f"✅ [RELEASE GATE PASS]: {len(checks)} check(s) verified against tree {current_tree[:8]}. Status: {disposition}")
sys.exit(0)
PYEOF
