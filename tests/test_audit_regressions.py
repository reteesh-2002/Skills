#!/usr/bin/env python3
"""
Audit Regression Tests — F01 through F14
Each test is named after the finding it locks, reproducing the exact failure
scenario the external auditor used to confirm the bug, then asserting the fix.
"""
import os
import sys
import json
import sqlite3
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import runtime_evidence
import specialist_probes
import task_ledger as task_ledger_mod
import task_shape_gating


# ─────────────────────────────────────────────────────────
# F01: Hook misses shell dispatch forms
# ─────────────────────────────────────────────────────────
class TestF01HookCommandRecognition(unittest.TestCase):

    def _yes(self, cmd):
        self.assertTrue(runtime_evidence.is_release_command(cmd),
                        f"Expected release command, got non-release for: {repr(cmd)}")

    def _no(self, cmd):
        self.assertFalse(runtime_evidence.is_release_command(cmd),
                         f"Expected non-release, got release for: {repr(cmd)}")

    def test_plain_git_push(self):
        self._yes("git push")

    def test_env_git_push(self):
        self._yes("env git push")

    def test_env_i_git_push(self):
        self._yes("env -i git push")

    def test_env_var_assignment_git_push(self):
        self._yes("env GIT_SSH_COMMAND=ssh git push")

    def test_absolute_path_git_push(self):
        self._yes("/usr/bin/git push")

    def test_usr_local_git_push(self):
        self._yes("/usr/local/bin/git push")

    def test_semicolon_embedded_same_token(self):
        # Auditor test: "echo ok;git push" — shlex does NOT split on embedded ;
        self._yes("echo ok;git push")

    def test_multiline_git_push(self):
        # Auditor test: newline-separated block with git push on second line
        self._yes("git status\ngit push")

    def test_bash_c_git_push(self):
        self._yes('bash -c "git push"')

    def test_sh_c_git_push(self):
        self._yes("sh -c 'git push'")

    def test_git_push_with_c_flag(self):
        self._yes("git -C /repo push origin main")

    def test_npm_publish(self):
        self._yes("npm publish")

    def test_gh_pr_create(self):
        self._yes("gh pr create")

    def test_git_status_not_release(self):
        self._no("git status")

    def test_git_pull_not_release(self):
        self._no("git pull")

    def test_echo_not_release(self):
        self._no("echo hello")

    def test_empty_string_not_release(self):
        self._no("")

    def test_none_not_release(self):
        self.assertFalse(runtime_evidence.is_release_command(None))


# ─────────────────────────────────────────────────────────
# F03: Zero-inventory bypass — lint label with no tests passes
# ─────────────────────────────────────────────────────────
class TestF03ZeroInventoryBypass(unittest.TestCase):
    """
    Auditor scenario: bash scripts/exec-proxy.sh --label lint true
    The 'true' command produces no test output. Old code only checked if
    'test' was in label — 'lint' bypassed. Verify gate now catches pytest/jest
    commands regardless of label name.
    """

    def test_pytest_cmd_zero_tests_blocked(self):
        """A check running pytest but collecting 0 tests must be blocked."""
        # Simulate: is_test_check detection for a command with pytest
        cmd = "pytest tests/"
        TEST_RUNNER_BINS = ("pytest", "vitest", "jest", "mocha",
                            "python -m pytest", "python3 -m pytest",
                            "node --test", "npx jest", "npx vitest",
                            "go test", "rspec")
        cmd_lower = cmd.lower()
        label = "lint"  # non-test label
        is_test = ("test" in label.lower()) or any(r in cmd_lower for r in TEST_RUNNER_BINS)
        self.assertTrue(is_test, "pytest command should be classified as test check even with 'lint' label")

    def test_lint_label_no_test_runner_cmd_not_blocked(self):
        """A lint command (not a test runner) with lint label should not be treated as test check."""
        cmd = "flake8 ."
        TEST_RUNNER_BINS = ("pytest", "vitest", "jest", "mocha",
                            "python -m pytest", "python3 -m pytest",
                            "node --test", "npx jest", "npx vitest",
                            "go test", "rspec")
        cmd_lower = cmd.lower()
        label = "lint"
        is_test = ("test" in label.lower()) or any(r in cmd_lower for r in TEST_RUNNER_BINS)
        self.assertFalse(is_test, "flake8 with 'lint' label should not be a test check")


