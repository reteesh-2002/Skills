# Worker Dashboard Template

Read at Phase 2 when multi-worker mode ($N \ge 2$) is active and the host supports artifacts (e.g., Google Antigravity).

Create or update `<artifact_dir>/worker-dashboard.md` at key milestones (**Milestone-Piggybacked Policy**, max 3–5 writes per run):
1. **Phase 2 (Post-Dispatch)**: Initialize with planned workers, assigned scopes, and model tiers (`🔵 Working...`).
2. **Phase 3 (Per-Worker Arrival)**: When any worker message arrives, Boss audits that worker's diff immediately and flips its row to `🟢 Audited (Ready for Merge)` while others remain `🔵 Working...`.
3. **Phase 4 & 5 (Integration & Finalize)**: Mark all integrated (`⭐ Merged & Integrated`), show test results, and finalize.

## Template

```markdown
# 🚀 Worker Orchestration Dashboard

**Phase**: <Phase Name> (e.g. Phase 3: Pipelined Auditing / Phase 4: Integration)  
**Status**: <X>/<N> workers completed | **Mode**: `multi(<N>)`

| Worker | Role / Scope | Model Tier | Status | Touched Files / Diff | Notes |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **Worker 1** | `<path-scope>` | `<tier>` | 🟢 **Audited (Ready for Merge)** | `4 files (+120 lines)` | Passed audit_diff.sh |
| **Worker 2** | `<path-scope>` | `<tier>` | 🟢 **Audited (Ready for Merge)** | `3 files (+85 lines)` | Passed audit_diff.sh |
| **Worker 3** | `<path-scope>` | `<tier>` | 🔵 **Working...** | In progress | Worktree active |
| **Worker 4** | `<path-scope>` | `<tier>` | ⏸️ **Queued** | Waiting for slot | Dependent on Worker 1 |

---

### Seam & Integration Checklist
- [x] Phase 0: Gate passed (`multi(<N>)`)
- [x] Phase 1.5: Frozen contract established
- [ ] Phase 4: All worker diff audits passed
- [ ] Phase 4: Full integration build & tests passed
- [ ] Phase 5: Safe worktree cleanup
```

## Rules
- Keep writes strictly piggybacked on active Boss turns (never invoke an extra turn solely for UI).
- Use canonical relative paths (`src/api/*`), never internal worktree paths (`.git/.orch-worktrees/*`).
- In non-artifact hosts, omit artifact creation and use standard terminal status checkpoints.
