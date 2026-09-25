---
name: adaptive-worker-orchestrator-v2
description: |
  Use when a coding task spans multiple independent modules or workstreams (roughly 12-15+ files, or separable backend/frontend/tests/infra/batch chunks) and parallel worker subagents on cheaper models might pay off. Do NOT use for tasks under ~12 files, single-file fixes, small refactors, or one-line changes; do those directly in solo mode. Phase 0 still decides solo vs multi(n) on every invocation.
---

# Adaptive Worker Orchestrator v2 (Boss & Workers)

Parallel dispatch must justify itself each run. The Boss (primary model) gates, partitions, freezes contracts, integrates, and reviews. Workers (cheaper models) implement against a frozen contract in isolated worktrees.

## Phase 0: Gate (every run, first)

**Runtime**: read host platform defaults from `references/runtime-probe.md`. Do not write temporary probe files to the user's workspace.

Answer three questions, emit a concise status update `[Orchestrator] Gating decision: solo | multi(n)` + reason, then proceed:

1. **Size**: rough LOC/files touched. Under ~12–15 files or <800 LOC → **solo**; fixed orchestration overhead (contract drafting, diff audits, merging) exceeds task savings.
2. **Coupling**: do workstreams share types/state or depend on each other's output? High coupling → sequence, or extract a frozen contract (Phase 1.5) and parallelize only what remains. Not extractable → **solo**.
3. **Risk**: auth, payments, concurrency-sensitive state, irreversible migrations, security boundaries → the Boss or a strong-tier worker authors that part directly.

If `solo`, the Boss does the work and stops here.

## Phase 1: Partition (skip if solo)

N = count of genuinely independent, low-coupling chunks, clamped to ~4 (beyond that, merge chunks; Boss review becomes the bottleneck). State N and why. N=3 or 4 is as valid as N=2.

**File isolation**: no two workers edit the same file. Enforced by worktrees in Phase 2, not by instruction alone.

Common shapes: feature-per-worker; backend / frontend / infra; implementation vs. tests; a batch split into N chunks.

## Phase 1.5: Frozen Contract (only if coupling exists)

If workstreams share anything, read `references/contract-format.md`, write the contract, and paste it verbatim into every worker prompt. If there is zero coupling, note that and skip.

## Phase 2: Dispatch

1. **Isolate**: in a git repo, run `scripts/setup_worktrees.sh <base-branch> <worker>...` (worktrees live inside `.git/.orch-worktrees/<worker>` with dependencies like `node_modules`/`.venv` symlinked automatically). Not a git repo → scoped directories only, and Phase 4 diff inspection is manual.
2. **Route per subtask**, not one blanket tier. Strongest tier for architecture, security, ambiguous requirements.
3. **Scope the prompt**: contract, allowed file scope, relevant conventions only. Build the prompt from `references/worker-template.md`.
4. **Respect the concurrency cap** (default 4). Track planned / launched / observed-peak-active separately. Queue overflow; launch a queued worker only when a slot frees and its dependencies are verified. Never batch past the cap or drop queued work.
5. **Boss owns** manifests, lockfiles, shared types, route/registry wiring, config. Workers request changes.
6. **Right-Side Dashboard (Pilot)**: In artifact-supporting hosts (e.g. Antigravity), initialize a user-facing markdown artifact `worker-dashboard.md` from `references/dashboard-template.md`. It automatically renders in the user's right panel, providing instant visibility into worker scopes, tiers, and statuses without cluttering the chat.

## Phase 3: Yield & Pipelined Reactive Auditing

The Boss emits a short progress checkpoint to the user and yields execution without polling.

**Per-Worker Reactive Wakeup**:
Whenever an incoming message arrives from ANY completed worker (e.g., Worker A finishes while Workers B, C, D are still working), the Boss wakes up automatically and processes that worker immediately in that single turn:
1. Run `scripts/audit_diff.sh <worktree> <base-branch> <allowed-path>...` on the returned worker.
2. In artifact-supporting hosts, update `worker-dashboard.md` immediately:
   - Mark that completed worker: `🟢 Audited (Ready for Merge)` with touched files and diff stats.
   - Leave still-active workers: `🔵 Working...`.
3. If other workers are still running, stop tool execution and yield again.

This pipelines diff auditing in real time, keeping the right-side dashboard live without waiting for the slowest worker.

## Phase 4: Integration (Once All Workers Pass Step 1)

1. **Incremental Pre-Audit Check**: Confirm all $N$ workers have reported in and passed their individual audits (most were already pre-audited incrementally in Phase 3).
2. **Correction (Single-Strike Rule)**: minor syntax issues → Boss patches. Structural discrepancy or contract drift → resume the *same* worker once with the specific failure. If it fails a second time, the Boss immediately absorbs and completes the slice to prevent token bleed.
3. **Blocked worker** (missing contract field, ambiguous requirement): it reports and waits; the Boss supplies a revised boundary or reassigns the slot.
4. **Integration (mandatory when N ≥ 2)**:
   - Merge worker branches into an integration branch in dependency order.
   - Run full build, typecheck, and tests.
   - Check every boundary signature against the frozen contract.
   - Seam failures: Boss patches if small; otherwise resume the owning worker.
5. **Dashboard Final Merge Update**: Update `worker-dashboard.md` to reflect all workers as `⭐ Merged & Integrated`.

## Phase 5: Finalize

Run `scripts/setup_worktrees.sh cleanup` (safely unmounts worktrees; preserves any unmerged code in `orch/rescue-*` branches), mark the right-side dashboard complete, commit, and present one unified summary.

## Phase 6: Outcome Log (every run)

Record run metrics (path chosen, workers launched, corrections, token estimates, wall-clock duration) in the session scratchpad or conversation summary. Avoid littering the project repository with untracked log files.
