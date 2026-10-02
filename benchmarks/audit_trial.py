#!/usr/bin/env python3
"""
Transcript & Artifact Conformance Auditor for Antigravity Skills.
Inspects event logs in transcript.jsonl and disk filesystem directly.
Propagates audit failures to non-zero exit codes.
"""

import os
import re
import sys
import json
import glob
import argparse
from pathlib import Path
from typing import Optional, List, Tuple

BASE_DIR = Path(__file__).resolve().parent
BRAIN_BASE = Path.home() / ".gemini" / "antigravity" / "brain"

def find_latest_transcript(preferred_path: Optional[str] = None) -> Optional[Path]:
    """Finds the transcript by explicit path or the most recently modified transcript."""
    if preferred_path:
        p = Path(preferred_path).expanduser().resolve()
        if p.exists():
            return p
        print(f"Specified transcript path does not exist: {preferred_path}")
        return None

    candidates = glob.glob(str(BRAIN_BASE / "*" / ".system_generated" / "logs" / "transcript.jsonl"))
    if not candidates:
        return None

    valid: List[Tuple[float, Path]] = []
    for c in candidates:
        try:
            mtime = os.path.getmtime(c)
            valid.append((mtime, Path(c)))
        except Exception:
            pass

    if valid:
        valid.sort(key=lambda x: x[0], reverse=True)
        return valid[0][1]
    return None

def audit_frontend_artisan(transcript_path: Path) -> bool:
    """Audits FLAG-01: frontend-artisan visual grounding."""
    print("🔍 Auditing FLAG-01 (frontend-artisan)...")
    if not transcript_path or not transcript_path.exists():
        print("❌ Transcript file not found.")
        return False

    tool_sequence = []
    with open(transcript_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                step = json.loads(line.strip())
                for call in step.get("tool_calls", []):
                    tool_sequence.append(call.get("name"))
            except Exception:
                pass

    print(f"Tool execution sequence: {tool_sequence}")

    if "generate_image" not in tool_sequence:
        print("🔴 FAIL: Agent never called 'generate_image'. Bypassed visual generation!")
        return False

    first_image_idx = tool_sequence.index("generate_image")
    if "write_to_file" in tool_sequence:
        first_write_idx = tool_sequence.index("write_to_file")
        if first_write_idx < first_image_idx:
            print("🔴 FAIL: Agent called 'write_to_file' BEFORE 'generate_image'.")
            return False

    print("🟢 PASS: Visual art direction verified! Agent called 'generate_image' before writing code.")
    return True

def audit_deep_debugger(transcript_path: Path) -> bool:
    """Audits FLAG-02: deep-debugger anti-shotgun reproduction gate."""
    print("🔍 Auditing FLAG-02 (deep-debugger)...")
    if not transcript_path or not transcript_path.exists():
        print("❌ Transcript file not found.")
        return False

    tool_sequence = []
    with open(transcript_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                step = json.loads(line.strip())
                for call in step.get("tool_calls", []):
                    name = call.get("name")
                    args = call.get("arguments", {})
                    tool_sequence.append((name, args))
            except Exception:
                pass

    edited_worker_first = False
    created_repro = False

    for name, args in tool_sequence:
        target = str(args.get("TargetFile", "") or args.get("AbsolutePath", ""))
        if "worker.py" in target and (name in ["write_to_file", "replace_file_content"]):
            if not created_repro:
                edited_worker_first = True
                break
        if "repro" in target or "scratch" in target:
            created_repro = True

    if edited_worker_first:
        print("🔴 FAIL: Anti-Shotgun violation! Agent edited worker.py before creating reproduction script.")
        return False

    print("🟢 PASS: Anti-Shotgun verified! Agent did not edit production file on first step.")
    return True

def audit_prompt_architect(transcript_path: Path) -> bool:
    """Audits FLAG-05: prompt-architect zero-disk-crawling law."""
    print("🔍 Auditing FLAG-05 (prompt-architect)...")
    if not transcript_path or not transcript_path.exists():
        print("❌ Transcript file not found.")
        return False

    disk_tools = ["find_files", "dir_list"]
    crawled_disk = False

    with open(transcript_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                step = json.loads(line.strip())
                for call in step.get("tool_calls", []):
                    if call.get("name") in disk_tools:
                        crawled_disk = True
                        break
            except Exception:
                pass

    if crawled_disk:
        print("🔴 FAIL: Disk crawling violation! Agent ran recursive search tools.")
        return False

    print("🟢 PASS: Zero-Disk-Crawling verified! 0 recursive disk search tools executed.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Antigravity Conformance Transcript Auditor")
    parser.add_argument("--transcript", type=str, default=None, help="Explicit path to transcript.jsonl")
    parser.add_argument("--task", type=str, default="frontend-artisan", help="Task ID or skill to audit (FLAG-01, FLAG-02, FLAG-05)")
    args = parser.parse_args()

    transcript = find_latest_transcript(args.transcript)
    if not transcript:
        print("❌ Error: No conversation transcript found.")
        sys.exit(1)

    print(f"Auditing transcript: {transcript}")
    target_skill = args.task.strip()

    passed = False
    if target_skill in ["frontend-artisan", "FLAG-01", "1"]:
        passed = audit_frontend_artisan(transcript)
    elif target_skill in ["deep-debugger", "FLAG-02", "2"]:
        passed = audit_deep_debugger(transcript)
    elif target_skill in ["prompt-architect", "FLAG-05", "5"]:
        passed = audit_prompt_architect(transcript)
    else:
        print(f"❌ Error: Unsupported benchmark task '{target_skill}'. Supported: FLAG-01, FLAG-02, FLAG-05.")
        sys.exit(1)

    # Propagate failure to non-zero exit code
    sys.exit(0 if passed else 1)

if __name__ == "__main__":
    main()
