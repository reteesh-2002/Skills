---
name: adaptive-worker-orchestrator-v2
description: |
  Use when a coding task spans multiple independent modules or workstreams (separable backend/frontend/tests/infra/batch chunks) and parallel worker subagents on cheaper models might pay off. Do NOT use for small, tightly coupled refactors or single-file fixes; do those directly in solo mode. Phase 0 decides solo vs multi(n) on every invocation based on task shape and conflict risk.
---

# Adaptive Worker Orchestrator v2 (Boss & Workers)

Parallel dispatch must justify itself on each run. The Boss (primary model) gates, partitions, freezes contracts, integrates, and reviews. Workers (targeted subagents) implement against a frozen contract in isolated worktrees.

---

## Phase 0: Task-Shape Gating (Every Run, First)

Choose the execution strategy based on uncertainty, blast radius, interfaces, and file-ownership conflicts:

| Task Shape | Execution Strategy | Rationale |
| :--- | :--- | :--- |
| **Small, clear change (<3 files)** | **Solo** | Fixed orchestration overhead exceeds task savings. |
| **Tightly coupled refactor** | **Solo / Sequenced** | Shared types and cyclic dependencies make parallel branching conflict-prone. |
| **High-impact auth/data/release** | **Solo + Specialist Review** | Security boundaries and migrations require unified architectural oversight. |
| **Independent modular chunks** | **Multi(N) Worktrees (N ≤ 4)** | Separable workstreams (e.g. backend API vs. frontend UI vs. standalone worker). |

Emit a concise status update: `[Orchestrator] Gating decision: solo | multi(n) (Reason: <summary>)`.
If `solo`, the Boss completes the work sequentially without spawning subagents.

---

## Phase 1: Partition & Task Ledger Setup (Multi-N Only)

1. **Initialize Canonical Task Ledger**:
   ```bash
   python3 scripts/task_ledger.py init "<Plan Title>"
   python3 scripts/task_ledger.py add --id T1 --title "<Module A>" --owner "Worker_A"
   ```
2. **File Isolation Invariant**: Enforce strict **1-writer-per-file** partitioning. No two workers may write to the same file.
3. **Clamp Concurrency**: $N \le 4$ active workers. Queue additional tasks if necessary.

---

## Phase 1.5: Frozen Interface Contract

If workstreams share any API contracts, types, or schemas:
1. Define the interfaces up front in `contract.yaml` (or TypeScript/Python types).
2. Paste the contract verbatim into each worker's prompt brief.
3. Boss exclusively owns shared types, root manifests, and configuration wiring.

---

## Phase 2: Worktree Dispatch

1. **Mount Worktrees**: Run `scripts/setup_worktrees.sh <base-branch> <worker>...`.
   - Worktrees live in `.git/.orch-worktrees/<worker>` with dependencies (`node_modules`, `.venv`) symlinked.
2. **Scoped Worker Briefs**: Give each worker a concise brief: goal, allowed file scope, contract, and test command.
3. **Record Running State**:
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
   - Check `.evidence/tasks.json` against actual git branch/worktree status.
   - Inspect `.git/.orch-worktrees/` and `git branch --list "orch/rescue-*"`.
   - Re-validate stale evidence against current commit HEAD.
   - Resume remaining pending tasks without duplicating already completed work.
