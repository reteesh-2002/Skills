#!/usr/bin/env python3
"""
Unit and integration tests for scripts/slice-guard.py (T2).
Tests mechanical boundary enforcement, contract whitelisting,
file LOC ceilings, and JSON output formatting.
"""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parent.parent
SLICE_GUARD_SCRIPT = REPO_ROOT / "scripts" / "slice-guard.py"


class TestSliceGuard(unittest.TestCase):
    """Test suite for slice-guard.py."""

    def test_clean_vertical_slice_project_passes(self):
        """A project where modules only import from contract passes cleanly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            modules = root / "src" / "modules"
            billing = modules / "billing"
            portfolio = modules / "portfolio"
            billing.mkdir(parents=True)
            portfolio.mkdir(parents=True)

            # Billing slice
            (billing / "contract.ts").write_text("export interface Invoice { id: string; }\n")
            (billing / "service.ts").write_text("export function getInvoice() { return { id: '1' }; }\n")

            # Portfolio slice importing ONLY from billing/contract
            (portfolio / "contract.ts").write_text("export interface Portfolio { id: string; }\n")
            (portfolio / "service.ts").write_text(
                "import { Invoice } from '../billing/contract';\n"
                "export function getPortfolio(): Invoice | null { return null; }\n"
            )

            cmd = [sys.executable, str(SLICE_GUARD_SCRIPT), str(root), "--json"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, f"Expected exit 0, got: {res.stdout}\n{res.stderr}")

            data = json.loads(res.stdout)
            self.assertEqual(data["status"], "pass")
            self.assertEqual(data["modules_checked"], 2)
            self.assertEqual(len(data["violations"]), 0)

    def test_illegal_cross_slice_internal_import_detected(self):
        """Importing from ../billing/service should be blocked with exit 1."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            modules = root / "src" / "modules"
            billing = modules / "billing"
            portfolio = modules / "portfolio"
            billing.mkdir(parents=True)
            portfolio.mkdir(parents=True)

            (billing / "contract.ts").write_text("export interface Invoice { id: string; }\n")
            (billing / "service.ts").write_text("export function calculateTax() { return 10; }\n")

            # Illegal import from billing/service
            (portfolio / "service.ts").write_text(
                "import { calculateTax } from '../billing/service';\n"
                "export function run() { return calculateTax(); }\n"
            )

            cmd = [sys.executable, str(SLICE_GUARD_SCRIPT), str(root), "--json"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(res.returncode, 1, f"Expected exit 1, got 0:\n{res.stdout}")

            data = json.loads(res.stdout)
            self.assertEqual(data["status"], "fail")
            self.assertGreaterEqual(len(data["violations"]), 1)
            v = data["violations"][0]
            self.assertEqual(v["type"], "illegal_cross_slice_import")
            self.assertEqual(v["severity"], "CRITICAL")
            self.assertIn("billing", v["message"])

    def test_path_alias_cross_slice_import_detected(self):
        """Path aliases like '@/modules/billing/service' should be blocked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            modules = root / "src" / "modules"
            billing = modules / "billing"
            portfolio = modules / "portfolio"
            billing.mkdir(parents=True)
            portfolio.mkdir(parents=True)

            (billing / "service.ts").write_text("export const x = 1;\n")
            (portfolio / "service.ts").write_text("import { x } from '@/modules/billing/service';\n")

            cmd = [sys.executable, str(SLICE_GUARD_SCRIPT), str(root), "--json"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(res.returncode, 1)
            data = json.loads(res.stdout)
            self.assertEqual(data["status"], "fail")
            self.assertIn("billing", data["violations"][0]["message"])

    def test_python_cross_slice_import_detection(self):
        """Python relative and absolute slice imports should be checked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            modules = root / "modules"
            billing = modules / "billing"
            portfolio = modules / "portfolio"
            billing.mkdir(parents=True)
            portfolio.mkdir(parents=True)

            (billing / "contract.py").write_text("class InvoiceContract: pass\n")
            (billing / "service.py").write_text("def calc_tax(): pass\n")

            # Illegal python import
            (portfolio / "service.py").write_text(
                "from ..billing.service import calc_tax\n"
                "def run(): pass\n"
            )

            cmd = [sys.executable, str(SLICE_GUARD_SCRIPT), str(root), "--json"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(res.returncode, 1)
            data = json.loads(res.stdout)
            self.assertEqual(data["status"], "fail")

    def test_python_allowed_contract_import_passes(self):
        """Python import from ..billing.contract should pass."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            modules = root / "modules"
            billing = modules / "billing"
            portfolio = modules / "portfolio"
            billing.mkdir(parents=True)
            portfolio.mkdir(parents=True)

            (billing / "contract.py").write_text("class InvoiceContract: pass\n")
            (portfolio / "service.py").write_text(
                "from ..billing.contract import InvoiceContract\n"
                "def run(): pass\n"
            )

            cmd = [sys.executable, str(SLICE_GUARD_SCRIPT), str(root), "--json"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0)
            data = json.loads(res.stdout)
            self.assertEqual(data["status"], "pass")

    def test_loc_ceiling_advisory_warning_default(self):
        """Files exceeding max-loc emit advisory warnings but do not fail build by default."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            modules = root / "src" / "modules"
            billing = modules / "billing"
            billing.mkdir(parents=True)

            # 320 non-empty lines
            lines = [f"const val_{i} = {i};" for i in range(320)]
            (billing / "service.ts").write_text("\n".join(lines) + "\n")

            cmd = [sys.executable, str(SLICE_GUARD_SCRIPT), str(root), "--max-loc", "300", "--json"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0)

            data = json.loads(res.stdout)
            self.assertEqual(data["status"], "pass")
            loc_violations = [v for v in data["violations"] if v["type"] == "loc_exceeded"]
            self.assertEqual(len(loc_violations), 1)
            self.assertGreater(loc_violations[0]["loc"], 300)
            self.assertEqual(loc_violations[0]["severity"], "WARNING")
            self.assertIn("cyclomatic complexity", loc_violations[0]["message"])

    def test_loc_ceiling_fails_with_fail_on_loc_flag(self):
        """With --fail-on-loc, files exceeding max-loc fail with exit 1."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            modules = root / "src" / "modules"
            billing = modules / "billing"
            billing.mkdir(parents=True)

            lines = [f"const val_{i} = {i};" for i in range(320)]
            (billing / "service.ts").write_text("\n".join(lines) + "\n")

            cmd = [sys.executable, str(SLICE_GUARD_SCRIPT), str(root), "--max-loc", "300", "--fail-on-loc", "--json"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(res.returncode, 1)

            data = json.loads(res.stdout)
            self.assertEqual(data["status"], "fail")
            loc_violations = [v for v in data["violations"] if v["type"] == "loc_exceeded"]
            self.assertEqual(len(loc_violations), 1)

    def test_schema_and_pragma_exemptions(self):
        """Declarative schemas and files with pragma are exempt from LOC warnings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            modules = root / "src" / "modules"
            billing = modules / "billing"
            billing.mkdir(parents=True)

            # schema.ts with 400 lines (declarative schema exemption)
            schema_lines = [f"export const field_{i} = '{i}';" for i in range(400)]
            (billing / "schema.ts").write_text("\n".join(schema_lines) + "\n")

            # state_machine.ts with pragma annotation
            sm_lines = ["// @slice-guard-allow-loc (atomic state machine)"] + [f"const step_{i} = {i};" for i in range(400)]
            (billing / "state_machine.ts").write_text("\n".join(sm_lines) + "\n")

            cmd = [sys.executable, str(SLICE_GUARD_SCRIPT), str(root), "--max-loc", "300", "--fail-on-loc", "--json"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0)
            data = json.loads(res.stdout)
            self.assertEqual(data["status"], "pass")
            self.assertEqual(len(data["violations"]), 0)

    def test_test_files_exempt_from_loc_ceiling(self):
        """Colocated test files are exempt from LOC limits."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            modules = root / "src" / "modules"
            billing = modules / "billing"
            billing.mkdir(parents=True)

            (billing / "contract.ts").write_text("export const x = 1;\n")
            (billing / "service.ts").write_text("export const y = 2;\n")

            # Test file with 400 lines
            test_lines = [f"test('case {i}', () => {{ expect(true).toBe(true); }});" for i in range(400)]
            (billing / "billing.test.ts").write_text("\n".join(test_lines) + "\n")

            cmd = [sys.executable, str(SLICE_GUARD_SCRIPT), str(root), "--max-loc", "300", "--fail-on-loc", "--json"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0)
            data = json.loads(res.stdout)
            self.assertEqual(data["status"], "pass")


if __name__ == "__main__":
    unittest.main()
