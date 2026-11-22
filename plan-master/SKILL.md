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

## 2. Actionable Plan Format

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

## 3. Grounding & Invariants

1. **Grounded Paths**: Read files before proposing edits. Mark new files `[NEW]`.
2. **Vertical Slice Boundaries**: 
   - 1 task targets 1 module slice at a time.
   - Slices interact strictly through public interfaces (`contract.ts` / public APIs), never by digging into a sibling slice's private internals.
   - Cohesion over artificial file chopping: Keep cohesive domain logic together (parsers, state machines) without fragmenting into shallow mechanical helpers.
3. **Sequential Default**: Recommend parallel `swarm` only when modules are genuinely separable with non-overlapping file ownership.
4. **Runnable Checks**: Every task has a concrete check command (`npm test`, `pytest`, `cargo test`).
5. **Single-Writer Isolation**: Never assign two tasks or parallel workers to the same file.

A planning request ends with the plan. A "plan and execute" request continues directly into implementation.
