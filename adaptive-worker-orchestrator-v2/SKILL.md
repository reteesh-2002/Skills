---
name: adaptive-worker-orchestrator-v2
description: |
  Multi-worker parallel orchestrator. Strictly explicit-only: use ONLY when the user explicitly requests parallel worker subagents for independent modular chunks. Default to solo sequential execution for all other tasks.
---

# Adaptive Worker Orchestrator v2 (Boss & Workers)

> [!IMPORTANT]
> **Explicit-Only Activation**: This skill is strictly explicit-only. It must NEVER auto-activate or auto-promote tasks to parallel workers unless the user explicitly requests multi-worker parallel execution. All standard tasks default to solo sequential execution.

Parallel dispatch must justify itself on each run. The Boss (primary model) gates, partitions, freezes contracts, integrates, and reviews. Workers (targeted subagents) implement against a frozen contract in isolated worktrees.

---

## Phase 0: Task-Shape Gating (Every Run, First)

Choose execution strategy based on uncertainty, blast radius, shared interfaces, and file-ownership conflicts. **Never select parallelism solely by file count**:

| Task Shape | Execution Strategy | Rationale |
|---|---|---|
| **Small, clear change (≤3 files)** | **Solo** | Fixed orchestration overhead exceeds task savings. |
| **Tightly coupled refactor** | **Solo / Sequenced** | Shared types and cyclic dependencies make parallel branching conflict-prone regardless of file count. |
| **High-impact auth/data/release** | **Solo + Specialist Review** | Security boundaries and migrations require unified architectural oversight. |
| **Independent modular chunks** | **Multi(N) Worktrees (N ≤ 4)** | Genuinely separable workstreams (e.g. backend API vs. frontend UI vs. standalone worker). |

For a deterministic gating decision, call the gating engine:
```python
import sys; sys.path.insert(0, "scripts")
from task_shape_gating import gate_task
d = gate_task(file_touch_count=..., workstream_count=..., tightly_coupled=..., is_auth_or_data=...)
print(d.mode, d.reason)
```

Emit a status update: `[Orchestrator] Gating decision: solo | multi(n) (Reason: <summary>)`.
If `solo`, the Boss executes the work sequentially without spawning subagents.

---

## Phase 1: Partition & Task Ledger Setup (Multi-N Only)

1. **Initialize Canonical Task Ledger**:
   ```bash
   python3 scripts/task_ledger.py init "<Plan Title>"
   python3 scripts/task_ledger.py add --id T1 --title "<Module A>" --owner "Worker_A"
   ```
2. **File Isolation & Lockfile Ownership**:
   - Enforce strict **1-writer-per-file** partitioning. Two workers cannot own the same output file.
   - **Lockfiles and Root Manifests**: Root files (`package.json`, `package-lock.json`, `Cargo.lock`, `pyproject.toml`, root configuration manifests) are **exclusively owned by the Coordinator/Boss**. Workers must not modify shared lockfiles concurrently.
3. **Dependency & Cycle Validation**:
   - Run `python3 scripts/task_ledger.py validate` to ensure zero dependency cycles or missing prerequisites before worker dispatch.
4. **Hard Worker Cap**: Enforce $N \le 4$ active workers (suite policy cap reserving coordinator capacity). Concurrency must never exceed 4 workers. Queue remaining workstreams.

---

## Phase 1.5: Frozen Interface Contract

If workstreams share any API contracts, types, or schemas:
1. Define interfaces up front in `contract.yaml` (or shared TypeScript/Python types).
2. Freeze the contract: record the contract content hash in `task_ledger.json` before dispatching workers. Workers must never be dispatched against an unfrozen or changing contract.
3. Paste the contract verbatim into each worker's prompt brief.
3. Boss exclusively owns shared types, root manifests, and configuration wiring.


---

## Phase 2: Worktree Dispatch & Build Isolation

1. **Mount Isolated Worktrees**: Run `scripts/setup_worktrees.sh <base-branch> <worker>...`.
   - Worktrees reside in `.git/.orch-worktrees/<worker>`.
2. **Isolate Writable Build Outputs**:
   - While read-only dependencies (`node_modules`, `.venv`) may be symlinked, **writable build caches and compilation output directories (`dist/`, `.next/`, `build/`, `target/`, `out/`, `__pycache__`) must be isolated per worktree**.
   - Concurrent workers must never write to shared compilation directories to prevent build races, cache thrashing, and output corruption.
3. **Scoped Worker Briefs (E-04)**: Build each brief using `scripts/task_shape_gating.py`:
   ```python
   from task_shape_gating import build_worker_brief
   brief = build_worker_brief(
       worker_id="Worker_A", goal="...",
       allowed_files=["api/routes.py"],
       test_command="pytest tests/test_routes.py",
       contract="<frozen schema snippet>",
       constraints=["Do not modify auth.py"],
   )
   ```
   Include only: goal, permitted scope, frozen contract, constraints, and test command. Exclude conversation history.
4. **Record Running State**:
   ```bash
   python3 scripts/task_ledger.py update --id <task_id> --status Running --detail "Implementing in worktree"
   ```

---

## Phase 3: Pipelined Reactive Auditing

The Boss yields execution without looping or polling.

**Reactive Wakeup on Worker Completion**:
When a worker reports back:
1. **Audit Diff**: Run `scripts/audit_diff.sh <worktree> <base-branch> <allowed-path>...`.
2. **Verify Evidence**: Verify that the worker executed test runs through `scripts/exec-proxy.sh`.
3. **Update Ledger**:
   ```bash
   python3 scripts/task_ledger.py update --id <task_id> --status Verifying --detail "Diff audited cleanly"
   ```
4. If other workers are still running, yield execution.

---

## Phase 4: Integration & Review

1. **Merge Order**: Merge worker branches into the integration branch in dependency order.
2. **Full Conformance Pass**: Run integration test suite across the combined codebase via `scripts/exec-proxy.sh`.
3. **Independent Review**: For high-risk deliverables, dispatch `code-reviewer` to audit the unified diff.
4. **Mark Done**:
   ```bash
   python3 scripts/task_ledger.py update --id <task_id> --status Done --detail "Integrated and verified"
   ```

---

## Phase 5: Safe Cleanup & Durable Recovery

1. **Safe Cleanup**:
   Run `scripts/setup_worktrees.sh cleanup`.
   - Uncommitted modifications are automatically committed to `orch/rescue-<worker>-*` rescue branches before deletion.
   - If a rescue commit fails, deletion is aborted and the dirty worktree is preserved intact.
2. **Durable Resume Protocol (Post-Interruption / Server Restart)**:
   When resuming after a disconnect:
   1. `git status` and `git log --oneline -5` — inspect actual repository state.
   2. `python3 scripts/task_ledger.py status` — read current task ledger revision.
   3. `python3 scripts/task_ledger.py reconcile` — re-queue any interrupted Running/Verifying tasks to Pending.
   4. Inspect `.git/.orch-worktrees/` and `git branch --list 'orch/rescue-*'` for surviving work.
   5. Compare `.evidence/manifest.v1.json` tree SHA against `git write-tree` — re-validate stale evidence.
   6. Resume from the first Pending task without re-running tasks already marked Done with valid evidence.
