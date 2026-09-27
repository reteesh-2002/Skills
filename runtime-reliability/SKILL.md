---
name: runtime-reliability
description: Operational resilience, database migration rehearsal, memory soak, and graceful lifecycle verifier. Rehearses zero-downtime expand/contract schema migrations, executes memory leak soak tests under load, and validates graceful shutdown signal handling. Trigger on database migrations, background queues, infrastructure changes, or performance-critical paths.
---

# Runtime Reliability

Verification of operational viability, production resilience, and lifecycle invariants. Ensures that code not only passes functional unit tests, but survives long-running workloads, schema transitions, and abrupt container lifecycles without data corruption or resource exhaustion.

## The Core Invariants

1. **Safe Migration Rehearsal**: Rehearse schema migrations against a representative disposable test database, proving either safe rollback or safe forward-recovery without data loss.
2. **Leak-Free Resilience**: High-throughput endpoints and long-running loops must undergo a soak test to prove heap memory plateaus rather than growing monotonically.
3. **Graceful Termination**: Services must trap `SIGTERM` and finish in-flight requests/jobs before closing connections.
4. **Tri-Surface Output**: High-density 15–20 line Executive Reliability Card in chat, raw probe logs in `.evidence/logs/`, structured receipt in `.evidence/manifest.v1.json`.

---

## 4-Stage Reliability Protocol

```
[1. Surface Classification] ──> [2. Rehearse & Soak] ──> [3. Execute via Proxy] ──> [4. Gate & Assessment]
```

### Stage 1: Reliability Surface Classification
Determine the operational requirements based on modified files:
- **Database Schema Changes**: Tables added, columns modified, indexes created, locks acquired.
- **Background Workers / Jobs**: Event loops, Redis/SQS consumers, scheduled crons.
- **Stateful Memory Caches**: In-memory maps, caches, event listeners, file descriptors.
- **Deployment / Service Lifecycle**: Health check endpoints (`/healthz`), shutdown hooks.

### Stage 2: Empirical Stress & Rehearsal Probes
1. **Migration Rehearsal (Expand / Contract)**:
   - Run forward migration on test database.
   - Verify table structure and constraints.
   - Run rollback migration -> Verify clean reversion to previous schema version.
   - Re-run forward migration -> Verify idempotency.
2. **Memory Soak Testing**:
   - Execute a loop of 5,000–10,000 synthetic operations.
   - Sample heap memory usage at intervals (start, 25%, 50%, 75%, end).
   - Verify memory returns to baseline after GC (no monotonically growing heap leak).
3. **Graceful Shutdown Probe**:
   - Spawn the process, issue synthetic requests, send `SIGTERM` (`kill -15`).
   - Verify process finishes active requests, cleanly closes database connections, and exits with code 0.

### Stage 3: Execution via Trusted Proxy
Run all reliability probes via the execution capture proxy:
```bash
bash scripts/exec-proxy.sh --label reliability_rehearsal <probe-command>
```

### Stage 4: Assessment & Output Format

On completion, emit the **Executive Reliability Card (15–20 Lines)**:

```markdown
### ⚙️ Runtime Reliability: [GREEN / RED] — [1-sentence outcome]

* **Operational Surface**: [Database Migration / Background Queue / Service Lifecycle]
* **Reliability Checks Executed**:
  - `Migration Rehearsal`: **PASS** (Forward + Rollback + Re-apply clean)
  - `Memory Soak Test`: **PASS** (10,000 ops completed; heap delta < 5%)
  - `Graceful Shutdown`: **PASS** (SIGTERM handled; 0 aborted jobs)
  - `Health Endpoint`: **PASS** (HTTP 200 OK within 50ms)
* **Receipts & Evidence**: Receipt `[rcpt_id]` recorded in [`.evidence/manifest.v1.json`](file:///.evidence/manifest.v1.json)
* **Release Gate**: [Production Ready / Blocked by Operational Defect]
```
