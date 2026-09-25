# Changelog: plan-master

## [2.0.0] - 2026-09-24

### Added
- **Native Idea Council v2.0 Verdict Ingestion**:
  - 🟢 **Go Ahead (Build Now)**: Direct mapping to Standard or Detailed execution plan.
  - 🟡 **Test First (Try Small)**: Dedicated **Spike / PoC Plan Template** with explicit hypotheses, time-boxes, and quantifiable Go/No-Go kill criteria.
  - 🟠 **Fix First (Needs Changes)**: Dedicated **Remediation Plan Template** addressing identified architectural objections and flaws.
  - ⏸️ **On Hold (Save for Later)**: Prerequisite Checklist and backlog record.
  - 🔴 **Drop It (Don't Build)**: Archival Decision Record (ADR) capturing rejection rationale and preventing unnecessary planning.
- **Depth-Tiered Planning Modes**:
  - **Compact**: Ultra-lean (<400 tokens), text-first, 3-5 concrete steps for bugfixes and small tasks (<12 files). Zero diagram or worktree overhead.
  - **Standard**: Inverted pyramid summary, 1-click execution handoff, Markdown task table, and optional visual Mermaid DAG.
  - **Detailed**: Multi-phase milestones, interface contracts, rollback triggers, and worktree-ready partitions.
- **Adaptive Orchestrator Profile (`adaptive-worker-orchestrator-v2`)**:
  - Enforces strict 1-writer-per-file isolation for git worktrees (`.git/.orch-worktrees/`).
  - Distinguishes coordinator-owned files (lockfiles, root manifests, registries) for sequential Phase 4 integration.
  - Aligns task verification targets with `scripts/audit_diff.sh`.
  - Graceful degradation: Seamlessly falls back to standard sequential execution if git or the orchestrator skill is absent.
- **Internal 6-Point Sanity Validation**:
  - Pre-flight checklist: (1) Acyclicity, (2) Zero write-collisions, (3) Grounded paths, (4) Bounded unknowns, (5) Concrete verification commands, (6) Explicit stop triggers.
- **Inverted Pyramid UX**:
  - Executive Outcome Card and 1-Click Execution Prompt positioned at the very top of plans.
- **Safe Mermaid Dependency Graphs**:
  - Visual DAG with safe quoted labels (`["Task Name"]`) to prevent rendering crashes across markdown hosts.
