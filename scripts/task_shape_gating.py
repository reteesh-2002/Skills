#!/usr/bin/env python3
"""
Antigravity Phase 0 Task-Shape Gating Engine
Deterministically selects execution strategy (solo / multi-N / sequenced)
based on task shape signals. No file count alone decides; uncertainty,
blast radius, interface ownership, and tool availability also factor in.

Canonical output: GatingDecision dataclass.
"""

from __future__ import annotations
import dataclasses
from enum import Enum
from typing import List, Optional


class ExecutionMode(str, Enum):
    SOLO         = "solo"           # < 3 files or tightly coupled; no subagents
    SEQUENCED    = "sequenced"      # Coupled refactor; sequential solo passes
    MULTI        = "multi"          # Independent workstreams; parallel workers (N ≤ 4)
    SOLO_REVIEW  = "solo+review"    # High-impact change; solo + specialist review
    BLOCKED      = "blocked"        # Cannot proceed without user clarification


@dataclasses.dataclass(frozen=True)
class GatingDecision:
    mode:         ExecutionMode
    worker_count: int           # 0 for solo/sequenced, 1-4 for multi
    reason:       str           # Human-readable rationale (≤ 120 chars)
    acceptance:   str           # Acceptance ID this satisfies


def gate_task(
    file_touch_count:     int,
    has_shared_interface: bool  = False,
    is_auth_or_data:      bool  = False,
    is_idea_evaluation:   bool  = False,
    workstream_count:     int   = 1,
    tightly_coupled:      bool  = False,
    subagent_tools_available: bool = True,
    max_workers:          int   = 4,
) -> GatingDecision:
    """
    Deterministic Phase 0 gating decision.

    Parameters
    ----------
    file_touch_count          : Estimated number of files to be modified.
    has_shared_interface      : Workstreams share API contracts / types.
    is_auth_or_data           : Auth, DB migration, or financial logic is touched.
    is_idea_evaluation        : User asked for idea council / deliberation.
    workstream_count          : Number of independent deliverable workstreams.
    tightly_coupled           : Known shared-file dependencies across workstreams.
    subagent_tools_available  : invoke_subagent is accessible in this environment.
    max_workers               : Configured cap on concurrent worker subagents (≥ 1).
    """

    # E-01: idea evaluation → never auto-spawn; always manual Idea Council
    if is_idea_evaluation:
        return GatingDecision(
            mode=ExecutionMode.SOLO,
            worker_count=0,
            reason="Idea evaluation is manual-only (Idea Council); no workers spawned.",
            acceptance="E-01",
        )

    # High-impact auth / data changes require specialist review, not just parallelism
    if is_auth_or_data:
        return GatingDecision(
            mode=ExecutionMode.SOLO_REVIEW,
            worker_count=0,
            reason="Auth/data/release change: solo implementation + mandatory specialist review.",
            acceptance="E-01",
        )

    # E-01: small, clear change — solo mode; fixed orchestration overhead not worth it
    if file_touch_count <= 3 and workstream_count <= 1:
        return GatingDecision(
            mode=ExecutionMode.SOLO,
            worker_count=0,
            reason=f"Small change ({file_touch_count} file(s)): solo mode; overhead exceeds savings.",
            acceptance="E-01",
        )

    # Tightly coupled refactor → sequenced solo to prevent merge collisions (E-03)
    if tightly_coupled:
        return GatingDecision(
            mode=ExecutionMode.SEQUENCED,
            worker_count=0,
            reason="Tightly coupled refactor: sequenced solo passes to prevent shared-file conflicts.",
            acceptance="E-03",
        )

    # E-02: independent workstreams → parallel multi mode
    if workstream_count >= 2 and subagent_tools_available:
        # Hard cap: never exceed 4 workers regardless of caller-supplied max_workers
        effective_max = min(max_workers, 4)
        n_workers = min(workstream_count, effective_max)
        reason = (
            f"{workstream_count} independent workstream(s): multi({n_workers}) workers in parallel."
        )
        if has_shared_interface:
            reason += " Shared interface contract frozen before dispatch (E-04)."
        return GatingDecision(
            mode=ExecutionMode.MULTI,
            worker_count=n_workers,
            reason=reason,
            acceptance="E-02",
        )

    # Large solo change with independent review
    if file_touch_count > 3:
        return GatingDecision(
            mode=ExecutionMode.SOLO_REVIEW,
            worker_count=0,
            reason=f"Ordinary feature ({file_touch_count} files): solo + independent final review.",
            acceptance="E-01",
        )

    # Default: solo
    return GatingDecision(
        mode=ExecutionMode.SOLO,
        worker_count=0,
        reason="Default: solo execution.",
        acceptance="E-01",
    )


def format_decision(d: GatingDecision) -> str:
    """Emit the canonical Orchestrator gating heartbeat line."""
    mode_str = d.mode.value
    if d.worker_count > 1:
        mode_str = f"multi({d.worker_count})"
    return f"[Orchestrator] Gating decision: {mode_str} | Reason: {d.reason} (Acceptance: {d.acceptance})"


def build_worker_brief(
    worker_id:         str,
    goal:              str,
    allowed_files:     List[str],
    test_command:      str,
    contract:          Optional[str] = None,
    constraints:       Optional[List[str]] = None,
) -> str:
    """
    C-2: Build a minimal worker brief.
    Contains only: goal, permitted scope, contract snippet, and test command.
    Excludes conversation history and extraneous skill instructions.
    """
    lines = [
        f"# Worker Brief: {worker_id}",
        "",
        f"## Goal",
        goal,
        "",
        f"## Allowed File Scope",
    ]
    for f in allowed_files:
        lines.append(f"- `{f}`")
    lines.append("")

    if contract:
        lines += ["## Frozen Interface Contract", "```", contract.strip(), "```", ""]

    if constraints:
        lines += ["## Constraints"]
        for c in constraints:
            lines.append(f"- {c}")
        lines.append("")

    lines += [
        "## Acceptance Verification",
        f"Run: `{test_command}`",
        "Route via: `bash scripts/exec-proxy.sh --label <task_id> " + test_command + "`",
        "",
        "> Do not read conversation history. Use only what is in this brief.",
    ]
    return "\n".join(lines)


def resume_protocol_steps() -> List[str]:
    """
    C-3: Durable resume protocol steps (for agent to follow on session restart).
    Returns ordered checklist items.
    """
    return [
        "1. Run `git status` and `git log --oneline -5` to inspect actual repository state.",
        "2. Run `python3 scripts/task_ledger.py status` to read current task ledger revision.",
        "3. Run `python3 scripts/task_ledger.py reconcile` to re-queue interrupted Running/Verifying tasks.",
        "4. Check `.git/.orch-worktrees/` for surviving worktrees; inspect `git branch --list 'orch/rescue-*'`.",
        "5. Validate evidence: compare `.evidence/manifest.v1.json` tree SHA against `git write-tree`.",
        "6. Resume from the first Pending task without re-running tasks already marked Done with valid evidence.",
    ]
