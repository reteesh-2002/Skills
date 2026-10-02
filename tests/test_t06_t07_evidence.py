#!/usr/bin/env python3
"""
Unit and Integration tests for T06 and T07:
- T06: Evidence adapter registry, framework detection, xfail counting, unverified flag, policy AMBER reduction.
- T07: Hook targeting, ambiguous command handling (eval, command substitution, unbalanced quotes), fail-safe gate blocks.
"""

import os
import sys
import json
import tempfile
import subprocess
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "scripts")
sys.path.insert(0, SCRIPTS_DIR)

import runtime_evidence

GATE_SCRIPT = os.path.join(SCRIPTS_DIR, "verify-release-gate.sh")
PROXY_SCRIPT = os.path.join(SCRIPTS_DIR, "exec-proxy.sh")


def _git(args, cwd):
    """Run git command in cwd, raise on non-zero exit."""
    return subprocess.check_output(
        ["git"] + args, cwd=cwd,
        stderr=subprocess.DEVNULL
    ).decode().strip()


def _init_repo():
    """Create a minimal git repo with one commit, return (tmpdir, tree_sha)."""
    tmpdir = tempfile.mkdtemp(prefix="t06_t07_repo_")
    _git(["init", "-b", "main"], cwd=tmpdir)
    _git(["config", "user.email", "ci@test.local"], cwd=tmpdir)
    _git(["config", "user.name", "CI Bot"], cwd=tmpdir)
    seed = os.path.join(tmpdir, "seed.txt")
    with open(seed, "w") as f:
        f.write("seed\n")
    _git(["add", "seed.txt"], cwd=tmpdir)
    _git(["commit", "-m", "init"], cwd=tmpdir)
    tree_sha = _git(["write-tree"], cwd=tmpdir)
    return tmpdir, tree_sha


