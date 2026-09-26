---
name: prompt-architect
description: Master prompt composer and skill orchestrator. Analyzes any raw project idea, bug, or feature request, selects the exact optimal subset of skills from your active Antigravity toolkit, injects domain hardening and anti-slop constraints, and crafts a battle-tested, execution-ready prompt. Use when you have an idea and want the ultimate prompt to execute it.
---

# Prompt Architect

> [!NOTE]
> **Consolidation Notice**: Prompt Architect's intent classification, skill team selection, and prompt hardening have been natively consolidated into [`plan-master`](../plan-master/SKILL.md) for single-entry planning. This skill remains active as a standalone alias for direct prompt composition.

The executive director and traffic controller for your entire Antigravity skills suite. Transforms rough, ambiguous, or unpolished user ideas into production-grade execution prompts equipped with the exact right skills, architectural safeguards, and anti-slop constraints.

---

## The Core Philosophy: Surgical Skill Selection

> **Never load all skills at once.**
> Overloading an AI with 8 skills burns thousands of tokens per turn and dilutes model attention. Prompt Architect selects only the **2 to 4 skills** that strictly apply to the task at hand.

---

## 4-Step Prompt Composition Pipeline

```
[1. Classify Domain] ──> [2. Select Skill Team] ──> [3. Inject Constraints] ──> [4. Deliver Execution Prompt]
```

### Step 1: Intent & Domain Classification
Analyze the user's input to determine the core category:
- **🎨 Frontend / UI Sprint**: Landing pages, design systems, visual tools, widgets, audio synths, dashboards.
- **🚀 Full-Stack / Data Feature**: Databases, REST/tRPC APIs, web crawlers, state management, full applications.
- **🩹 Bugfix / Hotfix**: Crashes, stack traces, broken behavior, performance leaks, regression repair.
- **🛡️ Security & Auth Audit**: Authentication, BOLA/IDOR, public APIs, input sanitization, tenant boundaries.
- **⚙️ Operations & Reliability**: Zero-downtime DB migrations, background queues, memory leak soaks, deployment health.
- **🏛️ High-Risk Architecture / Decision**: Evaluating new frameworks, build vs buy, database selection, major pivots.
- **📦 Multi-File Refactor (>12 files)**: Mass migrations, multi-module overhauls across frontend/backend/tests.

### Step 2: Skill Team Selection (The Power Presets)
Map the domain to the optimal, minimal skill combination:

| Domain | Assigned Skill Team | Omitted Skills & Why |
| :--- | :--- | :--- |
| **Frontend / UI Sprint** | `/anti-slop-spec`<br>`/frontend-artisan`<br>`/qa-sentinel` | Omit `orchestrator`, `schema-craft`, `idea-council` to prevent token bloat. |
| **Full-Stack / Data** | `/plan-master`<br>`/schema-craft`<br>`/qa-sentinel`<br>`/ship-it` | Add `/security-verifier` if public APIs or auth are involved. |
| **Bugfix / Hotfix** | `/deep-debugger`<br>`/qa-sentinel` | Omit all planning, council, and design skills. Direct root-cause repair only. |
| **Security / Auth Audit** | `/security-verifier`<br>`/qa-sentinel`<br>`/ship-it` | Direct boundary and synthetic tenant testing against OWASP API Top 10. |
| **Operations / Reliability**| `/runtime-reliability`<br>`/schema-craft`<br>`/ship-it` | Rehearse migrations, test graceful shutdown, and run memory soaks. |
| **High-Risk Decision** | `/idea-council`<br>`/plan-master` | Omit implementation and git tools until the decision verdict is sealed. |
| **Large Multi-Module (>12 files)**| `/adaptive-worker-orchestrator-v2`<br>`/plan-master`<br>`/qa-sentinel` | Activates git worktrees (`.git/.orch-worktrees/`) for parallel worker subagents. |

### Step 3: Domain Hardening & Negative Constraints
Every generated prompt MUST include:
1. **Explicit Negative Constraints (Anti-Slop)**:
   - For UI: Ban generic purple gradients, rounded-xl cards, cyan pills, and Inter font. Enforce a specific archetype from `frontend-artisan`.
   - For DB: Ban unindexed foreign keys, implicit cascades, and non-timezone timestamps.
   - For Network: Ban unsafe unspooling/redirects without private IP SSRF filters.
2. **Deterministic Verification & False-Green Defense**:
   - Mandate executing all checks via `scripts/exec-proxy.sh`.
   - Demand explicit count verification (`collected > 0`, `passed == collected`).
   - Mandate running `scripts/verify-release-gate.sh` before any release actions in `/ship-it`.
3. **Tri-Surface Output Density & Pipeline Suppression**:
   - Instruct all chained skills to adhere to the Tri-Surface model: stream raw verbose logs to background disk files (`.evidence/logs/`), update the machine manifest (`.evidence/manifest.v1.json`), and cap foreground chat output to a **15–25 line Executive Card**.
   - Enforce **intermediate pipeline suppression**: in multi-skill chains (e.g. `deep-debugger` -> `qa-sentinel` -> `ship-it`), intermediate skills emit a 1-line milestone (`✓ [skill]: status`); only the terminal skill emits the final Executive Card.
4. **Delivery Invariants**:
   - Instruct `/ship-it` to scan for secret leaks and format Conventional Commits.

---

## Output Format: The Execution Blueprint

When invoked, Prompt Architect presents:

```markdown
### 🎯 Prompt Architecture Analysis
* **Identified Domain**: [Frontend / Full-Stack / Hotfix / Architecture]
* **Selected Skill Team**: [`/skill-1`, `/skill-2`, `/skill-3`]
* **Why This Team**: [1-2 sentences on why these tools were chosen and why others were omitted]

---

### 📋 The Execution Prompt (Copy-Paste Ready)

```text
Use [/selected-skills]

[Hardened, highly specific, structured prompt containing:
 - Clear scope & deliverables
 - Architecture & data invariants
 - Visual archetype & design language
 - Negative constraints & banned patterns
 - False-green defense & empirical verification criteria
 - Output density constraints (15-25 line Executive Card, background disk logs, intermediate milestone suppression)]
```
```

