---
name: plan-master
description: Turns user requirements or an existing blueprint into a grounded, actionable execution plan. Automatically activates for multi-step feature, system, or architecture requests. Do not activate before create-architect; do not regenerate the blueprint. Use plan-master to produce the plan after the blueprint exists.
---

# Plan Master

Translate user requirements or a supplied blueprint into a grounded, dependency-aware execution plan. Inspect relevant source, manifests, and tests before asserting that files or commands exist. Mark proposed new files explicitly as `[NEW]`.

---

## Activation and action boundary

Automatically activate when the user asks to plan, implement, architect, or build a multi-step feature or system.

**Do not:**
- Regenerate or copy the architecture blueprint into the plan
- Produce an architecture blueprint — use `create-architect` for that
- Launch implementation workers, run migrations, or deploy solely because this skill was activated
- Require a second approval before implementation when the user's request already authorizes it
- Select a mandatory minimum number of skills for the execution prompt

**Three request modes:**
- **Plan only** (default): inspect read-only, produce the plan, stop.
- **Plan + handoff**: produce plan and a copyable handoff prompt for another executor or session.
- **Plan + execute**: finish and validate the plan, then continue authorized implementation without asking again.

---

## 1. Grounding

Before writing tasks, verify proportionately:
- Read entry points, directory structure, manifests, and relevant tests
- Confirm that referenced file paths exist; flag missing ones explicitly
- Note the current state of any files the plan will modify
- If working from a specification, reference its requirement IDs (`FR-01`, `A-01`); do not reproduce them

---

## 2. Task fields

Each task must include:

```
Task ID | Outcome | Requirement or acceptance IDs | Files or scope |
Context Scope | Dependencies | Verification command | Risk or recovery action
```

- Use stable IDs: tasks `T1`, `T2`…; acceptance criteria `A1`, `A2`…
- Propose new files as `[NEW] path/to/file`
- Verification must be a runnable command, not a vague assertion
- **`[CONTEXT SCOPE]`** — mandatory field listing the exact 2–4 files the agent is permitted to load for this task. Never list entire directories. When working with vertical slice modules, the scope is `contract.ts + service.ts + <slice>.test.ts` for that slice only. All other files remain invisible.

---

## 3. Depth tiers

Select the smallest useful depth. See [`references/templates.md`](references/templates.md) for fill-in blocks.

| Depth | When | Format |
|---|---|---|
| **Compact** | Small bugfixes, single-file edits, < 12 files | Text only, < 400 tokens, no diagram |
| **Standard** | Single features or medium components | Executive card, task table, optional dependency diagram |
| **Detailed** | Large multi-phase systems or parallel workers | Standard + interface contracts, milestones, rollback triggers |

---

## 4. Sequencing, Parallelism & the Sub-600 LOC Context Rule

- Provide a valid sequential order for every plan.
- Sequential execution is the default. Recommend the orchestrator (`adaptive-worker-orchestrator-v2`) only when the user requests workers and the work is genuinely separable with non-overlapping file ownership.
- Enforce strict 1-writer-per-file isolation for any concurrent tasks.
- Dependency diagrams are optional; use them only when branching is clearer than an ordered list.

**Sub-600 LOC Context Rule (enforced for vertical slice projects):**
When a project uses vertical slice architecture (`src/modules/<slice>/`), each task must be scoped to a single slice. The agent context per task must stay below 600 lines by loading only the target slice files. Never plan a task that requires reading two different module slices simultaneously — break it into two separate tasks. See [`references/slice-dag-rules.md`](references/slice-dag-rules.md) for example DAGs.

- **1-Slice-Per-Task invariant**: A single task targets exactly one module slice.
- **Explicit Context Ceiling**: If the `[CONTEXT SCOPE]` would exceed ~600 lines, split the task.
- **Cross-Slice Communication**: Tasks may reference another slice's `contract.ts` (its public interface) but never its `service.ts` or internal files.
- **Cohesion Over File Chopping**: Individual cohesive files (state machines, parsers, schemas) may be larger (up to 1,200–1,500 LOC); do not fragment cohesive domain files into shallow helpers merely to satisfy line metrics.

---

## 5. Recommending specialist skills

Plan Master may recommend relevant specialists (`schema-craft`, `security-verifier`, `runtime-reliability`, etc.) where the work genuinely benefits. Do not activate them automatically. The user or a subsequent explicit request activates them.

---

## 6. Handling specification conflicts

If the plan reveals a conflict with the specification or an unresolved scope decision, surface it as a focused decision item. Do not silently rewrite product intent or expand scope.

---

## 7. Pre-flight sanity check

Before finalizing the plan:
1. **Acyclicity** — no circular task dependencies
2. **Write isolation** — no two concurrent tasks own the same file
3. **Grounded paths** — existing paths verified; new files flagged `[NEW]`
4. **Bounded unknowns** — genuine unknowns converted to discovery tasks with exit criteria
5. **Runnable verification** — every task has a concrete check command
6. **Stop triggers** — defined failure conditions that pause execution
7. **Slice isolation** (vertical slice projects) — no task writes to more than one module slice; no task's `[CONTEXT SCOPE]` contains internal files from a sibling slice; cross-slice interaction is limited to reading the sibling's `contract.ts` only

Fix discrepancies before presenting the plan.

---

## 8. Output

In artifact-supporting hosts, write the plan as `plan.md`. In chat, use the inverted-pyramid structure from `references/templates.md`: executive card first, execution prompt at top, then task table, then risks.

A planning-only request ends with the plan. A "plan and execute" request continues into implementation after the plan is validated, without requiring another approval.

Generate an execution handoff prompt only when explicitly requested, for another executor, or for a separate session.

---

## Reference files

- [`references/templates.md`](references/templates.md) — Plan format templates (compact, standard, detailed, spike, remediation)
- [`references/slice-dag-rules.md`](references/slice-dag-rules.md) — Vertical slice DAG rules with sample 10-task plan and context scope annotations
