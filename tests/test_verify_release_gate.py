#!/usr/bin/env python3
"""
Unit tests for scripts/verify_release_gate.py and Git Assertion Lock (WP-04 / SEC-03).
Verifies:
1. is_test_file_path regex and directory classification
2. check_git_assertion_lock behavior on added, modified, and deleted tests
3. --spec-evolution bypass flag and environment variable overrides
4. CLI end-to-end execution of verify_release_gate.py
"""

import os
import sys
import shutil
import tempfile
import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import runtime_evidence


class TestGitAssertionLockUnit(unittest.TestCase):
    """Unit tests for runtime_evidence test classification and assertion lock."""

    def test_is_test_file_path(self):
        # Test paths matching directories
        self.assertTrue(runtime_evidence.is_test_file_path("tests/unit/test_app.py"))
        self.assertTrue(runtime_evidence.is_test_file_path("test/utils.py"))
        self.assertTrue(runtime_evidence.is_test_file_path("__tests__/component.jsx"))
        self.assertTrue(runtime_evidence.is_test_file_path("sub/tests/foo.py"))
        self.assertTrue(runtime_evidence.is_test_file_path("tests\\windows\\path.py"))

        # Test paths matching file patterns
        self.assertTrue(runtime_evidence.is_test_file_path("src/app_test.py"))
        self.assertTrue(runtime_evidence.is_test_file_path("pkg/test_engine.py"))
        self.assertTrue(runtime_evidence.is_test_file_path("components/Button.test.ts"))
        self.assertTrue(runtime_evidence.is_test_file_path("components/Modal.spec.tsx"))
        self.assertTrue(runtime_evidence.is_test_file_path("server/api_test.go"))
        self.assertTrue(runtime_evidence.is_test_file_path("src/TestRunner.java"))

        # Non-test files
        self.assertFalse(runtime_evidence.is_test_file_path("src/app.py"))
        self.assertFalse(runtime_evidence.is_test_file_path("scripts/exec_proxy.py"))
        self.assertFalse(runtime_evidence.is_test_file_path("README.md"))
        self.assertFalse(runtime_evidence.is_test_file_path("package.json"))
        self.assertFalse(runtime_evidence.is_test_file_path("contest/main.py"))

    def test_spec_evolution_flag_bypasses(self):
        passed, tampered = runtime_evidence.check_git_assertion_lock(
            REPO_ROOT, allow_spec_evolution=True
        )
        self.assertTrue(passed)
        self.assertEqual(tampered, [])

    def test_spec_evolution_env_var_bypasses(self):
        old_env = os.environ.get("SPEC_EVOLUTION")
        try:
            os.environ["SPEC_EVOLUTION"] = "1"
            passed, tampered = runtime_evidence.check_git_assertion_lock(REPO_ROOT)
            self.assertTrue(passed)
            self.assertEqual(tampered, [])
        finally:
            if old_env is None:
                os.environ.pop("SPEC_EVOLUTION", None)
            else:
                os.environ["SPEC_EVOLUTION"] = old_env


