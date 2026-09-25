# 🛠️ Antigravity Engineering Skills Suite

A lean, high-craft collection of 12 native Antigravity skills covering the full software lifecycle from prompt to production.

---

## 🎯 The Master Entry Point: `/prompt-architect`

If you have a rough idea, bug, or feature and don't know which skills to call:
```text
Use /prompt-architect.
[Paste your raw idea, dilemma, or task here]
```
Prompt Architect will automatically classify the domain, pick the exact minimal skill team, inject anti-slop rules, and give you the execution-ready prompt.

---

## ⚡ Power Combos (Quick Copy-Paste)

Instead of wondering which skills to use, use these standard combinations:

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

### 4. 🛡️ The Security & Auth Audit
> Use for authentication changes, API endpoints, and sensitive data access:
```text
Use /security-verifier, /qa-sentinel, and /ship-it.
[Your request here]
```

### 5. ⚙️ Production Operations & Reliability
> Use for zero-downtime DB migrations, background workers, and memory soaks:
```text
Use /runtime-reliability, /schema-craft, and /ship-it.
[Your request here]
```

---

## 🎛️ The Tri-Surface Evidence Standard & Release Gate

To eliminate output fatigue and close the self-grading trust boundary, all execution skills operate across three surfaces:

1. **Surface 1: Foreground Executive Card (15–25 Lines)**: High-density, structured summary displayed in chat containing exact test counts, commands, and exit codes.
2. **Surface 2: Background Forensic Log Sink**: Full raw `stdout`/`stderr` logs and traces are streamed directly to disk files (`.evidence/logs/`), eliminating context rot.
3. **Surface 3: Machine-Readable Evidence Manifest**: Receipts bound to the immutable `git write-tree` SHA are recorded in `.evidence/manifest.v1.json`.
4. **Deterministic Release Gate**: `scripts/verify-release-gate.sh` strictly blocks `ship-it` and `git push` if evidence is missing, stale, or fails non-zero test checks.
5. **The Amber Protocol**: Clear 3-state signaling: 🟢 Clean Pass, 🟡 Pass with caveats/skips (requires authorized waiver), 🔴 Failure/regression.
6. **Intermediate Pipeline Suppression**: Multi-skill chains suppress intermediate noise to single-line milestone heartbeats; only the terminal skill or coordinator emits the full Executive Card.

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
| **`qa-sentinel`** | Sanity Gatekeeper | Automated verification runner via `scripts/exec-proxy.sh` with False-Green defense. |
| **`security-verifier`**| API Security Verifier | OWASP API Top 10, BOLA/IDOR, input sanitization, SSRF, and dependency CVE checks. |
| **`runtime-reliability`**| Resilience Engine | Reversible database migrations, memory leak soak tests, and graceful shutdown probes. |
| **`ship-it`** | Release & Git Hygiene | Secret leak checks, atomic Conventional Commits, and gatekeeper verification. |
| **`adaptive-orchestrator`** | Worktree Parallelism | Multi-worker subagents in isolated git worktrees for large projects (>12 files). |

