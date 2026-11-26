#!/usr/bin/env python3
"""
Unit tests for suite-policy.json enforcement.
Validates activation modes, skill rosters, routing rules, and output defaults.
"""

import json
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
        """Verify exactly 12 skills are explicit-only."""
        explicit_skills = self.policy.get("activation_modes", {}).get("explicit_only", [])
        self.assertEqual(len(explicit_skills), 12, "Exactly 12 skills must be explicit-only")
        expected = {
            "create-architect",
            "frontend-artisan",
            "schema-craft",
            "code-reviewer",
            "security-verifier",
            "runtime-reliability",
            "idea-council",
            "ship-it",
            "playwright-cli",
            "infra-pilot",
            "docs-architect",
            "repo-auditor",
        }
        self.assertEqual(set(explicit_skills), expected)

    def test_all_15_skills_exist_on_disk(self):
        """Verify all 15 policy skills have corresponding directories with SKILL.md."""
        auto_skills = [e["skill"] for e in self.policy.get("activation_modes", {}).get("auto", [])]
        explicit_skills = self.policy.get("activation_modes", {}).get("explicit_only", [])
        all_policy_skills = auto_skills + explicit_skills
        self.assertEqual(len(all_policy_skills), 15)

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
        self.assertTrue(routing.get("anti_overengineering_gate"))

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

    def test_agents_and_gemini_md_parity(self):
        """Verify AGENTS.md and GEMINI.md are identical and place skills in the right sections."""
        auto_skills = {e["skill"] for e in self.policy["activation_modes"]["auto"]}
        explicit_skills = set(self.policy["activation_modes"]["explicit_only"])
        agents_text = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        gemini_text = (REPO_ROOT / "GEMINI.md").read_text(encoding="utf-8")
        self.assertEqual(agents_text, gemini_text, "AGENTS.md and GEMINI.md must stay identical")

        auto_section = agents_text.split("## Automatic skill activation")[1].split("## All other skills")[0]
        explicit_section = agents_text.split("## All other skills")[1].split("## Key rules")[0]
        for s in auto_skills:
            self.assertIn(f"`{s}`", auto_section, f"AGENTS.md auto section missing `{s}`")
        for s in explicit_skills:
            self.assertIn(f"`{s}`", explicit_section, f"AGENTS.md explicit section missing `{s}`")
        for removed in ("swarm", "anti-slop-spec", "design-md", "image-to-code", "web-interface-guidelines"):
            self.assertNotIn(f"`{removed}`", agents_text, f"AGENTS.md still lists removed `{removed}`")

    def test_disk_to_policy_and_disjoint_triggers(self):
        """Verify disk skills match policy bidirectionally and auto triggers/budgets exist."""
        auto_entries = self.policy["activation_modes"]["auto"]
        auto_skills = {e["skill"] for e in auto_entries}
        explicit_skills = set(self.policy["activation_modes"]["explicit_only"])
        self.assertEqual(len(auto_skills & explicit_skills), 0, "auto and explicit_only must be disjoint")
        for entry in auto_entries:
            self.assertTrue(entry.get("triggers"), f"Auto skill {entry['skill']} missing triggers")

        disk_skills = {
            p.name for p in REPO_ROOT.iterdir()
            if p.is_dir() and not p.name.startswith(".") and (p / "SKILL.md").is_file()
        }
        self.assertEqual(disk_skills, auto_skills | explicit_skills)
        self.assertIn("effort_profiles", self.policy)
        self.assertIn("token_targets", self.policy)


if __name__ == "__main__":
    unittest.main()
