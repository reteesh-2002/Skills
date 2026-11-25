---
name: runtime-reliability
description: Operational resilience, database migration rehearsal, memory soak, and graceful lifecycle verifier. Rehearses zero-downtime expand/contract schema migrations, executes memory leak soak tests under load, and validates graceful shutdown signal handling. Trigger on database migrations, background queues, infrastructure changes, or performance-critical paths.
---

# Runtime Reliability

Verification of operational resilience, resource plateaus, and lifecycle invariants. Exercises long-running workloads, schema transitions, and service lifecycles under controlled test conditions.

---

## 1. Core Invariants

1. **Migration Rehearsal**: Rehearse schema migrations against a disposable representative database, proving either safe rollback or safe forward-recovery without data loss. Share migration fixtures and schemas with `schema-craft` rather than building duplicate rehearsal environments.
2. **Resource Plateau Probing**: High-throughput loops and caches undergo bounded soak tests to verify heap memory and descriptor counts plateau rather than grow monotonically. Zero-iteration tests are marked **UNVERIFIED**.
3. **Graceful Process Termination**: Services must intercept termination signals (`SIGTERM`), complete or safely persist in-flight work, and exit cleanly within declared deadlines.
4. **No Blanket Readiness Claims**: Avoid claims like "production ready" or "bulletproof." Expose exact sample sufficiency, measured scope, and test environment limits.

---

## 2. Operational Verification Profiles

Select checks based on the operational surface changed:

### Profile A: Memory Soak & Resource Plateau
*When to run: Caches, long-running batch workers, event listeners, websocket servers.*
- Warm up process (run initial iterations to prime JIT/caches).
- Sample process RSS memory (e.g., via `resource.getrusage` or `psutil`) across bounded synthetic operations (e.g., 1,000–5,000 ops).
- Measure memory delta across sample intervals. Verify consumption stabilizes within an acceptable threshold rather than climbing monotonically.
- If iterations $\le 0$: mark as `UNVERIFIED (insufficient iterations)`.

### Profile B: Graceful Shutdown & Drain
*When to run: Background workers, queue consumers, HTTP servers with in-flight transactions.*
- Spawn a real child process via `subprocess.Popen`.
- Dispatch synthetic in-flight work.
- Send real `SIGTERM` (`os.kill(child.pid, signal.SIGTERM)`).
- Assert process exits within declared deadline (`drain_timeout_ms`) with 0 aborted tasks. A process that drops work or hangs past deadline fails.

### Profile C: Database Migration Rehearsal (Expand / Contract)
*When to run: Schema modifications, table migrations, column additions.*
- Apply forward migration on disposable test database.
- Insert representative fixture data and verify queries.
- Rehearse rollback migration (or forward-recovery strategy) and verify data integrity.
- Re-apply migration to prove idempotency.

---

## 3. Scope, Sample Sufficiency & Limits Disclosure

Every reliability report must explicitly disclose:
- **Measured Scope**: Exact services, endpoints, or migration scripts exercised.
- **Sample Sufficiency**: Exact iteration count, test duration, concurrency level, and memory delta measured.
- **Environmental Limits**: Single-node local limits vs. production multi-node cluster realities.
- **Inconclusive Evidence**: If iterations were insufficient or environment simulated, declare result **INCONCLUSIVE / UNVERIFIED** rather than fabricating a pass.

---

## 4. Output Policy & Reliability Card

Follow [`references/output-policy.md`](../references/output-policy.md):

### Routine Summary (4–8 lines target in chat):
- **Outcome**: Status (🟢 GREEN / 🟡 AMBER / 🔴 RED) and operational verdict.
- **Profile Executed**: Profile A (Memory), Profile B (Shutdown), or Profile C (Migration).
- **Sample Sufficiency**: Iterations, duration, samples, and measured deltas.
- **Limits & Unverified Conditions**: Disclosed boundaries (e.g. local single-process, local SQLite, not distributed Postgres).
- **Evidence**: Command executed, exit code, and measured deltas.

### Intermediate Milestone:
`✓ [runtime-reliability]: Soak & lifecycle check PASS (N samples)`
