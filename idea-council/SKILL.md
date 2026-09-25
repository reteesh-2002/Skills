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
  - **Express Council (3 Seats)**: Uses Value advocate, Constructive skeptic, and Feasibility lead. Used when the user requests a fast review, for routine code choices, or when host concurrency is constrained.
- **Model Tiering**: When the host exposes model selection (e.g. Google Antigravity), dispatch participants on fast/cheaper models (e.g. `flash`), while the Chair synthesizes on the primary model (`inherit` / `pro`). This reduces token costs by ~75% and latency to <45 seconds. In single-model environments, inherit the session model.
- **Live Deliberation Chamber (Antigravity & Artifact Hosts)**: In artifact-supporting hosts, initialize a user-facing markdown artifact `council-deliberation.md` (read `references/chamber-template.md`) at Round 1 dispatch. Update it at Round 2 and final synthesis so users can watch the live roundtable debate on their right-side screen.
- Confirm that all participants can receive or resume for a second round before starting.

## Perspectives

Assign every participant a unique name and focus:

| Participant | Council Mode | Focus |
| :--- | :---: | :--- |
| **Value advocate** | Full & Express | Identify the problem solved, intended beneficiaries, strongest advantages, differentiators, and conditions under which the idea is worthwhile. |
| **Constructive skeptic** | Full & Express | Examine weak assumptions, disadvantages, opportunity costs, failure scenarios, and reasons to reject or simplify the idea. |
| **Feasibility lead** | Full & Express | Assess implementation or execution, dependencies, technical constraints, integration, and maintenance. |
| **User advocate** | Full only | Examine real user workflows, adoption, accessibility, friction, and developer/user experience. |
| **Delivery and economics lead** | Full only | Assess time, staffing, cost, operational load, sustainability, and realistic minimum scope. |
| **Risk and evidence lead** | Full only | Examine reliability, security/privacy, evidence quality, hidden uncertainty, and falsification experiments. |

Require every participant to identify both benefits and drawbacks. Do not force advocates to approve or skeptics to reject.

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

> Evaluate the shared brief from the perspective of [role]. Work independently. Do not spawn agents, change project files, or implement the idea. Return a concise assessment:
> 1. Provisional Position: (🟢 Go Ahead / 🟡 Test First / 🟠 Fix First / ⏸️ On Hold / 🔴 Drop It)
> 2. Strongest benefits
> 3. Strongest drawbacks
> 4. Key assumptions or evidence gaps
> 5. Feasible improvement or alternative
> 6. One direct question for a named other participant
> Give concise reasons and source pointers. Distinguish facts, assumptions, and estimates. Target 200–350 words.

Collect results. If running in an artifact host, update `council-deliberation.md` with Round 1 positions.

## Round Two: Cross-Examination and Revision

1. Condense round one into an attributed position sheet.
2. Send every participant the shared sheet and targeted challenges from other participants. Ensure each responds to at least one actual peer claim.
3. Ask each participant to answer the challenge, assess the strongest opposing case fairly, and state what they retain, concede, or revise.
4. Request a final position (Go Ahead / Test First / Fix First / On Hold / Drop It), confidence (low / medium / high with reason), and one next action. Target 120–200 words per participant.
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
   │ GO / NO-GO TRIGGER: [Specific condition that would reverse this decision]
   └──────────────────────────────────────────────────────────────┘
   ```
2. **1-Click Execution Handoff**: A pre-formatted prompt ready for `plan-master` or an orchestrator skill so the user can immediately act on the decision.
3. **Advantages and Disadvantages**: Compact table covering material benefits, drawbacks, and relevant mitigations.
4. **Key Debates**: Two or three attributed exchanges summarizing actual concessions and unresolved objections.
5. **Final Positions**: Table of all participants with their final stance and confidence level.
6. **Best Version of the Idea**: Concrete scope, what to prioritize, and what to postpone or remove.
7. **Next Steps**: 3 to 5 prioritized actions or experiments with observable success/failure criteria.
8. **Exportable Decision Record**: Optionally save the decision record to `DECISION.md` or `docs/decisions/` in the project repository.

## Invocation Examples

- `$idea-council Think about this idea: an offline document summarizer for college students.`
- `Run Idea Council (Express) on whether to use SQLite or JSON files for local caching.`
- `/idea-council Evaluate this feature: adding WebSockets to our notification backend.`
