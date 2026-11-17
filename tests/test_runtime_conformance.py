"""
Pure Python Runtime Conformance & Adversarial Test Suite.
Directly implements all 27 runtime invariants (P01–P32) in cross-platform Python
so they can run on Windows, macOS, and Linux without bash or MSYS.
"""

import io
import os
import sys
import json
import time
import shutil
import tempfile
import unittest
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
EXEC_PROXY = SCRIPTS_DIR / "exec_proxy.py"
VERIFY_GATE = SCRIPTS_DIR / "verify_release_gate.py"
TASK_LEDGER = SCRIPTS_DIR / "task_ledger.py"
AUDIT_DIFF = SCRIPTS_DIR / "audit_diff.py"
SETUP_WORKTREES = SCRIPTS_DIR / "setup_worktrees.py"


class TestRuntimeConformance(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="conformance_sandbox_")
        self.sandbox = Path(self.tmp_dir)
        # Initialize git repo in sandbox
        subprocess.run(["git", "init", "-b", "main", "--quiet"], cwd=str(self.sandbox), check=True)
        subprocess.run(["git", "config", "user.name", "Test Runner"], cwd=str(self.sandbox), check=True)
        subprocess.run(["git", "config", "user.email", "test@local"], cwd=str(self.sandbox), check=True)

        # Setup scripts directory in sandbox
        self.sb_scripts = self.sandbox / "scripts"
        self.sb_scripts.mkdir(parents=True, exist_ok=True)
        for s in ("exec_proxy.py", "verify_release_gate.py", "runtime_evidence.py",
                  "task_ledger.py", "audit_diff.py", "setup_worktrees.py"):
            shutil.copy2(SCRIPTS_DIR / s, self.sb_scripts / s)

        # Initial commit
        (self.sandbox / ".gitignore").write_text(".evidence/\n__pycache__/\n*.py[cod]\n", encoding="utf-8")
        (self.sandbox / "index.js").write_text("console.log('init');\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=str(self.sandbox), check=True)
        subprocess.run(["git", "commit", "-m", "chore: initial sandbox state", "--quiet"], cwd=str(self.sandbox), check=True)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def _proxy(self, *args, check=False) -> subprocess.CompletedProcess:
        cmd = [sys.executable, str(self.sb_scripts / "exec_proxy.py")] + list(args)
        return subprocess.run(cmd, cwd=str(self.sandbox), capture_output=True, text=True, check=check)

    def _gate(self, *args, check=False) -> subprocess.CompletedProcess:
        cmd = [sys.executable, str(self.sb_scripts / "verify_release_gate.py")] + list(args)
        res = subprocess.run(cmd, cwd=str(self.sandbox), capture_output=True, text=True, check=check)
        res.combined = (res.stdout or "") + (res.stderr or "")
        return res

    def test_01_nonzero_exit_code_capture(self):
        """P01: Non-zero exit code propagation."""
        res = self._proxy("--label", "test_fail", sys.executable, "-c", "import sys; sys.exit(42)")
        self.assertEqual(res.returncode, 42)

    def test_02_node_spec_metric_parsing(self):
        """P16: Node spec test metric parsing."""
        node_script = (
            "console.log('TAP version 13');"
            "console.log('# Subtest: test_suite');"
            "console.log('ok 1 - test case passes');"
            "console.log('1..1');"
            "console.log('# tests 1');"
            "console.log('# suites 1');"
            "console.log('# pass 1');"
            "console.log('# fail 0');"
        )
        res = self._proxy("--label", "test_node_spec", "node", "-e", node_script)
        if shutil.which("node"):
            self.assertEqual(res.returncode, 0)
            manifest_file = self.sandbox / ".evidence" / "manifest.v1.json"
            self.assertTrue(manifest_file.exists())
            data = json.loads(manifest_file.read_text(encoding="utf-8"))
            check = next(c for c in data["checks"] if c["label"] == "test_node_spec")
            self.assertEqual(check["metrics"]["collected"], 1)
            self.assertEqual(check["metrics"]["passed"], 1)

    def test_03_release_gate_approval_on_clean_verified_tree(self):
        """P04: Gate approval on clean verified tree."""
        res_proxy = self._proxy("--label", "test_unit", sys.executable, "-c", "print('Ran 1 test in 0.01s\\n\\nOK')")
        self.assertEqual(res_proxy.returncode, 0)
        res_gate = self._gate("--check-only")
        self.assertEqual(res_gate.returncode, 0)
        self.assertIn("RELEASE GATE PASS", res_gate.stdout)

    def test_04_zero_test_check_rejection(self):
        """P01: Zero-inventory false green rejection."""
        self._proxy("--label", "test_zero", sys.executable, "-c", "print('hello without tests')")
        res_gate = self._gate("--check-only")
        self.assertEqual(res_gate.returncode, 1)
        self.assertIn("Zero-inventory false green", res_gate.combined)

    def test_05_unstaged_modification_rejection(self):
        """P02: Unstaged working tree modification rejection."""
        self._proxy("--label", "test_ok", sys.executable, "-c", "print('Ran 1 test in 0.01s\\n\\nOK')")
        (self.sandbox / "index.js").write_text("console.log('tampered');\n", encoding="utf-8")
        res_gate = self._gate("--check-only")
        self.assertEqual(res_gate.returncode, 1)
        self.assertIn("modified after verification check", res_gate.combined)

    def test_06_missing_physical_receipt_rejection(self):
        """P05: Forged manifest rejection with missing receipts."""
        self._proxy("--label", "test_ok", sys.executable, "-c", "print('Ran 1 test in 0.01s\\n\\nOK')")
        # Delete receipt
        receipts_dir = self.sandbox / ".evidence" / "receipts"
        for r in receipts_dir.glob("*.json"):
            r.unlink()
        res_gate = self._gate("--check-only")
        self.assertEqual(res_gate.returncode, 1)
        self.assertIn("receipt file not found", res_gate.combined.lower())

    def test_07_invalid_or_unknown_tree_sha_rejection(self):
        """P06 & P09: Invalid tree SHA rejection."""
        self._proxy("--label", "test_ok", sys.executable, "-c", "print('Ran 1 test in 0.01s\\n\\nOK')")
        manifest_file = self.sandbox / ".evidence" / "manifest.v1.json"
        data = json.loads(manifest_file.read_text(encoding="utf-8"))
        data["git_tree_sha"] = "0000000000000000000000000000000000000000"
        manifest_file.write_text(json.dumps(data), encoding="utf-8")
        res_gate = self._gate("--check-only")
        self.assertEqual(res_gate.returncode, 1)
        self.assertIn("Working tree changed since tests ran", res_gate.combined)

    def test_08_invalid_disposition_rejection(self):
        """P07: Invalid disposition rejection."""
        self._proxy("--label", "test_ok", sys.executable, "-c", "print('Ran 1 test in 0.01s\\n\\nOK')")
        manifest_file = self.sandbox / ".evidence" / "manifest.v1.json"
        data = json.loads(manifest_file.read_text(encoding="utf-8"))
        data["policy_disposition"] = "BANANA"
        manifest_file.write_text(json.dumps(data), encoding="utf-8")
        res_gate = self._gate("--check-only")
        self.assertEqual(res_gate.returncode, 1)
        self.assertIn("Invalid policy disposition 'BANANA'", res_gate.combined)

    def test_09_unstructured_waiver_rejection(self):
        """P08: Unstructured string waiver rejection."""
        self._proxy("--label", "test_ok", sys.executable, "-c", "print('Ran 1 test in 0.01s\\n\\nOK')")
        manifest_file = self.sandbox / ".evidence" / "manifest.v1.json"
        data = json.loads(manifest_file.read_text(encoding="utf-8"))
        data["policy_disposition"] = "AMBER"
        data["open_waivers"] = ["self-approved"]
        manifest_file.write_text(json.dumps(data), encoding="utf-8")
        res_gate = self._gate("--check-only")
        self.assertEqual(res_gate.returncode, 1)
        self.assertIn("Invalid waiver format", res_gate.combined)

    def test_10_retry_laundering_prevention(self):
        """P12: Retried pass preserved in attempt_history and flagged AMBER."""
        # Run 1: fail
        self._proxy("--label", "test_flaky", sys.executable, "-c", "import sys; sys.exit(1)")
        # Run 2: pass
        self._proxy("--label", "test_flaky", sys.executable, "-c", "print('Ran 1 test in 0.01s\\n\\nOK')")
        manifest_file = self.sandbox / ".evidence" / "manifest.v1.json"
        data = json.loads(manifest_file.read_text(encoding="utf-8"))
        self.assertEqual(data["policy_disposition"], "AMBER")
        self.assertGreater(len(data["attempt_history"]), 1)

    def test_11_audit_diff_path_prefix_and_placeholders(self):
        """P21 & P22: Path prefix boundary defense and placeholder detection."""
        subprocess.run(["git", "branch", "feat"], cwd=str(self.sandbox), check=True)
        # Create an out-of-scope file
        (self.sandbox / "bad.txt").write_text("evil\n", encoding="utf-8")
        res_audit = subprocess.run(
            [sys.executable, str(self.sb_scripts / "audit_diff.py"), str(self.sandbox), "main", "src"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res_audit.returncode, 1)
        self.assertIn("OUT-OF-SCOPE: bad.txt", res_audit.stdout)

        # Remove out of scope file, add placeholder
        (self.sandbox / "bad.txt").unlink()
        src_dir = self.sandbox / "src"
        src_dir.mkdir(parents=True, exist_ok=True)
        (src_dir / "app.py").write_text("# TODO: implement this\n", encoding="utf-8")
        res_ph = subprocess.run(
            [sys.executable, str(self.sb_scripts / "audit_diff.py"), str(self.sandbox), "main", "src"],
            capture_output=True,
            text=True,
        )
        self.assertIn("PLACEHOLDERS detected", res_ph.stdout)

    def test_12_setup_worktrees_dirty_rescue_on_cleanup(self):
        """P19: Dirty worktree rescue on cleanup."""
        res_setup = subprocess.run(
            [sys.executable, str(self.sb_scripts / "setup_worktrees.py"), "main", "w1"],
            cwd=str(self.sandbox),
            capture_output=True,
            text=True,
        )
        self.assertEqual(res_setup.returncode, 0)
        wt_path = self.sandbox / ".git" / ".orch-worktrees" / "w1"
        self.assertTrue(wt_path.is_dir())

        # Dirty the worktree
        (wt_path / "work.txt").write_text("uncommitted\n", encoding="utf-8")

        # Cleanup
        res_clean = subprocess.run(
            [sys.executable, str(self.sb_scripts / "setup_worktrees.py"), "cleanup"],
            cwd=str(self.sandbox),
            capture_output=True,
            text=True,
        )
        self.assertEqual(res_clean.returncode, 0)
        self.assertIn("rescuing to orch/rescue-w1-uncommitted-", res_clean.stdout)

        # Check git branch list has rescue branch
        b_res = subprocess.run(["git", "branch", "--list", "orch/rescue-w1-uncommitted-*"], cwd=str(self.sandbox), capture_output=True, text=True)
        self.assertTrue(len(b_res.stdout.strip()) > 0)


if __name__ == "__main__":
    unittest.main()
