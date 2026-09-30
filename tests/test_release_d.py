#!/usr/bin/env python3
"""
Release D — Acceptance Test Suite
Verifies specialist skill verification probes:
  - Frontend Artisan: WCAG AA contrast & viewport overflow detection
  - Schema Craft: Disposable database migration rehearsal & idempotency
  - Security Verifier: Synthetic dual-tenant IDOR boundary probe
  - Runtime Reliability: Graceful drain & memory soak plateau
  - Deep Debugger & Ship-It: Rollback protection & readiness separation invariants
"""

import os
import sys
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

import specialist_probes as probes


class TestFrontendArtisanProbes(unittest.TestCase):
    """Frontend Artisan verification hardening."""

    def test_wcag_contrast_high_contrast_passes(self):
        # Pure white on pure black -> 21.0:1
        res = probes.verify_wcag_aa("#ffffff", "#000000")
        self.assertTrue(res["passed"])
        self.assertGreaterEqual(res["ratio"], 20.0)

    def test_wcag_contrast_subtle_dark_fails_normal_text(self):
        # Dark zinc (#3f3f46) on black (#000000) -> fails 4.5:1
        res = probes.verify_wcag_aa("#3f3f46", "#000000")
        self.assertFalse(res["passed"])
        self.assertLess(res["ratio"], 4.5)

    def test_wcag_contrast_large_text_relaxed_threshold(self):
        # Medium gray (#71717a) on black -> passes 3.0:1 for large text
        res = probes.verify_wcag_aa("#71717a", "#000000", is_large_text=True)
        self.assertTrue(res["passed"])

    def test_viewport_overflow_detects_fixed_pixel_hazard(self):
        html = '<div style="width: 800px;">Fixed broad container</div>'
        res = probes.check_html_viewport_overflow(html, viewports=[375, 768])
        self.assertFalse(res["passed"])
        self.assertGreater(res["hazards_found"], 0)
        self.assertEqual(res["hazards"][0]["hazard"], "fixed_pixel_overflow")

    def test_viewport_overflow_clean_responsive_passes(self):
        html = """
        <!DOCTYPE html>
        <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1"></head>
        <body><div class="w-full max-w-lg mx-auto">Responsive Box</div></body>
        </html>
        """
        res = probes.check_html_viewport_overflow(html)
        self.assertTrue(res["passed"])
        self.assertEqual(res["hazards_found"], 0)


