#!/usr/bin/env bash
# Antigravity Release Gate Verifier
# Deterministically evaluates evidence manifests against current git tree to block unverified releases.

set -euo pipefail

GATE_HOOK_MODE=0

if [[ "$#" -gt 0 && "$1" == "--pre-tool" ]]; then
  GATE_HOOK_MODE=1
  export GATE_HOOK_MODE
  if [[ "$#" -gt 1 ]]; then
    PRE_TOOL_CMD="$2"
  elif ! [ -t 0 ]; then
    PRE_TOOL_INPUT=$(cat)
    PRE_TOOL_CMD=$(python3 -c "import sys, json
try:
    data = json.loads(sys.argv[1]) if sys.argv[1] else {}
    tool_call = data.get('toolCall', {})
    args = tool_call.get('args', {})
    print(args.get('CommandLine') or data.get('tool_input', {}).get('CommandLine') or data.get('command') or '')
except Exception:
    print('')" "${PRE_TOOL_INPUT}" 2>/dev/null || echo "")
  fi

  # Check if pre-tool command invokes a release gate trigger (git push, gh pr create, npm publish)
  # Uses shlex command tokenization to correctly handle git options with arguments (e.g. git -C . push origin main)
  IS_RELEASE=$(python3 -c "import sys, shlex
cmd = sys.argv[1]
if not cmd or not cmd.strip():
    print('0')
    sys.exit(0)
try:
    tokens = shlex.split(cmd)
except Exception:
    tokens = cmd.split()

cmds = []
curr = []
for t in tokens:
    if t in (';', '&&', '||', '|', '&'):
        if curr:
            cmds.append(curr)
            curr = []
    else:
        curr.append(t)
if curr:
    cmds.append(curr)

is_rel = False
for c in cmds:
    if not c:
        continue
    if len(c) >= 2 and c[0] == 'npm' and c[1] == 'publish':
        is_rel = True; break
    if len(c) >= 3 and c[0] == 'gh' and c[1] in ('pr', 'release') and c[2] == 'create':
        is_rel = True; break
    if c[0] == 'git':
        idx = 1
        opts_with_arg = {'-C', '-c', '--git-dir', '--work-tree', '--namespace', '--super-prefix', '--exec-path', '--config-env'}
        while idx < len(c):
            arg = c[idx]
            if arg in opts_with_arg:
                idx += 2
                continue
            if any(arg.startswith(prefix + '=') for prefix in ('--git-dir', '--work-tree', '--namespace', '--super-prefix', '--exec-path', '--config-env')):
                idx += 1
                continue
            if arg.startswith('-'):
                idx += 1
                continue
            if arg == 'push':
                is_rel = True
            break
    if is_rel:
        break
print('1' if is_rel else '0')
" "${PRE_TOOL_CMD:-}" 2>/dev/null || echo "1")

  if [[ "${IS_RELEASE}" == "0" ]]; then
    if [[ "${GATE_HOOK_MODE}" -eq 1 ]]; then
      echo '{"decision": "allow"}'
    fi
    exit 0
  fi
fi

fail_gate() {
  local reason="$1"
  if [[ "${GATE_HOOK_MODE}" -eq 1 ]]; then
    echo "❌ [RELEASE GATE BLOCKED]: ${reason}" >&2
    python3 -c "import sys, json; print(json.dumps({'decision': 'deny', 'reason': sys.argv[1]}))" "${reason}"
  else
    echo "❌ [RELEASE GATE BLOCKED]: ${reason}" >&2
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

def fail_python_gate(reason):
    print(f"❌ [RELEASE GATE BLOCKED]: {reason}", file=sys.stderr)
    if os.environ.get("GATE_HOOK_MODE") == "1":
        print(json.dumps({"decision": "deny", "reason": reason}))
    sys.exit(1)

try:
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except Exception as e:
        fail_python_gate(f"Invalid JSON in manifest: {e}")

    # 1. Schema check (F11)
    if manifest.get("schema_version") != "manifest.v1":
        fail_python_gate("Unsupported schema_version in manifest")

    disposition = manifest.get("policy_disposition", "RED")
    if disposition not in ("GREEN", "AMBER"):
        fail_python_gate(f"Invalid policy disposition '{disposition}'. Must be GREEN or AMBER.")

    # 2. Git Tree Freshness & Unknown Tree Rejection (F02, F05)
    try:
        current_tree = subprocess.check_output(["git", "-C", repo_root, "write-tree"], stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        current_tree = "unknown"

    manifest_tree = manifest.get("git_tree_sha", "")

    if not current_tree or current_tree in ("unknown", "uninitialized"):
        fail_python_gate("Current git tree cannot be determined.")

    if not manifest_tree or manifest_tree in ("unknown", "uninitialized"):
        fail_python_gate(f"Manifest contains invalid or uninitialized git_tree_sha: '{manifest_tree}'")

    if current_tree != manifest_tree:
        fail_python_gate(f"Stale evidence. Working tree changed since tests ran. Tested: {manifest_tree[:8]}, Current: {current_tree[:8]}. Re-run verification suite via scripts/exec-proxy.sh before releasing.")

    # 3. Check inventory
    checks = manifest.get("checks", [])
    if not checks:
        fail_python_gate("Manifest contains 0 verification checks.")

    # 4. Check results, False-green defense, Working tree disk check & Physical evidence verification (F01, F02b, F02c, F03, F06)
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

        # F03: Physical receipt existence and comprehensive content verification
        if not receipt_id:
            fail_python_gate(f"Check '{label}' missing receipt_id.")
        receipt_file = os.path.join(evidence_dir, "receipts", f"{receipt_id}.json")
        if not os.path.exists(receipt_file):
            fail_python_gate(f"Physical receipt file not found: {receipt_file}")

        try:
            with open(receipt_file, "r", encoding="utf-8") as rf:
                rcpt_data = json.load(rf)
        except Exception as e:
            fail_python_gate(f"Receipt '{receipt_id}' is corrupt or unreadable: {e}")

        for req_field in ("receipt_id", "command", "exit_code", "git_tree_sha", "metrics"):
            if req_field not in rcpt_data:
                fail_python_gate(f"Receipt '{receipt_id}' missing mandatory field '{req_field}'.")

        if rcpt_data.get("receipt_id") != receipt_id:
            fail_python_gate(f"Receipt ID mismatch in {receipt_file}.")

        rcpt_cmd = rcpt_data.get("command")
        rcpt_exit = rcpt_data.get("exit_code")
        rcpt_tree = rcpt_data.get("git_tree_sha")
        rcpt_wt_sha = rcpt_data.get("working_tree_sha")
        rcpt_wt_dirty = rcpt_data.get("working_tree_dirty", False)
        rcpt_metrics = rcpt_data.get("metrics", {})
        rcpt_failed = rcpt_metrics.get("failed", 0)
        rcpt_passed = rcpt_metrics.get("passed", 0)
        rcpt_collected = rcpt_metrics.get("collected", 0)

        # Cross-validate manifest fields against physical receipt
        if rcpt_cmd != cmd:
            fail_python_gate(f"Command mismatch between manifest ('{cmd}') and receipt '{receipt_id}' ('{rcpt_cmd}').")

        if rcpt_exit != exit_code:
            fail_python_gate(f"Exit code mismatch between manifest ({exit_code}) and receipt '{receipt_id}' ({rcpt_exit}) for '{label}'.")

        if rcpt_tree != check_tree:
            fail_python_gate(f"Git tree SHA mismatch between manifest ({check_tree[:8]}) and receipt '{receipt_id}' ({rcpt_tree[:8]}) for '{label}'.")

        if rcpt_wt_dirty or c.get("working_tree_dirty", False):
            fail_python_gate(f"Check '{label}' was executed against a dirty working tree with unstaged modifications.")

        if rcpt_wt_sha and c.get("working_tree_sha") and rcpt_wt_sha != c.get("working_tree_sha"):
            fail_python_gate(f"Working tree SHA mismatch between manifest ({c.get('working_tree_sha')[:8]}) and receipt '{receipt_id}' ({rcpt_wt_sha[:8]}).")

        if rcpt_failed != failed or rcpt_passed != passed or rcpt_collected != collected:
            fail_python_gate(f"Test metric mismatch between manifest (P:{passed}, F:{failed}, C:{collected}) and receipt '{receipt_id}' (P:{rcpt_passed}, F:{rcpt_failed}, C:{rcpt_collected}) for '{label}'.")

        # Independent physical receipt integrity checks
        if rcpt_exit != 0:
            fail_python_gate(f"Physical receipt '{receipt_id}' recorded non-zero exit code {rcpt_exit} for '{label}'.")

        if rcpt_failed > 0:
            fail_python_gate(f"Physical receipt '{receipt_id}' recorded {rcpt_failed} failed tests for '{label}'.")

        if rcpt_tree != current_tree:
            fail_python_gate(f"Mixed snapshot detected. Physical receipt '{receipt_id}' tree {rcpt_tree[:8]} does not match current git tree {current_tree[:8]}.")

        if rcpt_wt_sha and rcpt_wt_sha != current_tree:
            fail_python_gate(f"Mixed snapshot detected. Receipt '{receipt_id}' tested against disk tree {rcpt_wt_sha[:8]}, but current tree is {current_tree[:8]}.")

        # F03: Physical log existence verification
        if log_rel:
            log_file = os.path.normpath(os.path.join(evidence_dir, log_rel))
            if not os.path.exists(log_file):
                fail_python_gate(f"Execution log file not found: {log_file}")

        # F02b: Mixed snapshot defense (every check must match current tree)
        if not check_tree or check_tree in ("unknown", "uninitialized"):
            fail_python_gate(f"Check '{label}' has invalid git_tree_sha '{check_tree}'.")
        if check_tree != current_tree:
            fail_python_gate(f"Mixed snapshot detected. Check '{label}' was tested against tree {check_tree[:8]}, but current tree is {current_tree[:8]}.")

        # Exit code & failure verification
        if exit_code != 0:
            fail_python_gate(f"Check '{label}' ('{cmd}') failed with exit code {exit_code}.")

        if failed > 0:
            fail_python_gate(f"Check '{label}' reported {failed} failed tests.")

        if collected > 0 and passed != collected:
            fail_python_gate(f"False-green trap in '{label}'. Passed ({passed}) != Collected ({collected}).")

        # F01: Test-labeled checks must collect > 0 tests
        is_test_check = ("test" in label.lower()) or ("test" in cmd.lower()) or ("pytest" in cmd.lower()) or ("vitest" in cmd.lower()) or ("jest" in cmd.lower())
        if is_test_check:
            has_test_checks = True
            total_collected_tests += collected
            if collected == 0:
                fail_python_gate(f"Test check '{label}' recorded 0 collected tests (Zero-inventory false green).")

    if has_test_checks and total_collected_tests == 0:
        fail_python_gate("Test checks were executed but total collected tests is 0.")

    # 5. Policy disposition & Strict waiver objects (F11)
    disposition = manifest.get("policy_disposition", "RED")
    if disposition not in ("GREEN", "AMBER"):
        fail_python_gate(f"Invalid policy disposition '{disposition}'. Must be GREEN or AMBER.")

    if disposition == "RED":
        fail_python_gate("Manifest policy disposition is RED.")

    if disposition == "AMBER":
        waivers = manifest.get("open_waivers", [])
        if not waivers:
            fail_python_gate("Manifest policy is AMBER but no authorized waiver is registered.")

        for w in waivers:
            if not isinstance(w, dict):
                fail_python_gate("Invalid waiver format. Must be a structured object with author, reason, and expires_at.")
            author = w.get("author")
            reason = w.get("reason")
            expires_at = w.get("expires_at")
            if not author or not reason or not expires_at:
                fail_python_gate("Incomplete waiver object. Missing author, reason, or expires_at.")

            exp = None
            for fmt in (None, "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ"):
                try:
                    if fmt is None:
                        parsed = datetime.datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                    else:
                        parsed = datetime.datetime.strptime(expires_at, fmt)
                    if parsed.tzinfo is None:
                        if len(expires_at.strip()) == 10:
                            parsed = parsed.replace(hour=23, minute=59, second=59, tzinfo=datetime.timezone.utc)
                        else:
                            parsed = parsed.replace(tzinfo=datetime.timezone.utc)
                    exp = parsed
                    break
                except Exception:
                    continue

            if exp is None:
                fail_python_gate(f"Waiver by '{author}' has invalid unparseable expires_at timestamp: '{expires_at}'.")

            now = datetime.datetime.now(datetime.timezone.utc)
            if exp < now:
                fail_python_gate(f"Waiver by '{author}' expired on {expires_at}.")

    # Success
    is_hook_mode = os.environ.get("GATE_HOOK_MODE") == "1"
    if is_hook_mode:
        print(json.dumps({"decision": "allow"}))
    else:
        print(f"✅ [RELEASE GATE PASS]: {len(checks)} check(s) verified against tree {current_tree[:8]}. Status: {disposition}")
    sys.exit(0)
except Exception as e:
    fail_python_gate(f"Verification runtime error: {e}")
PYEOF
