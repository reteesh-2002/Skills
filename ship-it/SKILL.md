---
name: ship-it
description: Production release and Git hygiene automator. Formats conventional commits, manages branch cleanups, checks for unstaged artifacts, verifies clean git diffs, and drafts production-ready PR descriptions with test plans and risk assessments. Use when ready to commit, stage, branch, or create a release pull request.
---

# Ship It

Clean Git release and repository hygiene automator. Converts working changes into atomic Conventional Commits, scans for leaked credentials, and keeps branches clean.

---

## 1. Clean Git Invariants

1. **Preserve Unrelated Changes**: Only stage files relevant to the active task. Never run destructive resets (`git reset --hard`, `git clean -fd`) that discard unrelated user work.
2. **Atomic Commits**: Keep cohesive changes (backend contract + UI component) together in a single commit.
3. **No Leaked Secrets**: Scan staged diffs for private keys, credentials, and tokens.
4. **No Build Residue**: Never commit build artifacts (`dist/`, `node_modules/`, `.env`, temp files).
5. **Push Requires Consent**: Evaluating technical readiness or committing locally does **not** push to remotes without explicit user instruction.

---

## 2. Release Steps

1. **Audit Diff**: Inspect `git status --porcelain` and `git diff --stat`.
2. **Scan Staged Secrets**:
   ```bash
   git diff --cached | grep -iE 'BEGIN (RSA|OPENSSH|EC|DSA|PGP) PRIVATE KEY|AIzaSy[0-9A-Za-z_-]{33}|ghp_[0-9A-Za-z]{36}|github_pat_[0-9A-Za-z_]{82}|sk-[a-zA-Z0-9]{20,}|AKIA[0-9A-Z]{16}' || true
   ```
   If a genuine secret is detected, halt immediately and alert the user.
3. **Conventional Commit**: Format commit message cleanly:
   `git commit -m "<type>(<optional-scope>): <imperative summary>"`
   Types: `feat`, `fix`, `refactor`, `perf`, `style`, `test`, `chore`.
4. **Deterministic Release Gate Evaluation**: When evidence compliance is enabled, run `verify-release-gate.sh` to enforce the Fail-Closed Rule before release.
5. **Ready for Push**: Report commit hash and summary. Wait for explicit user confirmation before `git push`.
