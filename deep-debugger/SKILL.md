---
name: deep-debugger
description: Systematic root cause investigation and surgical bug repair. Enforces a 6-stage scientific protocol (Reproduce -> Isolate -> Inspect State -> Root Cause Hypothesis -> Surgical Fix -> Regression Proof) to prevent shotgun debugging and token-burning patch loops. Use when code fails, tests break, unexpected runtime behavior occurs, or the user asks to debug or fix an error.
---

# Deep Debugger

Systematic, hypothesis-driven root cause analysis and surgical defect remediation. Eliminates guessing, premature patching, and token-wasting trial-and-error loops by strictly isolating the exact point of failure before proposing or touching code.

## The Anti-Shotgun Rules

1. **Never edit code without an isolated reproduction**: If you cannot trigger or observe the failure in a controlled step, you do not yet understand the bug.
2. **Never change multiple unrelated things at once**: "Shotgun fixes" obscure the root cause and introduce secondary regressions.
3. **Never touch working files outside the failure path**: Preserve untouched code integrity.
4. **Log before you patch**: When state is unclear, insert non-destructive diagnostic logging or probe with minimal inspector commands before making persistent edits.
5. **Protect Unrelated User Edits**: During rollback or reversion, only touch files modified during the active defect investigation. Never execute indiscriminate `git reset --hard` or wipe unrelated uncommitted changes.

---

## The "3 + 5" Escalation Protocol (Max 8 Cycles)

To balance deep investigation of stubborn race-conditions with zero tolerance for infinite hallucination spirals:

```
[Cycles 1–3: Fast Surgical Probing]
  │  Direct root-cause hypotheses on the immediate failure site.
  ▼
[⚠️ CYCLE-3 SANITY CHECKPOINT] ──> Resolved? ──(YES)──> [Exit 0 & Verify]
  │ (NO)
  ├── 1. Blast Radius Check: Did we touch >2 files? If YES: REVERT investigation edits (protect unrelated user files).
  ├── 2. Anti-Shotgun Audit: Reject blind try/catch wrappers or typecasts (as any).
  └── 3. Escalate: Announce "Surgical fix failed. Escalating to Deep Trace Mode."
  ▼
[Cycles 4–8: Deep Trace & Minimal Reproduction]
  │  Construct isolated minimal repro script in scratch/repro_[id].ext.
  │  Instrument state timeline logging (Before -> Action -> Corrupted State).
  ▼
[🛑 CYCLE-8 HARD CEILING] ──> Resolved? ──(YES)──> [Exit 0 & Verify]
  │ (NO)
  └── HALT execution immediately. Output Failure Autopsy with 8 hypotheses tested.
      Yield cleanly to human developer with zero unverified file mutations.

---

## The 6-Stage Investigation Protocol

```
[1. Reproduce] ──> [2. Isolate] ──> [3. Inspect State] ──> [4. Root Cause] ──> [5. Surgical Fix] ──> [6. Regression Proof]
```

### Stage 1: Concrete Failure Capture
Capture the failure in its raw, unambiguous state:
- Exact command or user interaction that triggered the failure.
- Complete, untruncated stderr, stdout, or stack trace.
- Exit code and environment details (runtime version, active env vars, working directory).
- Classify failure type:
  - **Syntax / Build Error**: Compilation failure, missing token, unclosed bracket.
  - **Runtime Exception**: Null pointer, undefined property, type mismatch, unhandled rejection.
  - **Logic / Semantic Defect**: Program runs with code 0 but produces wrong output or incorrect state.
  - **Environmental / Dependency**: Missing binary, version mismatch, port collision, permission denied.

### Stage 2: Scope Isolation (Binary Search / Bisect)
Narrow down the blast radius to the smallest possible unit:
- Identify the exact file, class, function, or line of code where the invariant broke.
- Distinguish between **symptom location** (where the crash happened) and **defect origin** (where bad data was created).
- If multiple modules are involved, mock or isolate upstream inputs to verify whether the failing component behaves correctly in isolation.

### Stage 3: State & Boundary Inspection
Examine actual runtime values immediately prior to the crash:
- Print, trace, or evaluate inputs, arguments, and environment variables at the function boundary.
- Check assumptions:
  - Is an array empty when expected to have elements?
  - Is an async promise resolving out of order (race condition)?
  - Is an object null or undefined due to missing optional chaining?
  - Is a path relative when an absolute path was expected?

### Stage 4: Falsifiable Root Cause Hypothesis
Formulate a single, testable hypothesis that answers three questions:
1. **What specifically is broken?** (e.g., `event.target.value` is undefined because the listener is bound to the parent SVG container instead of the input element).
2. **Why did it fail now?** (What changed in input, state, or environment).
3. **Why did it work previously?** (If it previously worked, identify the breaking commit or environmental shift).

*If your hypothesis cannot predict the exact reproduction failure, reject it and return to Stage 3.*

### Stage 5: Minimal Surgical Fix
Implement the smallest necessary change that directly resolves the root cause:
- Change the minimum number of lines required.
- Do not refactor surrounding architecture during a bug fix unless explicitly requested.
- Maintain existing style, variable naming conventions, and docstrings.
- Add defensive guards or assertions if appropriate to prevent future silent degradation.

### Stage 6: Regression & Verification Proof
Prove the fix works using empirical evidence:
1. Re-run the reproduction command via the trusted execution proxy:
   `bash scripts/exec-proxy.sh --label debug_verify <reproduction command>`
   Verify clean exit code 0 and valid output.
2. Run adjacent tests via `exec-proxy.sh` -> Verify zero secondary regressions and update `.evidence/manifest.v1.json`.
3. Clean up any temporary diagnostic print statements or debug logs before concluding.

---

---

## Dual-Surface Evidence Model & Output Format

To maintain user attention and avoid context bloat while preserving 100% auditability:
1. **Background Disk Sink**: Full, uncompressed stack traces, heap dumps, bisect logs, and verbose inspector traces are saved to `<appDataDir>/brain/<conversation-id>/scratch/debug-[id].log`.
2. **Foreground Executive Card (15–20 Lines Target)**:
   When running standalone or as the terminal task:

```markdown
### 🐞 Defect Resolution Record: [GREEN / RED]

* **Failure Symptom**: [One-sentence description of observed error & exit code]
* **Root Cause**: [Exact mechanism that broke the invariant and why]
* **Location**: [`file.ext:L12-15`](file:///absolute/path/to/file.ext#L12-L15)
* **Surgical Fix**: [What was modified in 1-2 sentences]
* **Verification Proof**:
  - `[verification command]` ──> **PASS** (exit 0; observed expected behavior)
* **Evidence**: Full diagnostic traces saved at [`debug-[id].log`](file:///path/to/log)
* **Next Action**: [Ready for QA Sentinel / Blocked]
```

3. **Intermediate Pipeline Suppression Rule**:
   When Deep Debugger is an **intermediate step** in a multi-skill pipeline (e.g. `deep-debugger` → `qa-sentinel` → `ship-it`), it suppresses the full DRR card to a **single-line milestone heartbeat**:
   `✓ [deep-debugger]: Fixed <bug> in <file.ext:L12> (verified with <cmd>, exit 0)`
   The terminal skill or orchestrator then emits the final unified card.

