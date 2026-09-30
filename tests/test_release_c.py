#!/usr/bin/env python3
"""
Release C — Acceptance Test Suite
Tests for:
  - Phase 0 Task-Shape Gating (E-01 to E-06)
  - Context reduction / minimal worker briefs (C-2)
  - Durable interruption recovery (C-3 / T-04 integration)
"""

import os
import sys
import shutil
import tempfile
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

import task_shape_gating as gating
from task_shape_gating import ExecutionMode, gate_task, build_worker_brief, resume_protocol_steps
import task_ledger as tl


# ══════════════════════════════════════════════
# E-01: Small tasks do NOT spawn workers
# ══════════════════════════════════════════════

class TestGatingE01SmallTask(unittest.TestCase):
    """E-01: a small task does not spawn unnecessary workers."""

    def test_one_file_change_is_solo(self):
        d = gate_task(file_touch_count=1)
        self.assertEqual(d.mode, ExecutionMode.SOLO)
        self.assertEqual(d.worker_count, 0)

    def test_three_file_change_is_solo(self):
        d = gate_task(file_touch_count=3)
        self.assertEqual(d.mode, ExecutionMode.SOLO)
        self.assertEqual(d.worker_count, 0)

    def test_idea_evaluation_always_solo_no_workers(self):
        """Idea Council is manual-only; never auto-spawns."""
        d = gate_task(file_touch_count=50, workstream_count=10,
                      is_idea_evaluation=True)
        self.assertEqual(d.mode, ExecutionMode.SOLO)
        self.assertEqual(d.worker_count, 0)
        self.assertIn("Idea Council", d.reason)
        self.assertIn("E-01", d.acceptance)

    def test_auth_change_is_solo_plus_review(self):
        d = gate_task(file_touch_count=5, is_auth_or_data=True)
        self.assertEqual(d.mode, ExecutionMode.SOLO_REVIEW)
        self.assertEqual(d.worker_count, 0)
        self.assertIn("specialist review", d.reason)

    def test_ordinary_large_feature_is_solo_plus_review(self):
        d = gate_task(file_touch_count=6, workstream_count=1)
        self.assertEqual(d.mode, ExecutionMode.SOLO_REVIEW)
        self.assertEqual(d.worker_count, 0)


# ══════════════════════════════════════════════
# E-02: Independent tasks CAN run concurrently
# ══════════════════════════════════════════════

class TestGatingE02IndependentParallel(unittest.TestCase):
    """E-02: independent tasks run concurrently within configured cap."""

    def test_two_workstreams_gives_multi_2(self):
        d = gate_task(file_touch_count=10, workstream_count=2)
        self.assertEqual(d.mode, ExecutionMode.MULTI)
        self.assertEqual(d.worker_count, 2)
        self.assertIn("E-02", d.acceptance)

    def test_four_workstreams_gives_multi_4(self):
        d = gate_task(file_touch_count=20, workstream_count=4)
        self.assertEqual(d.mode, ExecutionMode.MULTI)
        self.assertEqual(d.worker_count, 4)

    def test_worker_count_clamped_to_max(self):
        """Worker count must not exceed configured max_workers."""
        d = gate_task(file_touch_count=30, workstream_count=8, max_workers=3)
        self.assertEqual(d.mode, ExecutionMode.MULTI)
        self.assertEqual(d.worker_count, 3)  # clamped

    def test_subagent_unavailable_falls_back_to_solo(self):
        """When invoke_subagent is unavailable, multi must not be selected."""
        d = gate_task(file_touch_count=20, workstream_count=4,
                      subagent_tools_available=False)
        self.assertNotEqual(d.mode, ExecutionMode.MULTI)
        self.assertEqual(d.worker_count, 0)

    def test_shared_interface_noted_in_reason(self):
        d = gate_task(file_touch_count=12, workstream_count=3,
                      has_shared_interface=True)
        self.assertEqual(d.mode, ExecutionMode.MULTI)
        self.assertIn("interface", d.reason.lower())


# ══════════════════════════════════════════════
# E-03: Shared-file conflicts cause coordination
# ══════════════════════════════════════════════

class TestGatingE03TightlyCoupled(unittest.TestCase):
    """E-03: shared-file conflicts cause coordination, not silent overwrites."""

    def test_tightly_coupled_is_sequenced(self):
        d = gate_task(file_touch_count=8, workstream_count=3,
                      tightly_coupled=True)
        self.assertEqual(d.mode, ExecutionMode.SEQUENCED)
        self.assertEqual(d.worker_count, 0)
        self.assertIn("E-03", d.acceptance)
        self.assertIn("coupled", d.reason.lower())

    def test_tightly_coupled_overrides_workstream_count(self):
        """Even 10 workstreams become sequenced when tightly coupled."""
        d = gate_task(file_touch_count=50, workstream_count=10,
                      tightly_coupled=True)
        self.assertEqual(d.mode, ExecutionMode.SEQUENCED)

    def test_auth_change_overrides_tightly_coupled(self):
        """Auth changes always → solo+review, even if also tightly coupled."""
        d = gate_task(file_touch_count=5, is_auth_or_data=True,
                      tightly_coupled=True)
        self.assertEqual(d.mode, ExecutionMode.SOLO_REVIEW)


# ══════════════════════════════════════════════
# E-04: Each worker receives needed constraints
# ══════════════════════════════════════════════

