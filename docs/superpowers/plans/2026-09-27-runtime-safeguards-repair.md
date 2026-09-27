# Runtime Safeguards Repair & Skills Refinement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Repair the 5 critical runtime safeguards, consolidate the planning triad into `plan-master` with thin aliases, adopt Superpowers TDD and review checkpoints, and construct a 3-task empirical benchmark.

**Architecture:** Harden physical shell scripts (`setup_worktrees.sh`, `exec-proxy.sh`, `verify-release-gate.sh`) with strict boolean error chaining, transient index disk hashing, receipt content validation, and JSON hook compliance. Reduce alias skills to 15-line forwarders, and construct a headless benchmark comparison harness.

**Tech Stack:** Bash, Python 3, Git, Node.js test runner, Antigravity Customization Engine.

**Spec:** `docs/superpowers/specs/2026-09-27-runtime-safeguards-repair-design.md`

## Global Constraints

- Never use `|| true` on destructive or error-recovery git operations.
- All receipt files must have validated schema, exit code consistency, and physical presence.
- Antigravity pre-tool hooks must always emit valid JSON (`{"decision": "allow"}` or `{"decision": "deny", "reason": "..."}`).
- Releases require a clean working tree (`working_tree_dirty == False`); ordinary commits are decoupled from pre-push gating.
- Every task must strictly follow TDD: write a failing test first, verify failure (RED), implement minimal code, verify pass (GREEN), then commit.

## Review Focus

1. Dirty worktree cleanup: verify cleanup aborts and preserves directory when rescue commit is blocked.
2. Unstaged disk modification: verify `exec-proxy.sh` detects dirty disk state so unstaged code cannot forge evidence for clean trees.
3. Empty/corrupt receipt: verify `verify-release-gate.sh` rejects `{}` receipts.
4. Unparseable waiver timestamp: verify gate fails closed on `"NOT-A-DATE"` instead of passing.
5. Hook invocation: verify stdout contains strictly valid JSON and zero human plaintext under `--pre-tool`.

---

### Task 1: Repair Worktree Cleanup Work Preservation

**Files:**
- Modify: `adaptive-worker-orchestrator-v2/scripts/setup_worktrees.sh:20-45`
- Test: `tests/verify_runtime.sh`

**Interfaces:**
- Consumes: Git CLI, working tree path `$wt`
- Produces: Safe cleanup that aborts and exits 1 if uncommitted changes cannot be committed

- [ ] **Step 1: Write the failing test**
Add probe to `tests/verify_runtime.sh` that makes rescue commit fail (e.g. invalid git index or hook failure) and verifies `setup_worktrees.sh cleanup` exits 1 and leaves the directory intact.

- [ ] **Step 2: Run test to verify it fails**
Run: `bash tests/verify_runtime.sh` (or isolated probe). Verify failure (RED).

- [ ] **Step 3: Implement minimal fix in `setup_worktrees.sh`**
Replace loose `|| true` with strict boolean checks:
```bash
if [ -n "$(git -C "$wt" status --porcelain 2>/dev/null)" ]; then
  rescue_wt_branch="orch/rescue-$wname-uncommitted-$(date +%s)"
  if git -C "$wt" checkout -b "$rescue_wt_branch" 2>/dev/null && \
     git -C "$wt" add -A 2>/dev/null && \
     git -C "$wt" commit -m "chore(orch): auto-rescue uncommitted work from $wname before worktree cleanup" --no-verify 2>/dev/null; then
    echo "Preserved uncommitted work from $wname in branch $rescue_wt_branch"
  else
    echo "ERROR: Failed to commit rescue branch for dirty worktree $wname. Aborting cleanup to prevent data loss." >&2
    exit 1
  fi
fi

if [ -n "$(git -C "$wt" status --porcelain 2>/dev/null)" ]; then
  echo "ERROR: Worktree $wname still contains uncommitted changes. Refusing to remove." >&2
  exit 1
fi
git -C "$repo" worktree remove "$wt"
```

- [ ] **Step 4: Verify test passes (GREEN)**
Run: `bash tests/verify_runtime.sh`. Verify clean pass.

- [ ] **Step 5: Commit**
`git commit -m "fix(orchestrator): prevent worktree deletion when rescue commit fails"`

---

### Task 2: Working Tree Disk State & Transient Index Hash in `exec-proxy.sh`