class TestT06FrameworkAndXfailParsing(unittest.TestCase):
    """T06: Test framework metric parsing, xfail handling, and framework detection."""

    def _simulate_exec_proxy_parser(self, command_str, log_content, exit_code=0):
        """Simulate the exec-proxy test framework parser logic."""
        import re
        collected = 0
        passed = 0
        failed = 0
        skipped = 0
        xfail = 0
        framework_detected = "unknown"

        if (re.search(r'\d+\s+(?:passed|failed|error(?:ed)?|skipped|xfailed)\b', log_content) and re.search(r'in \d+\.?\d*s', log_content)) or ("pytest" in command_str.lower() and (re.search(r'collected \d+ items', log_content) or re.search(r'no tests ran in', log_content))):
            framework_detected = "pytest"
            m_pass = re.search(r'(\d+)\s+passed', log_content)
            m_fail = re.search(r'(\d+)\s+failed', log_content)
            m_err  = re.search(r'(\d+)\s+error(?:ed)?', log_content)
            m_skip = re.search(r'(\d+)\s+skipped', log_content)
            m_xfail = re.search(r'(\d+)\s+xfailed', log_content)

            if m_pass and m_pass.group(1): passed = int(m_pass.group(1))
            fail_count = int(m_fail.group(1)) if (m_fail and m_fail.group(1)) else 0
            err_count = int(m_err.group(1)) if (m_err and m_err.group(1)) else 0
            failed = fail_count + err_count
            if m_skip and m_skip.group(1): skipped = int(m_skip.group(1))
            if m_xfail and m_xfail.group(1):
                xfail = int(m_xfail.group(1))
                skipped += xfail
            collected = passed + failed + skipped
        elif "# tests" in log_content or "ℹ tests" in log_content or "✔" in log_content or "ℹ pass" in log_content or "node --test" in command_str.lower():
            framework_detected = "node-tap"
            m_tests = re.search(r'(?:#|ℹ)\s+tests\s+(\d+)', log_content)
            m_pass = re.search(r'(?:#|ℹ)\s+pass(?:ed)?\s+(\d+)', log_content)
            m_fail = re.search(r'(?:#|ℹ)\s+fail(?:ed)?\s+(\d+)', log_content)
            m_skip = re.search(r'(?:#|ℹ)\s+(?:cancelled|skipped|todo)\s+(\d+)', log_content)

            if m_tests and m_tests.group(1): collected = int(m_tests.group(1))
            if m_pass and m_pass.group(1): passed = int(m_pass.group(1))
            if m_fail and m_fail.group(1): failed = int(m_fail.group(1))
            if m_skip and m_skip.group(1): skipped = int(m_skip.group(1))

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

                if m_pass: passed = int(m_pass.group(1))
                if m_fail: failed = int(m_fail.group(1))
                if m_skip: skipped = int(m_skip.group(1))
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
                if m_pass: passed = int(m_pass.group(1))
                if m_fail: failed = int(m_fail.group(1))
                if m_skip: skipped = int(m_skip.group(1))
                collected = passed + failed + skipped
        elif "test result:" in log_content or "cargo test" in command_str.lower():
            framework_detected = "cargo"
            m_cargo = re.search(r'test result:\s+\w+\.\s+(\d+)\s+passed;\s+(\d+)\s+failed;\s+(\d+)\s+ignored', log_content)
            if m_cargo:
                passed = int(m_cargo.group(1))
                failed = int(m_cargo.group(2))
                skipped = int(m_cargo.group(3))
                collected = passed + failed + skipped
        elif ("Ran " in log_content and (" tests in " in log_content or " test in " in log_content)) or "python -m unittest" in command_str.lower() or "python3 -m unittest" in command_str.lower():
            framework_detected = "python-unittest"
            m_ran = re.search(r'Ran\s+(\d+)\s+tests?\s+in', log_content)
            m_fail = re.search(r'FAILED\s*\(.*?failures=(\d+)', log_content)
            m_err  = re.search(r'FAILED\s*\(.*?errors=(\d+)', log_content)
            m_skip = re.search(r'skipped=(\d+)', log_content)
            if m_ran:
                collected = int(m_ran.group(1))
                failed    = (int(m_fail.group(1)) if m_fail else 0) + (int(m_err.group(1)) if m_err else 0)
                skipped   = int(m_skip.group(1)) if m_skip else 0
                passed    = collected - failed - skipped

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

    def test_pytest_xfail_counted_as_skipped(self):
        log = "===== 1 passed, 2 xfailed in 0.05s ====="
        res = self._simulate_exec_proxy_parser("pytest tests/", log)
        self.assertEqual(res["framework_detected"], "pytest")
        self.assertEqual(res["passed"], 1)
        self.assertEqual(res["failed"], 0)
        self.assertEqual(res["xfail"], 2)
        self.assertEqual(res["skipped"], 2)
        self.assertEqual(res["collected"], 3)
        self.assertFalse(res["unverified"])

    def test_pytest_xfail_plus_skipped(self):
        log = "===== 2 passed, 1 skipped, 1 xfailed in 0.12s ====="
        res = self._simulate_exec_proxy_parser("pytest tests/", log)
        self.assertEqual(res["framework_detected"], "pytest")
        self.assertEqual(res["passed"], 2)
        self.assertEqual(res["failed"], 0)
        self.assertEqual(res["xfail"], 1)
        self.assertEqual(res["skipped"], 2)  # 1 skipped + 1 xfail
        self.assertEqual(res["collected"], 4)

    def test_pytest_only_xfail(self):
        log = "===== 3 xfailed in 0.04s ====="
        res = self._simulate_exec_proxy_parser("pytest tests/", log)
        self.assertEqual(res["framework_detected"], "pytest")
        self.assertEqual(res["passed"], 0)
        self.assertEqual(res["failed"], 0)
        self.assertEqual(res["xfail"], 3)
        self.assertEqual(res["skipped"], 3)
        self.assertEqual(res["collected"], 3)

    def test_jest_metric_parsing(self):
        log = "Tests:       1 failed, 2 skipped, 3 passed, 6 total"
        res = self._simulate_exec_proxy_parser("npx jest", log)
        self.assertEqual(res["framework_detected"], "jest")
        self.assertEqual(res["passed"], 3)
        self.assertEqual(res["failed"], 1)
        self.assertEqual(res["skipped"], 2)
        self.assertEqual(res["collected"], 6)

    def test_vitest_metric_parsing(self):
        log = "Tests  1 failed | 2 passed (3)"
        res = self._simulate_exec_proxy_parser("npx vitest run", log)
        self.assertEqual(res["framework_detected"], "vitest")
        self.assertEqual(res["passed"], 2)
        self.assertEqual(res["failed"], 1)
        self.assertEqual(res["collected"], 3)

    def test_cargo_metric_parsing(self):
        log = "test result: ok. 5 passed; 0 failed; 2 ignored; 0 measured; 0 filtered out"
        res = self._simulate_exec_proxy_parser("cargo test", log)
        self.assertEqual(res["framework_detected"], "cargo")
        self.assertEqual(res["passed"], 5)
        self.assertEqual(res["failed"], 0)
        self.assertEqual(res["skipped"], 2)
        self.assertEqual(res["collected"], 7)

    def test_node_tap_metric_parsing(self):
        log = "# tests 4\n# pass 3\n# fail 1\n# cancelled 0"
        res = self._simulate_exec_proxy_parser("node --test", log)
        self.assertEqual(res["framework_detected"], "node-tap")
        self.assertEqual(res["passed"], 3)
        self.assertEqual(res["failed"], 1)
        self.assertEqual(res["collected"], 4)

    def test_python_unittest_metric_parsing(self):
        log = "Ran 10 tests in 0.020s\n\nFAILED (failures=2, errors=1, skipped=1)"
        res = self._simulate_exec_proxy_parser("python3 -m unittest", log)
        self.assertEqual(res["framework_detected"], "python-unittest")
        self.assertEqual(res["collected"], 10)
        self.assertEqual(res["failed"], 3)
        self.assertEqual(res["skipped"], 1)
        self.assertEqual(res["passed"], 6)


