---
name: security-verifier
description: API security, tenant isolation, and boundary threat verifier. Exercises OWASP API Top 10 vulnerabilities (BOLA/IDOR, broken authorization, injection, SSRF, data leaks) using synthetic accounts and deterministic test probes. Trigger on authentication changes, API modifications, database access, uploads, or dependency updates.
---

# Security Verifier

Deterministic security boundary inspection and vulnerability verification. Closes the gap between superficial static secret scanning and real-world runtime exploitability by executing concrete adversarial probes against APIs, authorization boundaries, and data pipelines.

## The Core Invariants

1. **Synthetic Isolation**: Always use synthetic, isolated test accounts and test data. Never probe third-party or production systems autonomously.
2. **Deterministic Evidence**: Never claim an endpoint is "secure" without executing a discriminating boundary probe through `scripts/exec-proxy.sh`.
3. **No Self-Waivers**: Cannot waive detected critical or high vulnerabilities.
4. **Tri-Surface Output**: High-density 15–20 line Executive Security Card in chat, raw probe logs in `.evidence/logs/`, structured receipt in `.evidence/manifest.v1.json`.

---

## 4-Stage Security Verification Protocol

```
[1. Threat Model & Scope] ──> [2. Synthesize Probes] ──> [3. Execute via Proxy] ──> [4. Gate & Assessment]
```

### Stage 1: Threat Modeling & Surface Mapping
Inspect the changed files to determine relevant risk vectors:
- **Authentication & Sessions**: Token issuance, expiry, session invalidation, password hashing.
- **Authorization Boundaries (BOLA / IDOR)**: Can User A access or mutate User B's resources by changing the object ID in params/body?
- **Injection Vectors**: Are user inputs concatenated into SQL queries, shell commands, or HTML templates without sanitization?
- **Network / SSRF Boundaries**: Does the endpoint fetch external URLs or webhooks without validating against private IP ranges (`127.0.0.1`, `10.0.0.0/8`, `169.254.169.254`)?
- **Dependency Audit**: Review dependency deltas for known CVEs (`npm audit`, `pip-audit`, `cargo audit`).

### Stage 2: Adversarial Probe Generation
Write targeted, reproducible test probes using the project's test framework:
- Exercise cross-tenant authorization (create User 1 and User 2; attempt `GET /api/documents/:user1_doc` with User 2's token -> must return `403 Forbidden` or `404 Not Found`).
- Pass malicious payloads to search/filter inputs (`' OR 1=1 --`, `{{7*7}}`, `../etc/passwd`).
- Pass private IP addresses to URL ingestion handlers (`http://169.254.169.254/latest/meta-data`).

### Stage 3: Execution via Trusted Proxy
Run the security test suite through the capture proxy:
```bash
bash scripts/exec-proxy.sh --label security_audit <test-command>
```
Verify that the test suite genuinely catches vulnerabilities when seeded, and passes cleanly on the hardened code.

### Stage 4: Assessment & Output Format

On completion, emit the **Executive Security Card (15–20 Lines)**:

```markdown
### 🛡️ Security Verifier: [GREEN / RED] — [1-sentence outcome]

* **Threat Surface**: [Auth / BOLA / Injection / SSRF / Dependencies]
* **Boundary Probes Executed**:
  - `BOLA Cross-Tenant Check`: **PASS** (403 Forbidden on foreign tenant object)
  - `Input Sanitization Probe`: **PASS** (Zero SQL/command injection paths)
  - `SSRF Private IP Filter`: **PASS** (Private subnet egress rejected)
  - `Dependency Vulnerability Delta`: **PASS** (0 critical/high CVEs)
* **Receipts & Evidence**: Receipt `[rcpt_id]` recorded in [`.evidence/manifest.v1.json`](file:///.evidence/manifest.v1.json)
* **Release Gate**: [Approved / Blocked by Open Vulnerabilities]
```
