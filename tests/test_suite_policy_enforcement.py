#!/usr/bin/env python3
"""
Unit tests for suite-policy.json enforcement.
Validates activation modes, skill rosters, routing rules, and output defaults.
"""

import json
import os
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestSuitePolicyEnforcement(unittest.TestCase):
    def setUp(self):
        self.policy_path = REPO_ROOT / "suite-policy.json"
        self.assertTrue(self.policy_path.exists(), "suite-policy.json must exist in repo root")
        with open(self.policy_path, "r", encoding="utf-8") as f:
            self.policy = json.load(f)

    def test_auto_activation_skills(self):
        """Verify exactly 3 skills auto-activate: deep-debugger, plan-master, qa-sentinel."""
        auto_entries = self.policy.get("activation_modes", {}).get("auto", [])
        self.assertEqual(len(auto_entries), 3, "Exactly 3 skills must be auto-activated")
        auto_skills = {entry["skill"] for entry in auto_entries}
        expected = {"deep-debugger", "plan-master", "qa-sentinel"}
        self.assertEqual(auto_skills, expected)

    def test_explicit_only_skills(self):
        """Verify exactly 16 skills are explicit-only."""
        explicit_skills = self.policy.get("activation_modes", {}).get("explicit_only", [])
        self.assertEqual(len(explicit_skills), 16, "Exactly 16 skills must be explicit-only")
        expected = {
            "create-architect",
            "frontend-artisan",
            "schema-craft",
            "swarm",
            "code-reviewer",
            "security-verifier",
            "runtime-reliability",
            "idea-council",
            "ship-it",
            "anti-slop-spec",
            "design-md",
            "image-to-code",
            "playwright-cli",
            "web-interface-guidelines",
            "infra-pilot",
            "docs-architect",
        }
        self.assertEqual(set(explicit_skills), expected)

    def test_all_19_skills_exist_on_disk(self):
        """Verify all 19 policy skills have corresponding directories with SKILL.md."""
        auto_skills = [e["skill"] for e in self.policy.get("activation_modes", {}).get("auto", [])]
        explicit_skills = self.policy.get("activation_modes", {}).get("explicit_only", [])
        all_policy_skills = auto_skills + explicit_skills
        self.assertEqual(len(all_policy_skills), 19)

        for skill_name in all_policy_skills:
            skill_dir = REPO_ROOT / skill_name
            self.assertTrue(skill_dir.is_dir(), f"Skill directory {skill_name} must exist")
            skill_md = skill_dir / "SKILL.md"
            self.assertTrue(skill_md.is_file(), f"SKILL.md must exist for {skill_name}")

    def test_routing_rules_configuration(self):
        """Verify routing rule invariants."""
        routing = self.policy.get("routing_rules", {})
        self.assertFalse(routing.get("create_architect_before_plan_master"))
        self.assertTrue(routing.get("plan_master_before_implementation"))
        self.assertEqual(routing.get("small_task_threshold_files"), 3)

    def test_output_defaults_exist(self):
        """Verify mandatory output formats are defined."""
        output_defaults = self.policy.get("output_defaults", {})
        for required_key in [
            "routine_task",
            "review",
            "failure",
            "intermediate_pipeline_stage",
            "engineering_blueprint",
            "execution_plan",
        ]:
            self.assertIn(required_key, output_defaults)
            self.assertIn("format", output_defaults[required_key])


if __name__ == "__main__":
    unittest.main()
