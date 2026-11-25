#!/usr/bin/env python3
"""
Unit and Integration Tests for Antigravity Runtime Guards.
Validates scripts/guard_anti_retry.py (Anti-Exact-Retry loop prevention).
"""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
GUARD_AER = SCRIPTS_DIR / "guard_anti_retry.py"

sys.path.insert(0, str(SCRIPTS_DIR))
import guard_anti_retry as gaer


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
        allowed, _ = gaer.evaluate_retry("run_command", {"CommandLine": "pytest"}, set())
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
        args2 = {"CommandLine": "pytest tests/broken_test.py -k test_fixed"}
        allowed, _ = gaer.evaluate_retry("run_command", args2, active_fails)
        self.assertTrue(allowed)

    def test_ephemeral_args_ignored_in_fingerprint(self):
        args1 = {"CommandLine": "pytest", "WaitMsBeforeAsync": 5000, "toolSummary": "Summary 1"}
        args2 = {"CommandLine": "pytest", "WaitMsBeforeAsync": 10000, "toolSummary": "Summary 2"}
        self.assertEqual(
            gaer.compute_action_fingerprint("run_command", args1),
            gaer.compute_action_fingerprint("run_command", args2),
        )

    def test_read_only_tools_exempt(self):
        active_fails = {"fake_fp"}
        allowed, _ = gaer.evaluate_retry("view_file", {"AbsolutePath": "/file"}, active_fails)
        self.assertTrue(allowed)

    def test_exploratory_commands_exempt(self):
        args = {"CommandLine": "grep -rn 'target' ."}
        fp = gaer.compute_action_fingerprint("run_command", args)
        active_fails = {fp}
        allowed, reason = gaer.evaluate_retry("run_command", args, active_fails)
        self.assertTrue(allowed)
        self.assertIn("Exploratory discovery command permitted", reason)

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

        res = subprocess.run(
            [sys.executable, str(GUARD_AER)],
            input=json.dumps({"cwd": str(self.tmp_path), "toolCall": {"name": "run_command", "args": cmd_args}}),
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        self.assertEqual(json.loads(res.stdout).get("decision"), "allow")

        post_fail = {
            "cwd": str(self.tmp_path),
            "toolCall": {"name": "run_command", "args": cmd_args},
            "status": "error",
            "error": "make: *** [test] Error 1",
            "result": {"exit_code": 2},
        }
        res = subprocess.run(
            [sys.executable, str(GUARD_AER)],
            input=json.dumps(post_fail),
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)

        res = subprocess.run(
            [sys.executable, str(GUARD_AER)],
            input=json.dumps({"cwd": str(self.tmp_path), "toolCall": {"name": "run_command", "args": cmd_args}}),
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data.get("decision"), "deny")
        self.assertIn("Anti-Exact-Retry violation", data.get("reason", ""))

        res = subprocess.run(
            [sys.executable, str(GUARD_AER)],
            input=json.dumps({"cwd": str(self.tmp_path), "toolCall": {"name": "replace_file_content", "args": {}}}),
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        self.assertEqual(json.loads(res.stdout).get("decision"), "allow")

        res = subprocess.run(
            [sys.executable, str(GUARD_AER)],
            input=json.dumps({"cwd": str(self.tmp_path), "toolCall": {"name": "run_command", "args": cmd_args}}),
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        self.assertEqual(json.loads(res.stdout).get("decision"), "allow")


if __name__ == "__main__":
    unittest.main()
