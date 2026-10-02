---
name: ship-it
description: Production release and Git hygiene automator. Formats conventional commits, manages branch cleanups, checks for unstaged artifacts, verifies clean git diffs, and drafts production-ready PR descriptions with test plans and risk assessments. Use when ready to commit, stage, branch, or create a release pull request.
---

# Ship It

Production Git release and repository hygiene engine. Converts working changes into clean, atomic Conventional Commits, enforces deterministic release readiness gates, and maintains repository hygiene.

---

## 1. Clean Repository Invariants

Before staging or committing, Ship It guarantees:
1. **Preserve Unrelated User Changes**: Only stage and commit files relevant to the active task. Never execute indiscriminate `git reset --hard`, `git clean -fd`, or automatic stashing that discards unrelated uncommitted work.
2. **Coherent Atomic Commits**: Keep cohesive changes (e.g. backend contract + frontend component) in a single atomic commit; do NOT split coherent commits solely by file type.
3. **No Accidental Secret Leaks**: Scan staged candidate for actual credentials, high-entropy tokens, and private keys.
4. **No Build or Debug Residue**: Exclude build caches (`node_modules`, `dist/`, `.venv`), temporary logs, or active `debugger;` / `breakpoint()`.
5. **Readiness vs. Publishing Separation**: Evaluating technical release readiness does **not** grant permission to push or publish. Publishing, tagging, or pushing requires explicit user authorization.

---

## 2. The 5-Step Release Workflow

### Step 1: Pre-Flight Working Tree Audit
Inspect git status and diff:
```bash
git status --porcelain
git diff --stat
```
Categorize modified, added, and untracked files. Do not touch or delete unrelated files.

### Step 2: Precise Staged Candidate Secret Scanning
Stage the candidate files, then scan the **staged candidate diff** using precise credential and key patterns:
```bash
git add <files>

# Precise pattern-based secret scan (avoids false-positive keyword blocks on variable names)
git diff --cached | grep -iE 'BEGIN (RSA|OPENSSH|EC|DSA|PGP) PRIVATE KEY|AIzaSy[0-9A-Za-z_-]{33}|ghp_[0-9A-Za-z]{36}|github_pat_[0-9A-Za-z_]{82}|sk-[a-zA-Z0-9]{20,}|AKIA[0-9A-Z]{16}|xox[baprs]-[0-9A-Za-z]{10,}' || true
```
- If a genuine credential, API token, or private key is found: **HALT IMMEDIATELY**. Alert the user and do not proceed.
- Also verify no `.env*`, `.pem`, or `.key` files are accidentally staged in `git diff --cached --name-only`.

### Step 3: Atomic Conventional Commit Construction
Construct the commit message following **Conventional Commits 1.0.0**:
```bash
git commit -m "<type>(<optional-scope>): <imperative description>"
```
- Types: `feat`, `fix`, `refactor`, `perf`, `style`, `test`, `chore`.
- Imperative mood, first line ≤ 72 characters, lowercase description after the colon.

### Step 4: Deterministic Release Gate Evaluation (Pre-Push)
After committing and before pushing, opening a PR, or publishing, evaluate the machine-readable evidence manifest against the clean committed tree:
```bash
# Run explicit final verification against the clean committed snapshot:
scripts/exec-proxy.sh --label test_conformance <your-test-command>
bash scripts/verify-release-gate.sh
```
- **Fail-Closed Rule**: If `verify-release-gate.sh` exits non-zero, **HALT IMMEDIATELY**.
- **Assistance vs. Boundary**: Local hook interception is a developer assistance guardrail, not a complete security boundary. Authoritative enforcement occurs at the supported release command and CI pipeline.
- **Fail conditions**:
  1. Git tree SHA in `.evidence/manifest.v1.json` does not match committed tree.
  2. Working tree has uncommitted modifications (`working_tree_dirty == true`).
  3. Manifest contains 0 verification checks or zero-inventory unverified checks.
  4. Any check exited non-zero or reported failing tests.
  5. Policy disposition is RED or un-waived AMBER.

---

## 3. Compact Readiness Receipt

Follow [`references/output-policy.md`](../references/output-policy.md). Structure release output using the **Compact Readiness Receipt**:

```markdown
### 📦 Release Readiness Receipt
- **Candidate**: `[commit_hash]` on branch `[branch]` (tree SHA: `[tree_sha]`)
- **Staged Surface**: [N] files modified (+[added] / -[deleted])
- **Checks Evaluated**:
  - `[check_1]`: 🟢 PASS ([N]/[N] tests, exit 0) — [rcpt_id]
  - `[check_2]`: 🟢 PASS (syntax clean) — [rcpt_id]
- **Unresolved Blockers**: None (or list of pending waivers)
- **Authorized Action**: Ready for review / awaiting push approval
- **Publication Result**: Unpublished (staged locally)
```

Clearly distinguish **ready to publish** from **published**. Pushing requires separate explicit user consent.

#### Pipeline Milestone Suppression:
When Ship-It runs inside an automated pipeline, emit a single-line milestone:
`✓ [ship-it]: Committed feat(scope): desc [hash] (clean tree, gate PASS)`
