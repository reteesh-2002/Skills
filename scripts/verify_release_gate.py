#!/usr/bin/env python3
"""
Antigravity Cross-Platform Deterministic Release Gate
Evaluates evidence manifests against current git tree to block unverified releases.
Supports CLI execution and Antigravity protojson PreToolUse hook interception.
Runs natively on Windows (PowerShell, CMD, Git Bash), Linux, and macOS.
"""

import os
import sys
import json
import datetime
import subprocess
from pathlib import Path

# Add script directory to sys.path to allow importing runtime_evidence
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

try:
    import runtime_evidence
except ImportError:
    from scripts import runtime_evidence


def fail_gate(reason: str, hook_mode: bool = False):
    if "--advisory" in sys.argv:
        print(f"⚠️ [RELEASE GATE ADVISORY]: {reason}", file=sys.stderr)
        sys.exit(0)
    print(f"❌ [RELEASE GATE BLOCKED]: {reason}", file=sys.stderr)
    if hook_mode:
        print(json.dumps({"decision": "deny", "reason": reason}))
    sys.exit(1)


def pass_gate(message: str, hook_mode: bool = False):
    if hook_mode:
        print(json.dumps({"decision": "allow"}))
    else:
        print(f"✅ [RELEASE GATE PASS]: {message}")
    sys.exit(0)


def extract_hook_command():
    # If passed as command-line argument: python verify_release_gate.py --pre-tool <cmd>
    if len(sys.argv) > 2:
        return sys.argv[2]

    # Else read from stdin if not a tty
    if not sys.stdin.isatty():
        try:
            stdin_data = sys.stdin.read().strip()
            if not stdin_data:
                return ""
            data = json.loads(stdin_data)
            tool_call = data.get("toolCall", {})
            args = tool_call.get("args", {})
            return (
                args.get("CommandLine")
                or data.get("tool_input", {}).get("CommandLine")
                or data.get("command")
                or ""
            )
        except Exception:
            return ""
    return ""


