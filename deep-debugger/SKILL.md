---
name: deep-debugger
description: Systematic root cause investigation and surgical bug repair. Enforces a 6-stage scientific protocol (Reproduce -> Isolate -> Inspect State -> Root Cause Hypothesis -> Surgical Fix -> Regression Proof) to prevent shotgun debugging and token-burning patch loops. Use when code fails, tests break, unexpected runtime behavior occurs, or the user asks to debug or fix an error.
---

# Deep Debugger

Systematic, scientific root cause analysis and surgical defect repair. Eliminates guessing, shotgun patching, and trial-and-error loops by strictly isolating failure mechanisms before editing code.

---

## 1. Ironclad Invariants

1. **Reproduction Before Mutation**: Never edit code without an isolated reproduction or verified observed error trace.
2. **Never Weaken Existing Tests**: Pre-existing test files at Git `HEAD` are strictly immutable during bug repairs. Never mutate, delete, or weaken existing assertions to fake a pass. Add new test cases to prove fixes.
3. **Surgical Minimal Fix**: Change the minimum lines required. Never touch working files outside the failure path.
4. **Blast Radius Check**: Assess risk and ensure fixes do not introduce blind try/catch blocks or regressions.
5. **Empirical Verification Proof**: Never claim a bug is fixed without running the reproducer command and confirming it exits with status code 0.
6. **Protect User Edits**: Only touch files modified during the active investigation. Never execute indiscriminate hard resets.

---

## 2. The 6-Stage Investigation Protocol

```
[1. Reproduce] ──> [2. Isolate] ──> [3. Inspect State] ──> [4. Root Cause] ──> [5. Surgical Fix] ──> [6. Regression Proof]
```

1. **Reproduce**: Capture exact command, stack trace, and exit code.
2. **Isolate**: Narrow the defect to the specific file and function boundary.
3. **Inspect State**: Inspect runtime values and arguments immediately prior to the crash.
4. **Root Cause**: Formulate a single falsifiable hypothesis explaining what broke and why.
5. **Surgical Fix**: Apply the minimal direct fix.
6. **Regression Proof**: Run the reproducer and test suite to confirm exit code 0 and zero secondary regressions.

---

## 3. Concise Output Format

Conclude with a clean, focused summary:
- **Root Cause**: Concrete mechanism and file link (`path/to/file:L12-15`).
- **Surgical Fix**: 1-sentence summary of the minimal change.
- **Verification**: Command executed and passing result (`exit code 0`).

### Intermediate Milestone:
`✓ [deep-debugger]: Root cause fixed & verified (exit 0)`
