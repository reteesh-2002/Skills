# Design Specification: Runtime Safeguards Repair & Skills Suite Refinement

**Date**: 2026-09-27  
**Author**: Antigravity & User Pair  
**Status**: APPROVED DESIGN SPECIFICATION  

---

## 1. Executive Summary

This specification establishes the architectural remediations for:
1. **Physical Runtime Safeguards**: Eliminating data loss in worktree cleanup, closing the staged-index vs. working-directory verification loophole, enforcing physical receipt content & waiver integrity, and correcting the Antigravity hook protocol.
2. **Workflow & Instruction Consolidation**: Establishing `plan-master` as the single authoritative planning engine, converting `prompt-architect` and `anti-slop-spec` into true thin aliases, replacing dogmatic aesthetic bans with contextual design intent, and grounding `idea-council` in empirical steel-manning.
3. **Superpowers Practice Adoption**: Introducing the "Iron Law of TDD" (verified RED before GREEN), risk-weighted independent code review gates, and workflow isolation.
4. **Empirical Benchmarking**: Providing an automated evaluation harness comparing the repaired suite against `obra/superpowers` across 3 representative tasks (Bug Fix, Feature, Refactor).

---

## 2. Component Specifications

### 2.1 Worktree Cleanup Data Protection (`setup_worktrees.sh`)
- **Problem**: When a rescue commit failed, `setup_worktrees.sh` reported preservation and executed `git worktree remove --force "$wt"`, deleting uncommitted files permanently.
- **Specification**:
  - In `setup_worktrees.sh cleanup`:
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

    # Mandatory clean assertion
    if [ -n "$(git -C "$wt" status --porcelain 2>/dev/null)" ]; then
      echo "ERROR: Worktree $wname still contains uncommitted changes. Refusing to remove." >&2
      exit 1
    fi

    git -C "$repo" worktree remove "$wt"
    ```

### 2.2 Working Tree Disk State vs. Staged Index Hash (`exec-proxy.sh` & Gate)
- **Problem**: `git write-tree` hashes `.git/index`. Tests run against working directory files on disk. Restoring an unstaged file allowed test passes on uncommitted code to pass the gate on clean commits.
- **Specification**:
  - In `exec-proxy.sh`:
    - Check if tracked files have unstaged modifications (`git diff --quiet`).
    - Compute the exact disk-level working tree SHA via an isolated transient index:
      ```bash
      TMP_IDX=$(mktemp)
      GIT_INDEX_FILE="$TMP_IDX" git -C "${REPO_ROOT}" read-tree HEAD 2>/dev/null || true
      GIT_INDEX_FILE="$TMP_IDX" git -C "${REPO_ROOT}" add -A 2>/dev/null || true
      WORKING_TREE_SHA=$(GIT_INDEX_FILE="$TMP_IDX" git -C "${REPO_ROOT}" write-tree 2>/dev/null || echo "unknown")
      rm -f "$TMP_IDX"
      ```
    - Check working tree dirty status: `IS_DIRTY=false`; if `git status --porcelain` is non-empty, `IS_DIRTY=true`.
    - Record in receipt: `"working_tree_sha": WORKING_TREE_SHA`, `"working_tree_dirty": IS_DIRTY`.
  - In `verify-release-gate.sh`:
    - Gate requires `c.get("working_tree_dirty") is False`. If true, block release: `Check tested against dirty working tree`.

### 2.3 Receipt Content Verification & Strict Waiver Parser (`verify-release-gate.sh`)
- **Problem**: Gate only checked `os.path.exists()`, allowing `{}` receipts to pass. Exception swallowing in date parsing allowed unparseable timestamps like `"NOT-A-DATE"`.
- **Specification**:
  - In `verify-release-gate.sh`:
    - Load every receipt file:
      ```python
      try:
          with open(receipt_file, "r", encoding="utf-8") as rf:
              rcpt_data = json.load(rf)
      except Exception as e:
          fail_gate(f"Receipt '{receipt_id}' is corrupt or unreadable: {e}")
      ```
    - Verify mandatory fields: `receipt_id`, `command`, `exit_code`, `git_tree_sha`, `metrics`.
    - Assert that `rcpt_data["exit_code"] == exit_code` and `rcpt_data["git_tree_sha"] == current_tree`.
    - Waiver timestamp validation:
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
          fail_gate(f"Waiver by '{author}' has invalid unparseable expires_at timestamp: '{expires_at}'")
      ```

