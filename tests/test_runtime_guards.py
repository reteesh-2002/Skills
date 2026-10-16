#!/usr/bin/env python3
"""
Unit and Integration Tests for Antigravity Runtime Guards (Selective Kernel Fusion).
Validates:
1. scripts/guard_read_before_write.py (Invariant 1: Read-Before-Write)
2. scripts/guard_anti_retry.py (Invariant 4: Anti-Exact-Retry)
3. scripts/verify-release-gate.sh (Invariant 3: Timestamp Freshness Check)
"""

import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
GUARD_RBW = SCRIPTS_DIR / "guard_read_before_write.py"
GUARD_AER = SCRIPTS_DIR / "guard_anti_retry.py"
GATE_SH = SCRIPTS_DIR / "verify-release-gate.sh"
GATE_PY = SCRIPTS_DIR / "verify_release_gate.py"

sys.path.insert(0, str(SCRIPTS_DIR))
import guard_read_before_write as grbw
import guard_anti_retry as gaer


class TestReadBeforeWriteGuard(unittest.TestCase):
    """Tests for guard_read_before_write.py."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="test_rbw_")
        self.tmp_path = Path(self.tmp_dir)
        self.evidence_dir = self.tmp_path / ".evidence"
        self.reads_file = grbw.get_reads_file(self.evidence_dir)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_uninspected_existing_file_denied(self):
        existing_file = self.tmp_path / "existing.py"
        existing_file.write_text("print('hello')")
        reads = grbw.load_reads(self.reads_file)

        allowed, reason = grbw.evaluate_mutation(str(existing_file), reads)
        self.assertFalse(allowed)
        self.assertIn("not inspected with view_file", reason)

    def test_new_file_scaffolding_allowed(self):
        new_file = self.tmp_path / "brand_new_file.py"
        reads = grbw.load_reads(self.reads_file)

        allowed, reason = grbw.evaluate_mutation(str(new_file), reads)
        self.assertTrue(allowed)
        self.assertIn("New file allowed", reason)

    def test_inspected_existing_file_allowed(self):
        existing_file = self.tmp_path / "module.py"
        existing_file.write_text("x = 1")
        grbw.record_read(self.reads_file, str(existing_file))

        reads = grbw.load_reads(self.reads_file)
        self.assertIn(str(existing_file.resolve()), reads)

        allowed, reason = grbw.evaluate_mutation(str(existing_file), reads)
        self.assertTrue(allowed)
        self.assertIn("Read recorded", reason)

    def test_none_target_file_allowed(self):
        allowed, reason = grbw.evaluate_mutation(None, set())
        self.assertTrue(allowed)

    def test_cli_integration_read_then_write_flow(self):
        existing_file = self.tmp_path / "target.txt"
        existing_file.write_text("initial")

        # 1. Blind edit attempt -> should be denied
        payload_write = {
            "cwd": str(self.tmp_path),
            "toolCall": {
                "name": "replace_file_content",
                "args": {"TargetFile": str(existing_file), "ReplacementContent": "new"}
            }
        }
        res = subprocess.run(
            [sys.executable, str(GUARD_RBW)],
            input=json.dumps(payload_write),
            capture_output=True,
            text=True
        )
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data.get("decision"), "deny")
        self.assertIn("Read-Before-Write violation", data.get("reason", ""))

        # 2. Inspect file via view_file -> should be allowed and recorded
        payload_read = {
            "cwd": str(self.tmp_path),
            "toolCall": {
                "name": "view_file",
                "args": {"AbsolutePath": str(existing_file)}
            }
        }
        res = subprocess.run(
            [sys.executable, str(GUARD_RBW)],
            input=json.dumps(payload_read),
            capture_output=True,
            text=True
        )
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data.get("decision"), "allow")

        # 3. Edit attempt again -> now allowed
        res = subprocess.run(
            [sys.executable, str(GUARD_RBW)],
            input=json.dumps(payload_write),
            capture_output=True,
            text=True
        )
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data.get("decision"), "allow")

    def test_cli_test_harness_flag(self):
        res = subprocess.run(
            [sys.executable, str(GUARD_RBW), "--test-harness"],
            capture_output=True,
            text=True
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("Read-Before-Write Guard ready", res.stdout)


class TestAntiRetryGuard(unittest.TestCase):
    """Tests for guard_anti_retry.py."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="test_aer_")
        self.tmp_path = Path(self.tmp_dir)
        self.evidence_dir = self.tmp_path / ".evidence"
        self.failures_file = gaer.get_failures_file(self.evidence_dir)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_first_call_allowed(self):
        allowed, reason = gaer.evaluate_retry("run_command", {"CommandLine": "pytest"}, set())
        self.assertTrue(allowed)

    def test_exact_retry_blocked(self):
        args = {"CommandLine": "pytest tests/broken_test.py"}
        fp = gaer.compute_action_fingerprint("run_command", args)
        gaer.record_failure(self.failures_file, fp, "run_command", "AssertionError")

        active_fails = gaer.load_failures(self.failures_file)
        self.assertIn(fp, active_fails)

        allowed, reason = gaer.evaluate_retry("run_command", args, active_fails)
        self.assertFalse(allowed)
        self.assertIn("Anti-Exact-Retry violation", reason)

    def test_modified_args_allowed(self):
        args1 = {"CommandLine": "pytest tests/broken_test.py"}
        fp1 = gaer.compute_action_fingerprint("run_command", args1)
        gaer.record_failure(self.failures_file, fp1, "run_command", "AssertionError")

        active_fails = gaer.load_failures(self.failures_file)

        # Alter command line
        args2 = {"CommandLine": "pytest tests/broken_test.py -k test_fixed"}
        allowed, reason = gaer.evaluate_retry("run_command", args2, active_fails)
        self.assertTrue(allowed)

    def test_ephemeral_args_ignored_in_fingerprint(self):
        # Changing toolSummary or WaitMsBeforeAsync should NOT evade the anti-retry guard
        args1 = {"CommandLine": "pytest", "WaitMsBeforeAsync": 5000, "toolSummary": "Summary 1"}
        args2 = {"CommandLine": "pytest", "WaitMsBeforeAsync": 10000, "toolSummary": "Summary 2"}
        self.assertEqual(
            gaer.compute_action_fingerprint("run_command", args1),
            gaer.compute_action_fingerprint("run_command", args2)
        )

    def test_read_only_tools_exempt(self):
        # Read-only tools should never be blocked from retrying
        active_fails = {"fake_fp"}
        allowed, reason = gaer.evaluate_retry("view_file", {"AbsolutePath": "/file"}, active_fails)
        self.assertTrue(allowed)

    def test_mutation_clears_failures(self):
        args = {"CommandLine": "pytest"}
        fp = gaer.compute_action_fingerprint("run_command", args)
        gaer.record_failure(self.failures_file, fp, "run_command")
        self.assertTrue(self.failures_file.exists())

        gaer.clear_failures(self.failures_file)
        self.assertFalse(self.failures_file.exists())
        self.assertEqual(len(gaer.load_failures(self.failures_file)), 0)

    def test_cli_failure_recording_and_retry_blocking(self):
        cmd_args = {"CommandLine": "make test"}

        # 1. First execution is allowed
        res = subprocess.run(
            [sys.executable, str(GUARD_AER)],
            input=json.dumps({"cwd": str(self.tmp_path), "toolCall": {"name": "run_command", "args": cmd_args}}),
            capture_output=True,
            text=True
        )
        self.assertEqual(res.returncode, 0)
        self.assertEqual(json.loads(res.stdout).get("decision"), "allow")

        # 2. Command fails: PostToolUse records the failure
        post_fail = {
            "cwd": str(self.tmp_path),
            "toolCall": {"name": "run_command", "args": cmd_args},
            "status": "error",
            "error": "make: *** [test] Error 1",
            "result": {"exit_code": 2}
        }
        res = subprocess.run(
            [sys.executable, str(GUARD_AER)],
            input=json.dumps(post_fail),
            capture_output=True,
            text=True
        )
        self.assertEqual(res.returncode, 0)

        # 3. Second identical execution is blocked
        res = subprocess.run(
            [sys.executable, str(GUARD_AER)],
            input=json.dumps({"cwd": str(self.tmp_path), "toolCall": {"name": "run_command", "args": cmd_args}}),
            capture_output=True,
            text=True
        )
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data.get("decision"), "deny")
        self.assertIn("Anti-Exact-Retry violation", data.get("reason", ""))

        # 4. Code mutation happens (replace_file_content) -> resets ledger
        res = subprocess.run(
            [sys.executable, str(GUARD_AER)],
            input=json.dumps({"cwd": str(self.tmp_path), "toolCall": {"name": "replace_file_content", "args": {}}}),
            capture_output=True,
            text=True
        )
        self.assertEqual(res.returncode, 0)
        self.assertEqual(json.loads(res.stdout).get("decision"), "allow")

        # 5. Same command is allowed again after code change
        res = subprocess.run(
            [sys.executable, str(GUARD_AER)],
            input=json.dumps({"cwd": str(self.tmp_path), "toolCall": {"name": "run_command", "args": cmd_args}}),
            capture_output=True,
            text=True
        )
        self.assertEqual(res.returncode, 0)
        self.assertEqual(json.loads(res.stdout).get("decision"), "allow")