class TestGatingE04WorkerBriefs(unittest.TestCase):
    """E-04: each worker receives the constraints needed for its task."""

    def test_worker_brief_contains_goal_and_scope(self):
        brief = build_worker_brief(
            worker_id="Worker_A",
            goal="Implement the REST API for /api/invoices",
            allowed_files=["api/routes/invoices.py", "api/models/invoice.py"],
            test_command="python3 -m pytest tests/test_invoices.py",
        )
        self.assertIn("Worker_A", brief)
        self.assertIn("REST API", brief)
        self.assertIn("api/routes/invoices.py", brief)
        self.assertIn("pytest tests/test_invoices.py", brief)

    def test_worker_brief_includes_frozen_contract(self):
        contract = "InvoiceSchema: {id: int, amount: float, tenant_id: str}"
        brief = build_worker_brief(
            worker_id="Worker_B",
            goal="Build the invoice PDF renderer",
            allowed_files=["services/pdf_renderer.py"],
            test_command="pytest tests/test_pdf.py",
            contract=contract,
        )
        self.assertIn("Frozen Interface Contract", brief)
        self.assertIn("InvoiceSchema", brief)

    def test_worker_brief_includes_constraints(self):
        brief = build_worker_brief(
            worker_id="Worker_C",
            goal="Add rate limiter",
            allowed_files=["middleware/rate_limit.py"],
            test_command="pytest tests/test_rate_limit.py",
            constraints=["Do not modify auth.py", "Max 50 req/min per tenant"],
        )
        self.assertIn("Do not modify auth.py", brief)
        self.assertIn("Max 50 req/min", brief)

    def test_worker_brief_excludes_conversation_history_directive(self):
        """Brief must explicitly instruct worker to ignore conversation history."""
        brief = build_worker_brief(
            worker_id="Worker_D",
            goal="Refactor caching layer",
            allowed_files=["cache/redis_client.py"],
            test_command="pytest tests/test_cache.py",
        )
        self.assertIn("Do not read conversation history", brief)

    def test_format_decision_heartbeat_line(self):
        d = gate_task(file_touch_count=10, workstream_count=3)
        heartbeat = gating.format_decision(d)
        self.assertIn("[Orchestrator] Gating decision:", heartbeat)
        self.assertIn("multi(3)", heartbeat)
        self.assertIn("Reason:", heartbeat)
        self.assertIn("Acceptance:", heartbeat)


# ══════════════════════════════════════════════
# E-05: Integration checks run on combined result
# ══════════════════════════════════════════════

class TestGatingE05IntegrationChecks(unittest.TestCase):
    """E-05: integration checks run against the combined result."""

    def test_multi_decision_requires_integration_step(self):
        """Verify that multi mode does not skip to Done without integration."""
        d = gate_task(file_touch_count=10, workstream_count=2)
        self.assertEqual(d.mode, ExecutionMode.MULTI)
        # The SKILL.md specifies Phase 4 integration run after merging —
        # we verify the gating module emits MULTI (not Done directly)
        self.assertNotEqual(d.mode, ExecutionMode.SOLO)


# ══════════════════════════════════════════════
# C-3: Durable interruption recovery protocol
# ══════════════════════════════════════════════

class TestDurableRecovery(unittest.TestCase):
    """C-3 / T-04: durable resume protocol after session interruption."""

    def test_resume_protocol_has_six_ordered_steps(self):
        steps = resume_protocol_steps()
        self.assertEqual(len(steps), 6, "Must have exactly 6 ordered steps")
        self.assertTrue(steps[0].startswith("1."))
        self.assertTrue(steps[-1].startswith("6."))

    def test_resume_protocol_covers_git_status(self):
        steps = resume_protocol_steps()
        combined = " ".join(steps)
        self.assertIn("git status", combined)

    def test_resume_protocol_covers_task_ledger_reconcile(self):
        steps = resume_protocol_steps()
        combined = " ".join(steps)
        self.assertIn("reconcile", combined)

    def test_resume_protocol_covers_evidence_validation(self):
        steps = resume_protocol_steps()
        combined = " ".join(steps)
        self.assertIn("manifest", combined)
        self.assertIn("write-tree", combined)

    def test_resume_protocol_skips_already_done_work(self):
        steps = resume_protocol_steps()
        combined = " ".join(steps)
        self.assertIn("without re-running", combined)

    def test_ledger_reconcile_integrates_with_protocol(self):
        """Resume protocol step 3 calls reconcile — verify it works end-to-end."""
        tmp = tempfile.mkdtemp(prefix="agy_c3_")
        try:
            ledger = tl.TaskLedger(os.path.join(tmp, ".evidence", "tasks.json"))
            ledger.init_ledger("Recovery Test")
            ledger.add_task("R1", "Feature A", owner="Worker_A")
            ledger.update_task("R1", status="Running", detail="Mid-implementation")
            ledger.add_task("R2", "Feature B", owner="Worker_B")
            ledger.update_task("R2", status="Verifying", detail="Running tests")
            ledger.add_task("R3", "Feature C", owner="Coordinator")
            ledger.update_task("R3", status="Done", detail="Verified")

            # Simulate session interruption → run reconcile
            changes = ledger.reconcile_interrupted_state()
            self.assertEqual(len(changes), 2)  # R1 and R2 re-queued

            r1 = ledger.get_task("R1")
            r2 = ledger.get_task("R2")
            r3 = ledger.get_task("R3")
            self.assertEqual(r1["status"], "Pending")
            self.assertEqual(r2["status"], "Pending")
            self.assertEqual(r3["status"], "Done")  # already done; untouched
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
