#!/usr/bin/env python3
"""
Unit and integration tests for install-skills.py and skills-doctor.py (T10).
Covers clean installation, safe merge, idempotence, uninstallation,
doctor diagnosis, and graceful degradation for optional tools.
"""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parent.parent
INSTALL_SCRIPT = REPO_ROOT / "scripts" / "install-skills.py"
DOCTOR_SCRIPT = REPO_ROOT / "scripts" / "skills-doctor.py"

# Add scripts directory to path for unit-testing internal functions
sys.path.insert(0, str(REPO_ROOT / "scripts"))
import importlib.util


class TestInstallSkills(unittest.TestCase):
    """Integration tests for scripts/install-skills.py."""

    def test_clean_workspace_installation(self):
        """Test clean installation into an isolated temporary workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_path = Path(tmpdir)
            cmd = [
                sys.executable,
                str(INSTALL_SCRIPT),
                "--target-dir",
                str(target_path),
                "--workspace",
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, f"Install failed: {res.stderr}\n{res.stdout}")

            # 1. Verify manifest
            manifest_file = target_path / ".skills-install-manifest.json"
            self.assertTrue(manifest_file.exists(), "Manifest file was not created")
            manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
            self.assertEqual(manifest["mode"], "workspace")
            self.assertEqual(len(manifest["installed_skills"]), 18)

            # 2. Verify skills installed in target_path/skills/
            for skill_name in manifest["installed_skills"]:
                skill_md = target_path / "skills" / skill_name / "SKILL.md"
                self.assertTrue(
                    skill_md.exists(), f"Expected skill file missing: {skill_md}"
                )

            # 3. Verify runtime helpers installed
            for helper in [
                "exec-proxy.sh",
                "verify-release-gate.sh",
                "runtime_evidence.py",
                "task_ledger.py",
                "task_shape_gating.py",
                "slice-guard.py",
                "guard_read_before_write.py",
                "guard_anti_retry.py",
            ]:
                helper_file = target_path / "scripts" / helper
                self.assertTrue(
                    helper_file.exists(), f"Runtime helper missing: {helper_file}"
                )

            # 4. Verify hooks installed and valid
            hooks_file = target_path / ".agents" / "hooks.json"
            self.assertTrue(hooks_file.exists(), "Hooks file missing")
            hooks_data = json.loads(hooks_file.read_text(encoding="utf-8"))
            self.assertIn("evidence-policy", hooks_data)

            # 5. Verify rules installed
            agents_md = target_path / "AGENTS.md"
            gemini_md = target_path / "GEMINI.md"
            self.assertTrue(agents_md.exists())
            self.assertTrue(gemini_md.exists())
            self.assertIn("Antigravity Skills Suite", agents_md.read_text(encoding="utf-8"))

    def test_idempotent_repeat_installation(self):
        """Test re-running install does not corrupt or duplicate configurations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_path = Path(tmpdir)
            cmd = [
                sys.executable,
                str(INSTALL_SCRIPT),
                "--target-dir",
                str(target_path),
                "--workspace",
            ]

            # First run
            res1 = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(res1.returncode, 0)

            # Second run
            res2 = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(res2.returncode, 0)

            # Rules must not be duplicated
            agents_content = (target_path / "AGENTS.md").read_text(encoding="utf-8")
            count_start = agents_content.count("<!-- BEGIN ANTIGRAVITY SKILLS SUITE RULES -->")
            self.assertEqual(count_start, 1, "Rules block was duplicated on repeat install")

            # Hooks must remain valid JSON with evidence-policy
            hooks_file = target_path / ".agents" / "hooks.json"
            hooks_data = json.loads(hooks_file.read_text(encoding="utf-8"))
            self.assertIn("evidence-policy", hooks_data)

    def test_safe_merge_existing_configuration(self):
        """Test install merges existing hooks and rules without overwriting user configs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_path = Path(tmpdir)

            # Pre-existing user rules
            user_rules_text = "# User Project Rules\n\n- Do not break existing APIs.\n- Keep commits small.\n"
            (target_path / "AGENTS.md").write_text(user_rules_text, encoding="utf-8")

            # Pre-existing user hooks
            (target_path / ".agents").mkdir(parents=True, exist_ok=True)
            user_hooks = {
                "custom-linter": {
                    "PostToolUse": [
                        {"matcher": "write_to_file", "hooks": [{"command": "flake8"}]}
                    ]
                }
            }
            (target_path / ".agents" / "hooks.json").write_text(
                json.dumps(user_hooks, indent=2), encoding="utf-8"
            )

            # Pre-existing user project file
            (target_path / "main.py").write_text("print('user app')", encoding="utf-8")

            # Run install
            cmd = [
                sys.executable,
                str(INSTALL_SCRIPT),
                "--target-dir",
                str(target_path),
                "--workspace",
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0)

            # Verify user code untouched
            self.assertEqual(
                (target_path / "main.py").read_text(encoding="utf-8"), "print('user app')"
            )

            # Verify AGENTS.md preserved user rules AND added suite rules
            agents_text = (target_path / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("# User Project Rules", agents_text)
            self.assertIn("- Do not break existing APIs.", agents_text)
            self.assertIn("<!-- BEGIN ANTIGRAVITY SKILLS SUITE RULES -->", agents_text)

            # Verify hooks merged user hooks AND evidence-policy
            merged_hooks = json.loads((target_path / ".agents" / "hooks.json").read_text(encoding="utf-8"))
            self.assertIn("custom-linter", merged_hooks)
            self.assertIn("evidence-policy", merged_hooks)

    def test_uninstall_cleanly_restores_and_removes(self):
        """Test --uninstall removes installed files and restores user configurations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_path = Path(tmpdir)

            # Pre-existing user rules and hooks
            original_user_rules = "# User Custom Rules\n- Strictly private.\n"
            (target_path / "AGENTS.md").write_text(original_user_rules, encoding="utf-8")

            (target_path / ".agents").mkdir(parents=True, exist_ok=True)
            original_user_hooks = {"my-hook": {"type": "pre-tool"}}
            (target_path / ".agents" / "hooks.json").write_text(
                json.dumps(original_user_hooks), encoding="utf-8"
            )

            user_file = target_path / "important_data.csv"
            user_file.write_text("col1,col2\n1,2\n", encoding="utf-8")

            # Install
            subprocess.run(
                [sys.executable, str(INSTALL_SCRIPT), "--target-dir", str(target_path), "--workspace"],
                check=True,
                capture_output=True,
            )

            # Now Uninstall
            uninst_cmd = [
                sys.executable,
                str(INSTALL_SCRIPT),
                "--target-dir",
                str(target_path),
                "--uninstall",
            ]
            uninst_res = subprocess.run(uninst_cmd, capture_output=True, text=True)
            self.assertEqual(uninst_res.returncode, 0, f"Uninstall failed: {uninst_res.stderr}")

            # Verify skills directory is completely removed
            self.assertFalse((target_path / "skills").exists(), "Skills folder was not removed")

            # Verify installed runtime helpers removed
            self.assertFalse(
                (target_path / "scripts" / "exec-proxy.sh").exists(),
                "Runtime helper was not removed",
            )

            # Verify manifest was removed
            self.assertFalse(
                (target_path / ".skills-install-manifest.json").exists(),
                "Manifest file was not removed",
            )

            # Verify user file is completely intact
            self.assertTrue(user_file.exists())
            self.assertEqual(user_file.read_text(encoding="utf-8"), "col1,col2\n1,2\n")

            # Verify user rules restored to exact original
            self.assertEqual((target_path / "AGENTS.md").read_text(encoding="utf-8"), original_user_rules)

            # Verify user hooks restored to exact original
            restored_hooks = json.loads((target_path / ".agents" / "hooks.json").read_text(encoding="utf-8"))
            self.assertEqual(restored_hooks, original_user_hooks)

    def test_uninstall_clean_project_without_prior_files(self):
        """Test --uninstall on a fresh install leaves no leftover files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_path = Path(tmpdir)

            # Install
            subprocess.run(
                [sys.executable, str(INSTALL_SCRIPT), "--target-dir", str(target_path), "--workspace"],
                check=True,
                capture_output=True,
            )

            # Uninstall
            subprocess.run(
                [sys.executable, str(INSTALL_SCRIPT), "--target-dir", str(target_path), "--uninstall"],
                check=True,
                capture_output=True,
            )

            # Newly created files should be deleted
            self.assertFalse((target_path / "AGENTS.md").exists())
            self.assertFalse((target_path / "GEMINI.md").exists())
            self.assertFalse((target_path / ".agents" / "hooks.json").exists())
            self.assertFalse((target_path / "suite-policy.json").exists())
            self.assertFalse((target_path / ".skills-install-manifest.json").exists())

    def test_global_mode_installation(self):
        """Test global mode installs into skills container directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_path = Path(tmpdir) / "skills"
            cmd = [
                sys.executable,
                str(INSTALL_SCRIPT),
                "--target-dir",
                str(target_path),
                "--global",
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0)

            # Skills installed directly in target_path/<skill_name>
            self.assertTrue((target_path / "plan-master" / "SKILL.md").exists())
            self.assertTrue((target_path / ".skills-install-manifest.json").exists())

            # Uninstall
            uninst_cmd = [
                sys.executable,
                str(INSTALL_SCRIPT),
                "--target-dir",
                str(target_path),
                "--uninstall",
            ]
            res_un = subprocess.run(uninst_cmd, capture_output=True, text=True)
            self.assertEqual(res_un.returncode, 0)
            self.assertFalse((target_path / "plan-master").exists())

    def test_selective_skill_removal(self):
        """Test --remove uninstalls only requested skills and updates manifest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_path = Path(tmpdir)
            # Install in target directory
            cmd = [sys.executable, str(INSTALL_SCRIPT), "--target-dir", str(target_path), "--workspace"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0)
            self.assertTrue((target_path / "skills" / "plan-master" / "SKILL.md").exists())
            self.assertTrue((target_path / "skills" / "idea-council" / "SKILL.md").exists())
            self.assertTrue((target_path / "skills" / "deep-debugger" / "SKILL.md").exists())

            # Selectively remove idea-council
            cmd_rem = [
                sys.executable,
                str(INSTALL_SCRIPT),
                "--target-dir",
                str(target_path),
                "--remove",
                "idea-council",
            ]
            res_rem = subprocess.run(cmd_rem, capture_output=True, text=True)
            self.assertEqual(res_rem.returncode, 0)
            self.assertIn("Successfully removed 1 skill(s)", res_rem.stdout)

            # idea-council should be deleted, but plan-master and deep-debugger remain
            self.assertFalse((target_path / "skills" / "idea-council").exists())
            self.assertTrue((target_path / "skills" / "plan-master" / "SKILL.md").exists())
            self.assertTrue((target_path / "skills" / "deep-debugger" / "SKILL.md").exists())

            # Manifest should be updated with 17 skills remaining
            manifest_file = target_path / ".skills-install-manifest.json"
            self.assertTrue(manifest_file.exists())
            m_data = json.loads(manifest_file.read_text(encoding="utf-8"))
            self.assertNotIn("idea-council", m_data["installed_skills"])
            self.assertEqual(len(m_data["installed_skills"]), 17)


class TestSkillsDoctor(unittest.TestCase):
    """Integration and unit tests for scripts/skills-doctor.py."""

    def test_doctor_sound_in_repo(self):
        """Test skills-doctor exits with 0 on the suite repository itself."""
        cmd = [sys.executable, str(DOCTOR_SCRIPT), "--project-dir", str(REPO_ROOT)]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Doctor check failed: {res.stderr}\n{res.stdout}")
        self.assertIn("HEALTHY", res.stdout)
        self.assertIn("Python Version", res.stdout)
        self.assertIn("Runtime Helpers", res.stdout)

    def test_doctor_json_output_structure(self):
        """Test skills-doctor --json produces valid schema with core_sound = true."""
        cmd = [sys.executable, str(DOCTOR_SCRIPT), "--project-dir", str(REPO_ROOT), "--json"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)

        data = json.loads(res.stdout)
        self.assertTrue(data["core_sound"])
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["python"]["status"], "ok")
        self.assertTrue(data["runtime_helpers"]["all_present"])
        self.assertTrue(data["hooks"]["evidence_policy_configured"])
        self.assertIn("pytest", data["optional_tools"])
        self.assertIn("playwright", data["optional_tools"])
        self.assertIn("git", data["optional_tools"])
        self.assertIn("node", data["optional_tools"])

    def test_doctor_on_freshly_installed_workspace(self):
        """Test doctor passes on an isolated workspace initialized by install-skills.py."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_path = Path(tmpdir)
            # Install
            subprocess.run(
                [sys.executable, str(INSTALL_SCRIPT), "--target-dir", str(target_path), "--workspace"],
                check=True,
                capture_output=True,
            )

            # Run Doctor
            cmd = [sys.executable, str(DOCTOR_SCRIPT), "--project-dir", str(target_path), "--json"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, f"Doctor failed on fresh workspace: {res.stderr}")

            data = json.loads(res.stdout)
            self.assertTrue(data["core_sound"])
            self.assertEqual(data["status"], "healthy")

    def test_doctor_graceful_degradation_missing_optional_tools(self):
        """Test missing optional tools report 'Optional: missing' without failing core health."""
        # Import skills_doctor directly to unit test tool checking
        spec = importlib.util.spec_from_file_location("skills_doctor", str(DOCTOR_SCRIPT))
        doctor_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(doctor_mod)

        # Nonexistent tool check
        tool_res = doctor_mod.check_optional_tool("nonexistent_binary_xyz123")
        self.assertFalse(tool_res["available"])
        self.assertEqual(tool_res["status"], "optional_missing")
        self.assertEqual(tool_res["message"], "Optional: missing")
        self.assertFalse(tool_res["critical"])

    def test_doctor_fails_on_missing_runtime_helpers(self):
        """Test doctor fails (exit 1, core_sound=False) when critical helpers are missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_path = Path(tmpdir)

            # Create hooks but no scripts/
            (target_path / ".agents").mkdir(parents=True, exist_ok=True)
            (target_path / ".agents" / "hooks.json").write_text(
                json.dumps({"evidence-policy": {"PreToolUse": []}}), encoding="utf-8"
            )

            cmd = [sys.executable, str(DOCTOR_SCRIPT), "--project-dir", str(target_path), "--json"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(res.returncode, 1, "Doctor should fail when runtime helpers are missing")

            data = json.loads(res.stdout)
            self.assertFalse(data["core_sound"])
            self.assertEqual(data["status"], "unhealthy")
            self.assertFalse(data["runtime_helpers"]["all_present"])

    def test_doctor_fails_on_missing_hooks(self):
        """Test doctor fails (exit 1) when .agents/hooks.json is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_path = Path(tmpdir)

            # Create scripts but no hooks
            (target_path / "scripts").mkdir(parents=True, exist_ok=True)
            for helper in [
                "exec-proxy.sh",
                "verify-release-gate.sh",
                "runtime_evidence.py",
                "task_ledger.py",
                "task_shape_gating.py",
                "slice-guard.py",
                "guard_read_before_write.py",
                "guard_anti_retry.py",
            ]:
                (target_path / "scripts" / helper).write_text("#!/bin/bash\n", encoding="utf-8")

            cmd = [sys.executable, str(DOCTOR_SCRIPT), "--project-dir", str(target_path), "--json"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(res.returncode, 1, "Doctor should fail when hooks are missing")

            data = json.loads(res.stdout)
            self.assertFalse(data["core_sound"])
            self.assertEqual(data["hooks"]["status"], "missing")

    def test_doctor_fix_repairs_missing_hooks_and_directories(self):
        """Test --fix heals missing .agents/hooks.json and creates required directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_path = Path(tmpdir)
            # Create dummy scripts
            (target_path / "scripts").mkdir(parents=True, exist_ok=True)
            for helper in [
                "exec-proxy.sh",
                "verify-release-gate.sh",
                "runtime_evidence.py",
                "task_ledger.py",
                "task_shape_gating.py",
                "slice-guard.py",
                "guard_read_before_write.py",
                "guard_anti_retry.py",
            ]:
                (target_path / "scripts" / helper).write_text("#!/bin/bash\n", encoding="utf-8")

            # First run without --fix should fail
            cmd_check = [sys.executable, str(DOCTOR_SCRIPT), "--project-dir", str(target_path), "--json"]
            res1 = subprocess.run(cmd_check, capture_output=True, text=True)
            self.assertEqual(res1.returncode, 1)

            # Second run WITH --fix
            cmd_fix = [sys.executable, str(DOCTOR_SCRIPT), "--project-dir", str(target_path), "--fix", "--json"]
            res2 = subprocess.run(cmd_fix, capture_output=True, text=True)
            self.assertEqual(res2.returncode, 0, f"Doctor --fix failed: {res2.stderr}")

            data = json.loads(res2.stdout)
            self.assertTrue(data["core_sound"])
            self.assertEqual(data["status"], "healthy")
            self.assertTrue((target_path / ".agents" / "hooks.json").exists())
            self.assertTrue((target_path / ".evidence" / "receipts").exists())
            self.assertTrue((target_path / ".evidence" / "logs").exists())
            self.assertIn("repairs_applied", data)
            self.assertGreater(len(data["repairs_applied"]), 0)

    def test_doctor_fix_restores_missing_runtime_helpers(self):
        """Test --fix restores missing runtime helpers from suite source."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_path = Path(tmpdir)
            # Empty workspace - missing everything
            cmd_fix = [sys.executable, str(DOCTOR_SCRIPT), "--project-dir", str(target_path), "--fix", "--json"]
            res = subprocess.run(cmd_fix, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, f"Doctor --fix failed: {res.stderr}")

            data = json.loads(res.stdout)
            self.assertTrue(data["core_sound"])
            self.assertTrue(data["runtime_helpers"]["all_present"])
            self.assertTrue((target_path / "scripts" / "runtime_evidence.py").exists())
            self.assertTrue((target_path / "scripts" / "task_ledger.py").exists())


if __name__ == "__main__":
    unittest.main()