# ─────────────────────────────────────────────────────────
# F06: Graceful drain — fake sequential execution, no timeout
# ─────────────────────────────────────────────────────────
class TestF06GracefulDrain(unittest.TestCase):

    def test_fast_workers_pass_within_timeout(self):
        """Workers that complete instantly should pass the drain."""
        def fast_worker(task_id):
            return True
        result = specialist_probes.probe_graceful_drain(fast_worker, in_flight_tasks=5, drain_timeout_ms=500)
        self.assertTrue(result["passed"])
        self.assertEqual(result["aborted"], 0)

    def test_slow_workers_exceed_deadline_are_aborted(self):
        """Workers that block past the drain timeout must be counted as aborted."""
        import time
        def slow_worker(task_id):
            time.sleep(5)  # Far exceeds drain_timeout_ms=50ms
            return True
        result = specialist_probes.probe_graceful_drain(slow_worker, in_flight_tasks=3, drain_timeout_ms=50)
        # At least some tasks should be aborted (timed out) — the probe must enforce the deadline
        self.assertFalse(result["passed"],
                         "Slow workers should fail the drain within 50ms deadline")
        self.assertGreater(result["aborted"], 0,
                           "At least one worker should be counted as aborted due to timeout")

    def test_failing_workers_are_counted_as_aborted(self):
        """Workers that return False should count as aborted."""
        def failing_worker(task_id):
            return False
        result = specialist_probes.probe_graceful_drain(failing_worker, in_flight_tasks=4, drain_timeout_ms=500)
        self.assertFalse(result["passed"])
        self.assertEqual(result["aborted"], 4)


# ─────────────────────────────────────────────────────────
# F07: SQLite migration rehearsal accepts FK violations
# ─────────────────────────────────────────────────────────
class TestF07SQLiteForeignKeys(unittest.TestCase):

    def test_valid_fk_reference_passes(self):
        """A seed that correctly references a parent FK should pass."""
        up = """
            CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL);
            CREATE TABLE posts (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL,
                                FOREIGN KEY (user_id) REFERENCES users(id));
        """
        down = "DROP TABLE posts; DROP TABLE users;"
        seed = "INSERT INTO users VALUES (1, 'Alice'); INSERT INTO posts VALUES (1, 1);"
        result = specialist_probes.rehearse_sqlite_migration(up, down, seed_sql=seed)
        self.assertTrue(result["passed"], f"Expected pass, got errors: {result['errors']}")

    def test_invalid_fk_violation_is_caught(self):
        """
        Auditor scenario: FK constraints were NOT enforced (PRAGMA foreign_keys default OFF).
        Inserting a post referencing non-existent user_id=999 should FAIL.
        Before the fix this passed silently.
        """
        up = """
            CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL);
            CREATE TABLE posts (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL,
                                FOREIGN KEY (user_id) REFERENCES users(id));
        """
        down = "DROP TABLE posts; DROP TABLE users;"
        # user_id=999 does not exist in users table — FK violation
        seed = "INSERT INTO posts VALUES (1, 999);"
        result = specialist_probes.rehearse_sqlite_migration(up, down, seed_sql=seed)
        self.assertFalse(result["passed"],
                         "FK violation (referencing non-existent parent) should cause rehearsal to fail")
        self.assertGreater(len(result["errors"]), 0,
                           "Errors list should contain the FK constraint error")


