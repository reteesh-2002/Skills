#!/usr/bin/env python3
"""Antigravity Guard: Anti-Exact-Retry (Invariant 4). Zero dependencies."""
import hashlib, json, os, re, sys, time
from pathlib import Path

def get_failures_file(evidence_dir: Path) -> Path:
    return evidence_dir / "failures.jsonl"

def compute_action_fingerprint(tool_name: str, args: dict) -> str:
    safe_args = args if isinstance(args, dict) else {}
    canon = {"name": str(tool_name).strip(), "args": {k: v for k, v in safe_args.items() if k not in ("WaitMsBeforeAsync", "toolSummary", "toolAction")}}
    return hashlib.sha256(json.dumps(canon, sort_keys=True, default=str).encode()).hexdigest()

def load_failures(failures_file: Path) -> set:
    if not failures_file.exists(): return set()
    fails = set()
    for line in failures_file.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.strip():
            try:
                fp = json.loads(line).get("fingerprint")
                if fp: fails.add(fp)
            except Exception: pass
    return fails

def record_failure(failures_file: Path, fp: str, tool_name: str, reason: str = "") -> None:
    failures_file.parent.mkdir(parents=True, exist_ok=True)
    with open(failures_file, "a", encoding="utf-8") as f:
        f.write(json.dumps({"fingerprint": fp, "tool": tool_name, "reason": reason[:200], "ts": time.time()}) + "\n")

def clear_failures(failures_file: Path) -> None:
    if failures_file.exists():
        try: failures_file.unlink()
        except OSError: pass

EXPLORATORY_COMMAND_PREFIXES = (
    "grep ", "fgrep ", "egrep ", "rg ", "ls ", "cat ", "head ", "tail ",
    "ps ", "ss ", "lsof ", "diff ", "test ", "find ", "curl -s", "curl -i",
    "which ", "type ", "git status", "git diff", "git log",
)

def is_exploratory_command(command_line: str) -> bool:
    """Check if command is a read-only inspection/discovery tool where non-zero exits are routine."""
    c = str(command_line or "").strip().lower()
    c = re.sub(r"^(?:[a-z_][a-z0-9_]*=\S+\s+)+", "", c)
    return any(c == p.strip() or c.startswith(p) for p in EXPLORATORY_COMMAND_PREFIXES)

def evaluate_retry(tool_name: str, args: dict, active_failures: set) -> tuple[bool, str]:
    safe_args = args if isinstance(args, dict) else {}
    if tool_name in ("view_file", "read_file", "list_dir", "manage_task"):
        return True, "Read-only inspection permitted"
    if tool_name == "run_command" and is_exploratory_command(safe_args.get("CommandLine", "")):
        return True, "Exploratory discovery command permitted"
    fp = compute_action_fingerprint(tool_name, safe_args)
    if fp in active_failures:
        cmd = f": '{safe_args.get('CommandLine')}'" if safe_args.get("CommandLine") else ""
        return False, f"Anti-Exact-Retry violation: invocation of '{tool_name}'{cmd} previously failed. Alter code or args before retrying."
    return True, "Call is novel"

def _is_nonzero_exit(exit_code) -> bool:
    if exit_code is None:
        return False
    try:
        return int(exit_code) != 0
    except (TypeError, ValueError):
        return bool(exit_code)

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--test-harness":
        print("Anti-Exact-Retry Guard ready"); sys.exit(0)
    try:
        payload = json.load(sys.stdin)
    except Exception:
        print(json.dumps({"decision": "allow"}))
        sys.exit(0)
    if not isinstance(payload, dict):
        print(json.dumps({"decision": "allow"}))
        sys.exit(0)
    tc = payload.get("toolCall") or payload.get("tool_call") or {}
    if not isinstance(tc, dict):
        tc = {}
    name = str(tc.get("name") or payload.get("name") or "")
    args = tc.get("args") or payload.get("args") or payload.get("tool_input") or {}
    if not isinstance(args, dict):
        args = {}
    ff = get_failures_file(Path(payload.get("cwd") or os.getcwd()).resolve() / ".evidence")
    res_obj = payload.get("result") if isinstance(payload.get("result"), dict) else (payload.get("output") if isinstance(payload.get("output"), dict) else {})
    status = payload.get("status") or res_obj.get("status")
    exit_code = payload.get("exit_code") if payload.get("exit_code") is not None else res_obj.get("exit_code")
    is_post = "result" in payload or "output" in payload
    mutation_tools = ("replace_file_content", "write_to_file", "edit_file", "write_file", "multi_replace_file_content")
    if is_post:
        if status == "error" or _is_nonzero_exit(exit_code):
            record_failure(ff, compute_action_fingerprint(name, args), name, str(payload.get("error") or ""))
        elif name in mutation_tools:
            clear_failures(ff)
        print("{}"); sys.exit(0)
    allowed, reason = evaluate_retry(name, args, load_failures(ff))
    if not allowed:
        print(json.dumps({"decision": "deny", "reason": reason})); sys.exit(0)
    print(json.dumps({"decision": "allow"}))

if __name__ == "__main__": main()
