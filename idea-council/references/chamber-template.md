# Council Deliberation Chamber Template

Used when running in an artifact-supporting host (e.g. Google Antigravity).

The Chair initializes `<artifact_dir>/council-deliberation.md` at Round 1 dispatch and updates it at key milestones (Round 1 collected, Round 2 debate dispatched, Round 2 revision collected, Final verdict).

## Template

```markdown
# 🏛️ Idea Council Deliberation Chamber

**Topic**: <Idea / Proposal Title>  
**Status**: Round 2 Cross-Examination in Progress | **Mode**: Full (6 Seats)

### Council Roundtable

| Seat / Role | Model | Round 1 Stance | Peer Challenge | Final Stance | Confidence |
| :--- | :---: | :---: | :--- | :---: | :---: |
| **Value Advocate** | `flash` | 🟢 **Go Ahead** | Challenged by Skeptic on ROI | 🟢 **Go Ahead** | High |
| **Constructive Skeptic** | `flash` | 🟠 **Fix First** | Challenged by Feasibility on worktrees | 🟡 **Test First** | High |
| **Feasibility Lead** | `flash` | 🟡 **Test First** | Answered dependency symlink question | 🟡 **Test First** | High |
| **User Advocate** | `flash` | 🟠 **Fix First** | Challenged on focus-stealing | 🟡 **Test First** | High |
| **Delivery & Economics** | `flash` | 🟡 **Test First** | Provided token cost calculation | 🟢 **Go Ahead** | High |
| **Risk & Evidence Lead** | `flash` | 🟠 **Fix First** | Demanded non-destructive cleanup | 🟡 **Test First** | High |

---

### Live Debate Seams
- **Disagreement 1**: Token overhead vs. developer trust
- **Disagreement 2**: Worktree isolation vs. container sandbox permissions

### Current Consensus Direction
🟡 **Test First (Try Small)** — 4 votes Test First, 2 votes Go Ahead. Consensus converged on small pilot with pre-flight fixes.
```
