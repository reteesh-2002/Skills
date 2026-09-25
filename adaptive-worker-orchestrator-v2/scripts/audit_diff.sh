#!/usr/bin/env bash
# Usage: audit_diff.sh <worktree> <base-branch> <allowed-path-prefix>...
# Checks a worker's changes (committed + uncommitted) against its declared scope.
# Flags: files outside scope, protected files, placeholder markers in added lines.
# Extra protected patterns: set PROTECTED_EXTRA="regex" (e.g. "^src/shared/|^contracts/").
# Exit 0 = clean, 1 = violations, 2 = usage error.
set -uo pipefail

[ $# -ge 3 ] || { echo "Usage: $0 <worktree> <base-branch> <allowed-path>..." >&2; exit 2; }
wt=$1; base=$2; shift 2
allowed=("$@")
cd "$wt" || exit 2

protected='(^|/)(package\.json|package-lock\.json|yarn\.lock|pnpm-lock\.yaml|pyproject\.toml|poetry\.lock|uv\.lock|requirements[^/]*\.txt|go\.mod|go\.sum|Cargo\.toml|Cargo\.lock|Gemfile(\.lock)?|composer\.(json|lock)|\.env[^/]*)$'
[ -n "${PROTECTED_EXTRA:-}" ] && protected="$protected|$PROTECTED_EXTRA"
# Exclude language constructs like NotImplementedError, pass, etc.
placeholder='(\bTODO\b|\bFIXME\b|\bXXX\b|\bnot implemented\b|\bplaceholder\b|\blorem ipsum\b)'

mb=$(git merge-base "$base" HEAD 2>/dev/null || echo "$base")
files=$( { git diff --name-only "$mb"; git ls-files --others --exclude-standard; } | sort -u )
fail=0

if [ -z "$files" ]; then echo "No changes found."; exit 0; fi

wt_root="$(pwd -P)"

while IFS= read -r f; do
  [ -z "$f" ] && continue

  # Handle symlinks safely (F12, P20)
  if [ -L "$f" ]; then
    target=$(readlink -f "$f" || true)
    case "$target" in
      "$wt_root"/*) ;; # Inside sandbox
      *)
        echo "OUT-OF-SCOPE-SYMLINK: $f points outside worktree sandbox ($target)"
        fail=1
        continue
        ;;
    esac
  fi

  ok=0
  for a in "${allowed[@]}"; do
    prefix="${a%/}"
    if [[ "$f" == "$prefix" || "$f" == "$prefix"/* ]]; then
      ok=1
      break
    fi
  done
  [ $ok -eq 0 ] && { echo "OUT-OF-SCOPE: $f"; fail=1; }
  if echo "$f" | grep -Eq "$protected"; then echo "PROTECTED: $f"; fail=1; fi
done <<< "$files"

# Check diff for placeholder markers
hits=$(git diff -U0 "$mb" | grep -E '^\+[^+]' | grep -v 'NotImplementedError' | grep -Ei "$placeholder" || true)

# Also check untracked files for placeholder markers (F13, P22)
untracked_files=$(git ls-files --others --exclude-standard)
if [ -n "$untracked_files" ]; then
  while IFS= read -r uf; do
    [ -f "$uf" ] || continue
    uh=$(grep -v 'NotImplementedError' "$uf" 2>/dev/null | grep -Ei "$placeholder" || true)
    if [ -n "$uh" ]; then
      hits=$(printf "%s\n%s: %s" "$hits" "$uf" "$uh")
    fi
  done <<< "$untracked_files"
fi

if [ -n "$hits" ]; then
  echo "WARNING: PLACEHOLDERS detected in added or untracked lines:"
  echo "$hits" | head -20
  if [ "${FAIL_ON_PLACEHOLDERS:-0}" = "1" ]; then
    fail=1
  fi
fi

[ $fail -eq 0 ] && echo "CLEAN: $(echo "$files" | wc -l) file(s), all in scope."
exit $fail
