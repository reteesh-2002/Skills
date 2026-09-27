---
name: ship-it
description: Production release and Git hygiene automator. Formats conventional commits, manages branch cleanups, checks for unstaged artifacts, verifies clean git diffs, and drafts production-ready PR descriptions with test plans and risk assessments. Use when ready to commit, stage, branch, or create a release pull request.
---

# Ship It

Production Git release and hygiene engine. Turns messy local working directories into clean, atomic Conventional Commits and production-ready Pull Request descriptions with zero stray artifacts.

## The Clean Repository Invariants

Before staging or committing, Ship It guarantees:
1. **No Accidental Secret Leaks**: Diff check for API keys, `.env` files, passwords, or bearer tokens.
2. **No Junk Artifacts**: `.DS_Store`, `node_modules`, `__pycache__`, `.system_generated`, or temporary test dumps are excluded or added to `.gitignore`.
3. **No Unfinished Debug Residue**: Remove stray `console.log("here 111")`, `breakpoint()`, or commented-out blocks of dead code.
4. **Atomic Commits**: Group related changes logically. Do not dump frontend styling, database migrations, and CI config into a single massive commit unless it is an initial commit.

---

## The 5-Step Release Workflow

### Step 1: Pre-Flight Working Tree Audit
Inspect the git status and diff:
```bash
git status --porcelain
git diff --stat
```
- Categorize modified files: source code, tests, docs, assets.
- Identify untracked files and verify whether they should be committed or ignored.

### Step 2: Secret & Artifact Scanning
Scan staged diffs for common leak patterns:
```bash
git diff --cached | grep -iE 'api[_-]?key|secret|password|bearer|aizasy[0-9a-za-z-_]{33}|ghp_[0-9a-za-z]{36}|github_pat_|sk-[a-za-z0-9]{20,}' || true
```
- If a potential secret is detected: **HALT IMMEDIATELY**. Alert the user and do not proceed with staging or committing.

### Step 3: Atomic Conventional Commit Construction
Stage the audited files and write commit messages following the **Conventional Commits 1.0.0** specification:

```bash
git add <files>
git commit -m "<type>(<optional scope>): <imperative description>"
```

### Step 4: Deterministic Release Gate Evaluation (MANDATORY BEFORE PUSH)
After committing and before executing `git push`, opening a PR, or tagging a release, evaluate the machine-readable evidence manifest against the clean committed tree:
```bash
bash scripts/verify-release-gate.sh
```
- **Fail-Closed Rule**: If `verify-release-gate.sh` exits non-zero, **HALT IMMEDIATELY**.
- Do NOT proceed with `git push` or PR creation if:
  1. The git tree SHA in `.evidence/manifest.v1.json` does not match `HEAD` / current tree.
  2. The working directory has unstaged modifications (`working_tree_dirty == true`).
  3. The manifest contains 0 verification checks.
  4. Any check exited non-zero or reported failing tests.
  5. The policy disposition is RED or un-waived AMBER.
- Never bypass this gate based on conversational chat statements or 1-line heartbeats.

#### Commit Types:
- `feat`: New user-facing feature or capability.
- `fix`: Bug fix for an existing defect.
- `refactor`: Code change that neither fixes a bug nor adds a feature.
- `perf`: Code change that improves performance.
- `style`: Formatting, missing semicolons, zero logic change.
- `test`: Adding or correcting tests.
- `chore`: Build process, dependency updates, tooling config.

#### Rules:
- Use imperative mood: *"add user auth"* (not *"added"* or *"adds"*).
- First line max 72 characters.
- Lowercase description after the colon.

### Step 5: The Dual-Surface Release Card (15–20 Lines Foreground)

On routine commits or feature releases, emit a compact, transparent release card:

```markdown
### 📦 Ship-It Release: [GREEN / AMBER] — [commit message]

* **Commit**: `[hash]` on branch `[branch-name]`
* **Audit**: 0 secrets detected · [N] files staged · clean working tree
* **Material Changes**:
  - [`file1.ext`](file:///path/to/file1) — [1-sentence summary]
  - [`file2.ext`](file:///path/to/file2) — [1-sentence summary]
* **Verification Reference**: Backed by QA run [`qa-[id].log`](file:///path/to/log)
* **Rollback Plan**: `git revert [hash]`
* **Run / Deploy**: `[command to run locally or deploy]`
```

#### Opt-In Full PR Description Mode:
Only generate the full multi-section PR document (Overview, 5-row changes table, Risk Assessment, and Rollback Checklist) when the user **explicitly asks** to *"draft a PR description"* or *"prepare release notes"*.

#### Pipeline Suppression:
When Ship-It runs inside a chained pipeline, it supplies its commit metadata directly to the parent orchestrator and emits a 1-line milestone:
`✓ [ship-it]: committed feat(scope): desc [hash] (clean working tree)`
