#!/usr/bin/env python3
"""
Acceptance Test Suite for T08b & T09b:
- T08b: Specialist Probes hardening:
  - probe_graceful_drain_subprocess: clean shutdown & timeout abort
  - probe_memory_soak_plateau: use_rss=True, 0 iterations unverified, memory leak detection
  - check_html_viewport_overflow: heuristic=True labels on return & hazards
- T09b: Task Ledger enhancements:
  - validate_dependencies: missing dependencies & dependency cycles
  - load: corrupt ledger preservation to .corrupt.<ts> & last_load_error recording
  - init_ledger: session_id tracking & get_session_id()
"""

import os
import sys
import glob
import json
import tempfile
import unittest
from unittest import mock

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

import specialist_probes as probes
import task_ledger


class TestT08bSpecialistProbes(unittest.TestCase):
    """T08b specialist probe hardening tests."""

    def test_subprocess_graceful_drain_clean_shutdown(self):
        """probe_graceful_drain_subprocess cleanly drains a child process handling SIGTERM."""
        res = probes.probe_graceful_drain_subprocess(drain_timeout_ms=1000)
        self.assertTrue(res["passed"])
        self.assertEqual(res["completed"], 1)
        self.assertEqual(res["aborted"], 0)
        self.assertIn("VERIFIED", res["verdict"])

    def test_subprocess_graceful_drain_timeout_abort(self):
        """probe_graceful_drain_subprocess aborts and terminates a hanging child past deadline."""
        hanging_cmd = [
            sys.executable,
            "-c",
            "import time, signal; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(10)"
        ]
        res = probes.probe_graceful_drain_subprocess(cmd=hanging_cmd, drain_timeout_ms=100)
        self.assertFalse(res["passed"])
        self.assertEqual(res["completed"], 0)
        self.assertEqual(res["aborted"], 1)
        self.assertIn("DRAIN FAILURE", res["verdict"])

    def test_memory_soak_zero_iterations_returns_unverified(self):
        """probe_memory_soak_plateau returns unverified when iterations <= 0."""
        res_zero = probes.probe_memory_soak_plateau(lambda: None, iterations=0)
        self.assertFalse(res_zero["passed"])
        self.assertTrue(res_zero.get("unverified"))
        self.assertEqual(res_zero.get("reason"), "Zero iterations - result is unverified")

        res_neg = probes.probe_memory_soak_plateau(lambda: None, iterations=-10)
        self.assertFalse(res_neg["passed"])
        self.assertTrue(res_neg.get("unverified"))
        self.assertEqual(res_neg.get("reason"), "Zero iterations - result is unverified")

    def test_memory_soak_with_use_rss(self):
        """probe_memory_soak_plateau measures RSS when use_rss=True."""
        def clean_op():
            x = [i * 3 for i in range(100)]
            _ = sum(x)

        res = probes.probe_memory_soak_plateau(clean_op, iterations=600, sample_interval=200, use_rss=True)
        self.assertTrue(res["passed"])
        self.assertTrue(res["plateau"])
        self.assertGreaterEqual(len(res["samples"]), 3)
        self.assertIn("rss_kb", res["samples"][0])
        self.assertIsInstance(res["samples"][0]["rss_kb"], int)

    def test_memory_soak_detects_monotonic_object_leak(self):
        """probe_memory_soak_plateau detects non-plateau memory expansion when objects leak."""
        leaky_store = []

        class LeakyItem:
            def __init__(self, val):
                self.val = val

        def leaking_op():
            leaky_store.extend([LeakyItem(i) for i in range(30)])

        res = probes.probe_memory_soak_plateau(leaking_op, iterations=1000, sample_interval=200, use_rss=False)
        self.assertFalse(res["passed"])
        self.assertFalse(res["plateau"])
        self.assertGreaterEqual(res["second_half_growth_rate"], 0.15)
        self.assertIn("MEMORY LEAK DETECTED", res["verdict"])

    def test_memory_soak_detects_rss_leak_via_mock(self):
        """probe_memory_soak_plateau detects RSS expansion when ru_maxrss grows above threshold."""
        with mock.patch("resource.getrusage") as mock_rusage:
            # Simulate growing RSS values across 5 samples
            rss_sequence = [100000, 120000, 150000, 200000, 300000]
            mock_rusage.side_effect = [mock.Mock(ru_maxrss=val) for val in rss_sequence]

            res = probes.probe_memory_soak_plateau(lambda: None, iterations=1000, sample_interval=200, use_rss=True)
            self.assertFalse(res["passed"])
            self.assertFalse(res["plateau"])
            self.assertIn("MEMORY LEAK DETECTED", res["verdict"])

    def test_viewport_overflow_labeled_as_heuristic(self):
        """check_html_viewport_overflow contains heuristic: True on return dict and all hazards."""
        # Clean responsive document
        clean_html = """
        <!DOCTYPE html>
        <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1"></head>
        <body><div class="w-full max-w-md">Safe Content</div></body>
        </html>
        """
        clean_res = probes.check_html_viewport_overflow(clean_html)
        self.assertTrue(clean_res["heuristic"])
        self.assertTrue(clean_res["passed"])

        # Document with hazards
        hazard_html = """
        <html>
        <body>
            <div style="width: 1200px;">Overflow Div</div>
            <div class="w-[600px]">Tailwind Fixed</div>
        </body>
        </html>
        """
        hazard_res = probes.check_html_viewport_overflow(hazard_html)
        self.assertTrue(hazard_res["heuristic"])
        self.assertFalse(hazard_res["passed"])
        self.assertGreater(hazard_res["hazards_found"], 0)
        for h in hazard_res["hazards"]:
            self.assertTrue(h.get("heuristic"), f"Hazard missing heuristic flag: {h}")


