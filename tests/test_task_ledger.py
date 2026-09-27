#!/usr/bin/env python3
"""
Unit tests for scripts/task_ledger.py (Task T4 / Release B Live Task Flow)
"""

import os
import sys
import json
import tempfile
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

try:
    import task_ledger
except ImportError:
    task_ledger = None

class TestTaskLedger(unittest.TestCase):
    def setUp(self):
        if task_ledger is None:
            self.fail("scripts/task_ledger.py not implemented yet (RED phase)")
        self.test_dir = tempfile.TemporaryDirectory()
        self.evidence_dir = os.path.join(self.test_dir.name, ".evidence")
        os.makedirs(self.evidence_dir, exist_ok=True)
        self.ledger_file = os.path.join(self.evidence_dir, "tasks.json")

    def tearDown(self):
        self.test_dir.cleanup()

    def test_init_and_add_tasks(self):
        ledger = task_ledger.TaskLedger(self.ledger_file)
        ledger.init_ledger("Skills Evolution Sprint")
        
        ledger.add_task(task_id="T1", title="Setup Contracts", owner="Coordinator", depends_on=[])
        ledger.add_task(task_id="T2", title="Implement Worker", owner="Worker_A", depends_on=["T1"])

        data = ledger.load()
        self.assertEqual(data["plan_title"], "Skills Evolution Sprint")
        self.assertEqual(len(data["tasks"]), 2)
        self.assertEqual(data["tasks"][0]["id"], "T1")
        self.assertEqual(data["tasks"][0]["status"], "Pending")

    def test_state_transitions(self):
        ledger = task_ledger.TaskLedger(self.ledger_file)
        ledger.init_ledger("Test Transitions")
        ledger.add_task(task_id="T1", title="Build Feature", owner="Worker_A")

        # Pending -> Running
        ledger.update_task("T1", status="Running", detail="Compiling modules")
        t = ledger.get_task("T1")
        self.assertEqual(t["status"], "Running")
        self.assertEqual(t["detail"], "Compiling modules")

        # Running -> Verifying
        ledger.update_task("T1", status="Verifying", detail="Running test suite")
        t = ledger.get_task("T1")
        self.assertEqual(t["status"], "Verifying")

        # Verifying -> Done
        ledger.update_task("T1", status="Done", detail="All tests pass", evidence_ref="rcpt_12345")
        t = ledger.get_task("T1")
        self.assertEqual(t["status"], "Done")
        self.assertEqual(t["evidence_ref"], "rcpt_12345")

    def test_markdown_rendering(self):
        ledger = task_ledger.TaskLedger(self.ledger_file)
        ledger.init_ledger("Markdown Render Test")
        ledger.add_task("T1", "Task 1", owner="Coordinator")
        ledger.update_task("T1", status="Done", detail="Finished")
        ledger.add_task("T2", "Task 2", owner="Worker_B", depends_on=["T1"])
        ledger.update_task("T2", status="Running", detail="In progress")

        md = ledger.render_markdown()
        self.assertIn("| T1 | Task 1 | Done | Coordinator | Finished |", md)
        self.assertIn("| T2 | Task 2 | Running | Worker_B | In progress |", md)
        self.assertIn("1 of 2 tasks complete", md)

if __name__ == "__main__":
    unittest.main()
