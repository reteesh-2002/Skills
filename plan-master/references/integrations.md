# Integration contracts

Use only integrations the user selects or source artifacts they provide. Planning must remain 100% functional standalone without any companion skills. Read a selected skill's current instructions before claiming to use it.

## Companion Skill Matrix

| Companion Skill | Input to Plan Master | Planner Responsibility | Execution Boundary |
| :--- | :--- | :--- | :--- |
| **Standalone (No skills)** | Idea, requirements, code, or user prompt | Ground the request, plan tasks/checks, produce a self-contained handoff. | No companion skills or subagents required. |
| **Idea Council Output** | Decision record with stance (🟢/🟡/🟠/⏸️/🔴), challenges, open questions | Map verdict directly to plan type: 🟢 → Execution Plan; 🟡 → Spike Plan with kill triggers; 🟠 → Remediation Plan; ⏸️ → Prerequisite list; 🔴 → Archival ADR. | Preserve dissent; translate accepted decisions into scope and unresolved assumptions into discovery tasks. |
| **Parallel Workers** | Plan plus multi-worker execution request | Format tasks into independent module batches with zero-overlap write scopes, coordinator-owned shared files, and clear verification targets. | Coordinator dispatches workers with isolated workspaces or non-overlapping file ownership for parallel edits. |
| **Council + Planner** | Strategic review to execution plan | Plan Master ingests council verdict and drafts a dependency-ordered plan for solo or parallel execution. | Pipeline runs sequentially: Council (strategic review) → Planner (contracts & DAG) → Implementer. |

---

## 1. Idea Council Verdict Routing Contract

When an Idea Council decision record is provided, map stances deterministically:

| Council Stance | Plan Typology | Structure & Mandatory Guardrails |
| :--- | :--- | :--- |
| 🟢 **Go Ahead (Build Now)** | **Full Execution Plan** | Standard or Detailed task DAG. Ready tasks partitioned for solo or multi-worker execution. |
| 🟡 **Test First (Try Small)** | **Spike / PoC Plan** | Time-boxed experiment plan. Strict boundary: build only the smallest prototype to test the hypothesis. Must include explicit **Go/No-Go Exit Criteria** and quantifiable kill triggers before full build. |
| 🟠 **Fix First (Needs Changes)** | **Remediation Plan** | Targeted architectural redesign plan addressing the specific objections and vulnerabilities identified in the council report. |
| ⏸️ **On Hold (Save for Later)** | **Prerequisite Checklist** | No implementation tasks. Summarizes required dependency releases, environmental prerequisites, and backlog tracking record. |
| 🔴 **Drop It (Don't Build)** | **Archival ADR** | No implementation tasks. Synthesizes rejection rationale, fatal flaws, and alternative recommendations for repository documentation. |

---

## 2. Parallel Worker Isolation Profile

When handing off to parallel workers or subagents, adhere to these isolation invariants:

1. **Strict 1-Writer-Per-File Isolation**:
   - Each parallel task must specify an explicit, non-overlapping list of target files or directories.
   - Never assign two parallel tasks to the same file (e.g. shared contract, common registry, or manifest).
2. **Coordinator-Owned Shared Files**:
   - Files shared across modules (e.g. `package.json`, root `CMakeLists.txt`, central routing tables, DB migrations) must be designated as **Coordinator-Owned**.
   - These are withheld from parallel worker assignments and integrated sequentially by the coordinator after landing worker diffs.
3. **Verification**:
   - Each task brief must define concrete automated verification commands (`pytest`, `npm test`, `cargo test`) and clean `git diff` review.
4. **Adaptive Gating Threshold**:
   - Only recommend parallel worker dispatch when the user requests parallel workers or the task spans genuinely independent modules with non-overlapping file ownership.
   - For tightly coupled or small tasks, specify **Solo Mode** with sequential execution.
5. **Graceful Host Degradation**:
   - If parallel workers or isolated workspaces are unavailable, fall back to sequential execution in the primary workspace without crashing.

---

## Prevent Coordination Loops

Assign responsibilities once:
1. **Council**: Evaluates choices and renders a verdict.
2. **Planner**: Establishes task boundaries, acceptance criteria, and dependency DAG.
3. **Executor**: Implements and verifies.

Never loop back recursively between skills unless an explicit replan condition is triggered by a failed contract or invalid assumption.
