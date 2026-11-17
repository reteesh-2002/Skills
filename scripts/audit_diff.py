#!/usr/bin/env python3
"""
Antigravity Cross-Platform Diff & Boundary Auditor
Usage: audit_diff.py <worktree> <base-branch> <allowed-path-prefix>...

Checks a worker's changes (committed + uncommitted) against its declared scope.
Flags: files outside scope, protected files, placeholder markers in added lines.
Extra protected patterns: set PROTECTED_EXTRA="regex" (e.g. "^src/shared/|^contracts/").
Exit 0 = clean, 1 = violations, 2 = usage error.
"""

import os
import re
import sys
import subprocess
from pathlib import Path


PROTECTED_DEFAULT_REGEX = (
    r"(^|/)(package\.json|package-lock\.json|yarn\.lock|pnpm-lock\.yaml|"
    r"pyproject\.toml|poetry\.lock|uv\.lock|requirements[^/]*\.txt|go\.mod|go\.sum|"
    r"Cargo\.toml|Cargo\.lock|Gemfile(\.lock)?|composer\.(json|lock)|\.env[^/]*)$"
)

PLACEHOLDER_REGEX = re.compile(
    r"(\bTODO\b|\bFIXME\b|\bXXX\b|\bnot implemented\b|\bplaceholder\b|\blorem ipsum\b)",
    re.IGNORECASE,
)


def run_git(args: list[str], cwd: Path) -> tuple[int, str]:
    """Run a git command in the target directory."""
    try:
        res = subprocess.run(
            ["git"] + args,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=False,
        )
        return res.returncode, res.stdout.strip()
    except Exception as e:
        return 1, ""


def main():
    if len(sys.argv) < 4:
        print(f"Usage: {sys.argv[0]} <worktree> <base-branch> <allowed-path>...", file=sys.stderr)
        sys.exit(2)

    wt_raw = sys.argv[1]
    base_branch = sys.argv[2]
    allowed_args = sys.argv[3:]

    wt_path = Path(wt_raw).resolve()
    if not wt_path.is_dir():
        print(f"Error: Worktree directory does not exist: {wt_raw}", file=sys.stderr)
        sys.exit(2)

    # Normalize allowed prefixes (strip leading ./ and trailing slashes)
    allowed_prefixes = []
    for a in allowed_args:
        clean = a.strip()
        while clean.startswith("./") or clean.startswith(".\\"):
            clean = clean[2:]
        clean = clean.replace("\\", "/").rstrip("/")
        if clean:
            allowed_prefixes.append(clean)

    # Compile protected pattern
    extra_prot = os.environ.get("PROTECTED_EXTRA", "")
    prot_pattern = f"{PROTECTED_DEFAULT_REGEX}|{extra_prot}" if extra_prot else PROTECTED_DEFAULT_REGEX
    prot_re = re.compile(prot_pattern)

    # Find merge base
    _, mb = run_git(["merge-base", base_branch, "HEAD"], cwd=wt_path)
    if not mb:
        mb = base_branch

    # Collect changed files (diff against merge-base + untracked files)
    _, diff_out = run_git(["diff", "--name-only", mb], cwd=wt_path)
    _, untracked_out = run_git(["ls-files", "--others", "--exclude-standard"], cwd=wt_path)

    all_files = set()
    if diff_out:
        all_files.update(diff_out.splitlines())
    if untracked_out:
        all_files.update(untracked_out.splitlines())

    clean_files = sorted([f.strip().replace("\\", "/") for f in all_files if f.strip()])
    if not clean_files:
        print("No changes found.")
        sys.exit(0)

    fail = 0

    for f_rel in clean_files:
        full_path = wt_path / f_rel

        # Symlink security boundary check (F12, P20)
        if full_path.is_symlink():
            try:
                resolved = full_path.resolve()
                if not (resolved == wt_path or str(resolved).startswith(str(wt_path) + os.sep)):
                    print(f"OUT-OF-SCOPE-SYMLINK: {f_rel} points outside worktree sandbox ({resolved})")
                    fail = 1
                    continue
            except Exception:
                print(f"OUT-OF-SCOPE-SYMLINK: {f_rel} resolution failed")
                fail = 1
                continue

        # Scope check against allowed prefixes
        in_scope = False
        for pfx in allowed_prefixes:
            if f_rel == pfx or f_rel.startswith(f"{pfx}/"):
                in_scope = True
                break

        if not in_scope:
            print(f"OUT-OF-SCOPE: {f_rel}")
            fail = 1

        # Protected file check
        if prot_re.search(f_rel):
            print(f"PROTECTED: {f_rel}")
            fail = 1

    # Check git diff lines for placeholders
    _, patch_out = run_git(["diff", "-U0", mb], cwd=wt_path)
    hits = []
    if patch_out:
        for line in patch_out.splitlines():
            if line.startswith("+") and not line.startswith("+++"):
                added_text = line[1:]
                if "NotImplementedError" in added_text:
                    continue
                if PLACEHOLDER_REGEX.search(added_text):
                    hits.append(added_text.strip())

    # Check untracked files for placeholders (F13, P22)
    if untracked_out:
        for uf in untracked_out.splitlines():
            uf_clean = uf.strip()
            uf_path = wt_path / uf_clean
            if uf_path.is_file() and not uf_path.is_symlink():
                try:
                    content = uf_path.read_text(encoding="utf-8", errors="ignore")
                    for line in content.splitlines():
                        if "NotImplementedError" in line:
                            continue
                        if PLACEHOLDER_REGEX.search(line):
                            hits.append(f"{uf_clean}: {line.strip()}")
                except Exception:
                    pass

    if hits:
        print("WARNING: PLACEHOLDERS detected in added or untracked lines:")
        for h in hits[:20]:
            print(h)
        if os.environ.get("FAIL_ON_PLACEHOLDERS") == "1":
            fail = 1

    if fail == 0:
        print(f"CLEAN: {len(clean_files)} file(s), all in scope.")
    sys.exit(fail)


if __name__ == "__main__":
    main()
