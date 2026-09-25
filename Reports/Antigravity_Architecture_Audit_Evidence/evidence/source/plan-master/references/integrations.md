# Integration contracts

Use only integrations the user selects or source artifacts they provide. Planning must remain 100% functional standalone without any companion skills. Read a selected skill's current instructions before claiming to use it.

## Companion Skill Matrix

| Companion Skill | Input to Plan Master | Planner Responsibility | Execution Boundary |
| :--- | :--- | :--- | :--- |
| **Standalone (No skills)** | Idea, requirements, code, or user prompt | Ground the request, plan tasks/checks, produce a self-contained handoff. | No companion skills or subagents required. |
| **Idea Council v2.0 Output** | Decision record with stance (🟢/🟡/🟠/⏸️/🔴), challenges, open questions | Map verdict directly to plan type: 🟢 $\rightarrow$ Execution Plan; 🟡 $\rightarrow$ Spike Plan with kill triggers; 🟠 $\rightarrow$ Remediation Plan; ⏸️ $\rightarrow$ Prerequisite list; 🔴 $\rightarrow$ Archival ADR. | Preserve dissent; translate accepted decisions into scope and unresolved assumptions into discovery tasks. |
| **adaptive-worker-orchestrator-v2** | Plan plus multi-worker execution request | Format tasks into independent worktree-friendly module batches with zero-overlap write scopes, coordinator-owned files, and `audit_diff.sh` test targets. | Executor determines real worker count and launches git worktrees in `.git/.orch-worktrees/`. Solo fallback if <12 files. |
| **Council + Planner + Orchestrator** | Strategic review to parallel execution | Plan Master ingests council verdict, drafts worktree-partitioned plan, and hands off execution prompt to orchestrator. | Pipeline runs sequentially: Council (strategic review) $\rightarrow$ Planner (contracts & DAG) $\rightarrow$ Orchestrator (parallel implementation). |

---

## 1. Idea Council v2.0 Verdict Routing Contract

When an Idea Council decision record is provided, map stances deterministically:

| Council Stance | Plan Typology | Structure & Mandatory Guardrails |
| :--- | :--- | :--- |
| 🟢 **Go Ahead (Build Now)** | **Full Execution Plan** | Standard or Detailed task DAG. Ready tasks partitioned for solo or multi-worker execution. |
| 🟡 **Test First (Try Small)** | **Spike / PoC Plan** | Time-boxed experiment plan. Strict boundary: build only the smallest prototype to test the hypothesis. Must include explicit **Go/No-Go Exit Criteria** and quantifiable kill triggers before full build. |
| 🟠 **Fix First (Needs Changes)** | **Remediation Plan** | Targeted architectural redesign plan addressing the specific objections and vulnerabilities identified in the council report. |
| ⏸️ **On Hold (Save for Later)** | **Prerequisite Checklist** | No implementation tasks. Summarizes required dependency releases, environmental prerequisites, and backlog tracking record. |
| 🔴 **Drop It (Don't Build)** | **Archival ADR** | No implementation tasks. Synthesizes rejection rationale, fatal flaws, and alternative recommendations for repository documentation. |

---

## 2. Adaptive Orchestrator Profile (`adaptive-worker-orchestrator-v2`)

When handing off to `adaptive-worker-orchestrator-v2`, adhere to orchestrator invariants:

1. **Strict 1-Writer-Per-File Isolation**:
   - Each parallel task must specify an explicit, non-overlapping list of target files or directories.
   - Never assign two parallel tasks to the same file (e.g. shared contract, common registry, or manifest).
2. **Coordinator-Owned Shared Files**:
   - Files shared across modules (e.g. `package.json`, root `CMakeLists.txt`, central routing tables, DB migrations) must be designated as **Coordinator-Owned**.
   - These are withheld from worker worktrees and integrated sequentially by the coordinator in Phase 4.
3. **Audit Targets (`audit_diff.sh`)**:
   - Each task brief must define concrete automated verification commands that the orchestrator's `audit_diff.sh` script can run against the worktree diff.
4. **Adaptive Gating Threshold**:
   - Only recommend parallel worker dispatch when the task scope exceeds **12–15+ files** or spans clearly independent modules (e.g. backend / frontend / test suite).
   - For smaller tasks (<12 files), specify **Solo Mode** with sequential execution.
5. **Graceful Host Degradation**:
   - If git is absent or worktrees fail, the executor must fall back to standard sequential execution in the primary workspace without crashing.

---

## Prevent Coordination Loops

Assign responsibilities once:
1. **Council**: Evaluates choices and renders a verdict.
2. **Planner**: Establishes task boundaries, acceptance criteria, and dependency DAG.
3. **Executor**: Implements and verifies.

Never loop back recursively between skills unless an explicit replan condition is triggered by a failed contract or invalid assumption.