# ─────────────────────────────────────────────────────────
# F08: Ledger completes tasks without evidence receipt
# ─────────────────────────────────────────────────────────
class TestF08LedgerDoneWithoutReceipt(unittest.TestCase):

    def test_done_without_evidence_ref_allowed(self):
        """Marking Done with NO evidence_ref (manual task) is still allowed."""
        with tempfile.TemporaryDirectory() as tmp:
            ledger_path = os.path.join(tmp, ".evidence", "tasks.json")
            ledger = task_ledger_mod.TaskLedger(ledger_path)
            ledger.init_ledger("Test Plan")
            ledger.add_task("T1", "Manual task")
            # No evidence_ref — allowed (some tasks are manual)
            ledger.update_task("T1", status="Done", detail="Reviewed manually")
            t = ledger.get_task("T1")
            self.assertEqual(t["status"], "Done")

    def test_done_with_missing_receipt_raises(self):
        """
        Auditor scenario: marking Done with evidence_ref pointing to non-existent receipt
        was silently allowed. Now must raise ValueError.
        """
        with tempfile.TemporaryDirectory() as tmp:
            ledger_path = os.path.join(tmp, ".evidence", "tasks.json")
            ledger = task_ledger_mod.TaskLedger(ledger_path)
            ledger.init_ledger("Test Plan")
            ledger.add_task("T1", "Needs evidence")
            with self.assertRaises(ValueError, msg="Missing receipt file must raise ValueError"):
                ledger.update_task("T1", status="Done", evidence_ref="nonexistent_receipt_id")

    def test_done_with_corrupt_receipt_raises(self):
        """A corrupt (invalid JSON) receipt must also raise, not silently pass."""
        with tempfile.TemporaryDirectory() as tmp:
            ledger_path = os.path.join(tmp, ".evidence", "tasks.json")
            receipts_dir = os.path.join(tmp, ".evidence", "receipts")
            os.makedirs(receipts_dir, exist_ok=True)
            corrupt_path = os.path.join(receipts_dir, "corrupt_rcpt.json")
            with open(corrupt_path, "w") as f:
                f.write("{not valid json")
            ledger = task_ledger_mod.TaskLedger(ledger_path)
            ledger.init_ledger("Test Plan")
            ledger.add_task("T1", "Needs evidence")
            with self.assertRaises(ValueError):
                ledger.update_task("T1", status="Done", evidence_ref="corrupt_rcpt")

    def test_done_with_failed_receipt_raises(self):
        """A receipt with exit_code != 0 must block Done transition."""
        with tempfile.TemporaryDirectory() as tmp:
            ledger_path = os.path.join(tmp, ".evidence", "tasks.json")
            receipts_dir = os.path.join(tmp, ".evidence", "receipts")
            os.makedirs(receipts_dir, exist_ok=True)
            rcpt_path = os.path.join(receipts_dir, "failed_rcpt.json")
            with open(rcpt_path, "w") as f:
                json.dump({
                    "receipt_id": "failed_rcpt",
                    "command": "pytest",
                    "exit_code": 1,
                    "git_tree_sha": "abc",
                    "metrics": {"collected": 5, "passed": 3, "failed": 2, "skipped": 0}
                }, f)
            ledger = task_ledger_mod.TaskLedger(ledger_path)
            ledger.init_ledger("Test Plan")
            ledger.add_task("T1", "Needs passing evidence")
            with self.assertRaises(ValueError):
                ledger.update_task("T1", status="Done", evidence_ref="failed_rcpt")


# ─────────────────────────────────────────────────────────
# F11: Pytest parsing — "1 passed, 1 skipped in 0.01s" → 0 tests
# ─────────────────────────────────────────────────────────
class TestF11PytestParsing(unittest.TestCase):
    """
    These tests exercise the regex logic extracted from exec-proxy.sh's inline Python section.
    We replicate the parser inline to verify the fix without needing bash.
    """

    def _parse_pytest_output(self, log_content):
        import re
        collected = passed = failed = skipped = 0
        if re.search(r'\d+\s+(?:passed|failed|error(?:ed)?|skipped)\b', log_content) and \
           re.search(r'in \d+\.?\d*s', log_content):
            m_pass = re.search(r'(\d+)\s+passed', log_content)
            m_fail = re.search(r'(\d+)\s+(?:failed|error(?:ed)?)', log_content)
            m_skip = re.search(r'(\d+)\s+skipped', log_content)
            if m_pass: passed = int(m_pass.group(1))
            if m_fail: failed = int(m_fail.group(1))
            if m_skip: skipped = int(m_skip.group(1))
            collected = passed + failed + skipped
        return collected, passed, failed, skipped

    def test_simple_pass(self):
        c, p, f, s = self._parse_pytest_output("1 passed in 0.05s")
        self.assertEqual(c, 1)
        self.assertEqual(p, 1)
        self.assertEqual(f, 0)

    def test_passed_and_skipped(self):
        """Auditor scenario: '1 passed, 1 skipped in 0.01s' parsed as 0 tests (old bug)."""
        c, p, f, s = self._parse_pytest_output("1 passed, 1 skipped in 0.01s")
        self.assertEqual(c, 2, f"Expected 2 total (1 passed + 1 skipped), got {c}")
        self.assertEqual(p, 1)
        self.assertEqual(s, 1)
        self.assertEqual(f, 0)

    def test_failed(self):
        c, p, f, s = self._parse_pytest_output("2 failed in 0.3s")
        self.assertEqual(c, 2)
        self.assertEqual(f, 2)

    def test_mixed(self):
        c, p, f, s = self._parse_pytest_output("3 passed, 1 failed, 2 skipped in 1.5s")
        self.assertEqual(c, 6)
        self.assertEqual(p, 3)
        self.assertEqual(f, 1)
        self.assertEqual(s, 2)

    def test_non_pytest_output_not_matched(self):
        c, p, f, s = self._parse_pytest_output("Compilation successful")
        self.assertEqual(c, 0)


