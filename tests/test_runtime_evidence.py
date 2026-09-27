#!/usr/bin/env python3
"""
Unit tests for scripts/runtime_evidence.py (Release A1 Evidence Engine)
"""

import os
import sys
import unittest
import datetime

# Add scripts directory to python path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

try:
    import runtime_evidence
except ImportError:
    runtime_evidence = None

class TestRuntimeEvidence(unittest.TestCase):
    def setUp(self):
        if runtime_evidence is None:
            self.fail("scripts/runtime_evidence.py not implemented yet (RED phase)")

    def test_parse_waiver_expiry_valid_formats(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        
        # Date only (normalized to 23:59:59 UTC)
        d_future = runtime_evidence.parse_waiver_expiry("2099-01-01")
        self.assertIsNotNone(d_future)
        self.assertGreater(d_future, now)
        self.assertEqual(d_future.tzinfo, datetime.timezone.utc)
        self.assertEqual(d_future.hour, 23)
        self.assertEqual(d_future.minute, 59)

        # ISO with Z
        iso_future = runtime_evidence.parse_waiver_expiry("2099-01-01T12:00:00Z")
        self.assertIsNotNone(iso_future)
        self.assertGreater(iso_future, now)
        self.assertEqual(iso_future.tzinfo, datetime.timezone.utc)

        # Past date
        past = runtime_evidence.parse_waiver_expiry("2020-01-01")
        self.assertIsNotNone(past)
        self.assertLess(past, now)

        # Invalid strings
        self.assertIsNone(runtime_evidence.parse_waiver_expiry("NOT-A-DATE"))
        self.assertIsNone(runtime_evidence.parse_waiver_expiry(""))
        self.assertIsNone(runtime_evidence.parse_waiver_expiry(None))

    def test_is_release_command_detection(self):
        # Direct push
        self.assertTrue(runtime_evidence.is_release_command("git push origin main"))
        # Global options with arguments
        self.assertTrue(runtime_evidence.is_release_command("git -C . push origin main"))
        self.assertTrue(runtime_evidence.is_release_command("git -C /tmp/repo --no-pager push"))
        self.assertTrue(runtime_evidence.is_release_command("git --git-dir=.git push"))
        self.assertTrue(runtime_evidence.is_release_command("git --work-tree=. push"))
        self.assertTrue(runtime_evidence.is_release_command("git -c user.name=foo push"))
        # Chained commands
        self.assertTrue(runtime_evidence.is_release_command("git status && git -C . push origin main"))
        # GH and npm
        self.assertTrue(runtime_evidence.is_release_command("gh pr create --title 'feat'"))
        self.assertTrue(runtime_evidence.is_release_command("npm publish"))
        
        # Non-release commands that contain "push" in argument
        self.assertFalse(runtime_evidence.is_release_command('git commit -m "push fix"'))
        self.assertFalse(runtime_evidence.is_release_command("git log -S push"))
        self.assertFalse(runtime_evidence.is_release_command('echo "git push"'))
        self.assertFalse(runtime_evidence.is_release_command("node -e 'console.log(1)'"))

    def test_calculate_policy_disposition(self):
        # All clean checks -> GREEN
        checks_clean = [
            {"exit_code": 0, "metrics": {"failed": 0, "passed": 1, "collected": 1}}
        ]
        self.assertEqual(runtime_evidence.calculate_policy_disposition(checks_clean), "GREEN")

        # Failing check -> RED
        checks_fail = [
            {"exit_code": 1, "metrics": {"failed": 1, "passed": 0, "collected": 1}}
        ]
        self.assertEqual(runtime_evidence.calculate_policy_disposition(checks_fail), "RED")

        # Flaky retry -> AMBER
        checks_flaky = [
            {"exit_code": 0, "flaky_retry": True, "metrics": {"failed": 0, "passed": 1, "collected": 1}}
        ]
        self.assertEqual(runtime_evidence.calculate_policy_disposition(checks_flaky), "AMBER")

        # Warnings -> AMBER
        checks_warn = [
            {"exit_code": 0, "has_warnings": True, "metrics": {"failed": 0, "passed": 1, "collected": 1}}
        ]
        self.assertEqual(runtime_evidence.calculate_policy_disposition(checks_warn), "AMBER")

    def test_flaky_retry_detection_snapshot_isolation(self):
        attempt_history = [
            {
                "label": "unit_test",
                "receipt_id": "rcpt_1",
                "exit_code": 1,
                "git_tree_sha": "sha_old",
                "working_tree_sha": "sha_old",
                "metrics": {"failed": 1}
            }
        ]
        
        # Same label passes on DIFFERENT snapshot -> NOT flaky retry (TDD progression)
        current_receipt_new = {
            "label": "unit_test",
            "receipt_id": "rcpt_2",
            "exit_code": 0,
            "git_tree_sha": "sha_new",
            "working_tree_sha": "sha_new",
            "metrics": {"failed": 0}
        }
        self.assertFalse(runtime_evidence.is_flaky_retry(attempt_history, current_receipt_new, "sha_new", "sha_new"))

        # Same label passes on EXACT SAME snapshot -> FLAKY RETRY
        current_receipt_same = {
            "label": "unit_test",
            "receipt_id": "rcpt_3",
            "exit_code": 0,
            "git_tree_sha": "sha_old",
            "working_tree_sha": "sha_old",
            "metrics": {"failed": 0}
        }
        self.assertTrue(runtime_evidence.is_flaky_retry(attempt_history, current_receipt_same, "sha_old", "sha_old"))

if __name__ == "__main__":
    unittest.main()