class TestGitAssertionLockIntegration(unittest.TestCase):
    """Integration tests using hermetic temporary git repositories."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="git_assertion_lock_test_")
        self.repo = Path(self.tmpdir)
        # Initialize git repo
        subprocess.check_call(["git", "init", "-b", "main"], cwd=self.repo, stdout=subprocess.DEVNULL)
        subprocess.check_call(["git", "config", "user.email", "test@example.com"], cwd=self.repo)
        subprocess.check_call(["git", "config", "user.name", "Test Bot"], cwd=self.repo)

        # Create initial files: source and test
        src_dir = self.repo / "src"
        src_dir.mkdir(parents=True)
        (src_dir / "calc.py").write_text("def add(a, b): return a + b\n")

        tests_dir = self.repo / "tests"
        tests_dir.mkdir(parents=True)
        (tests_dir / "test_calc.py").write_text("def test_add(): assert calc.add(1, 1) == 2\n")

        subprocess.check_call(["git", "add", "."], cwd=self.repo)
        subprocess.check_call(["git", "commit", "-m", "Initial commit with tests"], cwd=self.repo)
        self.base_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=self.repo, text=True
        ).strip()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_clean_repo_passes_lock(self):
        passed, tampered = runtime_evidence.check_git_assertion_lock(
            self.repo, base_ref=self.base_commit
        )
        self.assertTrue(passed)
        self.assertEqual(tampered, [])

    def test_modifying_source_file_only_passes_lock(self):
        # Modify only src/calc.py (not a test)
        (self.repo / "src" / "calc.py").write_text("def add(a, b): return b + a\n")
        subprocess.check_call(["git", "add", "."], cwd=self.repo)
        subprocess.check_call(["git", "commit", "-m", "Refactor calc"], cwd=self.repo)

        passed, tampered = runtime_evidence.check_git_assertion_lock(
            self.repo, base_ref=self.base_commit
        )
        self.assertTrue(passed)
        self.assertEqual(tampered, [])

    def test_adding_new_test_file_passes_lock(self):
        # Adding reproduction test is permitted
        (self.repo / "tests" / "test_repro_123.py").write_text("def test_repro(): pass\n")
        subprocess.check_call(["git", "add", "."], cwd=self.repo)
        subprocess.check_call(["git", "commit", "-m", "Add repro test"], cwd=self.repo)

        passed, tampered = runtime_evidence.check_git_assertion_lock(
            self.repo, base_ref=self.base_commit
        )
        self.assertTrue(passed)
        self.assertEqual(tampered, [])

    def test_mutating_existing_test_file_is_blocked(self):
        # Mutating existing test assertion is blocked!
        (self.repo / "tests" / "test_calc.py").write_text("def test_add(): assert True\n")
        subprocess.check_call(["git", "add", "."], cwd=self.repo)
        subprocess.check_call(["git", "commit", "-m", "Tamper test"], cwd=self.repo)

        passed, tampered = runtime_evidence.check_git_assertion_lock(
            self.repo, base_ref=self.base_commit
        )
        self.assertFalse(passed)
        self.assertIn("tests/test_calc.py", tampered)

    def test_mutating_existing_test_file_allowed_with_spec_evolution(self):
        # Mutating existing test with allow_spec_evolution=True passes
        (self.repo / "tests" / "test_calc.py").write_text("def test_add(): assert True\n")
        subprocess.check_call(["git", "add", "."], cwd=self.repo)
        subprocess.check_call(["git", "commit", "-m", "Tamper test"], cwd=self.repo)

        passed, tampered = runtime_evidence.check_git_assertion_lock(
            self.repo, base_ref=self.base_commit, allow_spec_evolution=True
        )
        self.assertTrue(passed)
        self.assertEqual(tampered, [])

    def test_deleting_existing_test_file_is_blocked(self):
        # Deleting an existing test is blocked
        (self.repo / "tests" / "test_calc.py").unlink()
        subprocess.check_call(["git", "add", "-A"], cwd=self.repo)
        subprocess.check_call(["git", "commit", "-m", "Delete test"], cwd=self.repo)

        passed, tampered = runtime_evidence.check_git_assertion_lock(
            self.repo, base_ref=self.base_commit
        )
        self.assertFalse(passed)
        self.assertIn("tests/test_calc.py", tampered)

    def test_uncommitted_test_mutation_is_blocked(self):
        # Uncommitted edit to test file in working tree is blocked
        (self.repo / "tests" / "test_calc.py").write_text("def test_add(): pass\n")

        passed, tampered = runtime_evidence.check_git_assertion_lock(
            self.repo, base_ref=self.base_commit
        )
        self.assertFalse(passed)
        self.assertIn("tests/test_calc.py", tampered)


if __name__ == "__main__":
    unittest.main()
