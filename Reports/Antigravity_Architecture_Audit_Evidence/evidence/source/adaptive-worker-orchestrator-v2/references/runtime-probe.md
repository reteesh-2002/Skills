# Runtime Configuration

Read at Phase 0 to determine host orchestration parameters. Do not pollute the user's repository with probe files. Use static platform defaults or environment variables.

## Default Platform Profile (Antigravity / Gemini)
- **subagent_types**: `["self", "research"]` (or custom defined)
- **model_tiers**:
  - Cheap / fast: `flash_lite` or `flash`
  - Frontier / strong: `inherit` or `pro`
- **workspace_modes**: `["inherit", "branch", "share"]`
- **concurrency_cap**: 4 simultaneously active workers

## Guidelines
- Avoid dynamic prompt-based probing of platform capabilities unless explicitly instructed.
- If running under another agent harness, check available tool declarations directly from the system prompt without querying the user.
- If caching is needed, store runtime state in agent scratchpad or in-memory context, not in `.orchestrator/runtime.md` within the user's workspace.
