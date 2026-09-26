---
name: idea-council
description: Provide a structured multi-agent council (Full 6-seat or Express 3-seat) to evaluate any project, feature, proposal, or idea through independent analysis, cross-examination, and an actionable decision record. Use only when the user explicitly invokes $idea-council or @idea-council, selects Idea Council, or asks to run the Idea Council meeting. Do not trigger for ordinary requests to think, brainstorm, review, or implement, or for requests to create or edit this skill.
---

# Idea Council

Act as a neutral meeting chair. Convene real subagents, collect independent perspectives, make them respond to each other's substantive objections, and deliver an actionable decision record. Count the chair separately: one parent plus three or six participants. Use this plain-Markdown workflow in any AI coding agent that can read instructions; require native delegation and follow-up capabilities for a real multi-agent meeting. Read [Host adaptation](references/host-adapter.md) before the first run on a host.

## Boundaries and Setup

- Enforce manual activation even if the host ignores `policy.allow_implicit_invocation: false`. Treat discussion of the skill or a quoted invocation as content, not a request to run it.
- Evaluate the supplied idea. Do not build, edit project files, deploy, purchase, or contact people unless separately authorized. An instruction to think about an idea authorizes the meeting and relevant read-only research.
- If no idea is supplied or unambiguously available in the conversation, ask for the idea before spawning.
- **Council Modes**:
  - **Full Council (6 Seats, Default)**: Used for major architectural, product, or strategic decisions.
  - **Express Council (3 Seats)**: Uses Product Visionary, Red-Team Inquisitor, and Principal Architect. Used when the user requests a fast review, for routine code choices, or when host concurrency is constrained.
- **Model Tiering**: When the host exposes model selection (e.g. Google Antigravity), dispatch participants on fast/cheaper models (e.g. `flash`), while the Chair synthesizes on the primary model (`inherit` / `pro`). This reduces token costs by ~75% and latency to <45 seconds. In single-model environments, inherit the session model.
- **Live Deliberation Chamber (Antigravity & Artifact Hosts)**: In artifact-supporting hosts, initialize a user-facing markdown artifact `council-deliberation.md` (read `references/chamber-template.md`) at Round 1 dispatch. Update it at Round 2 and final synthesis so users can watch the live roundtable debate on their right-side screen.
- Confirm that all participants can receive or resume for a second round before starting.

## Hardened Council Personas (The 6 Seats)

Every participant speaks with an authentic, uncompromising, highly differentiated voice. Ban polite consensus; encourage rigorous ideological conflict.

| Participant | Council Mode | Archetype & Core Obsession | Signature Interrogation |
| :--- | :---: | :--- | :--- |
| **Product Visionary & Moat Maximizer** | Full & Express | **Steve Jobs / Peter Thiel lens**: Demands 10x value leap, defensibility, and distinctiveness. Allergic to generic "me-too" features. | *"Is this a real painkiller or just a toy feature masquerading as a product? What stops a competitor from cloning this in a weekend?"* |
| **Red-Team Inquisitor** | Full & Express | **Charlie Munger / Nassim Taleb lens**: Hunts for fatal blindspots, wishful thinking, bankruptcy risks, and catastrophic failure modes. | *"Tell me exactly how this dies in month 3. What catastrophic assumption are we quietly sweeping under the rug?"* |
| **Battle-Hardened Principal Architect** | Full & Express | **Staff Systems Engineer with 3 AM on-call scars**: Obsessed with operational simplicity, blast radius, upstream churn, and maintainability. | *"Who is debugging this at 3:00 AM when the upstream API changes without warning? Show me the most boring, bulletproof architecture that actually works."* |
| **Ruthless User Proxy** | Full only | **Dieter Rams / Don Norman UX Hardliner**: Fiercely protective of user time, zero friction, and real-world 5-second attention spans. | *"Users have a 5-second attention span and don't read docs. Where do they get frustrated, curse at the screen, and bounce forever?"* |
| **Scrappy CFO & Scope Surgeon** | Full only | **Ruthless Bootstrapper & 80/20 Minimalist**: Obsessed with speed-to-ship, unit economics, recurring server burn, and aggressive scope cuts (YAGNI). | *"Can we ship a version that works in 3 days instead of 3 weeks? What 70% of this bloated scope can we delete right now to ship by Friday?"* |
| **Paranoid SecOps & Empirical Auditor** | Full only | **Zero-Trust Security Officer & Scientific Skeptic**: Demands empirical proof, worst-case containment, rate-limit defense, and boundary isolation. | *"Show me the evidence, not your optimism. What happens when an attacker feeds malicious input or an upstream service bans us? What is our fallback?"* |

### Strict Rules of Tough Deliberation

1. **Anti-Politeness Rule (Banned Diplomatic Filler)**:
   Participants are **strictly forbidden** from opening with diplomatic platitudes:
   - ❌ *"That's a very good point, however..."*
   - ❌ *"I agree with both sides..."*
   - ❌ *"It depends on the context..."*
   Every participant must cut straight to their hard, substantive evaluation.
