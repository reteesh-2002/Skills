"""Regression tests for modern Antigravity tool schemas (read_file, edit_file, write_file)."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
AGENT_SCRIPTS_DIR = REPO_ROOT / ".agents" / "scripts"
GUARD_RBW = SCRIPTS_DIR / "guard_read_before_write.py"
GUARD_AER = SCRIPTS_DIR / "guard_anti_retry.py"


class TestModernToolHooks(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="test_modern_hooks_")
        self.tmp_path = Path(self.tmp_dir)
        (self.tmp_path / ".evidence").mkdir(parents=True, exist_ok=True)
        self.target_file = self.tmp_path / "src" / "widget.py"
        self.target_file.parent.mkdir(parents=True, exist_ok=True)
        self.target_file.write_text("x = 1\n", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def _run_guard(self, script: Path, payload: dict) -> dict:
        res = subprocess.run(
            [sys.executable, str(script)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(res.stdout)

    def test_read_file_allows_edit_file_and_write_file(self):
        """read_file(Path) records read so edit_file(Path) and write_file(Path) are allowed."""
        # Blind edit_file should be denied
        deny_edit = self._run_guard(
            GUARD_RBW,
            {
                "cwd": str(self.tmp_path),
                "toolCall": {"name": "edit_file", "args": {"Path": str(self.target_file)}},
            },
        )
        self.assertEqual(deny_edit.get("decision"), "deny")

        # Blind write_file should be denied
        deny_write = self._run_guard(
            GUARD_RBW,
            {
                "cwd": str(self.tmp_path),
                "toolCall": {"name": "write_file", "args": {"Path": str(self.target_file)}},
            },
        )
        self.assertEqual(deny_write.get("decision"), "deny")

        # Inspect via read_file(Path)
        allow_read = self._run_guard(
            GUARD_RBW,
            {
                "cwd": str(self.tmp_path),
                "toolCall": {"name": "read_file", "args": {"Path": str(self.target_file)}},
            },
        )
        self.assertEqual(allow_read.get("decision"), "allow")

        # Subsequent edit_file and write_file are allowed
        allow_edit = self._run_guard(
            GUARD_RBW,
            {
                "cwd": str(self.tmp_path),
                "toolCall": {"name": "edit_file", "args": {"Path": str(self.target_file)}},
            },
        )
        self.assertEqual(allow_edit.get("decision"), "allow")

        allow_write = self._run_guard(
            GUARD_RBW,
            {
                "cwd": str(self.tmp_path),
                "toolCall": {"name": "write_file", "args": {"Path": str(self.target_file)}},
            },
        )
        self.assertEqual(allow_write.get("decision"), "allow")

    def test_transcript_fallback_recognizes_read_file(self):
        """check_transcript_for_read detects read_file(Path) in transcript.jsonl."""
        sys.path.insert(0, str(SCRIPTS_DIR))
        try:
            import guard_read_before_write as rbw
        finally:
            sys.path.pop(0)

        transcript_dir = self.tmp_path / "logs"
        transcript_dir.mkdir(parents=True, exist_ok=True)
        transcript_file = transcript_dir / "transcript.jsonl"
        entry = {
            "tool_calls": [
                {"name": "read_file", "args": {"Path": str(self.target_file)}}
            ]
        }
        transcript_file.write_text(json.dumps(entry) + "\n", encoding="utf-8")

        import glob

        orig_glob = glob.glob
        glob.glob = lambda pattern: [str(transcript_file)]
        try:
            found = rbw.check_transcript_for_read(str(self.target_file.resolve()))
        finally:
            glob.glob = orig_glob

        self.assertTrue(found)

    def test_anti_retry_modern_tools_and_post_tool_use(self):
        """read_file is exempt; failing edit_file blocks exact retry and clears on success."""
        edit_args = {"Path": str(self.target_file), "Target": "x = 1", "Replacement": "x = 2"}

        # 1. PreToolUse allows initial edit_file
        res1 = self._run_guard(
            GUARD_AER,
            {
                "cwd": str(self.tmp_path),
                "toolCall": {"name": "edit_file", "args": edit_args},
            },
        )
        self.assertEqual(res1.get("decision"), "allow")

        # 2. PostToolUse failure records fingerprint
        res_post_err = self._run_guard(
            GUARD_AER,
            {
                "cwd": str(self.tmp_path),
                "toolCall": {"name": "edit_file", "args": edit_args},
                "output": {"status": "error"},
                "error": "Target not found",
            },
        )
        self.assertEqual(res_post_err, {})

        # 3. Exact retry is denied
        res_retry = self._run_guard(
            GUARD_AER,
            {
                "cwd": str(self.tmp_path),
                "toolCall": {"name": "edit_file", "args": edit_args},
            },
        )
        self.assertEqual(res_retry.get("decision"), "deny")

        # 4. read_file remains exempt even with active failure
        res_read = self._run_guard(
            GUARD_AER,
            {
                "cwd": str(self.tmp_path),
                "toolCall": {"name": "read_file", "args": {"Path": str(self.target_file)}},
            },
        )
        self.assertEqual(res_read.get("decision"), "allow")

        # 5. Successful PostToolUse on write_file clears active failures
        res_post_ok = self._run_guard(
            GUARD_AER,
            {
                "cwd": str(self.tmp_path),
                "toolCall": {"name": "write_file", "args": {"Path": str(self.target_file)}},
                "output": {"status": "success"},
            },
        )
        self.assertEqual(res_post_ok, {})

        # 6. Original edit_file is now allowed again
        res_after_clear = self._run_guard(
            GUARD_AER,
            {
                "cwd": str(self.tmp_path),
                "toolCall": {"name": "edit_file", "args": edit_args},
            },
        )
        self.assertEqual(res_after_clear.get("decision"), "allow")

    def test_agent_scripts_copies_in_sync(self):
        """Ensure .agents/scripts/ guard copies match scripts/ byte-for-byte."""
        for fname in ("guard_read_before_write.py", "guard_anti_retry.py"):
            self.assertEqual(
                (SCRIPTS_DIR / fname).read_text(encoding="utf-8"),
                (AGENT_SCRIPTS_DIR / fname).read_text(encoding="utf-8"),
                f"{fname} out of sync between scripts/ and .agents/scripts/",
            )


if __name__ == "__main__":
    unittest.main()