### 2.4 Antigravity Hook Protocol Compliance (`verify-release-gate.sh`)
- **Problem**: Looked for `tool_input` instead of `toolCall.args.CommandLine`. Printed plain text on success in `--pre-tool` mode instead of valid JSON.
- **Specification**:
  - Parse `data.get("toolCall", {}).get("args", {}).get("CommandLine") || data.get("tool_input", {}).get("CommandLine") || data.get("command", "")`.
  - In `--pre-tool` mode:
    - Never write plain text to stdout.
    - On allow: `print(json.dumps({"decision": "allow"}))`
    - On deny: `print(json.dumps({"decision": "deny", "reason": reason}))`

### 2.5 Commit vs. Release Separation (`ship-it/SKILL.md`)
- **Problem**: Step 2.5 required `verify-release-gate.sh` before committing, while the gate failed on uncommitted changes.
- **Specification**:
  - Step 1: Stage atomic files (`git add`).
  - Step 2: Secret & artifact scan (`git diff --cached`).
  - Step 3: Atomic conventional commit (`git commit`).
  - Step 4: Deterministic Release Gate (`verify-release-gate.sh`) enforced prior to `git push`, PR creation, or production tagging.

---

## 3. Skill Consolidation & Instruction Refinements

### 3.1 `plan-master` as the Authoritative Entry Point
- Natively handles intent classification, domain routing (2–4 skills max), depth-tiered planning, and contextual anti-slop visual discipline.

### 3.2 Thin Aliases for `prompt-architect` and `anti-slop-spec`
- Strip duplicate instructions down to ~15 lines:
  ```markdown
  ---
  name: prompt-architect
  description: Forwarding alias to plan-master.
  ---
  # Prompt Architect
  > [!NOTE]
  > Prompt Architect has been natively consolidated into [`plan-master`](../plan-master/SKILL.md).
  > When planning a feature or composing execution prompts, activate `plan-master`.
  ```

### 3.3 Nuanced Aesthetic Guidance (`frontend-artisan` & `plan-master`)
- Replace blanket dogmatic bans with contextual design intent:
  - If the project has an existing design system, brand guidelines, or component library, respect and match that system.
  - If greenfield, intentionally choose one of the 10 craft archetypes rather than defaulting to generic SaaS clichés.

### 3.4 Rigorous Dissent in `idea-council`
- Remove unmeasured quantitative claims.
- Mandate intellectual steel-manning: aggressively stress-test assumptions, but build constructively upon sound arguments.

---

## 4. Borrowed Superpowers Practices
1. **The Iron Law of TDD**: Explicitly embed in `qa-sentinel` and `plan-master`: No production code without a verified failing RED test first.
2. **Independent Code Review**: Enforce a dedicated review checkpoint before release on high-risk changes (>12 files or security/auth boundary edits).
3. **Workflow Isolation**: Prevent loading `plan-master` and `superpowers:writing-plans` in the same turn.

---

## 5. Empirical Benchmark Methodology
- Construct `tests/benchmark_comparison.py`:
  - 3 standardized tasks: Bug Fix, Feature, Refactor.
  - Identical model and environment settings.
  - Track:
    1. Completion & Correctness (test pass: true/false)
    2. Manual Corrections (interventions count)
    3. Elapsed Wall-Clock Time (seconds)
    4. Total Tokens (prompt + completion + worker subagents)
