---
name: security-verifier
description: API security, tenant isolation, and boundary threat verifier. Exercises OWASP API Top 10 vulnerabilities (BOLA/IDOR, broken authorization, injection, SSRF, data leaks) using synthetic accounts and deterministic test probes. Trigger on authentication changes, API modifications, database access, uploads, or dependency updates.
---

# Security Verifier

Deterministic security boundary inspection and vulnerability verification. Closes the gap between superficial static secret scanning and runtime exploitability by executing concrete adversarial probes against APIs, authorization boundaries, and data pipelines.

---

## 1. Core Invariants

1. **Synthetic Isolation**: Always use synthetic, isolated test accounts and test data. Never probe third-party or production systems autonomously.
2. **Deterministic Evidence**: Never claim an endpoint is "secure" without executing a discriminating boundary probe through `scripts/exec-proxy.sh`.
3. **Payload & Side-Effect Validation**: Do not rely solely on HTTP status codes. An endpoint returning `200 OK` that leaks another tenant's records, exposes password hashes, or leaks internal tokens is a critical failure. Always inspect response bodies, data fields, and persistent side-effects.
4. **Explicit Boundary Disclosure**: Explicitly list which trust boundaries were probed and which were out of scope. Never generalize a single passing check into blanket system-wide security.

---

## 2. 4-Stage Security Verification Protocol

```
[1. Threat Model & Scope] ──> [2. Synthesize Probes] ──> [3. Execute via Proxy] ──> [4. Gate & Assessment]
```

### Stage 1: Threat Modeling & Scope Definition
Inspect modified files to define the attack surface and boundary targets:
- **Authentication & Sessions**: Token issuance, expiry, session invalidation, password hashing.
- **Authorization Boundaries (BOLA / IDOR)**: Can Tenant A read or mutate Tenant B's data?
- **Injection Vectors**: Are user inputs concatenated into SQL queries, shell commands, or HTML templates?
- **Network / SSRF Boundaries**: Does the service fetch user-supplied URLs without blocking loopback and private subnets (`127.0.0.1`, `10.0.0.0/8`, `169.254.169.254`)?
- **Data Leakage & Response Sanitization**: Does the response payload include sensitive fields (PII, credentials, internal IDs)?

### Stage 2: Adversarial Probe Generation
Write targeted, reproducible probes using test runners or `scripts/specialist_probes.py`:
- **Cross-Tenant Isolation Probe**:
  - Test request with Tenant A's credentials against Tenant B's resource ID.
  - Assert that access is denied (`403`/`404`) **AND** verify response body contains zero Tenant B records.
- **Data Leakage Probe**:
  - Inspect response JSON schemas to confirm omitted password hashes, sensitive tokens, or private user data.
- **Injection Probes**:
  - Submit crafted payloads (`' OR 1=1 --`, `{{7*7}}`, `../etc/passwd`) and assert inputs are safely parameterized or sanitized.
- **SSRF Probes**:
  - Submit private IP addresses (`http://169.254.169.254/latest/meta-data`) and assert egress is blocked.

### Stage 3: Execution via Trusted Proxy
Run the security test suite through the capture proxy:
```bash
bash scripts/exec-proxy.sh --label security_audit <test-command>
```
Verify that tests genuinely fail when vulnerabilities are present and pass cleanly once hardened.

### Stage 4: Assessment & Output Format
Follow [`references/output-policy.md`](../references/output-policy.md):

1. **Routine Summary (4–8 lines target in chat)**:
   - **Outcome**: Status (🟢 GREEN / 🔴 RED) and 1-sentence verdict.
   - **Tested Boundaries**: Explicit list of probed boundaries (e.g. Tenant isolation, SQL injection).
   - **Payload & Effect Results**: Confirmation that response bodies and side-effects were verified.
   - **Untested Boundaries**: Explicit note of any out-of-scope surfaces.
   - **Evidence**: Receipt ID and manifest path in `.evidence/manifest.v1.json`.
2. **Intermediate Milestone**:
   `✓ [security-verifier]: Security audit PASS (<N> boundaries verified, rcpt_id)`
