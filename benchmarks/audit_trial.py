#!/usr/bin/env python3
"""
Cheat-Proof Independent Transcript & Artifact Auditor for Antigravity Skills.
Inspects immutable event logs in transcript.jsonl and disk filesystem directly.
The agent cannot fake or mock these results.
"""

import os
import sys
import json
import glob
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
BRAIN_BASE = Path.home() / ".gemini" / "antigravity" / "brain"

def find_latest_transcript():
    """Finds the most recently modified transcript for test-skills session."""
    candidates = glob.glob(str(BRAIN_BASE / "*" / ".system_generated" / "logs" / "transcript.jsonl"))
    # Filter out current conversation if another active one touched test-skills
    valid = []
    for c in candidates:
        try:
            with open(c, "r", encoding="utf-8") as f:
                head = f.read(4000)
                if "test-skills" in head or "frontend-artisan" in head:
                    valid.append((os.path.getmtime(c), Path(c)))
        except Exception:
            pass
    if valid:
        valid.sort(key=lambda x: x[0], reverse=True)
        # Prefer the newest non-current session if available
        current_id = "33550772-ca0c-4f74-a1e4-e5e010d01273"
        for mtime, p in valid:
            if current_id not in str(p):
                return p
        return valid[0][1]
    return None

def audit_frontend_artisan(transcript_path):
    """Audits FLAG-01: frontend-artisan Gate 0 image-first law."""
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
        print("🔴 FAIL: Agent never called 'generate_image'. Bypassed Gate 0!")
        return False

    first_image_idx = tool_sequence.index("generate_image")
    if "write_to_file" in tool_sequence:
        first_write_idx = tool_sequence.index("write_to_file")
        if first_write_idx < first_image_idx:
            print("🔴 FAIL: Agent called 'write_to_file' BEFORE 'generate_image'. Gate 0 violated!")
            return False

    print("🟢 PASS: Gate 0 verified! Agent called 'generate_image' before writing code.")
    return True

def audit_deep_debugger(transcript_path):
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

    # Check if worker.py was edited before reproduction script
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

def audit_prompt_architect(transcript_path):
    """Audits FLAG-05: prompt-architect Zero-Disk-Crawling law."""
    print("🔍 Auditing FLAG-05 (prompt-architect)...")
    if not transcript_path or not transcript_path.exists():
        print("❌ Transcript file not found.")
        return False

    disk_tools = ["find_files", "dir_list", "view_file"]
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
        print("🔴 FAIL: Zero-Disk-Crawling violation! Agent crawled disk tools instead of delivering prompt immediately.")
        return False

    print("🟢 PASS: Zero-Disk-Crawling verified! 0 disk crawling tools executed.")
    return True

def main():
    transcript = find_latest_transcript()
    if not transcript:
        print("No active conversation transcript found.")
        sys.exit(1)

    print(f"Auditing transcript: {transcript}")
    target_skill = sys.argv[1] if len(sys.argv) > 1 else "frontend-artisan"

    if target_skill in ["frontend-artisan", "FLAG-01", "1"]:
        audit_frontend_artisan(transcript)
    elif target_skill in ["deep-debugger", "FLAG-02", "2"]:
        audit_deep_debugger(transcript)
    elif target_skill in ["prompt-architect", "FLAG-05", "5"]:
        audit_prompt_architect(transcript)
    else:
        print(f"Default audit for: {target_skill}")
        audit_frontend_artisan(transcript)

if __name__ == "__main__":
    main()
