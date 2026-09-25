---
name: qa-sentinel
description: Automated verification and sanity validation engine. Guarantees code actually runs before declaring completion by testing syntax (node -c, py_compile), endpoint health (curl/status codes), visual contrast/rendering, broken imports, and regression safety. Use before marking any feature done, after major refactors, or when verifying project health.
---

# QA Sentinel

Automated verification gatekeeper. Enforces that no code change, feature, or refactor is marked "complete" without empirical, executed proof that it works in the real environment.

## The Zero-Honor-System Rule

> **Never assume code works because it looks correct in markdown.**
> An AI agent MUST execute verification commands in the terminal and report actual exit codes and observed output before concluding a task.

---

## 4-Tier Verification Matrix

QA Sentinel checks the application across 4 escalating tiers:

### Pre-Flight Binary Detection & Fallback
Before executing any verification probe, verify tool availability:
- `command -v node >/dev/null 2>&1 || echo "NO_NODE"`
- `command -v python3 >/dev/null 2>&1 || echo "NO_PYTHON"`
- `command -v curl >/dev/null 2>&1 || echo "NO_CURL"`
If a specific tool is missing in the host environment, use an available fallback (e.g., if `curl` is missing, use `python3 -c "import urllib.request; ..."` or `node -e "fetch('...').then(...)"`). If no valid runner exists, explicitly record the check as `SKIPPED (missing binary)` in the report rather than crashing the task.

### Tier 1: Static Code & Syntax Integrity
Run fast zero-execution syntax checks on all modified files:
- **JavaScript / TypeScript**: `node -c <file.js>` or `npx tsc --noEmit` / `eslint`.
- **Python**: `python3 -m py_compile <file.py>` or `flake8` / `ruff`.
- **Shell Scripts**: `bash -n <script.sh>` or `shellcheck`.
- **JSON / Configs**: `jq . <config.json>` or `node -e 'JSON.parse(fs.readFileSync(...))'`.
- **Import Resolution**: Verify all `import ... from '...'` paths resolve to real files on disk.

### Tier 2: Process & Runtime Health
Verify services boot cleanly without immediate crashes or silent deaths:
- Start the server/app daemonized or in background with a bounded timeout.
- Verify the process stays alive (not exited with code 1 within 500ms).
- Probe endpoints with `curl -s -o /dev/null -w "%{http_code}" http://localhost:<port>`.
  - Expect `200 OK` (or valid redirect `301`/`302`).
  - Flag any `500 Internal Server Error` or connection refused (`code 7`).
- Check stderr logs for unhandled promise rejections or uncaught exceptions.

### Tier 3: DOM, Assets & Visual Sanity
Verify frontends render assets cleanly:
- Check that all CSS variables referenced with `var(--...)` are defined in `:root` or stylesheets.
- Verify linked image/font paths exist locally or resolve to valid URLs.
- Check for common responsive regressions (e.g., horizontal overflow on mobile `width > 100vw`).
- Verify keyboard accessibility: buttons and interactive elements have `:focus-visible` states.

### Tier 4: Boundary & Edge Case Probing
Verify defensive resilience:
- Pass empty strings, unexpected types, or malformed payloads to key input handlers.
- Verify grace degradation: UI displays a friendly error state or toast instead of crashing to a blank white screen.
- Verify local storage / persistence error handling when storage is cleared or disabled.

---

## False-Green Defense & Meaningful Counts

Never equate `exit code 0` with successful verification:
1. **Zero-Test Trap**: If a test command executes 0 tests (e.g. Jest `--passWithNoTests` with no matching files), fail the verification gate immediately.
2. **Explicit Counts Required**: Never say "All tests passed." Always state exact counts: `collected N; passed N; skipped N; failed N`.
3. **Flaky Retries**: Tests that pass only on retry must be flagged as **Amber (Flaky)**, never clean first-pass success.
4. **Separation of Dimensions**: Distinguish *Execution* (`completed`/`failed`), *Verification* (`pass`/`warn`/`fail`), and *Next Action* (`eligible`/`blocked`).

---

## The Amber Protocol (3-State Status)

* 🟢 **GREEN (Clean Pass)**: All required checks executed, 100% assertions passed, 0 new warnings, 0 unmeasured scopes.
* 🟡 **AMBER (Pass with Caveats)**: All assertions passed, BUT non-fatal deprecation warnings exist, tests were skipped, or pass occurred after retry. Disclose the warning cause and location in the first 2 lines.
* 🔴 **RED (Failure / Regression)**: Any required check fails or exits non-zero. Instantly uncompresses to the full, raw diagnostic stack trace.

---

## The Dual-Surface Output Model (15–25 Lines Foreground)

1. **Background Disk Sink**: Full raw `stdout`/`stderr` logs are streamed directly to disk (e.g. `<appDataDir>/artifacts/qa-[id].log`).
2. **Foreground Chat Card (15–25 Lines Target)**:
   When running as a standalone check or as the terminal step of a task:

```markdown
### 🛡️ QA Sentinel: [GREEN / AMBER / RED] — [1-sentence plain outcome]

* **Scope**: [What was tested; e.g. unit tests, HTTP health, syntax]
* **Verification Proof**:
  - `[command 1]` ──> **PASS** (exit 0; collected 24, passed 24, skipped 0)
  - `[command 2]` ──> **PASS** (exit 0; HTTP 200 OK)
* **Caveats & Warnings**: [0 warnings / 1 deprecation warning in file.js:L12]
* **Evidence**: Full raw logs at [`qa-[id].log`](file:///path/to/log)
* **Next Action**: [Eligible to ship / Blocked pending fix]
```

3. **Pipeline Suppression Rule**:
   When QA Sentinel is an **intermediate step** inside a multi-skill pipeline (e.g. `deep-debugger` → `qa-sentinel` → `ship-it`), it suppresses the full card to a **single-line milestone heartbeat**:
   `✓ [qa-sentinel]: 24/24 tests PASS (exit 0, 0 warnings)`
   Allowing the terminal orchestrating skill to emit the final unified task card.
