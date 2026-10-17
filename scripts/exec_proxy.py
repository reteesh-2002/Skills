#!/usr/bin/env python3
"""
Antigravity Cross-Platform Trusted Execution Proxy
Executes commands, captures exit codes, streams bounded logs, parses test metrics,
and writes physical receipts and manifest records under cross-platform lock.
Supports Windows (PowerShell, CMD, Git Bash), Linux, and macOS.
"""

import os
import sys
import re
import json
import time
import random
import shutil
import tempfile
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


import shlex

def parse_args():
    args = sys.argv[1:]
    label = "check"
    if len(args) >= 2 and args[0] == "--label":
        label = args[1]
        args = args[2:]
    elif len(args) >= 1 and args[0].startswith("--label="):
        label = args[0].split("=", 1)[1]
        args = args[1:]

    if not args:
        print("Error: No command specified to exec_proxy.py", file=sys.stderr)
        print("Usage: python scripts/exec_proxy.py [--label LABEL] <command...>", file=sys.stderr)
        sys.exit(1)

    command_str = shlex.join(args)
    return label, command_str, args


def get_git_info(repo_root: Path):
    # Check if inside git repository
    try:
        toplevel = subprocess.check_output(
            ["git", "-C", str(repo_root), "rev-parse", "--show-toplevel"],
            stderr=subprocess.PIPE,
            text=True
        ).strip()
    except Exception as e:
        print(f"Error: Target repository {repo_root} is not inside a git repository: {e}", file=sys.stderr)
        sys.exit(1)

    # Check working tree dirty
    try:
        porcelain = subprocess.check_output(
            ["git", "-C", str(repo_root), "status", "--porcelain"],
            stderr=subprocess.PIPE,
            text=True
        )
        working_tree_dirty = bool(porcelain.strip())
    except Exception:
        working_tree_dirty = False

    # Git tree SHA
    try:
        git_tree_sha = subprocess.check_output(
            ["git", "-C", str(repo_root), "write-tree"],
            stderr=subprocess.PIPE,
            text=True
        ).strip()
    except Exception:
        git_tree_sha = "unknown"

    # Working tree SHA via temporary index
    working_tree_sha = "unknown"
    tmp_fd, tmp_idx = tempfile.mkstemp(prefix="agy_proxy_idx_")
    os.close(tmp_fd)
    try:
        env = os.environ.copy()
        env["GIT_INDEX_FILE"] = tmp_idx
        subprocess.run(
            ["git", "-C", str(repo_root), "read-tree", "HEAD"],
            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        subprocess.run(
            ["git", "-C", str(repo_root), "add", "-A"],
            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        out = subprocess.check_output(
            ["git", "-C", str(repo_root), "write-tree"],
            env=env, stderr=subprocess.DEVNULL, text=True
        ).strip()
        if out:
            working_tree_sha = out
    except Exception:
        pass
    finally:
        try:
            if os.path.exists(tmp_idx):
                os.unlink(tmp_idx)
        except Exception:
            pass

    return git_tree_sha, working_tree_sha, working_tree_dirty


def parse_test_framework_metrics(log_content: str, command_str: str, exit_code: int):
    collected = 0
    passed = 0
    failed = 0
    skipped = 0
    xfail = 0
    framework_detected = "unknown"

    # 1. Pytest
    if (re.search(r'\d+\s+(?:passed|failed|error(?:ed)?|skipped|xfailed)\b', log_content) and re.search(r'in \d+\.?\d*s', log_content)) or ("pytest" in command_str.lower() and (re.search(r'collected \d+ items', log_content) or re.search(r'no tests ran in', log_content))):
        framework_detected = "pytest"
        m_pass = re.search(r'(\d+)\s+passed', log_content)
        m_fail = re.search(r'(\d+)\s+failed', log_content)
        m_err  = re.search(r'(\d+)\s+error(?:ed)?', log_content)
        m_skip = re.search(r'(\d+)\s+skipped', log_content)
        m_xfail = re.search(r'(\d+)\s+xfailed', log_content)

        if m_pass and m_pass.group(1):
            passed = int(m_pass.group(1))
        fail_count = int(m_fail.group(1)) if (m_fail and m_fail.group(1)) else 0
        err_count = int(m_err.group(1)) if (m_err and m_err.group(1)) else 0
        failed = fail_count + err_count
        if m_skip and m_skip.group(1):
            skipped = int(m_skip.group(1))
        if m_xfail and m_xfail.group(1):
            xfail = int(m_xfail.group(1))
            skipped += xfail  # Count xfail as skipped (not failed) since xfails are expected
        collected = passed + failed + skipped
    elif "# tests" in log_content or "ℹ tests" in log_content or "✔" in log_content or "ℹ pass" in log_content or "node --test" in command_str.lower():
        # 2. Node.js TAP / built-in test runner
        framework_detected = "node-tap"
        m_tests = re.search(r'(?:#|ℹ)\s+tests\s+(\d+)', log_content)
        m_pass = re.search(r'(?:#|ℹ)\s+pass(?:ed)?\s+(\d+)', log_content)
        m_fail = re.search(r'(?:#|ℹ)\s+fail(?:ed)?\s+(\d+)', log_content)
        m_skip = re.search(r'(?:#|ℹ)\s+(?:cancelled|skipped|todo)\s+(\d+)', log_content)

        if m_tests and m_tests.group(1):
            collected = int(m_tests.group(1))
        if m_pass and m_pass.group(1):
            passed = int(m_pass.group(1))
        if m_fail and m_fail.group(1):
            failed = int(m_fail.group(1))
        if m_skip and m_skip.group(1):
            skipped = int(m_skip.group(1))

        if collected == 0:
            pass_matches = len(re.findall(r'✔\s+.+', log_content))
            fail_matches = len(re.findall(r'✖\s+.+', log_content))
            if pass_matches > 0 or fail_matches > 0:
                passed = pass_matches
                failed = fail_matches
                collected = passed + failed
        if collected > 0 and passed == 0 and failed == 0 and skipped == 0:
            passed = collected
    elif "Tests:" in log_content or "jest" in command_str.lower() or "vitest" in command_str.lower():
        # 3. Jest / Vitest
        if "vitest" in command_str.lower():
            framework_detected = "vitest"
        else:
            framework_detected = "jest"
        m_tests_line = re.search(r'Tests:?\s+([^\n\r]+)', log_content)
        if m_tests_line:
            t_line = m_tests_line.group(1)
            m_pass = re.search(r'(\d+)\s+passed', t_line)
            m_fail = re.search(r'(\d+)\s+failed', t_line)
            m_skip = re.search(r'(\d+)\s+(?:skipped|todo)', t_line)
            m_tot = re.search(r'(\d+)\s+total', t_line) or re.search(r'\((\d+)\)', t_line)

            if m_pass:
                passed = int(m_pass.group(1))
            if m_fail:
                failed = int(m_fail.group(1))
            if m_skip:
                skipped = int(m_skip.group(1))
            if m_tot:
                collected = int(m_tot.group(1))
            else:
                collected = passed + failed + skipped
            if collected > 0 and passed == 0 and failed == 0 and skipped == 0:
                passed = collected
        else:
            m_pass = re.search(r'(\d+)\s+passed', log_content)
            m_fail = re.search(r'(\d+)\s+failed', log_content)
            m_skip = re.search(r'(\d+)\s+skipped', log_content)
            if m_pass:
                passed = int(m_pass.group(1))
            if m_fail:
                failed = int(m_fail.group(1))
            if m_skip:
                skipped = int(m_skip.group(1))
            collected = passed + failed + skipped
    elif "test result:" in log_content or "cargo test" in command_str.lower():
        # 4. Cargo test
        framework_detected = "cargo"
        m_cargo = re.search(r'test result:\s+\w+\.\s+(\d+)\s+passed;\s+(\d+)\s+failed;\s+(\d+)\s+ignored', log_content)
        if m_cargo:
            passed = int(m_cargo.group(1))
            failed = int(m_cargo.group(2))
            skipped = int(m_cargo.group(3))
            collected = passed + failed + skipped
    elif ("Ran " in log_content and (" tests in " in log_content or " test in " in log_content)) or "python -m unittest" in command_str.lower() or "python3 -m unittest" in command_str.lower():
        # 5. Python unittest
        framework_detected = "python-unittest"
        m_ran = re.search(r'Ran\s+(\d+)\s+tests?\s+in', log_content)
        m_fail = re.search(r'FAILED\s*\(.*?failures=(\d+)', log_content)
        m_err  = re.search(r'FAILED\s*\(.*?errors=(\d+)', log_content)
        m_skip = re.search(r'skipped=(\d+)', log_content)
        if m_ran:
            collected = int(m_ran.group(1))
            failed = (int(m_fail.group(1)) if m_fail else 0) + (int(m_err.group(1)) if m_err else 0)
            skipped = int(m_skip.group(1)) if m_skip else 0
            passed = collected - failed - skipped

    # 6. Unverified flag
    is_test_runner = runtime_evidence.is_known_test_runner(command_str)
    unverified = (collected == 0 and not is_test_runner and exit_code == 0)

    return {
        "collected": collected,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "xfail": xfail,
        "framework_detected": framework_detected,
        "unverified": unverified
    }


def main():
    label, command_str, cmd_args = parse_args()

    evidence_dir = REPO_ROOT / ".evidence"
    logs_dir = evidence_dir / "logs"
    receipts_dir = evidence_dir / "receipts"
    manifest_path = evidence_dir / "manifest.v1.json"
    lock_path = evidence_dir / "manifest.lock"

    logs_dir.mkdir(parents=True, exist_ok=True)
    receipts_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    run_id = f"rcpt_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 99999)}"
    log_path = logs_dir / f"{run_id}.log"
    receipt_path = receipts_dir / f"{run_id}.json"

    git_tree_sha, working_tree_sha, working_tree_dirty = get_git_info(REPO_ROOT)

    # Write initial receipt
    init_receipt = {
        "receipt_id": run_id,
        "timestamp_utc": timestamp,
        "label": label,
        "command": command_str,
        "exit_code": -1,
        "duration_ms": 0,
        "git_tree_sha": git_tree_sha,
        "working_tree_sha": working_tree_sha,
        "working_tree_dirty": working_tree_dirty,
        "log_path": f".evidence/logs/{run_id}.log",
        "metrics": {"collected": 0, "passed": 0, "failed": 0, "skipped": 0},
        "has_warnings": False
    }
    with open(receipt_path, "w", encoding="utf-8") as rf:
        json.dump(init_receipt, rf, indent=2)

    # Execute command and stream output
    start_time = time.time()
    with open(log_path, "wb") as log_f:
        try:
            # Determine execution form: if cmd_args is a list of tokens, execute without shell=True
            # to prevent command injection and metacharacter expansion vulnerabilities.
            use_shell = False
            exec_target = cmd_args
            if len(cmd_args) == 1 and any(c in cmd_args[0] for c in ("|", "&&", "||", ";", ">", "<")):
                # Compound pipeline on POSIX or Windows fallback
                use_shell = True
                exec_target = command_str

            proc = subprocess.Popen(
                exec_target,
                shell=use_shell,
                cwd=str(REPO_ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )
            
            # Unbuffered real-time line streaming to log file (and console if VERBOSE_STREAM=1)
            verbose_stream = (os.environ.get("VERBOSE_STREAM", "0") == "1")
            if proc.stdout:
                for line in iter(proc.stdout.readline, b""):
                    log_f.write(line)
                    log_f.flush()
                    if verbose_stream:
                        try:
                            sys.stdout.buffer.write(line)
                            sys.stdout.buffer.flush()
                        except Exception:
                            pass
                proc.stdout.close()
            exit_code = proc.wait()
        except Exception as exc:
            log_f.write(f"\nExecution error: {exc}\n".encode("utf-8"))
            exit_code = 127
    duration_ms = int((time.time() - start_time) * 1000)

    # Read log content for metric parsing
    try:
        log_content = log_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        log_content = ""

    parsed = parse_test_framework_metrics(log_content, command_str, exit_code)
    has_warnings = ("DeprecationWarning" in log_content or "ExperimentalWarning" in log_content)

    rel_log_path = os.path.relpath(log_path, evidence_dir)

    receipt = {
        "receipt_id": run_id,
        "label": label,
        "command": command_str,
        "exit_code": exit_code,
        "duration_ms": duration_ms,
        "git_tree_sha": git_tree_sha,
        "working_tree_sha": working_tree_sha,
        "working_tree_dirty": working_tree_dirty,
        "log_path": rel_log_path,
        "framework_detected": parsed["framework_detected"],
        "unverified": parsed["unverified"],
        "xfail": parsed["xfail"],
        "metrics": {
            "collected": parsed["collected"],
            "passed": parsed["passed"],
            "failed": parsed["failed"],
            "skipped": parsed["skipped"]
        },
        "has_warnings": has_warnings
    }

    # Write receipt atomically
    tmp_receipt = str(receipt_path) + ".tmp"
    with open(tmp_receipt, "w", encoding="utf-8") as f:
        json.dump(receipt, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_receipt, receipt_path)

    # Update manifest under exclusive lock
    with open(lock_path, "w") as lf:
        with runtime_evidence.file_lock(lf):
            manifest = {
                "schema_version": "manifest.v1",
                "git_tree_sha": git_tree_sha,
                "policy_disposition": "GREEN" if exit_code == 0 and (parsed["collected"] == 0 or parsed["passed"] == parsed["collected"]) else "RED",
                "checks": [],
                "attempt_history": [],
                "open_waivers": []
            }
            if manifest_path.exists():
                try:
                    with open(manifest_path, "r", encoding="utf-8") as mf:
                        manifest = json.load(mf)
                except Exception:
                    pass

            manifest.setdefault("checks", [])
            manifest.setdefault("attempt_history", [])
            manifest.setdefault("open_waivers", [])

            manifest["attempt_history"].append(receipt)

            # Check flaky retry
            if runtime_evidence.is_flaky_retry(manifest["attempt_history"], receipt, git_tree_sha, working_tree_sha):
                receipt["flaky_retry"] = True
                receipt["prior_failures_count"] = 1

            manifest["checks"] = [c for c in manifest["checks"] if c.get("label") != label]
            manifest["checks"].append(receipt)
            manifest["git_tree_sha"] = git_tree_sha

            manifest["policy_disposition"] = runtime_evidence.calculate_policy_disposition(manifest["checks"])

            tmp_manifest = str(manifest_path) + ".tmp"
            with open(tmp_manifest, "w", encoding="utf-8") as mf:
                json.dump(manifest, mf, indent=2)
                mf.flush()
                os.fsync(mf.fileno())
            os.replace(tmp_manifest, manifest_path)

    # Console output formatting
    collected = parsed["collected"]
    passed = parsed["passed"]
    failed = parsed["failed"]

    if exit_code == 0:
        if collected > 0:
            print(f"[exec-proxy] ✓ Check '{label}' passed ({duration_ms}ms, tests: {passed}/{collected}).")
        else:
            print(f"[exec-proxy] ✓ Check '{label}' completed successfully ({duration_ms}ms, exit code 0).")
        print(f"[exec-proxy] Receipt: {receipt_path}")
        print(f"[exec-proxy] Log: {log_path}")
    else:
        print(f"❌ [exec-proxy] Check '{label}' failed with exit code {exit_code} ({duration_ms}ms).", file=sys.stderr)
        lines = log_content.splitlines()
        excerpt = "\n".join(lines[-20:]) if lines else "No output recorded."
        print(f"[exec-proxy] Failure Excerpt (last 20 lines of {log_path}):", file=sys.stderr)
        print(excerpt, file=sys.stderr)
        print(f"[exec-proxy] Full Log: {log_path}", file=sys.stderr)
        print(f"[exec-proxy] Receipt: {receipt_path}", file=sys.stderr)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
