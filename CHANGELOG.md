# Changelog

All notable changes to the Antigravity Skills Suite are documented in this file.

## [2.2.0] - 2026-10-20

### Benchmark Verification & Harness² Hardening
- **Harness² & JobBench Verification (100% Pass)**:
  - Validated all 19 skills against Google Research `Harness²` surface rules and always-on token budgets (2,673 chars vs 24,000 cap).
  - Executed live multi-domain benchmarks on official Google Research `JobBench` datasets (`web_administrators/task1` and `computer_and_information_systems_managers/task1`), scoring **106/106 (100%)** across 16 weighted rubrics.
- **Skill Hardening & Optimizations**:
  - `deep-debugger`: Added Anti-Shotgun Rule 6 and strengthened Stage 6 with mandatory exit code 0 reproducer output verification to eliminate premature exit bugs.
  - `schema-craft`: Explicitly enforced non-transactional isolation for PostgreSQL `CREATE INDEX CONCURRENTLY` to prevent transaction block abortions.
  - `adaptive-worker-orchestrator-v2`: Mandated freezing `contract.yaml` content hash in `task_ledger.json` prior to worker dispatch to prevent parallel desync.
  - `docs-architect`: Standardized OpenAPI 3.1 error response models to default to RFC 7807 Problem Details (`application/problem+json`).
  - `scripts/slice_guard.py`: Added compatibility symlink ensuring compliance with standard agent harness identifier conventions.

## [2.1.0] - 2026-10-02

### Architecture & Skill Boundaries
- **Prompt Architect & Plan Master Separation**:
  - `prompt-architect`: Exclusively produces complete, high-density 24-section master engineering specifications (`engineering-specification.v24`). Zero implementation code, no task lists, no auto-trigger before planning. Template moved to `prompt-architect/references/specification-template.md`.
  - `plan-master`: Exclusively produces grounded, dependency-aware execution plans (`T1`, `T2`...). Never reproduces or regenerates the 24-section specification. Removed mandatory minimum 2–4 skills quota and mandatory tactile interaction rules. Depth tiers preserved (Compact <400 tokens, Standard, Detailed).
- **Centralized Suite Policy (`suite-policy.json`)**:
  - Single authoritative policy for activation modes (3 automatic: `deep-debugger`, `plan-master`, `qa-sentinel`; 14 explicit on-demand).
  - Shortened `AGENTS.md` and `GEMINI.md` to lean routing summaries referencing `suite-policy.json`.
  - Added automated contract drift detection in `scripts/validate-skills.py`.
  - Documented progressive disclosure defaults and effort profiles in `references/output-policy.md`.

### Frontend & Image Workflow Cleanup
- **4-Mode Frontend Workflow (`frontend-artisan`)**:
  - `Existing design`: Uses current tokens and components with zero image generation.
  - `Supplied reference`: Implements from user screenshot or mockup with cropping and zooming permitted.
  - `New concept`: Generates at most 1 overview and 1 detail image maximum.
  - `Functional edit`: Preserves visual appearance with targeted viewport verification; zero concept images.
- **Image-to-Code Streamlining (`image-to-code`)**:
  - Reduced entrypoint token footprint from ~7,593 to ~1,307 tokens (~83% reduction).
  - Consolidated into a single 5-step flow (Classify -> Inspect/Generate -> Extract -> Implement -> Verify).
  - Merged duplicated anti-patterns into `frontend-artisan/references/anti-patterns.md`.

### Specialist Skills Refinements
- `deep-debugger`: Progress and risk-based escalation replacing rigid 2-file rollback; permits verified production evidence when local reproduction is unavailable.
- `qa-sentinel`: TDD guidance separated from verification-only tasks; exempts trivial non-behavioral edits (docs, comments, typo fixes) from test creation.
- `schema-craft`: Single ORM adapter selection; minimal relevant seed data; target-DB specific evidence replacing blanket zero-lock claims.
- `security-verifier`: Verifies response data payloads and state mutations in addition to HTTP status codes; reports precise boundary test coverage.
- `runtime-reliability`: Sample sufficiency and environmental limits exposed; eliminates uncalibrated universal production-readiness claims.
- `code-reviewer`: No mandatory finding quota (clean passes are valid and encouraged); mandates explicit `Self-Review` labeling when subagent delegation is unavailable.
- `idea-council`: Personas shortened to functional responsibilities; roster parameterized (Full 6-seat vs Express 3-seat); transcript artifact optional.
- `adaptive-worker-orchestrator-v2`: Hard worker cap enforced ($\le 4$); isolated build output directories; multi-mode gating driven by conflict risk, not file count alone.
- `ship-it`: Scans final staged candidate for keys/secrets; separates technical release readiness checks from user publishing authorization.
- `anti-slop-spec`: Forwarding alias directly to `plan-master` and `frontend-artisan` without duplicate planning passes.

### Evidence, Verification & Release Gate Hardening
- **Evidence Adapters (`exec-proxy.sh`)**:
  - Added support for Pytest `xfail` (counted as `skipped`, not `failed`).
  - Added structured framework detection (`pytest`, `jest`, `vitest`, `cargo`, `node-tap`, `python-unittest`).
  - Added `unverified: true` flag for commands exiting 0 with 0 tests collected from non-test-runner binaries, preventing zero-inventory false greens.
- **Deterministic Release Gate (`verify-release-gate.sh` & `runtime_evidence.py`)**:
  - Unverified checks lower policy disposition to `AMBER`.
  - Non-test runner zero-inventory checks blocked from passing under `GREEN` disposition.
  - Shell command ambiguity handling: `eval`, command substitution, and unbalanced quotes containing release keywords return `"unsupported"`, triggering fail-safe release gate blocking.
  - Safe local command substitutions (e.g. `$(mktemp)`) permitted without false positive blocks.

### Specialist Probes & Task Ledger Hardening
- **Specialist Probes (`specialist_probes.py`)**:
  - `probe_graceful_drain_subprocess`: Real child process lifecycle test sending real `SIGTERM` with deadline enforcement.
  - `probe_memory_soak_plateau`: Added RSS memory measurement (`use_rss=True`); zero iterations flagged as unverified; non-plateau memory expansion detected.
  - `check_html_viewport_overflow`: Explicitly tagged as static heuristic analysis (`heuristic: True`).
- **Task Ledger (`task_ledger.py`)**:
  - `validate_dependencies()`: Missing dependency detection and DFS cycle detection.
  - Corrupt ledger preservation: Backs up invalid JSON to `.corrupt.<timestamp>` and records `last_load_error`.
  - Run identity tracking: Supports `session_id` in ledger initialization and querying via `get_session_id()`.

### Tooling, Installation & Diagnostics
- **`scripts/install-skills.py`**: Safe, idempotent installation with manifest tracking (`.skills-install-manifest.json`), preserving existing user configurations and supporting clean `--uninstall`.
- **`scripts/skills-doctor.py`**: Environment diagnostics reporting Python version, runtime helpers, hooks, and tool availability with graceful degradation for optional dependencies.
- **`benchmarks/audit_trial.py`**: Removed hardcoded historical conversation IDs; added `--transcript` and `--task` CLI flags; propagated audit failures to non-zero exit codes.
- **CI Workflow (`.github/workflows/validate.yml`)**: Automated pipeline verifying metadata, contracts, skills doctor, 169 pytest tests, and 27 runtime shell checks.