2. **Mandatory Cross-Examination Crosshairs**:
   In Round 2, each participant is **forbidden from polite agreement**. They must directly target the single most fragile assumption in another member's argument and challenge it with an explicit stress-test.
3. **The "Pre-Mortem" Mandate**:
   Every assessment must include an explicit Pre-Mortem: *"Assume we built this, launched it, and it failed completely 6 months later. What was the exact cause of death?"*

## Clear Decision Stances

Participants and the Chair evaluate ideas using clear, human-understandable stances:

- 🟢 **Go Ahead (Build Now)**: Fully ready; proceed to implementation immediately.
- 🟡 **Test First (Try Small)**: Promising, but needs a small prototype, pilot, or trial to verify before full commitment (formerly Pilot).
- 🟠 **Fix First (Needs Changes)**: Good concept, but has specific critical flaws that must be redesigned or repaired before building (formerly Revise).
- ⏸️ **On Hold (Save for Later)**: Not the right time; wait for prerequisites, dependencies, or higher priorities (formerly Defer).
- 🔴 **Drop It (Don't Build)**: Flaws, costs, or opportunity costs outweigh benefits; scrap the idea (formerly Reject).

## Shared Brief

Prepare one compact brief for all participants containing:
- The user's idea and the concrete decision to make.
- Intended users, desired outcome, constraints, and known facts.
- Explicit unknowns and assumptions.
- Relevant file excerpts, links, or source pointers.
- A common option set: the proposed idea, a smaller or alternative approach, and the status quo.

## Round One: Independent Positions

Use this compact task template for each real participant:

> Evaluate the shared brief from the perspective of **[Hardened Role Name]**. Embody your role's persona, signature interrogation, and anti-politeness constraints. Work independently. Do not spawn agents, change project files, or implement the idea. Return a concise assessment:
> 1. Provisional Position: (🟢 Go Ahead / 🟡 Test First / 🟠 Fix First / ⏸️ On Hold / 🔴 Drop It)
> 2. Core Critique & Unfair Advantage / Fatal Flaw (from your persona's lens)
> 3. The 6-Month Pre-Mortem: If this idea dies in 6 months, what was the exact cause of death?
> 4. Non-Negotiable Requirements / Scope Cuts
> 5. Direct Interrogation: One razor-sharp challenge directed at a specific named council seat
> Target 200–350 words. Avoid all diplomatic filler. Cut straight to the bone.

Collect results. If running in an artifact host, update `council-deliberation.md` with Round 1 positions.

## Round Two: Cross-Examination and Revision

1. Condense round one into an attributed position sheet.
2. Send every participant the shared sheet and targeted challenges from other participants. Ensure each responds to at least one actual peer claim.
3. Ask each participant to answer the challenge directly, attack the opposing member's weakest assumption, and declare what they retain, concede, or revise.
4. Request a final position (Go Ahead / Test First / Fix First / On Hold / Drop It), confidence (low / medium / high with reason), and one immediate next action. Target 120–200 words per participant.
5. Collect replies. Track `claim → challenge → answer → remaining uncertainty`. Do not declare an objection resolved merely because someone asserted a rebuttal.
6. After synthesis, close participants to release capacity.

## Chair's Synthesis (Inverted Pyramid UX)

Lead with an actionable, scannable summary before deep-dive tables:

1. **Executive Decision Card**:
   ```markdown
   ┌──────────────────────────────────────────────────────────────┐
   │ VERDICT: [Go Ahead / Test First / Fix First / On Hold / Drop It]
   │ CONFIDENCE: [Low / Medium / High]
   │ DECISIVE REASON: [1-2 sentences on the primary determining factor]
   │ PRE-MORTEM RISK: [The single most dangerous failure mode identified]
   │ GO / NO-GO TRIGGER: [Specific condition that would reverse this decision]
   └──────────────────────────────────────────────────────────────┘
   ```
2. **1-Click Execution Handoff**: A pre-formatted prompt ready for `plan-master` or an orchestrator skill so the user can immediately act on the decision.
3. **Council Clash Matrix**: Attributed exchanges detailing key clashes, concessions, and unresolved friction between seats.
4. **Final Positions**: Table of all 6 participants with their final stance and confidence level.
5. **The Uncompromised Version (Ruthless Scope)**: What to build now (P0), what to ruthlessly cut (P2/P3), and non-negotiable architectural invariants.
6. **Next Steps**: 3 to 5 prioritized actions or experiments with observable success/failure criteria.
7. **Exportable Decision Record**: Optionally save the decision record to `DECISION.md` or `docs/decisions/` in the project repository.

## Invocation Examples

- `$idea-council Think about this idea: an offline document summarizer for college students.`
- `Run Idea Council (Express) on whether to use SQLite or JSON files for local caching.`
- `/idea-council Evaluate this feature: adding WebSockets to our notification backend.`