class TestT09bTaskLedger(unittest.TestCase):
    """T09b task ledger enhancement tests."""

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.evidence_dir = os.path.join(self.test_dir.name, ".evidence")
        os.makedirs(self.evidence_dir, exist_ok=True)
        self.ledger_file = os.path.join(self.evidence_dir, "tasks.json")

    def tearDown(self):
        self.test_dir.cleanup()

    def test_validate_dependencies_clean(self):
        """validate_dependencies returns empty list when all dependencies are valid and acyclic."""
        ledger = task_ledger.TaskLedger(self.ledger_file)
        ledger.init_ledger("Clean Dependency Sprint")
        ledger.add_task("T1", "Initial setup", depends_on=[])
        ledger.add_task("T2", "Worker implementation", depends_on=["T1"])
        ledger.add_task("T3", "Verification", depends_on=["T2"])

        errs = ledger.validate_dependencies()
        self.assertEqual(errs, [])

    def test_validate_dependencies_detects_missing_dep(self):
        """validate_dependencies detects references to non-existent tasks."""
        ledger = task_ledger.TaskLedger(self.ledger_file)
        ledger.init_ledger("Missing Dependency Sprint")
        ledger.add_task("T1", "Task 1", depends_on=["T_NON_EXISTENT"])
        ledger.add_task("T2", "Task 2", depends_on=["T1", "T_GHOST"])

        errs = ledger.validate_dependencies()
        self.assertEqual(len(errs), 2)
        self.assertIn("Task T1 depends on non-existent task T_NON_EXISTENT", errs)
        self.assertIn("Task T2 depends on non-existent task T_GHOST", errs)

    def test_validate_dependencies_detects_self_cycle(self):
        """validate_dependencies detects self-referencing task cycle."""
        ledger = task_ledger.TaskLedger(self.ledger_file)
        ledger.init_ledger("Self Cycle Sprint")
        ledger.add_task("T1", "Self loop task", depends_on=["T1"])

        errs = ledger.validate_dependencies()
        self.assertTrue(any("Dependency cycle detected: T1 -> T1" in e for e in errs))

    def test_validate_dependencies_detects_mutual_cycle(self):
        """validate_dependencies detects 2-node cycle (A -> B -> A)."""
        ledger = task_ledger.TaskLedger(self.ledger_file)
        ledger.init_ledger("Mutual Cycle Sprint")
        ledger.add_task("T1", "Task A", depends_on=["T2"])
        ledger.add_task("T2", "Task B", depends_on=["T1"])

        errs = ledger.validate_dependencies()
        self.assertTrue(any("Dependency cycle detected:" in e and "T1" in e and "T2" in e for e in errs))

    def test_validate_dependencies_detects_multi_node_cycle(self):
        """validate_dependencies detects 3-node cycle (T1 -> T2 -> T3 -> T1)."""
        ledger = task_ledger.TaskLedger(self.ledger_file)
        ledger.init_ledger("3-Node Cycle Sprint")
        ledger.add_task("T1", "Task 1", depends_on=["T2"])
        ledger.add_task("T2", "Task 2", depends_on=["T3"])
        ledger.add_task("T3", "Task 3", depends_on=["T1"])

        errs = ledger.validate_dependencies()
        self.assertTrue(any("Dependency cycle detected:" in e and "T1" in e and "T2" in e and "T3" in e for e in errs))

    def test_corrupt_ledger_preserved_and_recorded(self):
        """load() preserves corrupt ledger into .corrupt.<ts> and records last_load_error."""
        corrupt_content = '{"plan_title": "Broken JSON", "tasks": [ incomplete'
        with open(self.ledger_file, "w", encoding="utf-8") as f:
            f.write(corrupt_content)

        ledger = task_ledger.TaskLedger(self.ledger_file)
        data = ledger.load()

        # Error must be recorded
        self.assertIsNotNone(ledger.last_load_error)
        self.assertIn("Expecting", ledger.last_load_error)

        # Corrupt file must be preserved
        corrupt_backups = glob.glob(f"{self.ledger_file}.corrupt.*")
        self.assertGreaterEqual(len(corrupt_backups), 1)
        with open(corrupt_backups[0], "r", encoding="utf-8") as bf:
            self.assertEqual(bf.read(), corrupt_content)

        # Fresh structure initialized with backup note
        self.assertIn("backup_note", data)
        self.assertIn("Corrupt ledger backed up to", data["backup_note"])
        self.assertEqual(data["tasks"], [])

    def test_init_ledger_and_get_session_id(self):
        """init_ledger tracks session_id and get_session_id retrieves it."""
        ledger = task_ledger.TaskLedger(self.ledger_file)
        ledger.init_ledger("Session Tracking Sprint", session_id="session-alpha-99")

        self.assertEqual(ledger.get_session_id(), "session-alpha-99")
        data = ledger.load()
        self.assertEqual(data.get("session_id"), "session-alpha-99")
        self.assertEqual(data.get("plan_title"), "Session Tracking Sprint")

    def test_init_ledger_goal_kwarg_and_none_session(self):
        """init_ledger accepts goal parameter and defaults session_id to None."""
        ledger = task_ledger.TaskLedger(self.ledger_file)
        ledger.init_ledger(goal="Autonomous Feature Build")

        self.assertIsNone(ledger.get_session_id())
        data = ledger.load()
        self.assertIsNone(data.get("session_id"))
        self.assertEqual(data.get("plan_title"), "Autonomous Feature Build")


if __name__ == "__main__":
    unittest.main()