class TestT06UnverifiedFlagAndPolicyDisposition(unittest.TestCase):
    """T06: Unverified flag logic and AMBER policy disposition."""

    def test_unverified_flag_on_non_test_runner(self):
        # Non-test runner with 0 tests collected and exit 0 -> unverified: True
        cmds = ["echo hello", "true", "flake8 .", "make build", "cat README.md"]
        for cmd in cmds:
            self.assertFalse(runtime_evidence.is_known_test_runner(cmd))
            is_unverified = (0 == 0 and not runtime_evidence.is_known_test_runner(cmd) and 0 == 0)
            self.assertTrue(is_unverified, f"Expected unverified=True for '{cmd}'")

    def test_unverified_flag_false_on_known_test_runners(self):
        # Known test runners with 0 tests collected -> unverified: False (handled by zero-inventory gate check)
        runners = [
            "pytest tests/", "python3 -m pytest tests/", "jest", "npx jest",
            "vitest", "npx vitest", "cargo test", "node --test", "go test", "rspec"
        ]
        for cmd in runners:
            self.assertTrue(runtime_evidence.is_known_test_runner(cmd), f"Expected known test runner for '{cmd}'")
            is_unverified = (0 == 0 and not runtime_evidence.is_known_test_runner(cmd) and 0 == 0)
            self.assertFalse(is_unverified, f"Expected unverified=False for known runner '{cmd}'")

    def test_policy_disposition_amber_on_unverified(self):
        # Single unverified check -> AMBER
        checks_unverified = [
            {"exit_code": 0, "unverified": True, "metrics": {"collected": 0, "passed": 0, "failed": 0}}
        ]
        self.assertEqual(runtime_evidence.calculate_policy_disposition(checks_unverified), "AMBER")

        # Verified test check + unverified non-test check -> AMBER
        checks_mixed = [
            {"exit_code": 0, "unverified": False, "metrics": {"collected": 5, "passed": 5, "failed": 0}},
            {"exit_code": 0, "unverified": True, "metrics": {"collected": 0, "passed": 0, "failed": 0}},
        ]
        self.assertEqual(runtime_evidence.calculate_policy_disposition(checks_mixed), "AMBER")

        # Unverified check + failing check -> RED (failures take precedence over AMBER)
        checks_failing = [
            {"exit_code": 0, "unverified": True, "metrics": {"collected": 0, "passed": 0, "failed": 0}},
            {"exit_code": 1, "unverified": False, "metrics": {"collected": 1, "passed": 0, "failed": 1}},
        ]
        self.assertEqual(runtime_evidence.calculate_policy_disposition(checks_failing), "RED")

        # Verified checks only with no unverified / flaky / skips -> GREEN
        checks_clean = [
            {"exit_code": 0, "unverified": False, "metrics": {"collected": 5, "passed": 5, "failed": 0}}
        ]
        self.assertEqual(runtime_evidence.calculate_policy_disposition(checks_clean), "GREEN")

    def test_validate_receipt_structure_allows_optional_fields(self):
        valid_rcpt = {
            "receipt_id": "rcpt_t06_01",
            "command": "pytest tests/",
            "exit_code": 0,
            "git_tree_sha": "abc12345" * 5,
            "metrics": {"collected": 5, "passed": 5, "failed": 0, "skipped": 0},
            "unverified": False,
            "framework_detected": "pytest",
            "xfail": 1
        }
        # Must not raise
        runtime_evidence.validate_receipt_structure(valid_rcpt, "rcpt_t06_01")

        # Invalid unverified type
        invalid_unverified = dict(valid_rcpt, unverified="yes")
        with self.assertRaises(ValueError):
            runtime_evidence.validate_receipt_structure(invalid_unverified, "rcpt_t06_01")

        # Invalid framework_detected type
        invalid_fw = dict(valid_rcpt, framework_detected=123)
        with self.assertRaises(ValueError):
            runtime_evidence.validate_receipt_structure(invalid_fw, "rcpt_t06_01")

        # Invalid xfail type
        invalid_xfail = dict(valid_rcpt, xfail="two")
        with self.assertRaises(ValueError):
            runtime_evidence.validate_receipt_structure(invalid_xfail, "rcpt_t06_01")


