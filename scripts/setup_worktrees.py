#!/usr/bin/env python3
"""
Antigravity Cross-Platform Worktree Isolation & Cleanup Engine
Usage:
  setup_worktrees.py <base-branch> <worker-name>...   create one worktree + branch per worker
  setup_worktrees.py cleanup                          safely remove worktrees and preserve unmerged branches

Worktrees live inside the repo's git dir: .git/.orch-worktrees/<worker>; branches are orch/<worker>.
"""

import os
import sys
import time
import shutil
import subprocess
from pathlib import Path


def run_git(args: list[str], cwd: Path | None = None) -> tuple[int, str]:
    """Execute git command and return (code, stdout)."""
    try:
        res = subprocess.run(
            ["git"] + args,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            check=False,
        )
        return res.returncode, res.stdout.strip()
    except Exception as e:
        return 1, str(e)


def get_repo_and_git_dir() -> tuple[Path, Path]:
    code, out = run_git(["rev-parse", "--show-toplevel"])
    if code != 0 or not out:
        print("Not a git repo: use scoped directories instead.", file=sys.stderr)
        sys.exit(2)
    repo = Path(out).resolve()

    code, out = run_git(["rev-parse", "--absolute-git-dir"], cwd=repo)
    if code != 0 or not out:
        code, out = run_git(["rev-parse", "--git-dir"], cwd=repo)
        git_dir = (repo / out).resolve()
    else:
        git_dir = Path(out).resolve()

    return repo, git_dir


def do_cleanup(repo: Path, root: Path):
    if not root.is_dir():
        print("nothing to clean")
        sys.exit(0)

    entries = sorted([p for p in root.iterdir() if p.is_dir()])
    if not entries:
        print("nothing to clean")
        sys.exit(0)

    for wt in entries:
        wname = wt.name
        branch = f"orch/{wname}"

        # 1. Check if worktree directory has uncommitted work (tracked or untracked) (F04, P19)
        code, status_out = run_git(["status", "--porcelain"], cwd=wt)
        if status_out.strip():
            ts = int(time.time())
            rescue_wt_branch = f"orch/rescue-{wname}-uncommitted-{ts}"
            print(f"Worktree {wname} has uncommitted changes; rescuing to {rescue_wt_branch} before detachment...")

            run_git(["checkout", "-b", rescue_wt_branch], cwd=wt)
            run_git(["add", "-A"], cwd=wt)
            c_code, _ = run_git(
                ["commit", "-m", f"chore(orch): auto-rescue uncommitted work from {wname} before worktree cleanup", "--no-verify"],
                cwd=wt,
            )
            if c_code == 0:
                print(f"Preserved uncommitted work from {wname} in branch {rescue_wt_branch}")
            else:
                print(f"ERROR: Failed to commit rescue branch for dirty worktree {wname}. Aborting cleanup to prevent data loss.", file=sys.stderr)
                sys.exit(1)

        # 2. Verify worktree is completely clean before removal
        code, status_check = run_git(["status", "--porcelain"], cwd=wt)
        if status_check.strip():
            print(f"ERROR: Worktree {wname} still contains uncommitted changes. Aborting cleanup to prevent data loss.", file=sys.stderr)
            sys.exit(1)

        # 3. Safely detach worktree (never force remove unverified state)
        rm_code, rm_err = run_git(["worktree", "remove", str(wt)], cwd=repo)
        if rm_code != 0:
            print(f"ERROR: Failed to remove worktree {wname}.", file=sys.stderr)
            sys.exit(1)

        # 4. Check if branch has unmerged work before deleting
        code, _ = run_git(["rev-parse", "--verify", "--quiet", branch], cwd=repo)
        if code == 0:
            code_merged, merged_out = run_git(["branch", "--merged", "HEAD"], cwd=repo)
            is_merged = any(line.strip().replace("*", "").strip() == branch for line in merged_out.splitlines())
            if is_merged:
                run_git(["branch", "-d", branch], cwd=repo)
            else:
                ts = int(time.time())
                rescue_branch = f"orch/rescue-{wname}-{ts}"
                run_git(["branch", "-m", branch, rescue_branch], cwd=repo)
                print(f"Preserved unmerged branch as {rescue_branch}")

        print(f"removed worktree {wname}")

    try:
        root.rmdir()
    except Exception:
        pass
    sys.exit(0)


def do_setup(repo: Path, root: Path, git_dir: Path, base_branch: str, workers: list[str]):
    code, _ = run_git(["rev-parse", "--verify", "--quiet", base_branch], cwd=repo)
    if code != 0:
        print(f"Unknown base branch: {base_branch}", file=sys.stderr)
        sys.exit(1)

    root.mkdir(parents=True, exist_ok=True)

    # Ensure local git exclude ignores symlinked dependency names
    info_exclude = git_dir / "info" / "exclude"
    info_exclude.parent.mkdir(parents=True, exist_ok=True)
    existing_excludes = info_exclude.read_text(encoding="utf-8", errors="ignore") if info_exclude.exists() else ""

    deps = ["node_modules", ".venv", "venv", "vendor", "target"]
    to_append = [d for d in deps if d not in existing_excludes.splitlines()]
    if to_append:
        with info_exclude.open("a", encoding="utf-8") as f:
            for d in to_append:
                f.write(f"\n{d}\n")

    for w in workers:
        wt_path = root / w
        code, err = run_git(["worktree", "add", "-b", f"orch/{w}", str(wt_path), base_branch], cwd=repo)
        if code != 0:
            print(f"Failed to add worktree {w}: {err}", file=sys.stderr)
            sys.exit(1)

        # Symlink or junction common project dependencies
        for dep in deps:
            src_dep = repo / dep
            dst_dep = wt_path / dep
            if src_dep.exists() and not dst_dep.exists():
                try:
                    if hasattr(os, "symlink"):
                        os.symlink(str(src_dep), str(dst_dep), target_is_directory=src_dep.is_dir())
                except Exception:
                    pass

        print(f"{w} -> {wt_path} (branch orch/{w})")


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <base-branch> <worker>... | cleanup", file=sys.stderr)
        sys.exit(1)

    repo, git_dir = get_repo_and_git_dir()
    root = git_dir / ".orch-worktrees"

    if sys.argv[1] == "cleanup":
        do_cleanup(repo, root)
    else:
        if len(sys.argv) < 3:
            print(f"Usage: {sys.argv[0]} <base-branch> <worker>... | cleanup", file=sys.stderr)
            sys.exit(1)
        base = sys.argv[1]
        workers = sys.argv[2:]
        do_setup(repo, root, git_dir, base, workers)


if __name__ == "__main__":
    main()
