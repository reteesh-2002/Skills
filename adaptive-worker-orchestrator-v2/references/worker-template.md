# Worker Prompt Template

Read at Phase 2, when building each worker's prompt. Trim for trivial scope.

```
You are Worker <X>. Task: <task>.
Working directory: <worktree path>. Scope: ONLY files in <allowed paths>.
Frozen contract: <paste contract verbatim, or "none">.
Do not modify files outside scope, shared state, the contract, entrypoints/registries, manifests, or lockfiles. Flag a need for these instead of editing them.
If a required contract field is missing: stop, report exactly what is missing and why, and wait. Do not invent a workaround.
Before returning: run scoped lint/typecheck on your files (defer global integration suites to Boss Phase 4) and commit to your branch.
Report: touched files, brief diff summary (no full file dumps), self-verification results, blockers.
```

## Notes
- Give each worker only the contract, its scope, and directly relevant conventions. Not the whole repo or conversation.
- Language-specific lint/typecheck commands go in the worker prompt, taken from the project's own config.
- Project dependencies (e.g. node_modules, .venv) are symlinked into the worker tree automatically.
