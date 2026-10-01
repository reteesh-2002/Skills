# 🧭 VaultPulse: Chronological Skill Execution Order

Execute each skill sequentially from 1 to 17 to build and verify the project:

| # | Skill | Phase | Command / Instruction | Execution Goal & Artifact |
| :-: | :--- | :--- | :--- | :--- |
| **1** | `prompt-architect` | Specification | `/prompt-architect Architect VaultPulse: Multi-tenant secrets gateway with ephemeral lease rotation and Linear-style dark console.` | Compiles the full 23-section Master Engineering Specification. |
| **2** | `anti-slop-spec` | Guardrails | `/anti-slop-spec VaultPulse dark security console` | Establishes negative visual guardrails (bans 4-card metric rows, neon cyan buttons, cards-in-cards nesting). |
| **3** | `idea-council` | Deliberation | `/idea-council Should VaultPulse use SQLite WAL + AES-GCM or full HashiCorp Vault backend for storage?` | Generates a 6-seat architectural decision record evaluating blast radius, speed, and operational overhead. |
| **4** | `plan-master` | Planning | `/plan-master Plan VaultPulse implementation based on Idea Council verdict.` | Decomposes task into an acyclic dependency graph with 1-writer-per-file boundaries and TDD acceptance criteria. |
| **5** | `adaptive-worker-orchestrator-v2` | Orchestration | `Use adaptive-worker-orchestrator-v2 to partition into backend and frontend worktrees.` | Evaluates Phase 0 gating, mounts isolated git worktrees, and initializes the canonical `task_ledger.py`. |
| **6** | `schema-craft` | Database | `/schema-craft Design PostgreSQL/SQLite schema for tenants, secrets, and ephemeral lease tokens.` | Designs relational DDL, compound indexes on `(tenant_id, expires_at)`, and runs 4-phase disposable migration rehearsal. |
| **7** | `image-to-code` | Visual Direction | `/image-to-code Generate visual design for VaultPulse dark security console.` | Calls `generate_image` to establish the visual layout anchor before any HTML/CSS code is written. |
| **8** | `design-md` | Design System | `/design-md Apply Linear True Dark palette to VaultPulse.` | Locks tokens to Linear True Dark: `#08090a` canvas, `#121316` surface, `#222326` borders, `#5e6ad2` electric indigo. |
| **9** | `web-interface-guidelines` | UX Standards | `/web-interface-guidelines VaultPulse keyboard controls & modal accessibility.` | Enforces WAI-ARIA keyboard navigation (`j`/`k`, `/`, `⌘K`), `:focus-visible` rings, and $\ge 44\text{px}$ touch targets. |
| **10** | `frontend-artisan` | Assembly | `/frontend-artisan Build the VaultPulse split-pane lease inspection console.` | Implements the production frontend adhering to zero-slop hard gates with responsive fluid layout. |
| **11** | `playwright-cli` | Browser Audit | `/playwright-cli Test VaultPulse responsive viewports and WCAG contrast.` | Runs headless audits across viewports (375px mobile, 768px tablet, 1440px desktop) asserting $\ge 4.5:1$ text contrast. |
| **12** | `deep-debugger` | Bug Remediation | `/deep-debugger Fix intermittent lease expiration race condition in worker loop.` | Executes 6-stage protocol: isolates repro in `scratch/repro.py`, implements minimal surgical fix, verifies zero regression. |
| **13** | `security-verifier` | Security Audit | `/security-verifier Run dual-tenant IDOR and SSRF boundary audit on VaultPulse API.` | Probes cross-tenant boundaries (Tenant A token accessing Tenant B secret returns 403) and blocks private IP egress. |
| **14** | `runtime-reliability` | Resilience | `/runtime-reliability Run 5,000-request soak test and SIGTERM graceful shutdown probe.` | Proves memory telemetry plateaus under load and zero in-flight lease renewals are dropped on SIGTERM. |
| **15** | `qa-sentinel` | Verification | `/qa-sentinel Run full verification suite across combined codebase.` | Executes test suites via `scripts/exec-proxy.sh`; runs mutation probes to prove tests fail RED when logic breaks. |
| **16** | `code-reviewer` | Diff Review | `/code-reviewer Review unified pull request diff before merge.` | Conducts adversarial code review, emitting structured finding cards (`[CRITICAL | WARNING | SUGGESTION]`). |
| **17** | `ship-it` | Release | `/ship-it Commit and prepare release candidate.` | Scans diff for secrets, formats Conventional Commits, verifies release gate pass, and prepares candidate pull request. |