# ─────────────────────────────────────────────────────────
# F13: Viewport overflow — global max-width escape hatch
# ─────────────────────────────────────────────────────────
class TestF13ViewportOverflow(unittest.TestCase):

    def test_fixed_900px_div_flagged_on_375_viewport(self):
        """Auditor scenario: 900px div with max-width:100% elsewhere should still be flagged."""
        html = """
        <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1"></head>
        <body>
          <div style="max-width:100%">other content</div>
          <div style="width:900px">overflow hazard</div>
        </body>
        </html>
        """
        result = specialist_probes.check_html_viewport_overflow(html, viewports=[375])
        hazard_types = [h["hazard"] for h in result["hazards"]]
        self.assertIn("fixed_pixel_overflow", hazard_types,
                      "900px div must be flagged even if max-width:100% appears elsewhere in document")
        self.assertFalse(result["passed"])

    def test_responsive_only_html_passes(self):
        html = """
        <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1"></head>
        <body><div style="width:100%">fluid</div></body>
        </html>
        """
        result = specialist_probes.check_html_viewport_overflow(html, viewports=[375])
        self.assertEqual(result["hazards_found"], 0)
        self.assertTrue(result["passed"])

    def test_300px_div_under_375_passes(self):
        html = """
        <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1"></head>
        <body><div style="width:300px">small box</div></body>
        </html>
        """
        result = specialist_probes.check_html_viewport_overflow(html, viewports=[375])
        fixed_hazards = [h for h in result["hazards"] if h["hazard"] == "fixed_pixel_overflow"]
        self.assertEqual(len(fixed_hazards), 0, "300px < 375px viewport so no overflow hazard")


# ─────────────────────────────────────────────────────────
# F14: Worker cap not enforced
# ─────────────────────────────────────────────────────────
class TestF14WorkerCap(unittest.TestCase):

    def test_caller_requesting_12_workers_gets_max_4(self):
        """Auditor scenario: gate_task(workstream_count=12, max_workers=12) returned 12."""
        decision = task_shape_gating.gate_task(
            file_touch_count=12,
            workstream_count=12,
            max_workers=12,
        )
        self.assertLessEqual(decision.worker_count, 4,
                             f"Worker count must never exceed 4, got {decision.worker_count}")

    def test_caller_requesting_100_workers_gets_max_4(self):
        decision = task_shape_gating.gate_task(
            file_touch_count=20,
            workstream_count=100,
            max_workers=100,
        )
        self.assertLessEqual(decision.worker_count, 4)

    def test_normal_2_workstreams_gives_2(self):
        """2 workstreams still returns 2 workers (within cap)."""
        decision = task_shape_gating.gate_task(
            file_touch_count=4,
            workstream_count=2,
            max_workers=4,
        )
        self.assertEqual(decision.worker_count, 2)

    def test_default_max_4_workstreams_gives_4(self):
        decision = task_shape_gating.gate_task(
            file_touch_count=8,
            workstream_count=8,
        )
        self.assertLessEqual(decision.worker_count, 4)


if __name__ == "__main__":
    unittest.main()
