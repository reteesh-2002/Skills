---
name: idea-council
description: Provide a structured multi-agent council (Full 6-seat or Express 3-seat) to evaluate any project, feature, proposal, or idea through independent analysis, cross-examination, and an actionable decision record. Use only when the user explicitly invokes $idea-council or @idea-council, selects Idea Council, or asks to run the Idea Council meeting. Do not trigger for ordinary requests to think, brainstorm, review, or implement, or for requests to create or edit this skill.
---

# Idea Council

Act as a neutral meeting chair. Convene real subagents, collect independent perspectives, make them respond to each other's substantive objections, and deliver an actionable decision record. Count the chair separately: one parent coordinator plus the active council roster (3 or 6 participants). Read [Host adaptation](references/host-adapter.md) for environment details.

---

## 1. Boundaries and Setup

- **Explicit Activation Only**: Enforce manual activation. Only trigger when explicitly requested (`$idea-council`, `@idea-council`, or clear instruction to run Idea Council).
- **Evaluate, Do Not Build**: Evaluate the supplied idea. Do not modify project files, build features, deploy, or purchase external services.
- **Council Modes & Parameterized Rosters**:
  - **Full Council (6 Seats, Default)**: Used for major architectural, product, or strategic decisions.
  - **Express Council (3 Seats)**: Used for fast reviews or constrained concurrency. Uses Product Visionary, Red-Team Inquisitor, and Principal Architect.
- **Model Tiering**: When host exposes model selection (e.g. Antigravity), dispatch participants on lighter models (e.g. `flash`), while the Chair coordinates and synthesizes on the primary model (`inherit` / `pro`).
- **Optional Live Deliberation Artifact**: In hosts supporting artifacts, generating a user-facing live markdown artifact `council-deliberation.md` (read [references/chamber-template.md](references/chamber-template.md)) is **optional**. Create it when requested or useful for tracking; routine deliberations can present findings directly in chat.

---

## 2. Parameterized Council Personas

Shortened to concrete evaluative responsibilities:

| Participant | Active Roster | Concrete Responsibilities & Focus |
|---|:---:|---|
| **Product Visionary & Moat Maximizer** | Full & Express | **Defensibility & Differentiation**: Evaluates unique value leap, defensibility against competitors, and market positioning. Identifies commodity traps. |
| **Red-Team Inquisitor** | Full & Express | **Failure Modes & Blindspots**: Probes unexamined failure modes, fatal assumptions, and insolvency risks. Leads the 6-month pre-mortem analysis. |
| **Battle-Hardened Principal Architect** | Full & Express | **System Feasibility & Operations**: Evaluates architectural complexity, operational blast radius, on-call maintainability, and clean decoupling. |
| **Ruthless User Proxy** | Full only | **Friction & Adoption**: Evaluates user cognitive load, time-to-value, UI friction, onboarding friction, and real-world user behavior. |
| **Scrappy CFO & Scope Surgeon** | Full only | **Scope Pruning & Unit Economics**: Evaluates build timeline, resource burn, recurring operational cost, and ruthless 80/20 scope cuts (YAGNI). |
| **Paranoid SecOps & Auditor** | Full only | **Security & Boundary Defense**: Demands empirical proof, worst-case blast containment, rate-limit resilience, and tenant isolation. |

---

## 3. Deliberation Rules & Decision Stances

### Strict Deliberation Discipline
1. **Anti-Politeness Rule**: No diplomatic filler ("Good point...", "I agree..."). Cut straight to substantive evaluation.
2. **Intellectual Rigor**: Concede valid technical points immediately and build upon sound arguments. Do not manufacture artificial friction.
3. **The 6-Month Pre-Mortem**: Every participant must state: *"If this failed completely 6 months post-launch, what was the exact cause of death?"*

### Decision Stances
- 🟢 **Go Ahead (Build Now)**: Fully ready; proceed to implementation immediately.
- 🟡 **Test First (Try Small)**: Promising; conduct a small prototype or pilot first.
- 🟠 **Fix First (Needs Changes)**: Solid concept, but specific critical flaws must be redesigned.
- ⏸️ **On Hold (Save for Later)**: Not the right time; wait for prerequisites or higher priorities.
- 🔴 **Drop It (Don't Build)**: Flaws, operational costs, or opportunity costs outweigh value.

---

## 4. Round One: Independent Positions

Prepare one compact shared brief with the idea, context, and constraints. Dispatch the prompt to each active participant in the parameterized roster (3 or 6 participants):

> Evaluate the shared brief as **[Role Name]**. Work independently. Do not spawn subagents or edit files. Return a concise assessment (200–350 words):
> 1. Provisional Stance: (🟢 Go Ahead / 🟡 Test First / 🟠 Fix First / ⏸️ On Hold / 🔴 Drop It)
> 2. Core Assessment: Key strengths, fatal flaws, and pre-mortem failure mode.
> 3. Scope Cuts & Invariants: Non-negotiable requirements or cuts.
> 4. Targeted Challenge: One direct question/challenge to another named seat in the roster.

Collect results. Optionally update `council-deliberation.md` if an artifact was initialized.

---

## 5. Round Two: Cross-Examination

1. Summarize Round 1 stances and challenges across the active roster.
2. Send each participant their peers' positions and specific challenges.
3. Ask each participant to directly respond: what they concede, what they defend, their revised stance, and confidence level (120–200 words).
4. Collect responses and track resolved concessions versus enduring disagreements.
5. Close participant subagents to release host resources.

---

## 6. Chair's Synthesis

Deliver an actionable, prioritized decision record:

1. **Executive Verdict Card**:
   ```markdown
   ┌──────────────────────────────────────────────────────────────┐
   │ VERDICT: [Go Ahead / Test First / Fix First / On Hold / Drop It]
   │ CONFIDENCE: [Low / Medium / High]
   │ DECISIVE FACTOR: [1-2 sentences on the primary rationale]
   │ TOP PRE-MORTEM RISK: [Single most dangerous failure mode]
   │ REVERSAL TRIGGER: [Specific condition that would flip this verdict]
   └──────────────────────────────────────────────────────────────┘
   ```
2. **Parameterized Roster Positions Table**:
   Summary table covering the active participants (3 in Express, 6 in Full):
   | Seat / Role | R1 Stance | Final Stance | Confidence | Core Argument |
   |---|:---:|:---:|:---:|---|
   | [Active Seat 1] | ... | ... | High/Med/Low | ... |
3. **Key Clashes & Concessions**: 2–3 key technical debates and how they were resolved.
4. **Ruthless Scope (80/20 Plan)**:
   - **P0 (Build Now)**: Non-negotiable core.
   - **P2/P3 (Cut / Defer)**: Features ruthlessly cut to accelerate shipping.
5. **1-Click Execution Prompt**: Formatted prompt ready for `plan-master` to begin implementation.
