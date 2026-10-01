# 🎯 VaultPulse: End-to-End 17-Skill Execution Roadmap

This document serves as the master execution checklist to verify that all 17 skills in the Antigravity suite are triggered and evaluated in their strict dependency order.

---

## 📋 Execution Order & Skill Responsibilities

| Order | Skill | Phase / Role | Trigger Command / Prompt | Output & Verification Artifact |
| :---: | :--- | :--- | :--- | :--- |
| **01** | `prompt-architect` | **Master Specification** | `/prompt-architect Architect VaultPulse: Multi-tenant secrets gateway with ephemeral lease rotation and Linear-style dark console.` | Full 23-section Master Engineering Specification. |
| **02** | `anti-slop-spec` | **Design Guardrails** | `/anti-slop-spec VaultPulse security war-room` | Explicit negative guardrail list (no 4-card metric rows, no cartoon buttons, no cards-in-cards nesting). |
| **03** | `idea-council` | **Architecture Council** | `/idea-council Should VaultPulse use SQLite WAL + AES-GCM or full HashiCorp Vault backend for storage?` | 6-Seat Decision Record (Product, Red-Team, Architect, UX, CFO, SecOps). |
| **04** | `plan-master` | **Acyclic Planning & TDD** | `/plan-master Plan implementation of VaultPulse based on Idea Council verdict.` | Master implementation DAG, 1-writer-per-file bounds, TDD acceptance matrix. |
| **05** | `adaptive-worker-orchestrator-v2` | **Worktree Partitioning** | `Use adaptive-worker-orchestrator-v2 to partition into backend and frontend worktrees.` | `scripts/task_ledger.py init`, isolated `.git/.orch-worktrees/worker_backend` and `worker_frontend`. |
| **06** | `schema-craft` | **Relational Architecture** | `/schema-craft Design PostgreSQL/SQLite schema for tenants, secrets, and ephemeral lease tokens.` | Relational DDL, compound indexes on `(tenant_id, expires_at)`, 4-phase disposable migration rehearsal (`rehearse_sqlite_migration`). |
| **07** | `image-to-code` | **Gate 0 Art Direction** | `/image-to-code Generate visual design for VaultPulse dark security console.` | `generate_image` artifact, visual layout anchor inspected via `view_file`. |
| **08** | `design-md` | **Design System Tokens** | `/design-md Apply Linear True Dark palette to VaultPulse.` | Locked tokens: `#08090a` canvas, `#121316` surface, `#222326` borders, `#5e6ad2` electric indigo. |
| **09** | `web-interface-guidelines` | **Production UI Standards** | `/web-interface-guidelines VaultPulse keyboard controls & modal accessibility.` | WAI-ARIA `:focus-visible` rings, `j`/`k` list navigation, `/` search, $\ge 44\text{px}$ touch targets. |
| **10** | `frontend-artisan` | **Master UI Assembly** | `/frontend-artisan Build the VaultPulse split-pane lease inspection console.` | Clean React/Tailwind frontend adhering to Gates 0–4 with zero slop. |
| **11** | `playwright-cli` | **Automated Browser Audit** | `/playwright-cli Test VaultPulse responsive viewports and WCAG contrast.` | Viewport matrix passes (375px mobile, 768px tablet, 1440px desktop) with $\ge 4.5:1$ text contrast. |
| **12** | `deep-debugger` | **Surgical Bug Repair** | `/deep-debugger Fix intermittent lease expiration race condition in worker loop.` | 6-stage protocol: reproduction script in `scratch/repro.py`, minimal fix, regression verification. |
| **13** | `security-verifier` | **Adversarial Security Audit** | `/security-verifier Run dual-tenant IDOR and SSRF boundary audit on VaultPulse API.` | Controlled probe: Tenant A token accessing Tenant B secret lease returns 403 Forbidden; private IP egress blocked. |
| **14** | `runtime-reliability` | **Resilience & Soak** | `/runtime-reliability Run 5,000-request soak test and SIGTERM graceful shutdown probe.` | Memory soak telemetry plateaus (no heap leak); 0 in-flight lease renewals dropped on SIGTERM. |
| **15** | `qa-sentinel` | **Anti-Tautology Verification** | `/qa-sentinel Run full verification suite across combined codebase.` | Physical receipts generated via `scripts/exec-proxy.sh`; mutation testing proves tests fail RED when logic breaks. |
| **16** | `code-reviewer` | **Adversarial Diff Review** | `/code-reviewer Review unified pull request diff before merge.` | Structured finding card (`[CRITICAL | WARNING | SUGGESTION]`) evaluating security and regression hazards. |
| **17** | `ship-it` | **Production Release Gate** | `/ship-it Commit and prepare release candidate.` | Secret scan passes; Conventional Commits; `verify-release-gate.sh` approves push with GREEN disposition. |

---

## 🛠️ Step-by-Step Instructions to Execute

To execute this project and watch the skills work in concert:

1. **Step 1: Start with Prompt Architect**:
   Send:
   > `/prompt-architect Architect VaultPulse: Multi-tenant secrets gateway with ephemeral lease rotation and Linear-style dark console.`

2. **Step 2: Deliberate Storage with Idea Council**:
   Send:
   > `/idea-council Should VaultPulse use SQLite WAL + AES-GCM or full HashiCorp Vault backend for storage?`

3. **Step 3: Generate the Execution Plan**:
   Send:
   > `/plan-master Plan the implementation of VaultPulse based on the Idea Council decision and master prompt.`

4. **Step 4: Execute Workstreams**:
   Proceed sequentially through the schema, frontend, security, and verification skills as outlined in the matrix above. Each step will generate evidence receipts and update the task ledger.