class TestGateFreshnessCheck(unittest.TestCase):
    """Tests for timestamp freshness check in verify-release-gate.sh & verify_release_gate.py."""

    def setUp(self):
        self.repo_dir = tempfile.mkdtemp(prefix="test_freshness_repo_")
        # Initialize git repo
        subprocess.run(["git", "init"], cwd=self.repo_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.repo_dir, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.repo_dir, check=True)

        # Commit an initial source file
        self.source_file = Path(self.repo_dir) / "app.py"
        self.source_file.write_text("def run(): pass\n")
        subprocess.run(["git", "add", "app.py"], cwd=self.repo_dir, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.repo_dir, check=True)

        # Add .gitignore ignoring .evidence and python bytecode
        (Path(self.repo_dir) / ".gitignore").write_text(".evidence/\n__pycache__/\n*.pyc\n")

        # Setup scripts in repo
        self.repo_scripts = Path(self.repo_dir) / "scripts"
        self.repo_scripts.mkdir(parents=True, exist_ok=True)
        shutil.copy(GATE_SH, self.repo_scripts / "verify-release-gate.sh")
        shutil.copy(GATE_PY, self.repo_scripts / "verify_release_gate.py")
        shutil.copy(SCRIPTS_DIR / "runtime_evidence.py", self.repo_scripts / "runtime_evidence.py")
        (self.repo_scripts / "verify-release-gate.sh").chmod(0o755)

        subprocess.run(["git", "add", ".gitignore", "scripts/"], cwd=self.repo_dir, check=True)
        subprocess.run(["git", "commit", "-m", "Add scripts and gitignore"], cwd=self.repo_dir, check=True)

        # Setup .evidence directory
        self.evidence_dir = Path(self.repo_dir) / ".evidence"
        self.receipts_dir = self.evidence_dir / "receipts"
        self.logs_dir = self.evidence_dir / "logs"
        self.receipts_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        self.gate_sh = self.repo_scripts / "verify-release-gate.sh"
        self.gate_py = self.repo_scripts / "verify_release_gate.py"

        self.tree_sha = subprocess.check_output(
            ["git", "-C", self.repo_dir, "write-tree"]
        ).decode().strip()

    def tearDown(self):
        shutil.rmtree(self.repo_dir, ignore_errors=True)

    def _create_evidence(self, timestamp_iso: str):
        rcpt_id = "rcpt_test_fresh_01"
        receipt = {
            "receipt_id": rcpt_id,
            "timestamp": timestamp_iso,
            "executed_at": timestamp_iso,
            "label": "unit_test",
            "command": "python3 -m unittest",
            "exit_code": 0,
            "duration_ms": 50,
            "git_tree_sha": self.tree_sha,
            "working_tree_sha": self.tree_sha,
            "working_tree_dirty": False,
            "log_path": f"logs/{rcpt_id}.log",
            "framework_detected": "python-unittest",
            "unverified": False,
            "xfail": 0,
            "metrics": {"collected": 2, "passed": 2, "failed": 0, "skipped": 0},
            "has_warnings": False
        }
        with open(self.receipts_dir / f"{rcpt_id}.json", "w") as f:
            json.dump(receipt, f)

        with open(self.logs_dir / f"{rcpt_id}.log", "w") as f:
            f.write("Ran 2 tests in 0.05s\nOK\n")

        manifest = {
            "schema_version": "manifest.v1",
            "git_tree_sha": self.tree_sha,
            "policy_disposition": "GREEN",
            "checks": [receipt],
            "attempt_history": [receipt],
            "open_waivers": []
        }
        with open(self.evidence_dir / "manifest.v1.json", "w") as f:
            json.dump(manifest, f)

    def test_stale_evidence_blocked_when_file_modified_after_test(self):
        # Age all repo files to 2 hours ago so only app.py is newer than receipt
        two_hours_ago = time.time() - 7200
        for p in Path(self.repo_dir).rglob("*"):
            if p.is_file():
                os.utime(p, (two_hours_ago, two_hours_ago))

        # Verification ran 1 hour ago
        past_iso = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)).isoformat()
        self._create_evidence(past_iso)

        # File is modified right now (mtime > receipt timestamp)
        time.sleep(0.01)
        self.source_file.write_text("def run(): print('modified after test')\n")

        # verify-release-gate.sh should block with stale evidence
        res = subprocess.run(
            ["bash", str(self.gate_sh)],
            cwd=self.repo_dir,
            capture_output=True,
            text=True
        )
        self.assertEqual(res.returncode, 1)
        self.assertIn("Stale evidence: working tree file 'app.py' modified after verification check was executed", res.stderr)

        # verify_release_gate.py should also block identically
        res_py = subprocess.run(
            [sys.executable, str(self.gate_py)],
            cwd=self.repo_dir,
            capture_output=True,
            text=True
        )
        self.assertEqual(res_py.returncode, 1)
        self.assertIn("Stale evidence: working tree file 'app.py' modified after verification check was executed", res_py.stderr)

    def test_fresh_evidence_allowed_when_file_not_modified_after_test(self):
        # Evidence is from the future relative to file mtime
        future_iso = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=10)).isoformat()
        self._create_evidence(future_iso)

        res = subprocess.run(
            ["bash", str(self.gate_sh)],
            cwd=self.repo_dir,
            capture_output=True,
            text=True
        )
        self.assertEqual(res.returncode, 0, f"Expected 0, stderr: {res.stderr}")

        res_py = subprocess.run(
            [sys.executable, str(self.gate_py)],
            cwd=self.repo_dir,
            capture_output=True,
            text=True
        )
        self.assertEqual(res_py.returncode, 0, f"Expected 0, stderr: {res_py.stderr}")


if __name__ == "__main__":
    unittest.main()
