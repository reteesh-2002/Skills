# v1 -> v2

1. Description narrowed to multi-module tasks with an explicit "do NOT use" clause; Phase 0 remains the per-run gate.
2. `solo | dual | multi(n)` -> `solo | multi(n)`.
3. File isolation enforced with git worktrees (scripts/setup_worktrees.sh); fallback for non-git dirs.
4. Mandatory integration step in Phase 4 (merge in dependency order, full build/test, contract check).
5. Runtime probe cached in `.orchestrator/runtime.md`.
6. Phase-specific material moved to references/ and scripts/; each pointer names its phase and condition.
7. New scripts/audit_diff.sh checks scope, protected files, and placeholders.

# v2 -> v2.1 (Idea Council Revisions)

1. Relocated worktrees from `../.orch-worktrees/` to `.git/.orch-worktrees/` to guarantee sandbox write permissions.
2. Added automatic dependency symlinking (`node_modules`, `.venv`, `target`) in `setup_worktrees.sh` so worker tests do not fail on missing dependencies.
3. Protected unmerged branches on cleanup (preserves them as `orch/rescue-*` rather than destructive `branch -D`).
4. Demoted placeholder regex check in `audit_diff.sh` to advisory warning and excluded language primitives like `NotImplementedError`.
5. Raised Phase 0 gating threshold from 5 to 12–15+ files / ~800+ LOC to prevent negative token ROI.
6. Replaced dynamic prompt probing and `.orchestrator/` repo file pollution with static defaults in `runtime-probe.md`.
7. Introduced Single-Strike Rule (Boss absorbs failed worker slices after 1 retry to cap token burn).
8. Added Right-Side Worker Dashboard (`worker-dashboard.md` artifact via `references/dashboard-template.md`) with a strict Milestone-Piggybacked update policy (max 3–5 updates per run) for live observability in Antigravity.
9. Implemented Pipelined Reactive Auditing in Phase 3: Boss audits each worker incrementally as its completion message arrives, flipping that worker to `🟢 Audited (Ready for Merge)` in the right-side dashboard in real time without waiting for slower workers.
