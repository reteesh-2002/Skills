#!/usr/bin/env bash
# Antigravity Release Gate Verifier
# Deterministically evaluates evidence manifests against current git tree to block unverified releases.

set -euo pipefail

PRE_TOOL_CMD=""
if [[ "$#" -gt 0 && "$1" == "--pre-tool" ]]; then
  if [[ "$#" -gt 1 ]]; then
    PRE_TOOL_CMD="$2"
    # If pre-tool command doesn't attempt release/push, allow immediately
    if ! echo "${PRE_TOOL_CMD}" | grep -qE 'git\s+push|gh\s+pr\s+create|npm\s+publish'; then
      exit 0
    fi
  fi
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MANIFEST_PATH="${REPO_ROOT}/.evidence/manifest.v1.json"

fail_gate() {
  local reason="$1"
  echo "❌ [RELEASE GATE BLOCKED]: ${reason}" >&2
  exit 1
}

if [[ ! -f "${MANIFEST_PATH}" ]]; then
  fail_gate "Evidence manifest not found at ${MANIFEST_PATH}. Run verification via scripts/exec-proxy.sh first."
fi

# Evaluate manifest using python policy reducer
python3 - "${MANIFEST_PATH}" << 'PYEOF'
import sys, os, subprocess, json

manifest_path = sys.argv[1]

try:
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
except Exception as e:
    print(f"❌ [RELEASE GATE BLOCKED]: Invalid JSON in manifest: {e}", file=sys.stderr)
    sys.exit(1)

# 1. Schema check
if manifest.get("schema_version") != "manifest.v1":
    print("❌ [RELEASE GATE BLOCKED]: Unsupported schema_version in manifest", file=sys.stderr)
    sys.exit(1)

# 2. Git Tree Freshness
try:
    current_tree = subprocess.check_output(["git", "write-tree"], stderr=subprocess.DEVNULL).decode().strip()
except Exception:
    current_tree = "unknown"

manifest_tree = manifest.get("git_tree_sha", "")

if current_tree != "unknown" and manifest_tree != "unknown":
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

# 4. Check results & false-green defense
for c in checks:
    cmd = c.get("command", "unknown")
    exit_code = c.get("exit_code", -1)
    metrics = c.get("metrics", {})
    collected = metrics.get("collected", 0)
    passed = metrics.get("passed", 0)
    failed = metrics.get("failed", 0)

    if exit_code != 0:
        print(f"❌ [RELEASE GATE BLOCKED]: Check '{cmd}' failed with exit code {exit_code}.", file=sys.stderr)
        sys.exit(1)

    if failed > 0:
        print(f"❌ [RELEASE GATE BLOCKED]: Check '{cmd}' reported {failed} failed tests.", file=sys.stderr)
        sys.exit(1)

    if collected > 0 and passed != collected:
        print(f"❌ [RELEASE GATE BLOCKED]: False-green trap in '{cmd}'. Passed ({passed}) != Collected ({collected}).", file=sys.stderr)
        sys.exit(1)

# 5. Policy disposition & Amber waivers
disposition = manifest.get("policy_disposition", "RED")
if disposition == "RED":
    print("❌ [RELEASE GATE BLOCKED]: Manifest policy disposition is RED.", file=sys.stderr)
    sys.exit(1)

if disposition == "AMBER":
    waivers = manifest.get("open_waivers", [])
    if not waivers:
        print("❌ [RELEASE GATE BLOCKED]: Manifest policy is AMBER (deprecations/skips exist) but no authorized waiver is registered.", file=sys.stderr)
        sys.exit(1)

# Success
print(f"✅ [RELEASE GATE PASS]: {len(checks)} check(s) verified against tree {current_tree[:8]}. Status: {disposition}")
sys.exit(0)
PYEOF