class TestT07IsReleaseCommandAmbiguity(unittest.TestCase):
    """T07: Ambiguous command handling in is_release_command (eval, $(), backticks, unbalanced quotes)."""

    def test_eval_returns_unsupported(self):
        eval_commands = [
            'eval "git push"',
            "eval 'git push origin main'",
            "eval git push",
            "eval $(which git)",
            "echo ok; eval git push",
            "eval 'echo safe'",
        ]
        for cmd in eval_commands:
            with self.subTest(cmd=cmd):
                res = runtime_evidence.is_release_command(cmd)
                self.assertEqual(res, "unsupported", f"'{cmd}' should return 'unsupported'")

    def test_command_substitution_returns_unsupported(self):
        subst_commands = [
            "$(git push)",
            "`git push`",
            "echo $(git push)",
            "VAR=$(git push)",
            "result=`git push`",
            "`npm publish`",
            "$(npm publish)",
        ]
        for cmd in subst_commands:
            with self.subTest(cmd=cmd):
                res = runtime_evidence.is_release_command(cmd)
                self.assertEqual(res, "unsupported", f"'{cmd}' should return 'unsupported'")

    def test_unbalanced_quotes_with_release_keywords_returns_unsupported(self):
        ambiguous = [
            'git push "origin',
            "npm publish 'v1.0.0",
            'gh pr create "title',
            "gh release create 'tag",
        ]
        for cmd in ambiguous:
            with self.subTest(cmd=cmd):
                res = runtime_evidence.is_release_command(cmd)
                self.assertEqual(res, "unsupported", f"'{cmd}' with unbalanced quotes and release keyword should return 'unsupported'")

    def test_unbalanced_quotes_without_release_keywords_returns_false(self):
        non_release_unbalanced = [
            'echo "hello',
            "git status 'main",
            'cat "file',
        ]
        for cmd in non_release_unbalanced:
            with self.subTest(cmd=cmd):
                res = runtime_evidence.is_release_command(cmd)
                self.assertFalse(res, f"'{cmd}' with unbalanced quotes and no release keyword should return False")

    def test_definite_release_commands_return_true(self):
        definite = [
            "git push",
            "git push origin main",
            "env git push",
            "env -i git push",
            "/usr/bin/git push",
            "/usr/local/bin/git push",
            "npm publish",
            "gh pr create --title 'feat'",
            "gh release create v1.0.0",
            'bash -c "git push"',
        ]
        for cmd in definite:
            with self.subTest(cmd=cmd):
                self.assertTrue(runtime_evidence.is_release_command(cmd), f"'{cmd}' should return True")

    def test_definite_non_release_commands_return_false(self):
        non_release = [
            "git status",
            "git pull origin main",
            "git diff HEAD",
            "git log -n 5",
            "echo hello",
            "python3 -m pytest tests/",
            'git commit -m "push fix"',
            'echo "git push"',
        ]
        for cmd in non_release:
            with self.subTest(cmd=cmd):
                self.assertFalse(runtime_evidence.is_release_command(cmd), f"'{cmd}' should return False")