**Files:**
- Modify: `scripts/exec-proxy.sh:54-65` and `scripts/exec-proxy.sh:240-265`
- Modify: `scripts/verify-release-gate.sh:150-170`
- Test: `tests/verify_runtime.sh`

**Interfaces:**
- Consumes: Physical repository tree, `git read-tree`, `git write-tree`
- Produces: `working_tree_sha` and `working_tree_dirty: bool` in receipts and manifest

- [ ] **Step 1: Write the failing test**
Add probe in `tests/verify_runtime.sh`: run test with unstaged file modification, restore file, run gate. Verify gate BLOCKS with "Stale or uncommitted working tree".

- [ ] **Step 2: Run test to verify it fails**
Run: `bash tests/verify_runtime.sh`. Verify failure (RED).

- [ ] **Step 3: Implement fix in `exec-proxy.sh` and `verify-release-gate.sh`**
In `exec-proxy.sh`:
Compute transient index working tree SHA and record `working_tree_dirty`:
```bash
TMP_IDX=$(mktemp)
GIT_INDEX_FILE="$TMP_IDX" git -C "${REPO_ROOT}" read-tree HEAD 2>/dev/null || true
GIT_INDEX_FILE="$TMP_IDX" git -C "${REPO_ROOT}" add -A 2>/dev/null || true
WORKING_TREE_SHA=$(GIT_INDEX_FILE="$TMP_IDX" git -C "${REPO_ROOT}" write-tree 2>/dev/null || echo "unknown")
rm -f "$TMP_IDX"

IS_DIRTY=false
if [ -n "$(git -C "${REPO_ROOT}" status --porcelain 2>/dev/null)" ]; then
  IS_DIRTY=true
fi
```
Pass `working_tree_sha` and `working_tree_dirty` into receipt JSON.
In `verify-release-gate.sh`:
Fail release if `check.get("working_tree_dirty") is True` or if `check.get("git_tree_sha") != current_tree`.

- [ ] **Step 4: Verify test passes (GREEN)**
Run: `bash tests/verify_runtime.sh`. Verify clean pass.

- [ ] **Step 5: Commit**
`git commit -m "fix(proxy): record physical working tree hash and block dirty releases"`

---

### Task 3: Receipt Validation, Content Integrity & Strict Waiver Parser

**Files:**
- Modify: `scripts/verify-release-gate.sh:140-160` and `scripts/verify-release-gate.sh:210-235`
- Test: `tests/verify_runtime.sh`

**Interfaces:**
- Consumes: Receipt JSON files on disk, manifest entries, waiver timestamps
- Produces: Strict validation failing closed on `{}` receipts and invalid waiver dates

- [ ] **Step 1: Write the failing test**
Add probe in `tests/verify_runtime.sh`:
1. Overwrite receipt with `{}` -> expect gate failure.
2. Register waiver with `expires_at: "NOT-A-DATE"` -> expect gate failure.

- [ ] **Step 2: Run test to verify it fails**
Run: `bash tests/verify_runtime.sh`. Verify failure (RED).

- [ ] **Step 3: Implement fix in `verify-release-gate.sh`**
1. Load and assert required receipt fields:
```python
try:
    with open(receipt_file, "r", encoding="utf-8") as rf:
        rcpt_data = json.load(rf)
except Exception as e:
    fail_gate(f"Receipt '{receipt_id}' is corrupt or unreadable: {e}")

for req_field in ("receipt_id", "command", "exit_code", "git_tree_sha", "metrics"):
    if req_field not in rcpt_data:
        fail_gate(f"Receipt '{receipt_id}' missing mandatory field '{req_field}'.")

if rcpt_data.get("exit_code") != exit_code:
    fail_gate(f"Exit code mismatch between manifest and receipt for '{label}'.")
```
2. Parse waiver date strictly without swallowing exceptions:
```python
exp = None
for fmt in (None, "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ"):
    try:
        if fmt is None:
            exp = datetime.datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        else:
            exp = datetime.datetime.strptime(expires_at, fmt).replace(tzinfo=datetime.timezone.utc)
        break
    except Exception:
        continue

if exp is None:
    fail_gate(f"Waiver by '{author}' has invalid unparseable expires_at timestamp: '{expires_at}'.")

now = datetime.datetime.now(datetime.timezone.utc)
if exp < now:
    fail_gate(f"Waiver by '{author}' expired on {expires_at}.")
```

- [ ] **Step 4: Verify test passes (GREEN)**
Run: `bash tests/verify_runtime.sh`. Verify clean pass.

