---
name: ship-it
description: Production release and Git hygiene automator. Formats conventional commits, manages branch cleanups, checks for unstaged artifacts, verifies clean git diffs, and drafts production-ready PR descriptions with test plans and risk assessments. Use when ready to commit, stage, branch, or create a release pull request.
---

# Ship It

Production Git release and repository hygiene engine. Converts working changes into clean, atomic Conventional Commits, enforces deterministic release readiness gates, and maintains repository hygiene.

---

## 1. Clean Repository Invariants

Before staging or committing, Ship It guarantees:
1. **No Accidental Secret Leaks**: Scan staged candidate for actual credentials, high-entropy tokens, and private keys.
2. **No Stray Build Artifacts**: Exclude or ignore `.DS_Store`, `node_modules`, `__pycache__`, build directories, or scratch logs.
3. **No Debug Residue**: Remove active `breakpoint()`, `debugger;`, or temporary tracing logs.
4. **Atomic Conventional Commits**: Group related changes logically following Conventional Commits 1.0.0.
5. **Readiness vs. Publishing Separation**: Evaluating technical release readiness does **not** grant permission to push or publish. Publishing, tagging, or pushing requires explicit user consent.

---

## 2. The 5-Step Release Workflow

### Step 1: Pre-Flight Working Tree Audit
Inspect the git status and diff:
```bash
git status --porcelain
git diff --stat
```
Categorize modified, added, and untracked files. Identify whether untracked files belong in `.gitignore`.

### Step 2: Precise Staged Candidate Secret Scanning
Stage the candidate files first, then scan the **staged candidate diff** using precise credential and key patterns:
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
- **Separate Readiness from Publishing Permission**: Passing the release gate proves the candidate commit is technically ready. It does **not** authorize autonomous `git push` or package publishing. Present the verified readiness result and request explicit user authorization before executing any network push or publish action.
- Block release if:
  1. Git tree SHA in `.evidence/manifest.v1.json` does not match committed tree.
  2. Working tree has uncommitted modifications (`working_tree_dirty == true`).
  3. Manifest contains 0 verification checks.
  4. Any check exited non-zero or reported failing tests.
  5. Policy disposition is RED or un-waived AMBER.

### Step 5: Routine Output Summary (4–8 Lines Target)
Follow [`references/output-policy.md`](../references/output-policy.md):

```markdown
### 📦 Ship-It: [GREEN / AMBER] — [commit message]
* **Commit**: `[hash]` on `[branch]` (clean tree, 0 secrets detected)
* **Changes**: [`file1.ext`](file:///path/to/file1) (summary), [`file2.ext`](file:///path/to/file2) (summary)
* **Verification Proof**: Backed by conformance run ([`.evidence/manifest.v1.json`](file:///.evidence/manifest.v1.json))
* **Release Status**: Candidate technically ready; awaiting user authorization to push.
* **Rollback Plan**: `git revert [hash]`
```

#### Pipeline Milestone Suppression:
When Ship-It runs inside an automated pipeline, emit a single-line milestone:
`✓ [ship-it]: Committed feat(scope): desc [hash] (clean tree, gate PASS)`