class TestT06T07VerifyReleaseGateIntegration(unittest.TestCase):
    """Integration tests for verify-release-gate.sh on unsupported commands and unverified checks."""

    def test_verify_release_gate_blocks_on_unsupported_eval(self):
        # Run verify-release-gate.sh with --pre-tool 'eval "git push"'
        proc = subprocess.run(
            ["bash", GATE_SCRIPT, "--pre-tool", 'eval "git push"'],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True
        )
        self.assertEqual(proc.returncode, 1, f"Expected non-zero exit for eval, got {proc.returncode}")
        self.assertIn("Command form is ambiguous or unsupported by static analyzer — fail-safe block", proc.stderr)
        self.assertIn("eval \"git push\"", proc.stderr)

    def test_verify_release_gate_blocks_on_unsupported_substitution(self):
        proc = subprocess.run(
            ["bash", GATE_SCRIPT, "--pre-tool", "$(git push)"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True
        )
        self.assertEqual(proc.returncode, 1, f"Expected non-zero exit for $(git push), got {proc.returncode}")
        self.assertIn("Command form is ambiguous or unsupported by static analyzer — fail-safe block", proc.stderr)
        self.assertIn("$(git push)", proc.stderr)

    def test_verify_release_gate_blocks_on_unsupported_backticks(self):
        proc = subprocess.run(
            ["bash", GATE_SCRIPT, "--pre-tool", "`git push`"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True
        )
        self.assertEqual(proc.returncode, 1, f"Expected non-zero exit for `git push`, got {proc.returncode}")
        self.assertIn("Command form is ambiguous or unsupported by static analyzer — fail-safe block", proc.stderr)

    def test_verify_release_gate_allows_safe_command_in_hook_mode(self):
        proc = subprocess.run(
            ["bash", GATE_SCRIPT, "--pre-tool", "git status"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn('"decision": "allow"', proc.stdout)

    def test_verify_release_gate_blocks_zero_inventory_non_test_runner(self):
        # Setup temporary clean git repo
        repo_dir, _ = _init_repo()
        import shutil
        repo_scripts = os.path.join(repo_dir, "scripts")
        shutil.copytree(SCRIPTS_DIR, repo_scripts)

        with open(os.path.join(repo_dir, ".gitignore"), "w") as f:
            f.write(".evidence/\n")
        _git(["add", "."], cwd=repo_dir)
        _git(["commit", "-m", "setup scripts"], cwd=repo_dir)
        tree_sha = _git(["write-tree"], cwd=repo_dir)

        evidence_dir = os.path.join(repo_dir, ".evidence")
        receipts_dir = os.path.join(evidence_dir, "receipts")
        logs_dir = os.path.join(evidence_dir, "logs")
        os.makedirs(receipts_dir, exist_ok=True)
        os.makedirs(logs_dir, exist_ok=True)

        rcpt_id = "rcpt_zero_echo"
        rcpt = {
            "receipt_id": rcpt_id,
            "label": "smoke_echo",
            "command": "echo ok",
            "exit_code": 0,
            "duration_ms": 10,
            "git_tree_sha": tree_sha,
            "working_tree_sha": tree_sha,
            "working_tree_dirty": False,
            "log_path": f"logs/{rcpt_id}.log",
            "framework_detected": "unknown",
            "unverified": True,
            "xfail": 0,
            "metrics": {"collected": 0, "passed": 0, "failed": 0, "skipped": 0},
            "has_warnings": False
        }
        with open(os.path.join(receipts_dir, f"{rcpt_id}.json"), "w") as f:
            json.dump(rcpt, f)
        with open(os.path.join(logs_dir, f"{rcpt_id}.log"), "w") as f:
            f.write("ok\n")

        # Manifest claims GREEN even though check is unverified (zero inventory)
        manifest = {
            "schema_version": "manifest.v1",
            "git_tree_sha": tree_sha,
            "policy_disposition": "GREEN",
            "checks": [rcpt],
            "attempt_history": [rcpt],
            "open_waivers": []
        }
        with open(os.path.join(evidence_dir, "manifest.v1.json"), "w") as f:
            json.dump(manifest, f)

        proc = subprocess.run(
            ["bash", os.path.join(repo_scripts, "verify-release-gate.sh")],
            cwd=repo_dir,
            capture_output=True,
            text=True
        )
        self.assertEqual(proc.returncode, 1)
        self.assertTrue(
            "unverified" in proc.stderr.lower() or "zero-inventory" in proc.stderr.lower(),
            f"Expected unverified/zero-inventory gate failure, got stderr:\n{proc.stderr}"
        )


if __name__ == "__main__":
    unittest.main()
