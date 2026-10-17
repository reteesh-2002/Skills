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
        """Files exceeding max-loc with complexity emit advisory warnings but do not fail build by default."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            modules = root / "src" / "modules"
            billing = modules / "billing"
            billing.mkdir(parents=True)

            # 320 lines with high cyclomatic complexity (uncohesive)
            branches = "\n".join([f"    if (x === {i}) return {i};" for i in range(20)])
            extra_lines = "\n".join([f"const val_{i} = {i};" for i in range(300)])
            code = f"export function process(x: number) {{\n{branches}\n  return -1;\n}}\n{extra_lines}\n"
            (billing / "service.ts").write_text(code)

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
        """With --fail-on-loc, uncohesive files exceeding max-loc fail with exit 1."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            modules = root / "src" / "modules"
            billing = modules / "billing"
            billing.mkdir(parents=True)

            branches = "\n".join([f"    if (x === {i}) return {i};" for i in range(20)])
            extra_lines = "\n".join([f"const val_{i} = {i};" for i in range(300)])
            code = f"export function process(x: number) {{\n{branches}\n  return -1;\n}}\n{extra_lines}\n"
            (billing / "service.ts").write_text(code)

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


    def test_mechanical_helper_file_detected(self):
        """Mechanical helper files (*_helpers, *_utils) in slice directories trigger warning."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            modules = root / "src" / "modules"
            billing = modules / "billing"
            billing.mkdir(parents=True)

            (billing / "contract.ts").write_text("export const x = 1;\n")
            (billing / "service.ts").write_text("export const y = 2;\n")
            (billing / "billing_helpers.ts").write_text("export function formatCurrency() { return '$'; }\n")

            cmd = [sys.executable, str(SLICE_GUARD_SCRIPT), str(root), "--json"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0)
            data = json.loads(res.stdout)
            violations = [v for v in data["violations"] if v["type"] == "mechanical_helper_detected"]
            self.assertEqual(len(violations), 1)
            self.assertIn("billing_helpers.ts", violations[0]["message"])

    def test_high_cyclomatic_complexity_detected(self):
        """Functions with cyclomatic complexity > 15 are flagged."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            modules = root / "src" / "modules"
            billing = modules / "billing"
            billing.mkdir(parents=True)

            # Generate function with 18 branches
            branches = "\n".join([f"    if (x === {i}) return {i};" for i in range(18)])
            func_code = f"export function complexBranching(x: number): number {{\n{branches}\n    return -1;\n}}\n"
            (billing / "service.ts").write_text(func_code)

            cmd = [sys.executable, str(SLICE_GUARD_SCRIPT), str(root), "--max-cyclomatic", "15", "--json"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0)
            data = json.loads(res.stdout)
            comp_violations = [v for v in data["violations"] if v["type"] == "high_cyclomatic_complexity"]
            self.assertEqual(len(comp_violations), 1)
            self.assertEqual(comp_violations[0]["function"], "complexBranching")
            self.assertGreater(comp_violations[0]["complexity"], 15)

    def test_high_fan_out_detected(self):
        """Modules importing from > 7 external packages/slices are flagged for high fan-out."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            modules = root / "src" / "modules"
            billing = modules / "billing"
            billing.mkdir(parents=True)

            # 9 distinct external imports
            imports = "\n".join([f"import pkg_{i} from 'external-pkg-{i}';" for i in range(9)])
            (billing / "service.ts").write_text(imports + "\nexport const x = 1;\n")

            cmd = [sys.executable, str(SLICE_GUARD_SCRIPT), str(root), "--max-fan-out", "7", "--json"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0)
            data = json.loads(res.stdout)
            fan_violations = [v for v in data["violations"] if v["type"] == "high_fan_out"]
            self.assertEqual(len(fan_violations), 1)
            self.assertEqual(fan_violations[0]["fan_out"], 9)

    def test_cohesive_module_large_loc_approved_under_semantic_enclosure(self):
        """Cohesive modules (≤15 CC, ≤50 total CC, ≤7 fan-out) between 600 and 1500 LOC pass cleanly as green PASS with zero warnings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            modules = root / "src" / "modules"
            billing = modules / "billing"
            billing.mkdir(parents=True)

            # 800 lines of cohesive, simple state machine logic
            lines = ["export function stateTransition(state: string) {"]
            for i in range(800):
                lines.append(f"  const step_{i} = {i};")
            lines.append("  return state;")
            lines.append("}")

            (billing / "service.ts").write_text("\n".join(lines) + "\n")

            cmd = [sys.executable, str(SLICE_GUARD_SCRIPT), str(root), "--max-loc", "600", "--max-cohesive-loc", "1500", "--json"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0)
            data = json.loads(res.stdout)
            self.assertEqual(data["status"], "pass")
            self.assertEqual(len(data["violations"]), 0)
            self.assertEqual(len(data["compliant_enclosures"]), 1)
            enc = data["compliant_enclosures"][0]
            self.assertGreaterEqual(enc["loc"], 800)
            self.assertLessEqual(enc["max_complexity"], 15)
            self.assertLessEqual(enc["total_complexity"], 50)
            self.assertLessEqual(enc["fan_out"], 7)

            # Also verify clean human-readable output contains [PASS: Semantic Enclosure] and no warning prefix
            cmd_human = [sys.executable, str(SLICE_GUARD_SCRIPT), str(root), "--max-loc", "600", "--max-cohesive-loc", "1500"]
            res_human = subprocess.run(cmd_human, capture_output=True, text=True)
            self.assertEqual(res_human.returncode, 0)
            self.assertIn("[PASS: Semantic Enclosure]", res_human.stdout)
            self.assertNotIn("[WARNING]", res_human.stdout)

    def test_file_exceeds_cohesive_ceiling_fails_with_fail_on_loc(self):
        """Files exceeding the absolute cohesive ceiling (1500 LOC) fail when --fail-on-loc is set."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            modules = root / "src" / "modules"
            billing = modules / "billing"
            billing.mkdir(parents=True)

            lines = [f"const line_{i} = {i};" for i in range(1600)]
            (billing / "service.ts").write_text("\n".join(lines) + "\n")

            cmd = [sys.executable, str(SLICE_GUARD_SCRIPT), str(root), "--max-cohesive-loc", "1500", "--fail-on-loc", "--json"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(res.returncode, 1)
            data = json.loads(res.stdout)
            self.assertEqual(data["status"], "fail")
            loc_violations = [v for v in data["violations"] if v["type"] == "loc_exceeded"]
            self.assertEqual(len(loc_violations), 1)
            self.assertIn("exceeds maximum cohesive ceiling", loc_violations[0]["message"])

    def test_aggregate_file_complexity_cap_detected(self):
        """Files where total aggregate cyclomatic complexity exceeds 50 are flagged for high_total_complexity."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            modules = root / "src" / "modules"
            billing = modules / "billing"
            billing.mkdir(parents=True)

            # 6 functions each with CC=10 => Total CC = 66 (> 50 limit)
            funcs = []
            for fn_idx in range(6):
                branches = "\n".join([f"    if (x === {i}) return {i};" for i in range(10)])
                funcs.append(f"export function fn_{fn_idx}(x: number) {{\n{branches}\n    return -1;\n}}\n")
            (billing / "service.ts").write_text("\n".join(funcs))

            cmd = [sys.executable, str(SLICE_GUARD_SCRIPT), str(root), "--max-total-cyclomatic", "50", "--json"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0)
            data = json.loads(res.stdout)
            total_violations = [v for v in data["violations"] if v["type"] == "high_total_complexity"]
            self.assertEqual(len(total_violations), 1)
            self.assertEqual(total_violations[0]["total_complexity"], 66)
            self.assertIn("Total file cyclomatic complexity of 66 exceeds ceiling of 50", total_violations[0]["message"])

    def test_fan_out_whitelists_standard_infrastructure(self):
        """Standard infrastructure/framework packages (React, Next, Zod, Pino, etc.) do NOT increment fan-out."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            modules = root / "src" / "modules"
            billing = modules / "billing"
            billing.mkdir(parents=True)

            # 8 infrastructure packages + 2 actual external domain packages = 10 imports total
            imports = [
                "import React from 'react';",
                "import ReactDOM from 'react-dom';",
                "import { NextResponse } from 'next/server';",
                "import { z } from 'zod';",
                "import pino from 'pino';",
                "import { clsx } from 'clsx';",
                "import { trace } from '@opentelemetry/api';",
                "import { Client } from 'pg';",
                "import { extA } from 'actual-domain-package-a';",
                "import { extB } from 'actual-domain-package-b';",
            ]
            (billing / "service.ts").write_text("\n".join(imports) + "\nexport const x = 1;\n")

            cmd = [sys.executable, str(SLICE_GUARD_SCRIPT), str(root), "--max-fan-out", "7", "--json"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0)
            data = json.loads(res.stdout)
            fan_violations = [v for v in data["violations"] if v["type"] == "high_fan_out"]
            self.assertEqual(len(fan_violations), 0)  # Fan-out is 2, well within <= 7 limit

    def test_expanded_lasagna_filter_detects_substates_and_ops(self):
        """Expanded lasagna filter catches *_ops, *_tools, *_handlers, *_delegates, *_substate, etc."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            modules = root / "src" / "modules"
            billing = modules / "billing"
            billing.mkdir(parents=True)

            (billing / "contract.ts").write_text("export const x = 1;\n")
            (billing / "billing_ops.ts").write_text("export const op = 1;\n")
            (billing / "billing_tools.ts").write_text("export const tool = 1;\n")
            (billing / "billing_delegates.ts").write_text("export const del = 1;\n")
            (billing / "billing_substate.ts").write_text("export const sub = 1;\n")

            cmd = [sys.executable, str(SLICE_GUARD_SCRIPT), str(root), "--json"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0)
            data = json.loads(res.stdout)
            helper_violations = [v for v in data["violations"] if v["type"] == "mechanical_helper_detected"]
            self.assertEqual(len(helper_violations), 4)
            detected_files = {v["file"] for v in helper_violations}
            self.assertTrue(any("billing_ops.ts" in f for f in detected_files))
            self.assertTrue(any("billing_tools.ts" in f for f in detected_files))
            self.assertTrue(any("billing_delegates.ts" in f for f in detected_files))
            self.assertTrue(any("billing_substate.ts" in f for f in detected_files))


if __name__ == "__main__":
    unittest.main()
