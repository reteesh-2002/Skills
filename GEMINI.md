# Antigravity Skills Suite — Routing Rules

Routing policy is defined in [`suite-policy.json`](suite-policy.json). This file summarizes the active rules.

## Automatic skill activation (3 skills only)

| User intent | Auto-activated skill |
|---|---|
| Fix a bug / error / breakage / failure | `deep-debugger` |
| Plan / implement / architect / build a multi-step feature or system | `plan-master` |
| Verify / test / validate code changes | `qa-sentinel` |

## All other skills: explicit only

`create-architect`, `frontend-artisan`, `schema-craft`, `code-reviewer`, `security-verifier`, `runtime-reliability`, `idea-council`, `ship-it`, `playwright-cli`, `infra-pilot`, `docs-architect`

These activate only when the user explicitly requests them or invokes their slash commands.

## Key rules

- `create-architect` does **not** auto-run before `plan-master`. Plan Master may plan directly from user requirements.
- A valid existing blueprint or specification skips blueprint generation.
- Small tasks (< 3 files, obvious edit) go directly to implementation with a proportionate check — no blueprint, council, worktree, or image generation required.
- Explicitly requested specialists may load their reference files but must not start a council, publish, or create workers without explicit instruction.
- Planning does not authorize publishing. A prior "implement" request does not require re-authorization when a skill changes stage.

## Output defaults

See `suite-policy.json` → `output_defaults` for per-context defaults.
An explicit blueprint request receives all 5 core engineering decisions.
