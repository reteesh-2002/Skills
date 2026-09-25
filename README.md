# 🛠️ Antigravity Engineering Skills Suite

A lean, high-craft collection of 10 native Antigravity skills covering the full software lifecycle from prompt to production.

---

## 🎯 The Master Entry Point: `/prompt-architect`

If you have a rough idea, bug, or feature and don't know which skills to call:
```text
Use /prompt-architect.
[Paste your raw idea, dilemma, or task here]
```
Prompt Architect will automatically classify the domain, pick the exact minimal skill team, inject anti-slop rules, and give you the execution-ready prompt.

---

## ⚡ The 3 Power Combos (Quick Copy-Paste)

Instead of wondering which skills to use, use these 3 standard combinations:

### 1. 🎨 The UI & Frontend Sprint
> Use for landing pages, web apps, components, and widgets with zero AI slop:
```text
Use /anti-slop-spec, /frontend-artisan, and /qa-sentinel.
[Your request here]
```

### 2. 🚀 The Full-Stack Feature Builder
> Use for full-stack features with database schemas, APIs, and release hygiene:
```text
Use /plan-master, /schema-craft, /qa-sentinel, and /ship-it.
[Your request here]
```

### 3. 🩹 The Surgical Bugfix
> Use when code crashes, tests break, or unexpected runtime behavior occurs:
```text
Use /deep-debugger and /qa-sentinel.
[Paste error log or description here]
```

---

## 🎛️ The Output Density Standard (Dual-Surface Model)

To eliminate output fatigue without compromising auditability, all execution skills adhere to the **Dual-Surface Evidence Standard**:

1. **Foreground Executive Card (15–25 Lines)**: High-density, structured summary displayed in chat containing exact test counts, commands, and exit codes.
2. **Background Disk Sink**: Full raw `stdout`/`stderr` logs and traces are streamed directly to disk files (`.log`), eliminating context rot and token waste.
3. **The Amber Protocol**: Clear 3-state signaling: 🟢 Clean Pass, 🟡 Pass with caveats/skips, 🔴 Failure/regression (triggers immediate full-trace uncompression).
4. **False-Green Defense**: Forbids declaring success based on `exit 0` alone; strictly validates non-zero test execution counts (`collected > 0; passed == collected`).
5. **Intermediate Pipeline Suppression**: Multi-skill chains suppress intermediate noise to single-line milestone heartbeats; only the terminal skill or coordinator emits the full Executive Card.

---

## 📚 Skill Directory

| Skill | Role | When to Use |
| :--- | :--- | :--- |
| **`prompt-architect`**| Skill Director | **The Master Entry Point**: Transforms raw ideas into optimal skill teams & hardened prompts. |
| **`anti-slop-spec`** | Design Sharpener | Purge AI clichés (Inter font, purple glows, rounded cards) before coding starts. |
| **`frontend-artisan`** | UI Craft Canon | Implement 10 curated design archetypes, tactile physics, and framework adapters. |
| **`idea-council`** | Evaluation Council | 6-seat multi-agent council to evaluate complex ideas with 5 emoji stances. |
| **`plan-master`** | Task & Prompt Planner | Break complex requirements into dependency-aware plans with sanity validation. |
| **`schema-craft`** | Database Architect | Production schemas, foreign key indexes, safe migrations, and edge-case seed data. |
| **`deep-debugger`** | Root Cause Investigator | 6-stage scientific protocol (`Reproduce → Isolate → Hypothesis → Surgical Fix`). |
| **`qa-sentinel`** | Sanity Gatekeeper | Automated verification runner (`node -c`, HTTP `curl`, DOM contrast checks). |
| **`ship-it`** | Release & Git Hygiene | Secret leak checks, atomic Conventional Commits, and PR release notes. |
| **`adaptive-orchestrator`** | Worktree Parallelism | Multi-worker subagents in isolated git worktrees for large projects (>12 files). |
