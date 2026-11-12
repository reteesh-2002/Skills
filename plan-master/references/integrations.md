# Integration contracts

Use only integrations the user selects or source artifacts they provide. Planning must remain 100% functional standalone without any companion skills. Read a selected skill's current instructions before claiming to use it.

## Companion Skill Matrix

| Companion Skill | Input to Plan Master | Planner Responsibility | Execution Boundary |
| :--- | :--- | :--- | :--- |
| **Standalone (No skills)** | Idea, requirements, code, or user prompt | Ground the request, plan tasks/checks, produce a self-contained handoff. | No companion skills or subagents required. |
| **Idea Council v2.0 Output** | Decision record with stance (🟢/🟡/🟠/⏸️/🔴), challenges, open questions | Map verdict directly to plan type: 🟢 $\rightarrow$ Execution Plan; 🟡 $\rightarrow$ Spike Plan with kill triggers; 🟠 $\rightarrow$ Remediation Plan; ⏸️ $\rightarrow$ Prerequisite list; 🔴 $\rightarrow$ Archival ADR. | Preserve dissent; translate accepted decisions into scope and unresolved assumptions into discovery tasks. |
| **swarm** | Plan plus multi-worker execution request | Format tasks into independent module batches with zero-overlap write scopes, coordinator-owned shared files, and clear verification targets. | Coordinator dispatches workers on the shared message board with `workspace:"share"` or `"branch"` for parallel edits. |
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

## 2. Parallel Swarm Profile (`swarm`)

When handing off to `swarm`, adhere to parallel isolation invariants:

1. **Strict 1-Writer-Per-File Isolation**:
   - Each parallel task must specify an explicit, non-overlapping list of target files or directories.
   - Never assign two parallel tasks to the same file (e.g. shared contract, common registry, or manifest).
2. **Coordinator-Owned Shared Files**:
   - Files shared across modules (e.g. `package.json`, root `CMakeLists.txt`, central routing tables, DB migrations) must be designated as **Coordinator-Owned**.
   - These are withheld from parallel worker `workspace:"share"` / `"branch"` assignments and integrated sequentially by the coordinator after landing worker diffs.
3. **Audit & Verification (`scripts/audit_diff.sh` & `scripts/exec_proxy.py`)**:
   - Each task brief must define concrete automated verification commands that can be executed via `python3 scripts/exec_proxy.py --label <task_id> "<cmd>"` and checked with `bash scripts/audit_diff.sh`.
4. **Adaptive Gating Threshold**:
   - Only recommend parallel worker dispatch when the user requests parallel workers or the task spans genuinely independent modules with non-overlapping file ownership.
   - For tightly coupled or small tasks, specify **Solo Mode** with sequential execution.
5. **Graceful Host Degradation**:
   - If `swarm` is unavailable or `workspace:"share"` cannot be created, fall back to sequential execution in the primary workspace without crashing.

---

## Prevent Coordination Loops

Assign responsibilities once:
1. **Council**: Evaluates choices and renders a verdict.
2. **Planner**: Establishes task boundaries, acceptance criteria, and dependency DAG.
3. **Executor**: Implements and verifies.

Never loop back recursively between skills unless an explicit replan condition is triggered by a failed contract or invalid assumption.
