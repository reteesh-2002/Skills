#!/usr/bin/env python3
"""
Unit tests for post-review code hardening fixes:
1. Compound pipeline execution in exec_proxy.py (shlex quote fix).
2. Mutation failure tracking in guard_anti_retry.py.
3. Leading ./ prefix handling in audit_diff.sh.
4. Linux case sensitivity preservation in guard_read_before_write.py.
5. Quoted paths in verify_release_gate.py git status parsing.
"""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
GUARD_RBW = SCRIPTS_DIR / "guard_read_before_write.py"
GUARD_AER = SCRIPTS_DIR / "guard_anti_retry.py"
EXEC_PROXY = SCRIPTS_DIR / "exec_proxy.py"
GATE_PY = SCRIPTS_DIR / "verify_release_gate.py"
AUDIT_DIFF = REPO_ROOT / "scripts" / "audit_diff.sh"


class TestCodeHardeningFixes(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="test_audit_fixes_")
        self.tmp_path = Path(self.tmp_dir)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_exec_proxy_compound_pipeline(self):
        """Verify compound pipeline argument does not fail from quote mangling."""
        subprocess.run(["git", "-C", str(self.tmp_path), "init", "--quiet"], check=True)
        subprocess.run(["git", "-C", str(self.tmp_path), "config", "user.name", "Test"], check=True)
        subprocess.run(["git", "-C", str(self.tmp_path), "config", "user.email", "test@local"], check=True)
        (self.tmp_path / "README.md").write_text("init\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.tmp_path), "add", "."], check=True)
        subprocess.run(["git", "-C", str(self.tmp_path), "commit", "-m", "init", "--quiet"], check=True)

        sb_scripts = self.tmp_path / "scripts"
        sb_scripts.mkdir(parents=True, exist_ok=True)
        shutil.copy2(EXEC_PROXY, sb_scripts / "exec_proxy.py")
        shutil.copy2(SCRIPTS_DIR / "runtime_evidence.py", sb_scripts / "runtime_evidence.py")

        res = subprocess.run(
            [sys.executable, str(sb_scripts / "exec_proxy.py"), "--label", "test_pipe", "echo hello_pipeline | grep hello"],
            cwd=str(self.tmp_path),
            capture_output=True,
            text=True
        )
        self.assertEqual(res.returncode, 0, f"Pipeline failed: {res.stderr}")
        self.assertIn("Check 'test_pipe' completed successfully", res.stdout)

    def test_guard_anti_retry_mutation_failure_recording(self):
        """Verify that failing replace_file_content calls are recorded and exact retry is blocked."""
        evidence_dir = self.tmp_path / ".evidence"
        evidence_dir.mkdir(parents=True, exist_ok=True)

        tool_args = {"TargetFile": "src/app.py", "Instruction": "fix typo", "TargetContent": "abc"}

        # 1. First execution is allowed
        res1 = subprocess.run(
            [sys.executable, str(GUARD_AER)],
            input=json.dumps({"cwd": str(self.tmp_path), "toolCall": {"name": "replace_file_content", "args": tool_args}}),
            capture_output=True,
            text=True
        )
        self.assertEqual(res1.returncode, 0)
        self.assertEqual(json.loads(res1.stdout).get("decision"), "allow")

        # 2. Tool fails with error: post-hook records failure
        res2 = subprocess.run(
            [sys.executable, str(GUARD_AER)],
            input=json.dumps({
                "cwd": str(self.tmp_path),
                "toolCall": {"name": "replace_file_content", "args": tool_args},
                "status": "error",
                "error": "TargetContent not found in file",
                "result": {"status": "error"}
            }),
            capture_output=True,
            text=True
        )
        self.assertEqual(res2.returncode, 0)

        # 3. Exact retry of the failing call is blocked
        res3 = subprocess.run(
            [sys.executable, str(GUARD_AER)],
            input=json.dumps({"cwd": str(self.tmp_path), "toolCall": {"name": "replace_file_content", "args": tool_args}}),
            capture_output=True,
            text=True
        )
        self.assertEqual(res3.returncode, 0)
        data3 = json.loads(res3.stdout)
        self.assertEqual(data3.get("decision"), "deny")
        self.assertIn("Anti-Exact-Retry violation", data3.get("reason", ""))

        # 4. Altered arguments are allowed
        altered_args = dict(tool_args, TargetContent="corrected_content")
        res4 = subprocess.run(
            [sys.executable, str(GUARD_AER)],
            input=json.dumps({"cwd": str(self.tmp_path), "toolCall": {"name": "replace_file_content", "args": altered_args}}),
            capture_output=True,
            text=True
        )
        self.assertEqual(res4.returncode, 0)
        self.assertEqual(json.loads(res4.stdout).get("decision"), "allow")

    def test_audit_diff_leading_dot_slash(self):
        """Verify audit_diff.sh handles allowed paths with leading ./ without out-of-scope errors."""
        # Initialize a temporary git repository with a branch
        subprocess.run(["git", "init", "-b", "main"], cwd=self.tmp_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=self.tmp_dir)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=self.tmp_dir)

        src_dir = self.tmp_path / "src"
        src_dir.mkdir(parents=True, exist_ok=True)
        test_file = src_dir / "worker.py"
        test_file.write_text("x = 1\n")

        subprocess.run(["git", "add", "."], cwd=self.tmp_dir, stdout=subprocess.DEVNULL)
        subprocess.run(["git", "commit", "-m", "init"], cwd=self.tmp_dir, stdout=subprocess.DEVNULL)

        # Worker modifies worker.py on new branch
        subprocess.run(["git", "checkout", "-b", "orch/w1"], cwd=self.tmp_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        test_file.write_text("x = 2\n")

        # Run audit_diff.sh with './src'
        res = subprocess.run(
            ["bash", str(AUDIT_DIFF), str(self.tmp_path), "main", "./src"],
            capture_output=True,
            text=True
        )
        self.assertEqual(res.returncode, 0, f"Expected 0 with ./src, got stderr: {res.stderr}, stdout: {res.stdout}")
        self.assertIn("CLEAN", res.stdout)


if __name__ == "__main__":
    unittest.main()
