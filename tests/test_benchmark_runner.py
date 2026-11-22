#!/usr/bin/env python3
"""
Unit tests for tests/benchmark_comparison.py (Task T2 / Acceptance B-01, B-02)
"""

import os
import sys
import unittest
import tempfile

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "tests"))

try:
    import benchmark_comparison
except ImportError:
    benchmark_comparison = None

class TestBenchmarkHarness(unittest.TestCase):
    def setUp(self):
        if benchmark_comparison is None:
            self.fail("tests/benchmark_comparison.py not imported")

    def test_task_definitions_exist(self):
        tasks = benchmark_comparison.BENCHMARK_TASKS
        self.assertGreaterEqual(len(tasks), 3)
        for t in tasks:
            self.assertIn("id", t)
            self.assertIn("name", t)
            self.assertIn("test_command", t)

    def test_run_real_task_execution(self):
        """B-01: Verifies that a real task execution produces real code execution and measurable outcome."""
        res = benchmark_comparison.execute_real_task_trial(
            task_id="TASK_A_BUGFIX",
            suite_name="Repaired Antigravity Suite"
        )
        self.assertTrue(res["success"])
        self.assertGreater(res["elapsed_seconds"], 0)
        self.assertIn("log_file", res)
        self.assertTrue(os.path.exists(res["log_file"]))

    def test_negative_scoring_on_failing_solution(self):
        """B-02: Verifies that an intentionally failing solution is scored as failure."""
        res = benchmark_comparison.execute_real_task_trial(
            task_id="TASK_A_BUGFIX",
            suite_name="Repaired Antigravity Suite",
            inject_defect=True
        )
        self.assertFalse(res["success"])

    def test_audit_trial_rejects_unknown_task(self):
        """T12: audit_trial.py must exit with code 1 when given an unsupported task."""
        import subprocess
        audit_script = os.path.join(REPO_ROOT, "benchmarks", "audit_trial.py")
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl") as f:
            f.write("{}\n")
            f.flush()
            res = subprocess.run([sys.executable, audit_script, "--transcript", f.name, "--task", "UNKNOWN_TASK"],
                                 capture_output=True, text=True)
            self.assertEqual(res.returncode, 1)
            self.assertIn("Unsupported benchmark task", res.stdout)

    def test_audit_trial_propagates_audit_failure_exit_code(self):
        """T12: audit_trial.py must exit with code 1 when transcript audit fails."""
        import subprocess
        audit_script = os.path.join(REPO_ROOT, "benchmarks", "audit_trial.py")
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl") as f:
            # Empty transcript fails audit
            f.write("")
            f.flush()
            res = subprocess.run([sys.executable, audit_script, "--transcript", f.name, "--task", "FLAG-01"],
                                 capture_output=True, text=True)
            self.assertEqual(res.returncode, 1)
            self.assertIn("FAIL", res.stdout)

    def test_run_real_benchmark_rejects_unsupported_task(self):
        """T12: run_real_benchmark.py must exit with code 1 when requested task does not exist."""
        import subprocess
        bench_script = os.path.join(REPO_ROOT, "tests", "run_real_benchmark.py")
        res = subprocess.run([sys.executable, bench_script, "--task", "FLAG-999"],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 1)
        self.assertIn("not found", res.stdout)

    def test_run_real_benchmark_list_succeeds(self):
        """T12: run_real_benchmark.py --list must succeed with exit code 0."""
        import subprocess
        bench_script = os.path.join(REPO_ROOT, "tests", "run_real_benchmark.py")
        res = subprocess.run([sys.executable, bench_script, "--list"],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("FLAG-01", res.stdout)


if __name__ == "__main__":
    unittest.main()