def main():
    hook_mode = False
    if len(sys.argv) > 1 and sys.argv[1] == "--pre-tool":
        hook_mode = True
        cmd = extract_hook_command()
        res = runtime_evidence.is_release_command(cmd)
        if res == "unsupported":
            fail_gate(f"Command form is ambiguous or unsupported by static analyzer — fail-safe block: {cmd}", hook_mode=True)
        elif res is False:
            pass_gate("Non-release command allowed.", hook_mode=True)
        # If release command, continue to release gate verification

    # 1. Enforce git repository presence and CWD alignment
    try:
        toplevel = subprocess.check_output(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "--show-toplevel"],
            stderr=subprocess.PIPE,
            text=True
        ).strip()
    except Exception as e:
        fail_gate(f"Target directory {REPO_ROOT} is not inside a git repository: {e}", hook_mode=hook_mode)

    try:
        cwd_top = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            stderr=subprocess.PIPE,
            text=True
        ).strip()
    except Exception as e:
        fail_gate(f"Current working directory {os.getcwd()} is not inside a git repository: {e}", hook_mode=hook_mode)

    # Normalize paths for comparison (especially on Windows with case/drive letters)
    if Path(cwd_top).resolve() != Path(toplevel).resolve():
        fail_gate(f"Working directory mismatch: CWD is '{cwd_top}' but script repository is '{toplevel}'.", hook_mode=hook_mode)

    # 2. Enforce Git Assertion Lock (WP-04 / SEC-03)
    # Pre-existing test files at Git base/HEAD are strictly immutable during bug repairs
    allow_spec_evolution = (
        "--spec-evolution" in sys.argv
        or os.environ.get("SPEC_EVOLUTION", "").lower() in ("1", "true", "yes")
        or os.environ.get("ANTIGRAVITY_SPEC_EVOLUTION", "").lower() in ("1", "true", "yes")
    )
    base_ref = None
    if "--base-ref" in sys.argv:
        try:
            b_idx = sys.argv.index("--base-ref")
            if b_idx + 1 < len(sys.argv):
                base_ref = sys.argv[b_idx + 1]
        except ValueError:
            pass

    passed_lock, tampered_files = runtime_evidence.check_git_assertion_lock(
        REPO_ROOT, base_ref=base_ref, allow_spec_evolution=allow_spec_evolution
    )
    if not passed_lock:
        fail_gate(
            f"Git Assertion Lock violation: Pre-existing test file(s) modified or deleted without --spec-evolution: {tampered_files}. "
            "Pre-existing tests at base are immutable during bug repairs to prevent assertion tampering. "
            "Add new test cases or pass --spec-evolution if specification changes are intentional.",
            hook_mode=hook_mode
        )

    evidence_dir = REPO_ROOT / ".evidence"
    manifest_path = evidence_dir / "manifest.v1.json"

    if not manifest_path.exists():
        fail_gate(f"Evidence manifest not found at {manifest_path}. Run verification via scripts/exec_proxy.py first.", hook_mode=hook_mode)

    # 3. Read manifest
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except Exception as e:
        fail_gate(f"Invalid JSON in manifest: {e}", hook_mode=hook_mode)

    if manifest.get("schema_version") != "manifest.v1":
        fail_gate("Unsupported schema_version in manifest", hook_mode=hook_mode)

    disposition = manifest.get("policy_disposition", "RED")
    if disposition not in ("GREEN", "AMBER"):
        fail_gate(f"Invalid policy disposition '{disposition}'. Must be GREEN or AMBER.", hook_mode=hook_mode)

    # 4. Git Tree Freshness & Unknown Tree Rejection
    try:
        current_tree = subprocess.check_output(
            ["git", "-C", str(REPO_ROOT), "write-tree"],
            stderr=subprocess.DEVNULL,
            text=True
        ).strip()
    except Exception:
        current_tree = "unknown"

    manifest_tree = manifest.get("git_tree_sha", "")
    if not current_tree or current_tree in ("unknown", "uninitialized"):
        fail_gate("Current git tree cannot be determined.", hook_mode=hook_mode)

    if not manifest_tree or manifest_tree in ("unknown", "uninitialized"):
        fail_gate(f"Manifest contains invalid or uninitialized git_tree_sha: '{manifest_tree}'", hook_mode=hook_mode)

    if current_tree != manifest_tree:
        fail_gate(f"Stale evidence. Working tree changed since tests ran. Tested: {manifest_tree[:8]}, Current: {current_tree[:8]}. Re-run verification suite via scripts/exec_proxy.py before releasing.", hook_mode=hook_mode)

    # 5. Check inventory
    checks = manifest.get("checks", [])
    if not checks:
        fail_gate("Manifest contains 0 verification checks.", hook_mode=hook_mode)

    # 6. Check results and physical evidence
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

        if not receipt_id:
            fail_gate(f"Check '{label}' missing receipt_id.", hook_mode=hook_mode)
        receipt_file = evidence_dir / "receipts" / f"{receipt_id}.json"
        if not receipt_file.exists():
            fail_gate(f"Physical receipt file not found: {receipt_file}", hook_mode=hook_mode)

        try:
            with open(receipt_file, "r", encoding="utf-8") as rf:
                rcpt_data = json.load(rf)
        except Exception as e:
            fail_gate(f"Receipt '{receipt_id}' is corrupt or unreadable: {e}", hook_mode=hook_mode)

        try:
            runtime_evidence.validate_receipt_structure(rcpt_data, receipt_id)
            runtime_evidence.cross_validate_manifest_and_receipt(c, rcpt_data, current_tree)
        except ValueError as ve:
            fail_gate(str(ve), hook_mode=hook_mode)

        if log_rel:
            log_file = (evidence_dir / log_rel).resolve()
            if not log_file.exists():
                fail_gate(f"Execution log file not found: {log_file}", hook_mode=hook_mode)

        if not check_tree or check_tree in ("unknown", "uninitialized"):
            fail_gate(f"Check '{label}' has invalid git_tree_sha '{check_tree}'.", hook_mode=hook_mode)
        if check_tree != current_tree:
            fail_gate(f"Mixed snapshot detected. Check '{label}' was tested against tree {check_tree[:8]}, but current tree is {current_tree[:8]}.", hook_mode=hook_mode)

        # Gravitas Invariant 3: Timestamp freshness check (test_mtime > file_mtime)
        rcpt_ts = rcpt_data.get("timestamp") or rcpt_data.get("executed_at") or rcpt_data.get("timestamp_utc")
        if rcpt_ts:
            try:
                if isinstance(rcpt_ts, (int, float)):
                    receipt_time = float(rcpt_ts)
                else:
                    receipt_time = datetime.datetime.fromisoformat(str(rcpt_ts).replace("Z", "+00:00")).timestamp()
            except Exception:
                receipt_time = os.path.getmtime(receipt_file)
        else:
            receipt_time = os.path.getmtime(receipt_file)

        try:
            status_out = subprocess.check_output(
                ["git", "-C", str(REPO_ROOT), "status", "--porcelain"],
                stderr=subprocess.DEVNULL
            ).decode("utf-8", errors="replace")
            for s_line in status_out.splitlines():
                if len(s_line) > 3:
                    rel_path = s_line[3:].strip()
                    if " -> " in rel_path:
                        rel_path = rel_path.split(" -> ")[-1].strip()
                    rel_path = rel_path.strip('"\'')
                    # Forgive internal metadata, scratch directories, and transient notes
                    if (rel_path.startswith(".evidence/") or 
                        rel_path.startswith(".git/") or 
                        rel_path.startswith(".scratch/") or 
                        rel_path.startswith("scratch/") or
                        rel_path.startswith(".tmp") or
                        rel_path.endswith(".tmp")):
                        continue
                    full_p = Path(REPO_ROOT) / rel_path
                    if full_p.is_file():
                        file_mtime = full_p.stat().st_mtime
                        if file_mtime > receipt_time:
                            fail_gate(f"Stale evidence: working tree file '{rel_path}' modified after verification check was executed. Working directory is dirty (uncommitted changes present).", hook_mode=hook_mode)

            dirty_entries = [
                s for s in status_out.splitlines()
                if len(s) > 3 and not any(
                    s[3:].strip().strip('"\'').startswith(prefix) for prefix in (
                        ".evidence/", ".git/", ".scratch/", "scratch/", ".tmp"
                    )
                ) and not s[3:].strip().strip('"\'').endswith(".tmp")
            ]
            if dirty_entries:
                fail_gate("Working directory is dirty (uncommitted or tracked modifications present). Stash, commit, or clean working tree before release. Changes:\n" + "\n".join(dirty_entries), hook_mode=hook_mode)
        except SystemExit:
            raise
        except Exception:
            pass

        if exit_code != 0:
            fail_gate(f"Check '{label}' ('{cmd}') failed with exit code {exit_code}.", hook_mode=hook_mode)

        if failed > 0:
            fail_gate(f"Check '{label}' reported {failed} failed tests.", hook_mode=hook_mode)

        if collected > 0 and passed != collected:
            fail_gate(f"False-green trap in '{label}'. Passed ({passed}) != Collected ({collected}).", hook_mode=hook_mode)

        is_unverified = c.get("unverified", False) or rcpt_data.get("unverified", False)
        cmd_lower = cmd.lower()
        is_test_check = (
            runtime_evidence.is_known_test_runner(cmd)
            or any(kw in label.lower() for kw in ("test", "unit", "spec", "pytest", "jest", "e2e"))
        )

        if is_test_check:
            has_test_checks = True
            total_collected_tests += collected
            if collected == 0 or is_unverified:
                fail_gate(f"Test check '{label}' (cmd: '{cmd}') recorded 0 collected tests (Zero-inventory false green). Required test check is unverified.", hook_mode=hook_mode)
        else:
            if is_unverified or (collected == 0 and exit_code == 0):
                if disposition == "GREEN":
                    fail_gate(f"Check '{label}' is unverified (zero test inventory from non-test-runner). Policy disposition cannot be GREEN.", hook_mode=hook_mode)

    if has_test_checks and total_collected_tests == 0:
        fail_gate("Test checks were executed but total collected tests is 0.", hook_mode=hook_mode)

    if not has_test_checks and disposition == "GREEN":
        fail_gate("No test checks executed. Zero-inventory checks from non-test-runners cannot pass the release gate.", hook_mode=hook_mode)

    # 7. Check waivers if policy is AMBER
    if disposition == "AMBER":
        open_waivers = manifest.get("open_waivers", [])
        if not open_waivers:
            fail_gate("Manifest policy is AMBER but no authorized waiver is registered.", hook_mode=hook_mode)

        now_utc = datetime.datetime.now(datetime.timezone.utc)
        valid_waiver = False
        waiver_errors = []

        for w in open_waivers:
            if not isinstance(w, dict):
                waiver_errors.append("Invalid waiver format. Must be a structured object with author, reason, and expires_at.")
                continue

            reason = w.get("reason")
            authorizer = w.get("authorizer") or w.get("author")
            expires_at = w.get("expires_at")

            if not reason or not authorizer or not expires_at:
                waiver_errors.append("Waiver missing mandatory fields (reason, author/authorizer, expires_at).")
                continue

            exp = runtime_evidence.parse_waiver_expiry(expires_at)
            if not exp:
                waiver_errors.append(f"Invalid waiver expires_at timestamp: '{expires_at}'. Must be ISO-8601 or YYYY-MM-DD.")
                continue

            if exp < now_utc:
                waiver_errors.append(f"Waiver expired at {exp.isoformat()}.")
                continue

            valid_waiver = True
            break

        if not valid_waiver:
            err_msg = "; ".join(waiver_errors) if waiver_errors else "No valid unexpired waiver found."
            fail_gate(f"Manifest policy is AMBER but waiver validation failed: {err_msg}", hook_mode=hook_mode)

    pass_gate(f"{len(checks)} check(s) verified against tree {current_tree[:8]}. Status: {disposition}", hook_mode=hook_mode)


if __name__ == "__main__":
    main()
