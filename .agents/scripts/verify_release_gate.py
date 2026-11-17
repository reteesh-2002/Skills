#!/usr/bin/env python3
"""
Delegation wrapper for .agents/scripts/verify_release_gate.py.
Delegates directly to canonical scripts/verify_release_gate.py.
"""
import sys
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
CANONICAL = REPO_ROOT / "scripts" / "verify_release_gate.py"

if not CANONICAL.exists():
    CANONICAL = Path.home() / ".gemini" / "config" / "scripts" / "verify_release_gate.py"

if CANONICAL.exists():
    cmd = [sys.executable, str(CANONICAL)] + sys.argv[1:]
    res = subprocess.run(cmd)
    sys.exit(res.returncode)
else:
    print('{"decision": "deny", "reason": "Canonical verify_release_gate.py not found."}', file=sys.stderr)
    sys.exit(1)
