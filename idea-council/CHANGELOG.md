# Changelog: idea-council

## v2.0 (Intuitive Stances & Inverted Pyramid Upgrade)

1. **Clear, Human-Understandable Stances**:
   - Replaced ambiguous academic terminology (`proceed / pilot / revise / defer / reject`) with crystal-clear decision labels:
     - 🟢 **Go Ahead (Build Now)**: Fully ready; proceed to implementation immediately.
     - 🟡 **Test First (Try Small)**: Promising, but run a small pilot/prototype first before full commitment.
     - 🟠 **Fix First (Needs Changes)**: Good concept, but has specific critical flaws that must be redesigned or repaired before building.
     - ⏸️ **On Hold (Save for Later)**: Not the right time; wait for prerequisites, dependencies, or higher priorities.
     - 🔴 **Drop It (Don't Build)**: Flaws, costs, or opportunity costs outweigh benefits; scrap the idea.

2. **Inverted Pyramid Output Layout**:
   - Replaced the initial "wall of text" with a prominent **Executive Decision Card** (Verdict, Confidence, Decisive Reason, Go/No-Go Trigger).
   - Added a **1-Click Execution Handoff** prompt immediately below the card ready for `plan-master` or an orchestrator skill.

3. **Dual Council Modes (Full vs Express)**:
   - **Full Council (6 Seats, Default)**: Full multi-agent roundtable for major architectural, product, or strategic decisions.
   - **Express Council (3 Seats)**: Value advocate, Constructive skeptic, and Feasibility lead for routine technical choices or when host slots are limited.

4. **Model-Tiering Support**:
   - In hosts that expose model selection (e.g. Antigravity), allows participants to run on fast/cheaper models (e.g. `flash`) while the Chair synthesizes on the primary model (`inherit` / `pro`), slashing token costs by ~75% and latency to <45 seconds.

5. **Live Deliberation Chamber Dashboard**:
   - Added `references/chamber-template.md` to render a live roundtable deliberation board in Antigravity's right-side panel during meetings.

6. **Exportable Architecture Decision Records**:
   - Standardized output format compatible with `docs/decisions/` and `DECISION.md`.
