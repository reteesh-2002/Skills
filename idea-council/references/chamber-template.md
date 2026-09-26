# Council Deliberation Chamber Template

Used when running in an artifact-supporting host (e.g. Google Antigravity).

The Chair initializes `<artifact_dir>/council-deliberation.md` at Round 1 dispatch and updates it at key milestones (Round 1 collected, Round 2 debate dispatched, Round 2 revision collected, Final verdict).

## Template

```markdown
# 🏛️ Idea Council Deliberation Chamber

**Topic**: <Idea / Proposal Title>  
**Status**: Round 2 Cross-Examination in Progress | **Mode**: Full (6 Seats)

### Council Roundtable

| Seat / Role | Model | Round 1 Stance | Key Interrogation & Peer Clash | Final Stance | Confidence |
| :--- | :---: | :---: | :--- | :---: | :---: |
| **Product Visionary & Moat Maximizer** | `flash` | 🟢 **Go Ahead** | Demands 10x differentiation; challenged on defensibility | 🟢 **Go Ahead** | High |
| **Red-Team Inquisitor** | `flash` | 🔴 **Drop It** | Highlighted 3-month failure mode; challenged on false assumptions | 🟠 **Fix First** | High |
| **Battle-Hardened Principal Architect** | `flash` | 🟡 **Test First** | Challenged upstream churn & 3 AM on-call operational failure blast | 🟡 **Test First** | High |
| **Ruthless User Proxy** | `flash` | 🟠 **Fix First** | Flagged 5-second attention span drop-off & onboarding friction | 🟡 **Test First** | High |
| **Scrappy CFO & Scope Surgeon** | `flash` | 🟡 **Test First** | Cut 60% of bloated scope; demanded weekend MVP | 🟢 **Go Ahead** | High |
| **Paranoid SecOps & Empirical Auditor** | `flash` | 🟠 **Fix First** | Demanded zero-trust boundary & rate-limit fallback proof | 🟡 **Test First** | High |

---

### Live Debate Seams & Pre-Mortem
- **Fatal Pre-Mortem Risk**: <The single most dangerous failure mode identified>
- **Core Clash 1**: Moat differentiation vs. operational complexity
- **Core Clash 2**: Radical scope cuts (YAGNI) vs. enterprise security boundaries

### Current Consensus Direction
🟡 **Test First (Try Small)** — Consensus converged on a stripped-down pilot with strict architectural invariants.
```