class TestSchemaCraftProbes(unittest.TestCase):
    """Schema Craft migration rehearsal engine."""

    def test_migration_rehearsal_clean_cycle(self):
        up_sql = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            email TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL
        );
        CREATE TABLE posts (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE INDEX idx_posts_user_id ON posts(user_id);
        """
        down_sql = """
        DROP INDEX IF EXISTS idx_posts_user_id;
        DROP TABLE IF EXISTS posts;
        DROP TABLE IF EXISTS users;
        """
        seed_sql = """
        INSERT INTO users (id, email, created_at) VALUES (1, 'alice@example.com', '2026-09-30');
        INSERT INTO posts (id, user_id, title) VALUES (10, 1, 'Hello World');
        """
        verify_query = "SELECT u.email, p.title FROM users u JOIN posts p ON u.id = p.user_id;"

        res = probes.rehearse_sqlite_migration(up_sql, down_sql, seed_sql, verify_query)
        self.assertTrue(res["passed"], f"Rehearsal failed: {res.get('errors')}")
        self.assertTrue(res["up_phase"])
        self.assertTrue(res["seed_phase"])
        self.assertTrue(res["verify_query_phase"])
        self.assertTrue(res["down_phase"])
        self.assertTrue(res["idempotency_phase"])
        self.assertIn("users", res["tables_created"])
        self.assertIn("posts", res["tables_created"])

    def test_migration_rehearsal_catches_broken_down_migration(self):
        up_sql = "CREATE TABLE orders (id INTEGER PRIMARY KEY, total REAL);"
        # Intentionally broken DOWN migration (drops wrong table)
        down_sql = "DROP TABLE IF EXISTS non_existent_table;"

        res = probes.rehearse_sqlite_migration(up_sql, down_sql)
        self.assertFalse(res["passed"])
        self.assertFalse(res["down_phase"])


class TestSecurityVerifierProbes(unittest.TestCase):
    """Security Verifier dual-tenant IDOR probes."""

    def test_idor_probe_secure_endpoint_passes(self):
        # Database / storage mock
        invoices = {
            "inv_tenant_b": {"tenant_id": "tenant_b", "amount": 5000}
        }

        # Secure access handler enforcing tenant boundary
        def secure_handler(auth_context, resource_id):
            doc = invoices.get(resource_id)
            if not doc:
                return (404, None)
            if doc["tenant_id"] != auth_context.get("tenant_id"):
                return (403, {"error": "Forbidden: Tenant isolation"})
            return (200, doc)

        res = probes.probe_tenant_isolation(
            access_fn=secure_handler,
            tenant_a_auth={"tenant_id": "tenant_a"},
            tenant_b_auth={"tenant_id": "tenant_b"},
            tenant_b_resource_id="inv_tenant_b"
        )
        self.assertTrue(res["passed"])
        self.assertFalse(res["data_leaked"])
        self.assertEqual(res["tenant_a_probe_status"], 403)

    def test_idor_probe_leaky_endpoint_fails(self):
        invoices = {
            "inv_tenant_b": {"tenant_id": "tenant_b", "amount": 5000}
        }

        # Vulnerable handler with BOLA / IDOR defect (ignores tenant_id)
        def leaky_handler(auth_context, resource_id):
            doc = invoices.get(resource_id)
            if not doc:
                return (404, None)
            return (200, doc)

        res = probes.probe_tenant_isolation(
            access_fn=leaky_handler,
            tenant_a_auth={"tenant_id": "tenant_a"},
            tenant_b_auth={"tenant_id": "tenant_b"},
            tenant_b_resource_id="inv_tenant_b"
        )
        self.assertFalse(res["passed"])
        self.assertTrue(res["data_leaked"])
        self.assertEqual(res["tenant_a_probe_status"], 200)


class TestRuntimeReliabilityProbes(unittest.TestCase):
    """Runtime Reliability lifecycle and soak probes."""

    def test_graceful_drain_clean_drain(self):
        # All tasks finish cleanly
        def mock_worker(task_id):
            return True

        res = probes.probe_graceful_drain(mock_worker, in_flight_tasks=15)
        self.assertTrue(res["passed"])
        self.assertEqual(res["completed"], 15)
        self.assertEqual(res["aborted"], 0)

    def test_graceful_drain_catches_aborted_tasks(self):
        # Tasks fail during abrupt termination
        def flaky_worker(task_id):
            return task_id % 2 == 0

        res = probes.probe_graceful_drain(flaky_worker, in_flight_tasks=10)
        self.assertFalse(res["passed"])
        self.assertGreater(res["aborted"], 0)

    def test_memory_soak_plateaus_on_clean_operations(self):
        # Clean stateless operations
        def clean_op():
            x = [i * 2 for i in range(50)]
            _ = sum(x)

        res = probes.probe_memory_soak_plateau(clean_op, iterations=1000, sample_interval=200)
        self.assertTrue(res["passed"])
        self.assertTrue(res["plateau"])


class TestSkillDocumentationInvariants(unittest.TestCase):
    """Deep Debugger & Ship-It behavioral invariants."""

    def test_deep_debugger_protects_unrelated_user_edits(self):
        skill_path = os.path.join(REPO_ROOT, "deep-debugger", "SKILL.md")
        with open(skill_path) as f:
            content = f.read()
        self.assertIn("Never touch working files outside the failure path", content)
        self.assertIn("Blast Radius Check", content)

    def test_ship_it_separates_readiness_from_permission(self):
        skill_path = os.path.join(REPO_ROOT, "ship-it", "SKILL.md")
        with open(skill_path) as f:
            content = f.read()
        self.assertIn("Deterministic Release Gate Evaluation", content)
        self.assertIn("verify-release-gate.sh", content)
        self.assertIn("Fail-Closed Rule", content)


if __name__ == "__main__":
    unittest.main(verbosity=2)
