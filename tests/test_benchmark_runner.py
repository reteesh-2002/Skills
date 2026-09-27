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

if __name__ == "__main__":
    unittest.main()
