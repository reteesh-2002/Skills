#!/usr/bin/env python3
"""Unit and integration tests for scripts/validate-skills.py."""

import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parent.parent
VALIDATE_SCRIPT = REPO_ROOT / "scripts" / "validate-skills.py"

spec = importlib.util.spec_from_file_location("validate_skills", VALIDATE_SCRIPT)
vs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vs)


class TestValidateSkills(unittest.TestCase):
    def test_parse_frontmatter_handles_bom_multiline_and_nested(self):
        content = (
            "\ufeff---\n"
            "name: sample-skill\n"
            "description: |\n"
            "  First line of description.\n"
            "\n"
            "  Second paragraph after blank line.\n"
            "metadata:\n"
            "  name: nested-should-not-overwrite\n"
            "---\n"
            "# Body\n"
        )
        fm, body = vs.parse_frontmatter(content)
        self.assertIsNotNone(fm)
        self.assertEqual(fm["name"], "sample-skill")
        self.assertIn("Second paragraph after blank line.", fm["description"])
        self.assertEqual(body.strip(), "# Body")

    def test_check_relative_links_catches_backticked_text_and_escapes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / "my-skill"
            skill_dir.mkdir()
            skill_file = skill_dir / "SKILL.md"
            (skill_dir / "real.md").write_text("# Real\n", encoding="utf-8")

            body = (
                "Valid: [`real.md`](real.md)\n"
                "Broken backticked: [`missing.md`](missing.md)\n"
                "Escape root: [outside](../../outside.md)\n"
                "````markdown\n[ignored](does-not-exist.md)\n````\n"
                "Inline example: `[ignored2](nope.md)`\n"
            )
            errors = vs.check_relative_links(skill_dir, skill_file, body, repo_root=root)
            self.assertEqual(len(errors), 2, f"Expected 2 errors, got: {errors}")
            self.assertTrue(any("missing.md" in e for e in errors))
            self.assertTrue(any("escapes repository root" in e for e in errors))

    def test_check_policy_parity_detects_duplicates_and_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "suite-policy.json").write_text(
                '{"activation_modes": {"auto": [{"skill": "a"}], "explicit_only": ["a", "b"]}}',
                encoding="utf-8",
            )
            errors = vs.check_policy_parity(root, ["a", "c"])
            joined = "\n".join(errors)
            self.assertIn("both auto and explicit_only", joined)
            self.assertIn("lists 'b' but directory does not exist", joined)
            self.assertIn("'c' is missing from suite-policy.json", joined)

    def test_token_targets_dict_enforced_from_policy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "scripts").mkdir()
            (root / "scripts" / "validate-skills.py").write_text(
                VALIDATE_SCRIPT.read_text(encoding="utf-8"), encoding="utf-8"
            )
            (root / "suite-policy.json").write_text(
                '{"activation_modes":{"auto":[],"explicit_only":["tiny-skill"]},'
                '"token_targets":{"ordinary_entrypoints_estimated_tokens":{"min":50,"max":100}}}',
                encoding="utf-8",
            )
            sk = root / "tiny-skill"
            sk.mkdir()
            (sk / "SKILL.md").write_text(
                "---\nname: tiny-skill\ndescription: A tiny test skill for token bounds.\n---\n# Tiny\n",
                encoding="utf-8",
            )
            res = subprocess.run([sys.executable, str(root / "scripts" / "validate-skills.py")], capture_output=True, text=True)
            self.assertNotEqual(res.returncode, 0)
            self.assertIn("below minimum token budget", res.stdout)

    def test_invalid_token_targets_and_null_hooks_fail_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "scripts").mkdir()
            (root / "scripts" / "validate-skills.py").write_text(
                VALIDATE_SCRIPT.read_text(encoding="utf-8"), encoding="utf-8"
            )
            (root / "suite-policy.json").write_text(
                '{"activation_modes":{"auto":[],"explicit_only":["ok-skill"]},'
                '"token_targets":{"ordinary_entrypoints_estimated_tokens":{"min":"bad_int","max":500}}}',
                encoding="utf-8",
            )
            (root / ".agents").mkdir()
            (root / ".agents" / "hooks.json").write_text('{"evidence-policy": null}', encoding="utf-8")
            sk = root / "ok-skill"
            sk.mkdir()
            (sk / "SKILL.md").write_text(
                "---\nname: ok-skill\ndescription: Valid skill description for schema test.\n---\n"
                + ("word " * 160) + "\n",
                encoding="utf-8",
            )
            res = subprocess.run([sys.executable, str(root / "scripts" / "validate-skills.py")], capture_output=True, text=True)
            self.assertNotEqual(res.returncode, 0)
            self.assertIn("Invalid token_targets configuration", res.stdout)
            self.assertIn("Invalid or missing 'evidence-policy'", res.stdout)

    def test_cli_passes_on_repo(self):
        res = subprocess.run([sys.executable, str(VALIDATE_SCRIPT)], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)


if __name__ == "__main__":
    unittest.main()
