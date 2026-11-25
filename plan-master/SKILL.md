---
name: plan-master
description: Turns user requirements or an existing blueprint into a grounded, actionable execution plan. Automatically activates for multi-step feature, system, or architecture requests.
---

# Plan Master

Translate user requirements into a lean, dependency-aware execution plan. Inspect relevant files, tests, and dependencies before asserting paths exist. Mark proposed new files explicitly as `[NEW]`.

---

## 1. Action Boundary

Automatically activate when the user asks to plan, architect, or build a multi-step feature.

**Execution Principles:**
- **Small tasks (< 3 files, obvious edits)**: Skip planning ceremony and go directly to implementation with proportionate testing.
- **Plan only**: Inspect read-only, output plan, stop.
- **Plan + execute**: Finish plan, then immediately proceed into authorized implementation without asking for redundant confirmations.
- Never duplicate blueprints or introduce compliance tables.

---

## 2. Anti-Overengineering Gate (Occam's Razor)

Before finalizing tasks, filter every proposed file and component through these 5 hard constraints:
1. **Standard Library & Framework First**: If the language standard library or host framework natively supports the capability, forbid custom wrapper libraries, shims, or homemade mini-frameworks.
2. **Rule of Three (Anti-Abstraction)**: Forbid creating interfaces, abstract base classes, or generic adapter layers that have only one concrete implementation. Build for today's concrete need; duplicate twice before abstracting on the third.
3. **No Shadow Infrastructure**: Never propose custom execution proxies, local task runners, or shadow state databases when native CLI tools (`git`, `npm test`, `pytest`, `sqlite3`) already solve it.
4. **Cohesion over Micro-Chopping**: Do not split a 50-line cohesive function across DTOs, interfaces, services, and repositories. Default to 1 vertical slice file.
5. **Delete-Key Scope Cut**: Remove speculative "future-proofing" (pluggable backends, hypothetical multi-tenancy, dynamic configuration for static constants) from the task plan. Build strictly for today's requirements.

---

## 3. Actionable Plan Format

Write the plan as an actionable markdown document (`plan.md` in artifact hosts):

```markdown
### Goal: <Clear 1-sentence deliverable>

#### Tasks:
- [ ] **T1: <Action title>**
  - Scope: `path/to/file` ([NEW] if new)
  - Details: What to implement/change
  - Verification: `<runnable command, e.g. pytest tests/test_foo.py>`

- [ ] **T2: <Action title>**
  - Scope: `path/to/file`
  - Dependencies: T1
  - Verification: `<runnable command>`
```

---

## 4. Grounding & Invariants

1. **Grounded Paths**: Read files before proposing edits. Mark new files `[NEW]`.
2. **Vertical Slice Boundaries**: 
   - 1 task targets 1 module slice at a time.
   - Slices interact strictly through public interfaces (`contract.ts` / public APIs), never by digging into a sibling slice's private internals.
   - Cohesion over artificial file chopping: Keep cohesive domain logic together (parsers, state machines) without fragmenting into shallow mechanical helpers.
3. **Sequential Default**: Recommend parallel subagents or swarm workers only when modules are genuinely separable with non-overlapping file ownership (fall back to sequential execution otherwise).
4. **Runnable Checks**: Every task has a concrete check command (`npm test`, `pytest`, `cargo test`).
5. **Single-Writer Isolation**: Never assign two tasks or parallel workers to the same file.

---

## 5. Optional References (Load on Demand)

The minimal `- [ ] **T1**` format above is the default. Load these only when the task needs them:
- [`references/templates.md`](references/templates.md) — Extended layouts for multi-phase or parallel plans
- [`references/slice-dag-rules.md`](references/slice-dag-rules.md) — Rules for `modules/<slice>/` codebases
- [`references/integrations.md`](references/integrations.md) — Idea Council verdict & parallel worker handoff contracts
- [`references/source-notice.md`](references/source-notice.md) — Attribution and lineage notice

A planning request ends with the plan. A "plan and execute" request continues directly into implementation.
