# Antigravity Core Autonomous Skill Routing Rule

You are equipped with a specialized suite of skills located in `~/.gemini/config/skills/`.

## Core Autonomous Intent-to-Skill Routing (Only 3 Skills)

Auto-detection and automatic activation are **strictly limited to the 3 core engineering workflows**:

| User Intent | Auto-Detected Skill | Operational Protocol |
| :--- | :--- | :--- |
| **Fix a bug / Error / Breakage / Failure** | `deep-debugger` | 1. Read `deep-debugger/SKILL.md`.<br>2. Execute 6-stage protocol: Reproduce → Isolate → State Inspection → Hypothesis → Surgical Minimal Fix → Regression Proof. |
| **Create new feature / System / Architecture / Change** | `plan-master` | 1. Read `plan-master/SKILL.md`.<br>2. Formulate execution plan, acceptance criteria, and task dependency graph. |
| **Verify / Test / Validate code changes** | `qa-sentinel` | 1. Read `qa-sentinel/SKILL.md`.<br>2. Apply Anti-Tautology discipline (observable side-effects, real failure questions).<br>3. Verify code actually executes via `scripts/exec-proxy.sh`. |


## Manual & On-Demand Only Skills

Do **NOT** automatically activate the following specialist skills unless the user explicitly requests them (or invokes their slash commands / tags):
- `frontend-artisan`: Manual only (UI / design / CSS).
- `schema-craft`: Manual only (database schema / migrations / models).
- `adaptive-worker-orchestrator-v2`: Manual only (multi-worktree parallel subagents).
- `code-reviewer`: Manual only (adversarial diff code review).
- `security-verifier`: Manual only (OWASP API / synthetic tenant audits).
- `runtime-reliability`: Manual only (soak tests / memory leak / migration rehearsal).
- `idea-council`: Manual only (multi-agent deliberation council).
- `ship-it`: Manual only (git release / tag / publish).

## Mandatory Behaviors
1. **Always read `SKILL.md`** using `view_file` when activating one of the 3 core skills.
2. **Never auto-trigger specialist skills** without explicit user instruction.
3. **Execution Discipline**: Route test commands through `scripts/exec-proxy.sh` for physical receipt generation and bounded log capture.
4. **Concise Reporting**: Chat summaries must stay compact (4–8 lines default), highlighting outcome, verified tests, and evidence paths.
