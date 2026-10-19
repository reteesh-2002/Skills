---
name: deep-debugger
description: Systematic root cause investigation and surgical bug repair. Enforces a 6-stage scientific protocol (Reproduce -> Isolate -> Inspect State -> Root Cause Hypothesis -> Surgical Fix -> Regression Proof) to prevent shotgun debugging and token-burning patch loops. Use when code fails, tests break, unexpected runtime behavior occurs, or the user asks to debug or fix an error.
---

# Deep Debugger

Systematic, hypothesis-driven root cause analysis and surgical defect remediation. Eliminates guessing, premature patching, and token-wasting trial-and-error loops by strictly isolating the exact mechanism of failure before proposing or touching code.

---

## The Anti-Shotgun Rules

1. **Reproduction or Observed Evidence First**: Never modify code without either an isolated reproduction or verified observed production evidence.
2. **Never change multiple unrelated things at once**: "Shotgun fixes" obscure the root cause and introduce secondary regressions.
3. **Never touch working files outside the failure path**: Preserve untouched code integrity.
4. **Log before you patch**: When state is unclear, insert non-destructive diagnostic logging or probe with minimal inspector commands before making persistent edits.
5. **Protect Unrelated User Edits**: During rollback or reversion, only touch files modified during the active defect investigation. Never execute indiscriminate `git reset --hard` or wipe unrelated uncommitted changes.
6. **Verification Proof Required**: Never claim or mark a bug fixed without actively executing the reproduction command and confirming it exits with code 0 and passing assertions.

---

## Escalation Protocol (Max 8 Cycles)

To balance deep investigation of stubborn issues with zero tolerance for infinite hallucination spirals:

```
[Cycles 1–3: Fast Surgical Probing]
  │  Direct root-cause hypotheses on the immediate failure site.
  ▼
[⚠️ CYCLE-3 SANITY CHECKPOINT] ──> Resolved? ──(YES)──> [Exit 0 & Verify]
  │ (NO)
  ├── 1. Blast Radius Check & Progress Evaluation: Did the hypotheses yield measurable diagnostic progress?
  │      Assess architectural risk; do NOT force rollback solely based on a 2-file count.
  ├── 2. Anti-Shotgun Audit: Reject blind try/catch wrappers or typecasts (as any).
  └── 3. Escalate: Announce "Surgical fix incomplete. Escalating to Deep Trace Mode."
  ▼
[Cycles 4–8: Deep Trace & Minimal Reproduction]
  │  Construct isolated minimal repro script or test fixture in scratch/repro_[id].ext.
  │  Instrument state timeline logging (Before -> Action -> Corrupted State).
  ▼
[🛑 CYCLE-8 HARD CEILING] ──> Resolved? ──(YES)──> [Exit 0 & Verify]
  │ (NO)
  └── HALT execution immediately. Output Failure Summary with tested hypotheses.
      Yield cleanly to human developer with zero unverified file mutations.
```

---

## The 6-Stage Investigation Protocol

```
[1. Reproduce] ──> [2. Isolate] ──> [3. Inspect State] ──> [4. Root Cause] ──> [5. Surgical Fix] ──> [6. Regression Proof]
```

### Stage 1: Concrete Failure Capture & Evidence
Capture the failure in its raw, unambiguous state:
- Exact command or user interaction that triggered the failure.
- Complete, untruncated stderr, stdout, or stack trace.
- Exit code and environment details (runtime version, active env vars, working directory).
- **Observed Production Evidence**: When local reproduction is unavailable (e.g. production-only network environment, race conditions, or third-party service failures), allow observed production evidence: crash telemetry, server logs, monitoring traces, or client error payloads. Clearly label the check as verified against observed production evidence rather than a local reproduction.
- Classify failure type:
  - **Syntax / Build Error**: Compilation failure, missing token, unclosed bracket.
  - **Runtime Exception**: Null pointer, undefined property, type mismatch, unhandled rejection.
  - **Logic / Semantic Defect**: Program runs with code 0 but produces wrong output or incorrect state.
  - **Environmental / Dependency**: Missing binary, version mismatch, port collision, permission denied.

