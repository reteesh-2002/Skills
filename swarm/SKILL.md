---
name: swarm
description: >-
  (Preview & Quota Heavy) Run a swarm: several agents working in parallel on
  one task, each in its own conversation, collaborating through a shared
  message board. Use when the work splits into pieces that can be done at the
  same time, or when a second pair of eyes should check the first pair's work.
metadata:
  icon: hub
  logo: logo.svg
---

# Swarm Coordinator

A swarm is a group of autonomous workers collaborating via a shared message board. As the coordinator, you interact with the user and orchestrate workers across isolated turns and workspaces.

## Available Tools

| Tool | Purpose |
| :--- | :--- |
| `swarm` | Lifecycle management: `status`, `models`, `add`, `model`, `kill`, `title`, `channel`. |
| `post_message` | Post assignments, updates, or handoffs to the board (`@<name>`). |
| `read_board` | Read message history sequentially (`since: <seq>`). |
| `swarm_wait` | Zero-token sleep until a matching message is posted (`since: <seq>`). |

---

## Operating Protocol

1. **Never Implement Inline**: All coding, testing, research, and refactoring belongs to workers. Keep your turns short: inspect state, assign tasks, and sleep.
2. **Size Before Starting**: Split tasks along non-overlapping boundaries (one worker per file, target, or subsystem). Never allow two workers to edit the same file simultaneously.
3. **Name the Swarm**: Set title immediately: `swarm{action: "title", title: "<name>"}`.
4. **Spawn Workers**:
   ```json
   swarm{
     "action": "add",
     "name": "parser",
     "brief": "You own src/parser.rs. Make failing cases in tests/parser_test.rs pass without modifying tests. Post diff summary and test output when complete."
   }
   ```
   - **Brief is Public**: Automatically posted as `@<name> <brief>`.
   - **Brief is Self-Contained**: Workers start with fresh context. Specify owned files, forbidden areas, constraints, and exact completion criteria.
   - **Sharded Pools**: For homogeneous batches, pass `tasks: [...]` or `n: <int>` to spawn `<name>-1` through `<name>-<k>`.
5. **Add Narrator & Monitor (If Available)**:
   - If `swarm_narrator` is present in skills, spawn `name: "narrator"` to maintain the UI overview. Relay user feedback as `@narrator user feedback: <text>`.
   - If `swarm_monitor` is present in skills, spawn `name: "monitor"` to catch deadlocks. Act immediately on `@coordinator [stall]`.

---

## Coordination Loop

Execute this loop until task acceptance criteria are satisfied:

```
                  ┌──────────────────────┐
                  │ swarm{action:"status"}│
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │  Assign work (@name) │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │  swarm_wait{since:N} │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │  read_board{since:N} │
                  └──────────┬───────────┘
```

1. **Check Status**: Inspect `waiting` (idle/ready), `working` (active turn), `stopped` (restart needed), or `killed`.
2. **Assign Work by Name**: Post `@<target> <instructions>`. Reference previous deliverables by `#seq` (e.g., `@verifier check #4 and #6`). Never copy-paste diffs between workers.
3. **Park Free**: Call `swarm_wait{since: <last_seen_seq>}`. Do not poll `read_board` in a tight loop.
4. **Evaluate Results**: Read incoming posts with `read_board{since: <last_seen_seq>}`. Accept, request revisions, or route to verifiers.
5. **Mark Done**: Once verified, post `[done] <summary>` (without `@` mentions) to quiet the stall monitor, then summarize results for the user.

---

## Topology & Isolation

- **Independent Verifiers**: Assign dedicated verifier workers (ratio of 1 verifier per 2–4 authors). Verifiers inspect diffs and run test suites; authors apply fixes.
- **Workspace Isolation**:
  - `workspace: "inherit"` (default): Shared working copy. Use for read-only workers, verifiers, and sequential scripts.
  - `workspace: "share"`: Dedicated working copy with shared git object store. Mandatory for authors editing concurrently.
  - `workspace: "branch"`: Fully isolated git clone.
  - *Hygiene*: Changes in share/branch must be committed or merged before `kill`, which destroys the workspace.
- **Context Forking**: Use `fork: "<member>"` when branching an investigation or replacing a dead worker to inherit conversational context.
- **Model Selection & Quota**:
  - Default: Omit `model` to inherit coordinator model.
  - Quota fallback: If a worker exhausts quota, switch it using `swarm{action: "model", name: "<worker>", model: "<new_model>"}` to preserve conversation history. Do not kill and respawn.

---

## Channels & Board Routing

- **Addressing Semantics**:
  - `@name`: Direct assignment. Wakes target worker only.
  - `@all`: Broadcast for universal invariants or global API freezes. Use sparingly; wakes every worker.
  - `@#channel`: Wakes all members subscribed to that channel.
- **Channel Partitioning** (when `channel` action is supported):
  - Isolate noisy sub-teams into dedicated channels (`#frontend`, `#engine`).
  - Keep `main` reserved for cross-area decisions and completion notices.
  - Commands: `create`, `subscribe`, `unsubscribe`, `list`, `archive`.

---

## Suite Integration

- **Execution Proxy**: Instruct workers to run tests via `python3 scripts/exec_proxy.py --label <id> "<cmd>"` to generate tamper-evident receipts in `.evidence/`.
- **Task Ledger**: Coordinate multi-stage DAG dependencies using `python3 scripts/task_ledger.py` to prevent circular blockers and ensure verifiable completion.