- [ ] **Step 5: Commit**
`git commit -m "fix(gate): validate physical receipt contents and enforce strict waiver timestamps"`

---

### Task 4: Antigravity Hook Protocol Compliance & Commit / Release Decoupling

**Files:**
- Modify: `scripts/verify-release-gate.sh:10-40` and `scripts/verify-release-gate.sh:230-240`
- Modify: `ship-it/SKILL.md:20-60`
- Test: `tests/verify_runtime.sh`

**Interfaces:**
- Consumes: Antigravity `PreToolUse` JSON payload on stdin
- Produces: Strict JSON output on stdout (`{"decision": "allow"}` or `{"decision": "deny"}`)

- [ ] **Step 1: Write the failing test**
Feed Antigravity protojson payload `{"toolCall": {"name": "run_command", "args": {"CommandLine": "git push origin main"}}}` on stdin to `verify-release-gate.sh --pre-tool`.
Assert that stdout is strictly valid JSON with no human plaintext prefix.

- [ ] **Step 2: Run test to verify it fails**
Verify failure (RED).

- [ ] **Step 3: Implement fix in `verify-release-gate.sh` and `ship-it/SKILL.md`**
1. In `verify-release-gate.sh`:
   - Parse command:
     ```python
     tool_call = data.get("toolCall", {})
     args = tool_call.get("args", {})
     cmd = args.get("CommandLine") or data.get("tool_input", {}).get("CommandLine") or data.get("command", "")
     ```
   - On success in `--pre-tool` mode, output `{"decision": "allow"}`.
   - On failure in `--pre-tool` mode, output `{"decision": "deny", "reason": reason}`.
   - In human CLI mode, output human text to stdout.
2. In `ship-it/SKILL.md`:
   - Clarify the lifecycle: local commit is Step 3; release gate is enforced at Step 4 prior to `git push` or release.

- [ ] **Step 4: Verify test passes (GREEN)**
Verify clean pass.

- [ ] **Step 5: Commit**
`git commit -m "fix(hook): implement Antigravity protojson hook protocol and decouple commit from release gate"`

---

### Task 5: Consolidate Planning Triad, Create Thin Aliases & Nuance Aesthetic Guidance

**Files:**
- Modify: `plan-master/SKILL.md`
- Rewrite: `prompt-architect/SKILL.md` (thin ~15-line alias)
- Rewrite: `anti-slop-spec/SKILL.md` (thin ~15-line alias)
- Modify: `frontend-artisan/SKILL.md`
- Modify: `idea-council/SKILL.md`
- Modify: `qa-sentinel/SKILL.md`

- [ ] **Step 1: Make `prompt-architect` and `anti-slop-spec` thin aliases**
Replace their redundant instruction bodies with clean 15-line forwarders to `plan-master`.

- [ ] **Step 2: Nuance aesthetic rules in `frontend-artisan` and `plan-master`**
Replace dogmatic bans with contextual design intent (respect existing design systems).

- [ ] **Step 3: Refine `idea-council`**
Remove unmeasured percentage and latency claims; mandate rigorous steel-manning.

- [ ] **Step 4: Add the Iron Law of TDD to `qa-sentinel` and `plan-master`**
Explicitly mandate verifying the failing RED test before implementing the GREEN code.

- [ ] **Step 5: Commit**
`git commit -m "feat(skills): consolidate planning triad into thin aliases, nuance design rules, and add TDD iron law"`

---

### Task 6: Construct the Automated 3-Task Benchmark Harness

**Files:**
- Create: `tests/benchmark_comparison.py`
- Create: `tests/fixtures/tasks/bugfix/`
- Create: `tests/fixtures/tasks/feature/`
- Create: `tests/fixtures/tasks/refactor/`

**Interfaces:**
- Consumes: Task definitions, test verification scripts
- Produces: JSON comparison table tracking completion, corrections, time, and tokens

- [ ] **Step 1: Write benchmark execution harness**
Automate running a test case through:
1. Baseline / Repaired Skills Suite
2. Superpowers Skills Suite
Tracking time, exit codes, and token logs.

- [ ] **Step 2: Run benchmark suite on Bug Fix, Feature, Refactor**
Execute `python3 tests/benchmark_comparison.py`.

- [ ] **Step 3: Output comparative report**
Generate markdown report of findings.

- [ ] **Step 4: Commit**
`git commit -m "feat(benchmark): add automated 3-task empirical evaluation harness"`