### Stage 2: Scope Isolation (Binary Search / Bisect)
Narrow down the blast radius to the smallest possible unit:
- Identify the exact file, class, function, or line of code where the invariant broke.
- Distinguish between **symptom location** (where the crash happened) and **defect origin** (where corrupted data originated).
- If multiple modules are involved, isolate upstream inputs to verify whether the failing component behaves correctly in isolation.

### Stage 3: State & Boundary Inspection
Examine actual runtime values immediately prior to the crash:
- Print, trace, or evaluate inputs, arguments, and environment variables at the function boundary.
- Check invariant assumptions:
  - Is an array empty when expected to have elements?
  - Is an async promise resolving out of order (race condition)?
  - Is an object null or undefined due to missing optional chaining?
  - Is a path relative when an absolute path was expected?

### Stage 4: Falsifiable Root Cause Hypothesis
Formulate a single, testable hypothesis that answers three questions:
1. **What specifically is broken?** (e.g., `event.target.value` is undefined because the listener is bound to the parent container instead of the input element).
2. **Why did it fail now?** (What changed in input, state, or environment).
3. **Why did it work previously?** (If it previously worked, identify the breaking commit or environmental shift).

*If your hypothesis cannot predict the exact reproduction failure, reject it and return to Stage 3.*

### Stage 5: Minimal Surgical Fix
Implement the smallest necessary change that directly resolves the root cause:
- Change the minimum number of lines required.
- **Multi-File Repairs Allowed**: While single-file edits are preferred when possible, multi-file fixes (e.g. 2–3 files spanning caller, callee, and schema) are fully permitted when the defect's architectural cause requires it.
- Do not refactor surrounding architecture during a bug fix unless explicitly requested.
- Maintain existing style, variable naming conventions, and docstrings.
- Add defensive guards or assertions if appropriate to prevent future silent degradation.
- **Git Assertion Lock Enforced**: Pre-existing test files at Git `HEAD` are strictly immutable during bug repairs. Never mutate, delete, or weaken existing test assertions to fake a pass. Write reproduction test cases as new tests. If requirements legitimately evolved and existing tests must change, `--spec-evolution` must be explicitly declared.

### Stage 6: Regression & Verification Proof
Prove the fix works using empirical evidence:
1. **Mandatory Execution Verification**: You MUST execute the original reproducer command and capture its full output before declaring success. A task is only complete when the reproducer exits with a clean status code 0 and all failing assertions pass:
   `bash scripts/exec-proxy.sh --label debug_verify <reproduction command>`
2. Run adjacent tests via `exec-proxy.sh` -> Verify zero secondary regressions and update `.evidence/manifest.v1.json`.
3. Clean up temporary diagnostic print statements and debug logs before concluding.

---

## Output Policy & Hypothesis Log

Follow the suite output policy ([`references/output-policy.md`](../references/output-policy.md)):

1. **Background Disk Sink & Log Redaction**: Full stack traces, bisect logs, and verbose inspector traces are saved to `.evidence/logs/` or `<appDataDir>/brain/<conversation-id>/scratch/debug-[id].log`. Redact sensitive environment variables, credentials, and API keys.
2. **Compact Hypothesis Log (For Multi-Cycle Investigations)**:
   ```markdown
   | # | Observation | Proposed Cause | Discriminating Check | Outcome |
   |---|---|---|---|---|
   | H1 | Null dereference | Config missing key | Inspect `config.json` | ❌ Falsified |
   | H2 | Async listener race | Missing await | Isolated probe | 🟢 Confirmed |
   ```
3. **Intermittent / Unreproduced Bugs**: If a bug cannot be reproduced reliably, preserve explicit uncertainty. Do not invent speculative root causes. State observed facts, tested hypotheses, and instrumentation added to catch the next occurrence.
4. **Routine Summary (4–8 lines target in chat)**:
   - **Outcome**: Defect identified and surgically resolved.
   - **Root Cause & Location**: Concrete mechanism and file link (`path/to/file.ext:L12-15`).
   - **Surgical Fix**: 1-sentence summary of the minimal change.
   - **Verification**: Command executed, exit code, and observed result.
   - **Evidence & Log Path**: Link to preserved diagnostic log.
5. **Pipeline Suppression**: When running as an intermediate stage in a multi-skill pipeline, emit a single-line milestone heartbeat:
   `✓ [deep-debugger]: Fixed <bug> in <file.ext:L12> (verified with <cmd>, exit 0)`

