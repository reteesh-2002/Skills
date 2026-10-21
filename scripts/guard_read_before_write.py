#!/usr/bin/env python3
"""Antigravity Guard: Read-Before-Write (Invariant 1). Zero dependencies."""
import json, os, sys, time
from pathlib import Path

def get_reads_file(evidence_dir: Path) -> Path:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    return evidence_dir / "reads.jsonl"

def load_reads(reads_file: Path) -> set:
    if not reads_file.exists(): return set()
    reads = set()
    for line in reads_file.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.strip():
            try:
                item = json.loads(line).get("file")
                if item: reads.add(item)
            except Exception: pass
    return reads

def record_read(reads_file: Path, file_path: str) -> None:
    reads_file.parent.mkdir(parents=True, exist_ok=True)
    canonical = str(Path(file_path).resolve())
    with open(reads_file, "a", encoding="utf-8") as f:
        f.write(json.dumps({"file": canonical, "ts": time.time()}) + "\n")

def check_transcript_for_read(canonical_path: str) -> bool:
    """Fallback check: scan active Antigravity session transcript for view_file."""
    import glob
    home = Path.home()
    pattern = str(home / ".gemini" / "antigravity" / "brain" / "*" / ".system_generated" / "logs" / "transcript.jsonl")
    transcripts = glob.glob(pattern)
    if not transcripts:
        return False
    transcripts.sort(key=os.path.getmtime, reverse=True)
    is_windows = sys.platform == "win32"
    target = canonical_path.lower() if is_windows else canonical_path
    for t_path in transcripts[:3]:
        try:
            with open(t_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if "view_file" in line:
                        try:
                            data = json.loads(line)
                            for tc in data.get("tool_calls", []):
                                if tc.get("name") == "view_file":
                                    p = tc.get("args", {}).get("AbsolutePath", "").strip('"\'')
                                    if p:
                                        res_p = str(Path(p).resolve())
                                        if (res_p.lower() if is_windows else res_p) == target:
                                            return True
                        except Exception:
                            pass
        except Exception:
            pass
    return False

def evaluate_mutation(target_file: str | None, reads: set, reads_file: Path | None = None) -> tuple[bool, str]:
    if not target_file: return True, "No target file"
    p = Path(target_file).resolve()
    if not p.exists(): return True, "New file allowed"
    canonical = str(p)
    if canonical in reads: return True, "Read recorded"
    if check_transcript_for_read(canonical):
        if reads_file:
            try: record_read(reads_file, canonical)
            except Exception: pass
        return True, "Read recorded from conversation transcript"
    return False, f"Read-Before-Write violation: file '{target_file}' not inspected with view_file in this session."

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--test-harness":
        print("Read-Before-Write Guard ready"); sys.exit(0)
    payload = {}
    try: payload = json.load(sys.stdin)
    except Exception: print("{}" if ("result" in payload or "output" in payload) else json.dumps({"decision": "allow"})); sys.exit(0)
    tc = payload.get("toolCall") or payload.get("tool_call") or {}
    name = tc.get("name") or payload.get("name") or ""
    args = tc.get("args") or payload.get("args") or payload.get("tool_input") or {}
    evidence_dir = Path(payload.get("cwd") or os.getcwd()).resolve() / ".evidence"
    rf = get_reads_file(evidence_dir)
    if name == "view_file" and args.get("AbsolutePath"):
        record_read(rf, args["AbsolutePath"])
    elif name in ("replace_file_content", "write_to_file"):
        allowed, reason = evaluate_mutation(args.get("TargetFile"), load_reads(rf), rf)
        if not allowed:
            print(json.dumps({"decision": "deny", "reason": reason})); sys.exit(0)
    print("{}" if ("result" in payload or "output" in payload) else json.dumps({"decision": "allow"}))

if __name__ == "__main__": main()
