# Suite Output Policy & Effort Profiles

Authoritative output reference for the Antigravity Skills Suite, derived from [`suite-policy.json`](../suite-policy.json).

---

## 1. Surface Defaults & Output Formats

| Surface / Context | Format & Target | Behavior |
|---|---|---|
| **Routine task** | Outcome + meaningful changes + verification + limitation (Target: **4–8 lines**) | Concise summary in chat. Avoid dumping full plans, exhaustive file lists, or raw command traces. |
| **Review** | Actionable findings first | **No mandatory finding quota**. Clean passes with zero findings are valid. Explicitly label self-review when independent reviewer is unavailable. |
| **Failure** | Cause/uncertainty + relevant excerpt + next action + full log path | Pinpoints failure without flooding chat; points to full disk log. |
| **Intermediate pipeline stage** | Single-line milestone heartbeat | Intermediate skills in a pipeline suppress full cards (e.g. `✓ [skill]: summary`). Only the terminal or coordinating skill emits the final summary. |
| **Engineering blueprint** | Inside-Out blueprint (5 core decisions) | Full blueprint when explicitly requested; routine-chat length caps do not apply. |
| **Execution plan** | Plan artifact + concise chat overview | Detailed step breakdown lives in the artifact; chat displays status and open decisions. |

---

## 2. Progressive Detail & User Preferences

Support conversational detail toggles without requiring special slash commands:
- **"brief" / "concise"**: 2–4 lines; high-level outcome and status.
- **"normal" / default**: 4–8 lines; outcome, changes, verification, evidence path.
- **"show details" / "verbose"**: Uncompressed logs, detailed finding breakdowns, or complete diff context.

---

## 3. Pipeline Invariants

1. **Terminal Writer Only**: The coordinating or terminal skill writes the user-facing summary; workers and intermediate skills emit single-line heartbeats.
2. **Bounded Output**: Keep chat failure summaries concise with the failing command, relevant excerpt, and next action.
3. **Secret Redaction**: Credentials, tokens, and private keys must be scrubbed from logs and summaries.
4. **Readiness vs. Publishing**: Verifying technical candidate readiness does not authorize publishing or pushing. Pushing or publishing requires explicit user consent.

---

## 4. Effort Profiles

| Profile | Scope & Checks | Boundaries |
|---|---|---|
| **Quick** | Smallest relevant workflow, targeted syntax/smoke checks | Skips optional visual mockups, Idea Council, and parallel workers. Ideal for <3 file edits. |
| **Standard** | Scoped planning, proportional verification tiers | Bounded exploration, standard test pass, solo or small worker dispatch. |
| **Thorough** | Deep planning, multi-tier verification, independent code review | Used for high-risk work (>12 files, auth, payments, migrations). Explicit budgets. |

---

## 5. Core Invariants

- An explicit blueprint request receives all 5 core engineering decisions regardless of effort profile.
- Effort profiles never override manual activation or host constraints.
- Do not claim token or cost limits are enforced unless host telemetry exists.
- Planning does not authorize publishing.
- A prior explicit implementation instruction does not require re-authorization when a skill transitions stages.
- Explicitly requested specialists may load reference files on demand, but must not spawn workers, start councils, or publish without instruction.
