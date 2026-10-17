#!/usr/bin/env python3
"""
Unit and integration tests for Windows Native Compatibility.
Tests cross-platform file locking, Windows memory/process probes,
pure Python execution proxy, and pure Python release gate.
"""

import os
import sys
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import runtime_evidence
import specialist_probes
import task_ledger


class TestCrossPlatformFileLocking(unittest.TestCase):
    """Tests file_lock behavior under POSIX and simulated Windows (msvcrt)."""

    def test_posix_file_lock_execution(self):
        with tempfile.NamedTemporaryFile("w+", delete=False) as f:
            lock_path = f.name
        try:
            with open(lock_path, "w") as lf:
                with runtime_evidence.file_lock(lf):
                    lf.write("locked content\n")
                    lf.flush()

            with open(lock_path, "r") as lf:
                self.assertEqual(lf.read().strip(), "locked content")
        finally:
            if os.path.exists(lock_path):
                os.unlink(lock_path)

    def test_simulated_windows_msvcrt_locking(self):
        """Simulate sys.platform == 'win32' and verify msvcrt.locking is called."""
        mock_msvcrt = MagicMock()
        mock_msvcrt.LK_LOCK = 1
        mock_msvcrt.LK_UNLCK = 2

        with tempfile.NamedTemporaryFile("w+", delete=False) as f:
            lock_path = f.name

        try:
            with patch("sys.platform", "win32"), patch.dict("sys.modules", {"msvcrt": mock_msvcrt}):
                with open(lock_path, "w") as lf:
                    with runtime_evidence.file_lock(lf):
                        lf.write("windows locked\n")

            self.assertTrue(mock_msvcrt.locking.called)
            self.assertEqual(mock_msvcrt.locking.call_count, 2)
            # First call locks, second call unlocks
            call_args = mock_msvcrt.locking.call_args_list
            self.assertEqual(call_args[0][0][1], mock_msvcrt.LK_LOCK)
            self.assertEqual(call_args[1][0][1], mock_msvcrt.LK_UNLCK)
        finally:
            if os.path.exists(lock_path):
                os.unlink(lock_path)

    def test_task_ledger_works_with_cross_platform_lock(self):
        """Verify TaskLedger operates cleanly under cross-platform lock."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_file = Path(tmpdir) / ".evidence" / "tasks.json"
            ledger = task_ledger.TaskLedger(str(ledger_file))
            ledger.init_ledger("Windows Compat Test Goal", session_id="test_win_sess")

            t = ledger.add_task(
                task_id="T1",
                title="Implement Windows Support",
                owner="Coordinator",
                depends_on=[]
            )
            self.assertEqual(t["status"], "Pending")

            ledger.update_task(t["id"], status="Running")
            current = ledger.get_task(t["id"])
            self.assertEqual(current["status"], "Running")


class TestWindowsProbesAndMemory(unittest.TestCase):
    """Tests specialist probes under simulated Windows and native POSIX."""

    def test_get_current_rss_kb_posix(self):
        rss = specialist_probes.get_current_rss_kb()
        self.assertIsInstance(rss, int)
        if sys.platform != "win32":
            self.assertGreater(rss, 0)

    def test_get_current_rss_kb_simulated_windows(self):
        """Simulate sys.platform == 'win32' with ctypes mock."""
        mock_kernel32 = MagicMock()
        mock_psapi = MagicMock()

        def fake_get_process_memory_info(handle, byref_counters, cb):
            counters = byref_counters._obj
            counters.WorkingSetSize = 10485760  # 10 MB in bytes
            return 1

        mock_psapi.GetProcessMemoryInfo = fake_get_process_memory_info

        with patch("sys.platform", "win32"):
            with patch("ctypes.windll", MagicMock(kernel32=mock_kernel32, psapi=mock_psapi), create=True):
                rss = specialist_probes.get_current_rss_kb()
                self.assertIsInstance(rss, int)

    def test_probe_memory_soak_plateau_with_rss_cross_platform(self):
        """Verify probe_memory_soak_plateau runs with use_rss=True without crashing."""
        items = []

        def work():
            items.append("a" * 100)

        res = specialist_probes.probe_memory_soak_plateau(work, iterations=20, sample_interval=5, use_rss=True)
        self.assertIn("passed", res)
        self.assertIn("samples", res)
        self.assertIn("verdict", res)


class TestPurePythonExecProxy(unittest.TestCase):
    """Tests scripts/exec_proxy.py functionality."""

    def test_exec_proxy_runs_command_and_writes_receipt(self):
        import exec_proxy

        label = "cmd_echo_win"
        cmd = [sys.executable, "-c", "print('win_compat_output')"]
        test_args = ["exec_proxy.py", "--label", label] + cmd

        with patch.object(sys, "argv", test_args):
            try:
                exec_proxy.main()
            except SystemExit as se:
                self.assertEqual(se.code, 0)

        # Check receipt existence
        repo_root = Path(__file__).resolve().parent.parent
        manifest_file = repo_root / ".evidence" / "manifest.v1.json"
        self.assertTrue(manifest_file.exists())
        with open(manifest_file, "r") as mf:
            m = json.load(mf)
        checks = [c for c in m.get("checks", []) if c.get("label") == label]
        self.assertTrue(len(checks) >= 1)
        self.assertEqual(checks[-1]["exit_code"], 0)

    def test_exec_proxy_batch_wrapper_exists(self):
        cmd_wrapper = SCRIPTS_DIR / "exec-proxy.cmd"
        self.assertTrue(cmd_wrapper.exists(), "exec-proxy.cmd must exist for Windows support")
        content = cmd_wrapper.read_text(encoding="utf-8")
        self.assertIn("exec_proxy.py", content)


class TestPurePythonReleaseGate(unittest.TestCase):
    """Tests scripts/verify_release_gate.py functionality."""

    def test_release_gate_pre_tool_allow_safe_command(self):
        import verify_release_gate

        test_args = ["verify_release_gate.py", "--pre-tool", "git status"]
        with patch.object(sys, "argv", test_args):
            try:
                verify_release_gate.main()
            except SystemExit as se:
                self.assertEqual(se.code, 0)

    def test_release_gate_pre_tool_block_ambiguous_eval(self):
        import verify_release_gate

        test_args = ["verify_release_gate.py", "--pre-tool", 'eval "git push"']
        with patch.object(sys, "argv", test_args):
            try:
                verify_release_gate.main()
            except SystemExit as se:
                self.assertEqual(se.code, 1)

    def test_release_gate_batch_wrapper_exists(self):
        cmd_wrapper = SCRIPTS_DIR / "verify-release-gate.cmd"
        self.assertTrue(cmd_wrapper.exists(), "verify-release-gate.cmd must exist for Windows support")
        content = cmd_wrapper.read_text(encoding="utf-8")
        self.assertIn("verify_release_gate.py", content)


if __name__ == "__main__":
    unittest.main()
