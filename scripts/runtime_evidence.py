#!/usr/bin/env python3
"""
Antigravity Runtime Evidence Engine
Shared validation, parsing, and policy reduction for exec-proxy.sh, verify-release-gate.sh, and hooks.
"""

import os
import sys
import json
import shlex
import datetime

# Canonical mandatory receipt fields
MANDATORY_RECEIPT_FIELDS = ("receipt_id", "command", "exit_code", "git_tree_sha", "metrics")

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
    Correctly accounts for:
      - git options with arguments (e.g. git -C . push)
      - env wrappers: env git push, env -i git push
      - absolute paths: /usr/bin/git push, /usr/local/bin/git push
      - shell separators embedded in tokens: echo ok;git push
      - newline-separated multi-statement commands: git status\\ngit push
      - bash -c / sh -c wrappers: bash -c "git push"
    """
    if not cmd_str or not isinstance(cmd_str, str) or not cmd_str.strip():
        return False

    # Normalize newlines to semicolons so multi-line blocks are handled uniformly
    cmd_str = cmd_str.replace("\n", ";").replace("\r", "")

    # Pre-split on common shell separators that shlex does not split on (embedded ;)
    try:
        raw_tokens = shlex.split(cmd_str)
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

    return any(_cmd_is_release(c) for c in cmds)

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

    if has_skips or has_flaky or has_warnings:
        return "AMBER"

    return "GREEN"

def validate_receipt_structure(rcpt_data, receipt_id):
    """
    Validates mandatory fields and basic structural integrity of a physical receipt.
    Raises ValueError on missing or corrupt fields.
    """
    if not isinstance(rcpt_data, dict):
        raise ValueError(f"Receipt '{receipt_id}' root is not a valid JSON object.")

    for req_field in MANDATORY_RECEIPT_FIELDS:
        if req_field not in rcpt_data:
            raise ValueError(f"Receipt '{receipt_id}' missing mandatory field '{req_field}'.")

    if rcpt_data.get("receipt_id") != receipt_id:
        raise ValueError(f"Receipt ID mismatch in {receipt_id}.json.")

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

    # 2. Independent receipt integrity
    if rcpt_exit != 0:
        raise ValueError(f"Physical receipt '{receipt_id}' recorded non-zero exit code {rcpt_exit} for '{label}'.")

    if rcpt_failed > 0:
        raise ValueError(f"Physical receipt '{receipt_id}' recorded {rcpt_failed} failed tests for '{label}'.")

    if rcpt_tree != current_tree:
        raise ValueError(f"Mixed snapshot detected. Physical receipt '{receipt_id}' tree {rcpt_tree[:8]} does not match current git tree {current_tree[:8]}.")
