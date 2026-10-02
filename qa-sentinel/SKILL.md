---
name: qa-sentinel
description: Automated verification and sanity validation engine. Guarantees code actually runs before declaring completion by testing syntax (node -c, py_compile), endpoint health (curl/status codes), visual contrast/rendering, broken imports, and regression safety. Use before marking any feature done, after major refactors, or when verifying project health.
---

# QA Sentinel

Automated verification gatekeeper. Enforces that code changes, features, and refactors are validated with empirical executed proof before concluding a task.

---

## 1. Verification vs. TDD Workflows

Differentiate between behavioral implementation tasks and verification-only tasks:

### A. Test-Driven Development (TDD) for Behavioral Changes
When implementing new features, capabilities, or bug fixes:
1. **RED**: Write a focused test exercising the required behavior or reproducing the defect.
2. **Verify RED**: Run via `scripts/exec-proxy.sh` and confirm the test fails for the expected missing capability.
3. **GREEN**: Write minimal implementation code to pass the test.
4. **Verify GREEN**: Confirm all tests pass with exit code 0.
5. **REFACTOR**: Clean up while preserving green tests.
6. **Final Verification on Committed Snapshot**: Pre-commit verification checks verify the working tree; once committed, run a final verification pass against the clean committed tree to generate an authoritative evidence manifest.

### B. Verification-Only Tasks
When asked to verify existing code, evaluate pull requests, or conduct health audits without writing new features:
- Do not invent speculative implementation tests.
- Execute existing test suites, probe endpoints, and run proportional sanity tiers against the current tree.

### C. Exemption for Trivial Non-Behavioral Edits
- **Do not require new tests for trivial non-behavioral edits**: documentation updates, comments, typo fixes, README changes, or metadata edits.
- For these tasks, run a proportionate syntax or formatting check (Tier 1) rather than mandating behavioral unit tests.

---

## 2. Meaningful Test Standard (Anti-Tautology Discipline)

Tests must defend real business invariants, not merely inflate coverage counts:
1. **The Realistic Bug Question**: Identify the concrete defect the test would catch. If an off-by-one, null reference, or boundary breach wouldn't trigger failure, rewrite the test.
2. **Independent Expected Values**: Derive expectations from specifications or static fixtures, never by copying the implementation logic into the test.
3. **Assert Observable Outcomes**: Test actual observable outputs, state transitions, and side-effects rather than counting internal method calls or asserting mock calls.
4. **Targeted Mutation Probes**: For critical auth, financial, or data algorithms, verify the test fails when an invariant condition is intentionally inverted.
5. **No Grepping as Behavioral Tests**: Checking if a file contains `function xyz()` is static linting, not a behavioral test. Behavioral tests must execute code.

---

## 3. Proportionate 4-Tier Verification Matrix

Select verification tiers proportionately based on the nature and blast radius of the change:

| Tier | When to Apply | Checks Performed |
|---|---|---|
| **Tier 1: Static & Syntax** | All edits (including docs, typos, scripts) | Syntax validity (`node -c`, `py_compile`, `bash -n`), JSON parse, import resolution. |
| **Tier 2: Process & Runtime** | Backend services, servers, CLI binaries | Service boot, health check probes (`curl -s -o /dev/null -w "%{http_code}"`), exit code 0, no unhandled rejections. |
| **Tier 3: Visual & DOM** | Frontend components, web pages, CSS | Viewport responsiveness (375px / 768px / 1440px), no horizontal overflow, asset resolution, `:focus-visible` outlines. |
| **Tier 4: Boundary & Edge** | Critical business logic, auth, data pipelines | Malformed payloads, boundary values (null, empty string, extreme numbers), error state degradation. |

### Tool Detection & Fallbacks
Before executing any check, verify tool availability:
- `command -v node >/dev/null 2>&1 || echo "NO_NODE"`
- `command -v python3 >/dev/null 2>&1 || echo "NO_PYTHON"`
- `command -v curl >/dev/null 2>&1 || echo "NO_CURL"`
If a tool is missing, use an available language fallback (e.g. `python3 -c "import urllib.request..."`). If no runner exists, record as `SKIPPED (missing runner)` rather than fabricating a pass.

---

## 4. False-Green Defense & Evidence Capture

1. **Zero-Test Trap**: Never accept an exit code 0 if 0 tests were executed (e.g. `--passWithNoTests`). A test run with 0 tests is blocked.
2. **Exact Metric Counts**: Report exact counts: `collected N; passed N; skipped N; failed N`.
3. **Flaky Retries**: Retried passes must be classified as **Amber (Flaky)**, never as clean passes.
4. **Execution Proxy**: Always run verification checks through `scripts/exec-proxy.sh`:
   ```bash
   bash scripts/exec-proxy.sh --label <check_name> <test_command>
   ```
   Full command logs are preserved in `.evidence/logs/` and recorded in `.evidence/manifest.v1.json`.

---

## 5. Output Policy & Reporting

Follow [`references/output-policy.md`](../references/output-policy.md):

1. **Routine Summary (4–8 lines target in chat)**:
   - **Outcome**: Status (🟢 GREEN / 🟡 AMBER / 🔴 RED) and 1-sentence verdict.
   - **Scope Tested**: Tiers executed (e.g. Tier 1 syntax, unit suite).
   - **Verification Proof**: Exact test counts (`collected N, passed N, failed N`, exit code 0).
   - **Caveats / Warnings**: Noticeable deprecations, skipped tests, or unverified boundaries.
   - **Evidence**: Receipt ID and path to `.evidence/manifest.v1.json`.
2. **Pipeline Suppression**: When running as an intermediate step, emit a single-line milestone:
   `✓ [qa-sentinel]: N/N tests PASS (exit 0, 0 warnings; rcpt_id registered)`
   The terminal coordinator emits the final summary.
