#!/usr/bin/env bash
# Usage:
#   setup_worktrees.sh <base-branch> <worker-name>...   create one worktree + branch per worker
#   setup_worktrees.sh cleanup                          safely remove worktrees and preserve unmerged branches
# Worktrees live inside the repo's git dir: .git/.orch-worktrees/<worker>; branches are orch/<worker>.
set -euo pipefail

repo=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "Not a git repo: use scoped directories instead." >&2; exit 2; }
git_dir=$(git -C "$repo" rev-parse --absolute-git-dir 2>/dev/null || git -C "$repo" rev-parse --git-dir)
root="$git_dir/.orch-worktrees"

if [ "${1:-}" = "cleanup" ]; then
  if [ -d "$root" ]; then
    for wt in "$root"/*; do
      [ -d "$wt" ] || continue
      wname=$(basename "$wt")
      branch="orch/$wname"

      # Check if worktree directory has uncommitted work (tracked or untracked) (F04, P19)
      wt_dirty=$(git -C "$wt" status --porcelain 2>/dev/null || true)
      if [ -n "$wt_dirty" ]; then
        rescue_wt_branch="orch/rescue-$wname-uncommitted-$(date +%s)"
        echo "Worktree $wname has uncommitted changes; rescuing to $rescue_wt_branch before detachment..."
        if git -C "$wt" checkout -b "$rescue_wt_branch" 2>/dev/null && \
           git -C "$wt" add -A 2>/dev/null && \
           git -C "$wt" commit -m "chore(orch): auto-rescue uncommitted work from $wname before worktree cleanup" --no-verify 2>/dev/null; then
          echo "Preserved uncommitted work from $wname in branch $rescue_wt_branch"
        else
          echo "ERROR: Failed to commit rescue branch for dirty worktree $wname. Aborting cleanup to prevent data loss." >&2
          exit 1
        fi
      fi

      # Verify worktree is completely clean before removal
      if [ -n "$(git -C "$wt" status --porcelain 2>/dev/null)" ]; then
        echo "ERROR: Worktree $wname still contains uncommitted changes. Aborting cleanup to prevent data loss." >&2
        exit 1
      fi

      # Safely detach worktree (never force remove unverified state)
      if ! git -C "$repo" worktree remove "$wt" 2>/dev/null; then
        echo "ERROR: Failed to remove worktree $wname." >&2
        exit 1
      fi

      # Check if branch has unmerged work before deleting
      if git -C "$repo" rev-parse --verify --quiet "$branch" >/dev/null; then
        if git -C "$repo" branch --merged HEAD 2>/dev/null | grep -qw "$branch"; then
          git -C "$repo" branch -d "$branch" >/dev/null 2>&1 || true
        else
          rescue_branch="orch/rescue-$wname-$(date +%s)"
          git -C "$repo" branch -m "$branch" "$rescue_branch" >/dev/null 2>&1 || true
          echo "Preserved unmerged branch as $rescue_branch"
        fi
      fi
      echo "removed worktree $wname"
    done
    rmdir "$root" 2>/dev/null || true
  else
    echo "nothing to clean"
  fi
  exit 0
fi

[ $# -ge 2 ] || { echo "Usage: $0 <base-branch> <worker>... | cleanup" >&2; exit 1; }
base=$1; shift
git -C "$repo" rev-parse --verify --quiet "$base" >/dev/null || { echo "Unknown base branch: $base" >&2; exit 1; }
mkdir -p "$root"

# Ensure local git exclude ignores symlinked dependency names so they don't appear as untracked in worktrees
info_exclude="$git_dir/info/exclude"
mkdir -p "$git_dir/info"
touch "$info_exclude"
for dep in node_modules .venv venv vendor target; do
  if ! grep -q "^$dep$" "$info_exclude" 2>/dev/null; then
    echo "$dep" >> "$info_exclude"
  fi
done

for w in "$@"; do
  wt_path="$root/$w"
  git -C "$repo" worktree add -b "orch/$w" "$wt_path" "$base" >/dev/null

  # Symlink common project dependencies so worker test/lint commands work without duplicating disk space
  for dep in node_modules .venv venv vendor target; do
    if [ -e "$repo/$dep" ] && [ ! -e "$wt_path/$dep" ]; then
      ln -s "$repo/$dep" "$wt_path/$dep" 2>/dev/null || true
    fi
  done

  echo "$w -> $wt_path (branch orch/$w)"
done
