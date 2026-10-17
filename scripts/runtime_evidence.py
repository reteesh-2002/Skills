#!/usr/bin/env python3
"""
Antigravity Runtime Evidence Engine
Shared validation, parsing, and policy reduction for exec-proxy.sh, verify-release-gate.sh, and hooks.
"""

import os
import sys
import re
import json
import shlex
import datetime
import contextlib

@contextlib.contextmanager
def file_lock(lock_file):
    """
    Cross-platform exclusive file lock context manager.
    Uses msvcrt on Windows, fcntl on POSIX.
    """
    if sys.platform == "win32":
        try:
            import msvcrt
            lock_file.seek(0)
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_LOCK, 1)
        except Exception:
            pass
        try:
            yield
        finally:
            try:
                lock_file.seek(0)
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
            except Exception:
                pass
    else:
        locked = False
        try:
            import fcntl
            fcntl.flock(lock_file, fcntl.LOCK_EX)
            locked = True
        except Exception:
            pass
        try:
            yield
        finally:
            if locked:
                try:
                    import fcntl
                    fcntl.flock(lock_file, fcntl.LOCK_UN)
                except Exception:
                    pass

# Canonical mandatory receipt fields
MANDATORY_RECEIPT_FIELDS = ("receipt_id", "command", "exit_code", "git_tree_sha", "metrics")

# Optional receipt fields permitted by validation schema
OPTIONAL_RECEIPT_FIELDS = (
    "label", "duration_ms", "working_tree_sha", "working_tree_dirty",
    "log_path", "has_warnings", "flaky_retry", "prior_failures_count",
    "unverified", "framework_detected", "xfail",
    "timestamp", "executed_at", "timestamp_utc"
)

# Known test runner binaries
KNOWN_TEST_RUNNERS = (
    "pytest", "vitest", "jest", "mocha", "cargo test",
    "python -m pytest", "python3 -m pytest",
    "python -m unittest", "python3 -m unittest",
    "node --test", "npx jest", "npx vitest",
    "go test", "rspec"
)

def is_known_test_runner(cmd):
    """
    Checks if command invokes a known test runner binary.
    """
    if not cmd or not isinstance(cmd, str):
        return False
    cmd_lower = cmd.lower()
    return any(runner in cmd_lower for runner in KNOWN_TEST_RUNNERS)

