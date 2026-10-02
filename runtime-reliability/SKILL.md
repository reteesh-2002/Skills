---
name: runtime-reliability
description: Operational resilience, database migration rehearsal, memory soak, and graceful lifecycle verifier. Rehearses zero-downtime expand/contract schema migrations, executes memory leak soak tests under load, and validates graceful shutdown signal handling. Trigger on database migrations, background queues, infrastructure changes, or performance-critical paths.
---

# Runtime Reliability

Verification of operational resilience, resource plateaus, and lifecycle invariants. Exercises long-running workloads, schema transitions, and service lifecycles under controlled test conditions.

---

## 1. Core Invariants

1. **Migration Rehearsal**: Rehearse schema migrations against a representative disposable test database, proving either safe rollback or safe forward-recovery without data loss.
2. **Resource Plateau Probing**: High-throughput loops and caches undergo bounded soak tests to verify heap memory and descriptor counts plateau rather than grow monotonically.
3. **Graceful Termination**: Services must intercept termination signals (`SIGTERM`) and drain in-flight jobs before exiting.
4. **No Blanket Readiness Claims**: Avoid claims like "production ready" or "bulletproof." Expose exact sample sufficiency, measured scope, and test environment limits.

---

## 2. Empirical Reliability Probes

Execute programmatic probes via test scripts or `scripts/specialist_probes.py`:

### A. Migration Rehearsal (Expand / Contract)
- Execute forward migration on disposable test database.
- Insert representative fixture data and verify queries.
- Execute rollback migration (or forward recovery script) and verify state integrity.
- Re-apply migration to prove idempotency.

### B. Memory Soak & Resource Plateau
- Run bounded iterations (e.g. 1,000–5,000 synthetic operations) via `probe_memory_soak_plateau()`.
- Record sample intervals, start/peak heap usage, and post-GC baseline.
- Verify memory consumption stabilizes within an acceptable bound rather than climbing linearly.

### C. Graceful Shutdown & Drain
- Start service/worker in background.
- Trigger in-flight asynchronous operations.
- Send `SIGTERM` (`kill -15`) and observe drain behavior via `probe_graceful_drain()`.
- Confirm 0 aborted tasks and clean process termination.

---

## 3. Scope, Sample Sufficiency & Limits Disclosure

Every reliability report must explicitly disclose:
- **Measured Scope**: Which exact services, endpoints, or migration scripts were exercised.
- **Sample Sufficiency**: Exact iteration count, test duration, concurrency level, and memory delta measured.
- **Environmental Limits**: Boundary limits of the test setup (e.g., single-node local environment, simulated network latency, synthetic database volume vs production scale).

---

## 4. Output Policy & Reporting

Follow [`references/output-policy.md`](../references/output-policy.md):

1. **Routine Summary (4–8 lines target in chat)**:
   - **Outcome**: Status (🟢 GREEN / 🟡 AMBER / 🔴 RED) and operational findings.
   - **Measured Scope**: Modules tested (e.g. background job queue, schema migration).
   - **Sample Sufficiency**: Iteration count, test duration, and measured resource metrics.
   - **Limits & Unverified Conditions**: Disclosed boundaries (e.g. single-process local test, not multi-node cluster).
   - **Evidence**: Receipt ID and log location in `.evidence/manifest.v1.json`.
2. **Intermediate Milestone**:
   `✓ [runtime-reliability]: Soak & lifecycle check PASS (N samples, rcpt_id)`
