# Antigravity Autonomous Skill Detection & Routing Rule

You are equipped with a specialized suite of skills located in `~/.gemini/config/skills/`.
Whenever the user asks to **create**, **change**, **refactor**, or **fix a bug**, you **MUST automatically detect** which skills apply to the task and follow their protocols without requiring the user to type slash commands (e.g. `/plan-master`, `/deep-debugger`).

## Autonomous Intent-to-Skill Routing Matrix

| User Intent | Auto-Detected Skills | Operational Protocol |
| :--- | :--- | :--- |
| **Fix a bug / Error / Breakage / Failure** | `deep-debugger` → `qa-sentinel` | 1. Read `deep-debugger/SKILL.md`.<br>2. Execute 6-stage protocol: Reproduce → Isolate → State Inspection → Hypothesis → Minimal Fix → Regression Proof.<br>3. Verify with `qa-sentinel` before claiming completion. |
| **Create new feature / System / Architecture** | `plan-master` → `qa-sentinel` | 1. Read `plan-master/SKILL.md`.<br>2. Formulate execution plan, acceptance criteria, and task dependency graph.<br>3. Enforce TDD Red-Green progression with `qa-sentinel`. |
| **Frontend / UI / CSS / Design / Web Component** | `frontend-artisan` | 1. Read `frontend-artisan/SKILL.md`.<br>2. Select distinctive visual archetype (no generic purple AI slop).<br>3. Verify responsive viewports, contrast, and keyboard navigation. |
| **Database / Migration / Schema / Models** | `schema-craft` | 1. Read `schema-craft/SKILL.md`.<br>2. Enforce foreign keys, indexes, and zero-downtime migrations.<br>3. Rehearse migration on ephemeral database testbed before deploying. |
| **Multi-module / Parallel tasks** | `adaptive-worker-orchestrator-v2` | 1. Read `adaptive-worker-orchestrator-v2/SKILL.md`.<br>2. Gating check: keep solo if coupled; partition into isolated worktrees if independent modules.<br>3. Track live state via `scripts/task_ledger.py`. |
| **Verify / Test / Validate** | `qa-sentinel` | 1. Read `qa-sentinel/SKILL.md`.<br>2. Apply Anti-Tautology discipline (observable side-effects, real failure questions).<br>3. Execute tests via `scripts/exec-proxy.sh`. |
| **High-risk code diff / Sensitive boundary** | `code-reviewer` | 1. Read `code-reviewer/SKILL.md`.<br>2. Conduct adversarial diff inspection for regressions, authorization leaks, and missing edge cases.<br>3. Format actionable finding cards. |
| **Security / Auth / API permissions** | `security-verifier` | 1. Read `security-verifier/SKILL.md`.<br>2. Probe OWASP API Top 10 using isolated synthetic accounts. |
| **Performance / Leaks / Shutdown** | `runtime-reliability` | 1. Read `runtime-reliability/SKILL.md`.<br>2. Rehearse graceful shutdown (SIGTERM/SIGINT) and memory soak stability. |
| **Commit / Push / Release / PR** | `ship-it` | 1. Read `ship-it/SKILL.md`.<br>2. Verify clean git tree, run release gate via `scripts/verify-release-gate.sh`, and format Conventional Commits. |

## Mandatory Behaviors
1. **Always read `SKILL.md`** using `view_file` when activating a detected skill (as mandated by Antigravity instructions).
2. **Never wait for manual slash commands** like `/plan-master` or `/deep-debugger` if the user's intent clearly maps to one of the workflows above.
3. **Execution Discipline**: Route test commands through `scripts/exec-proxy.sh` for physical receipt generation and bounded log capture.
4. **Concise Reporting**: Chat summaries must stay compact (4–8 lines default), highlighting outcome, verified tests, and evidence paths without dumping raw terminal logs.