def parse_waiver_expiry(expires_at):
    """
    Parses a waiver expiration string into a timezone-aware UTC datetime.
    Accepts ISO timestamps or date-only YYYY-MM-DD (normalized to end of day 23:59:59 UTC).
    Returns None if unparseable or invalid.
    """
    if not expires_at or not isinstance(expires_at, str):
        return None
    expires_at = expires_at.strip()
    if not expires_at:
        return None

    exp = None
    for fmt in (None, "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            if fmt is None:
                parsed = datetime.datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            else:
                parsed = datetime.datetime.strptime(expires_at, fmt)

            if parsed.tzinfo is None:
                if len(expires_at) == 10:
                    parsed = parsed.replace(hour=23, minute=59, second=59, tzinfo=datetime.timezone.utc)
                else:
                    parsed = parsed.replace(tzinfo=datetime.timezone.utc)
            exp = parsed
            break
        except Exception:
            continue
    return exp

def is_release_command(cmd_str):
    """
    Tokenizes and inspects a command string using POSIX shlex.
    Detects release commands: git push, gh pr create, gh release create, npm publish.
    Returns:
      True: Definite release command
      False: Definite non-release command
      "unsupported": Ambiguous or unsupported command form (eval, command substitution, unbalanced quotes with release keywords)
    """
    if not cmd_str or not isinstance(cmd_str, str) or not cmd_str.strip():
        return False

    # Check for commands that cannot be safely analyzed via static shell tokenization
    if "eval " in cmd_str or re.search(r'\beval\s+', cmd_str):
        return "unsupported"

    release_keywords = ("git push", "publish", "gh pr create", "gh release create")

    # Command substitution with release keywords or release binaries is unsupported
    if "$(" in cmd_str or "`" in cmd_str:
        if any(kw in cmd_str for kw in release_keywords) or re.search(r'(\$\(|\`)[^\)\`]*(git|gh|npm)\b', cmd_str):
            return "unsupported"

    # Normalize newlines to semicolons so multi-line blocks are handled uniformly
    cmd_str = cmd_str.replace("\n", ";").replace("\r", "")

    # Pre-split on common shell separators that shlex does not split on (embedded ;)
    try:
        raw_tokens = shlex.split(cmd_str)
    except ValueError:
        # shlex.split raises ValueError on unbalanced quotes
        release_keywords = ("git push", "publish", "gh pr create", "gh release create")
        if any(kw in cmd_str for kw in release_keywords):
            return "unsupported"
        return False
    except Exception:
        raw_tokens = cmd_str.split()

    # Re-expand tokens that have embedded semicolons (e.g. "ok;git" -> ["ok", ";", "git"])
    expanded = []
    for t in raw_tokens:
        if ";" in t:
            parts = t.split(";")
            for i, p in enumerate(parts):
                if p:
                    expanded.append(p)
                if i < len(parts) - 1:
                    expanded.append(";")
        else:
            expanded.append(t)

    cmds = []
    curr = []
    for t in expanded:
        if t in (";", "&&", "||", "|", "&"):
            if curr:
                cmds.append(curr)
                curr = []
        else:
            curr.append(t)
    if curr:
        cmds.append(curr)

    opts_with_arg = {
        "-C", "-c", "--git-dir", "--work-tree",
        "--namespace", "--super-prefix", "--exec-path", "--config-env"
    }

    def _cmd_is_release(c):
        """Inspect a single tokenised command list for release patterns."""
        if not c:
            return False

        idx = 0
        # Strip leading env / command wrappers and VAR=val assignments
        while idx < len(c) and c[idx] in ("env", "command"):
            idx += 1
            while idx < len(c) and (c[idx].startswith("-") or "=" in c[idx]):
                idx += 1

        # Strip bash -c / sh -c wrappers; recurse into the -c argument
        if idx < len(c) and c[idx] in ("bash", "sh", "dash"):
            if idx + 1 < len(c) and c[idx + 1] == "-c" and idx + 2 < len(c):
                return is_release_command(c[idx + 2])
            return False

        if idx >= len(c):
            return False

        head = c[idx]
        # Normalise absolute paths: /usr/bin/git -> git, /usr/local/bin/npm -> npm
        head_base = os.path.basename(head)

        if len(c) - idx >= 2 and head_base == "npm" and c[idx + 1] == "publish":
            return True
        if len(c) - idx >= 3 and head_base == "gh" and c[idx + 1] in ("pr", "release") and c[idx + 2] == "create":
            return True
        if head_base == "git":
            i2 = idx + 1
            while i2 < len(c):
                arg = c[i2]
                if arg in opts_with_arg:
                    i2 += 2
                    continue
                if any(arg.startswith(prefix + "=") for prefix in opts_with_arg):
                    i2 += 1
                    continue
                if arg.startswith("-"):
                    i2 += 1
                    continue
                if arg == "push":
                    return True
                break
        return False

    results = [_cmd_is_release(c) for c in cmds]
    if any(r is True for r in results):
        return True
    if any(r == "unsupported" for r in results):
        return "unsupported"
    return False

def is_flaky_retry(attempt_history, receipt, curr_tree, curr_wt_sha):
    """
    Checks if this passing check had prior failures ON THE EXACT SAME SNAPSHOT.
    Distinguishes genuine flaky retries on unchanged code from TDD Red-Green progressions.
    """
    label = receipt.get("label")
    rcpt_id = receipt.get("receipt_id")
    prior_failed_same_snapshot = [
        a for a in attempt_history
        if a.get("label") == label
        and a.get("receipt_id") != rcpt_id
        and (a.get("exit_code") != 0 or a.get("metrics", {}).get("failed", 0) > 0)
        and a.get("git_tree_sha") == curr_tree
        and a.get("working_tree_sha", "") == curr_wt_sha
    ]
    return len(prior_failed_same_snapshot) > 0

def calculate_policy_disposition(checks):
    """
    Reduces a list of checks into a policy disposition: RED, AMBER, or GREEN.
    If any check has unverified: True, disposition cannot be GREEN (set to AMBER if no RED failures).
    """
    has_failure = any(
        c.get("exit_code") != 0 or c.get("metrics", {}).get("failed", 0) > 0
        for c in checks
    )
    if has_failure:
        return "RED"

    has_skips = any(c.get("metrics", {}).get("skipped", 0) > 0 for c in checks)
    has_flaky = any(c.get("flaky_retry", False) for c in checks)
    has_warnings = any(c.get("has_warnings", False) for c in checks)
    has_unverified = any(c.get("unverified", False) for c in checks)

    if has_skips or has_flaky or has_warnings or has_unverified:
        return "AMBER"

    return "GREEN"

def validate_receipt_structure(rcpt_data, receipt_id):
    """
    Validates mandatory fields and basic structural integrity of a physical receipt.
    Allows optional fields: 'unverified', 'framework_detected', 'xfail', etc.
    Raises ValueError on missing or corrupt fields.
    """
    if not isinstance(rcpt_data, dict):
        raise ValueError(f"Receipt '{receipt_id}' root is not a valid JSON object.")

    for req_field in MANDATORY_RECEIPT_FIELDS:
        if req_field not in rcpt_data:
            raise ValueError(f"Receipt '{receipt_id}' missing mandatory field '{req_field}'.")

    if rcpt_data.get("receipt_id") != receipt_id:
        raise ValueError(f"Receipt ID mismatch in {receipt_id}.json.")

    if "unverified" in rcpt_data and not isinstance(rcpt_data["unverified"], bool):
        raise ValueError(f"Receipt '{receipt_id}' field 'unverified' must be boolean.")

    if "framework_detected" in rcpt_data and not isinstance(rcpt_data["framework_detected"], str):
        raise ValueError(f"Receipt '{receipt_id}' field 'framework_detected' must be string.")

    if "xfail" in rcpt_data and not isinstance(rcpt_data["xfail"], int):
        raise ValueError(f"Receipt '{receipt_id}' field 'xfail' must be an integer.")

def cross_validate_manifest_and_receipt(check_entry, rcpt_data, current_tree):
    """
    Performs complete field-level cross-consistency and independent receipt integrity validation.
    Raises ValueError with a specific description on any discrepancy.
    """
    label = check_entry.get("label", "unknown")
    cmd = check_entry.get("command", "unknown")
    exit_code = check_entry.get("exit_code", -1)
    check_tree = check_entry.get("git_tree_sha", "")
    metrics = check_entry.get("metrics", {})
    receipt_id = check_entry.get("receipt_id", "unknown")

    rcpt_cmd = rcpt_data.get("command")
    rcpt_exit = rcpt_data.get("exit_code")
    rcpt_tree = rcpt_data.get("git_tree_sha")
    rcpt_wt_sha = rcpt_data.get("working_tree_sha")
    rcpt_wt_dirty = rcpt_data.get("working_tree_dirty", False)
    rcpt_metrics = rcpt_data.get("metrics", {})

    failed = metrics.get("failed", 0)
    passed = metrics.get("passed", 0)
    collected = metrics.get("collected", 0)

    rcpt_failed = rcpt_metrics.get("failed", 0)
    rcpt_passed = rcpt_metrics.get("passed", 0)
    rcpt_collected = rcpt_metrics.get("collected", 0)

    # 1. Manifest vs Receipt alignment
    if rcpt_cmd != cmd:
        raise ValueError(f"Command mismatch between manifest ('{cmd}') and receipt '{receipt_id}' ('{rcpt_cmd}').")

    if rcpt_exit != exit_code:
        raise ValueError(f"Exit code mismatch between manifest ({exit_code}) and receipt '{receipt_id}' ({rcpt_exit}) for '{label}'.")

    if rcpt_tree != check_tree:
        raise ValueError(f"Git tree SHA mismatch between manifest ({check_tree[:8]}) and receipt '{receipt_id}' ({rcpt_tree[:8]}) for '{label}'.")

    if rcpt_wt_dirty or check_entry.get("working_tree_dirty", False):
        raise ValueError(f"Check '{label}' was executed against a dirty working tree with unstaged modifications.")

    if rcpt_wt_sha and check_entry.get("working_tree_sha") and rcpt_wt_sha != check_entry.get("working_tree_sha"):
        raise ValueError(f"Working tree SHA mismatch between manifest ({check_entry.get('working_tree_sha')[:8]}) and receipt '{receipt_id}' ({rcpt_wt_sha[:8]}).")

    if rcpt_failed != failed or rcpt_passed != passed or rcpt_collected != collected:
        raise ValueError(f"Test metric mismatch between manifest (P:{passed}, F:{failed}, C:{collected}) and receipt '{receipt_id}' (P:{rcpt_passed}, F:{rcpt_failed}, C:{rcpt_collected}) for '{label}'.")

    if check_entry.get("unverified", False) != rcpt_data.get("unverified", False):
        raise ValueError(f"Unverified status mismatch between manifest ({check_entry.get('unverified', False)}) and receipt '{receipt_id}' ({rcpt_data.get('unverified', False)}) for '{label}'.")

    # 2. Independent receipt integrity
    if rcpt_exit != 0:
        raise ValueError(f"Physical receipt '{receipt_id}' recorded non-zero exit code {rcpt_exit} for '{label}'.")

    if rcpt_failed > 0:
        raise ValueError(f"Physical receipt '{receipt_id}' recorded {rcpt_failed} failed tests for '{label}'.")

    if rcpt_tree != current_tree:
        raise ValueError(f"Mixed snapshot detected. Physical receipt '{receipt_id}' tree {rcpt_tree[:8]} does not match current git tree {current_tree[:8]}.")


def is_test_file_path(file_path: str) -> bool:
    """
    Identifies whether a repository path is a test or specification file.
    Matches paths in tests/ directories or files following test/spec naming conventions.
    """
    if not file_path:
        return False
    norm_path = file_path.replace("\\", "/").strip().lower()
    parts = norm_path.split("/")
    if any(part in ("tests", "test", "__tests__") for part in parts):
        return True
    filename = parts[-1]
    patterns = (
        r"^test_.*\.py$",
        r".*_test\.py$",
        r".*\.(?:test|spec)\.[jt]sx?$",
        r".*_test\.go$",
        r"^test.*\.java$",
        r"^.*test\.java$"
    )
    return any(re.match(pat, filename, re.IGNORECASE) for pat in patterns)


def check_git_assertion_lock(repo_root, base_ref=None, allow_spec_evolution=False):
    """
    Enforces the Git Assertion Lock (WP-04 / SEC-03):
    Pre-existing test files at Git base/HEAD are strictly immutable during bug repairs.
    Any modification ('M') or deletion ('D') to an existing test file is blocked unless
    allow_spec_evolution is True.
    Newly added test files ('A') are always permitted.

    Returns:
        tuple[bool, list[str]]: (passed, list_of_tampered_files)
    """
    if allow_spec_evolution:
        return True, []

    if os.environ.get("SPEC_EVOLUTION", "").lower() in ("1", "true", "yes") or \
       os.environ.get("ANTIGRAVITY_SPEC_EVOLUTION", "").lower() in ("1", "true", "yes"):
        return True, []

    import subprocess
    repo_path = str(repo_root)
    tampered_files = set()

    # 1. Inspect uncommitted modifications vs HEAD
    try:
        diff_out = subprocess.check_output(
            ["git", "-C", repo_path, "diff", "--name-status", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True
        )
        for line in diff_out.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split(None, 1)
            status_code = parts[0]
            file_name = parts[1] if len(parts) > 1 else ""
            if " -> " in file_name:
                file_name = file_name.split(" -> ")[-1]
            if is_test_file_path(file_name):
                if status_code.startswith("M") or status_code.startswith("D"):
                    tampered_files.add(file_name)
    except Exception:
        pass

    # 2. Inspect committed modifications between base_ref and HEAD
    if not base_ref:
        for candidate in ["origin/main", "origin/master", "main", "master", "@{u}"]:
            try:
                mb = subprocess.check_output(
                    ["git", "-C", repo_path, "merge-base", "HEAD", candidate],
                    stderr=subprocess.DEVNULL,
                    text=True
                ).strip()
                head_sha = subprocess.check_output(
                    ["git", "-C", repo_path, "rev-parse", "HEAD"],
                    stderr=subprocess.DEVNULL,
                    text=True
                ).strip()
                if mb and mb != head_sha:
                    base_ref = mb
                    break
            except Exception:
                continue

    if base_ref:
        try:
            diff_base = subprocess.check_output(
                ["git", "-C", repo_path, "diff", "--name-status", base_ref, "HEAD"],
                stderr=subprocess.DEVNULL,
                text=True
            )
            for line in diff_base.splitlines():
                line = line.strip()
                if not line:
                    continue
                parts = line.split(None, 1)
                status_code = parts[0]
                file_name = parts[1] if len(parts) > 1 else ""
                if " -> " in file_name:
                    file_name = file_name.split(" -> ")[-1]
                if is_test_file_path(file_name):
                    # 'A' means added on this branch -> permitted
                    # 'M' or 'D' means existed on base and was mutated/removed -> prohibited
                    if status_code.startswith("M") or status_code.startswith("D"):
                        tampered_files.add(file_name)
        except Exception:
            pass

    tampered_list = sorted(list(tampered_files))
    return len(tampered_list) == 0, tampered_list

