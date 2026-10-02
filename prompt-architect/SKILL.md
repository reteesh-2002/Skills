---
name: prompt-architect
description: Produces complete 24-section master engineering specifications from raw user ideas. Activate when the user asks for a specification, master prompt, or architecture document for a new system or feature. Manual for all other requests. Do not activate automatically before plan-master or implementation.
---

# Prompt Architect

Translate a raw idea into a **complete 24-section master engineering specification** — a precise, self-contained description of what to build, expected behavior, constraints, and acceptance criteria.

This skill produces specifications only. It does not produce execution plans, task lists, implementation code, or select skill teams. Use `plan-master` to turn a specification into an actionable plan.

---

## Activation and boundaries

**Activate when the user explicitly asks for:**
- A specification, master prompt, architecture document, or product brief
- Direct invocation: `$prompt-architect`, `@prompt-architect`

**Do not activate automatically for:**
- Bug fixes, small edits, or routine implementation tasks → route directly or use `deep-debugger`
- Execution planning → use `plan-master`
- Any request where a valid specification already exists — skip directly to planning or implementation

**Action boundaries:**
- Read user-specified repositories, files, and APIs to ground the specification. Do not crawl unrelated directories.
- Do not start implementation workers, run commands, or produce a second execution plan as part of specification generation.
- Do not infer existing interfaces as though verified — mark unconfirmed discoveries as assumptions or open questions.
- Preserve an established stack and design system unless the user explicitly requests changes.

---

## Grounding rules

1. **Distinguish confirmed facts, assumptions, and open decisions.** Label each explicitly in the specification.
2. **Ask about missing information only if it materially affects correctness or scope.** At most 2–3 targeted questions; do not block output for peripheral details.
3. **Do not invent scope to fill sections.** If a section is genuinely not applicable (e.g. no AI model involved for §16, no database for §8), write "Not applicable — [reason]". Do not create a database or auth system merely to produce a populated section.
4. **State each requirement once; cross-reference thereafter.** Use `MUST`, `SHOULD`, `MAY` only where they clarify priority.
5. **Remove performance claims not tied to measurable budgets.** Avoid "production-ready", "battle-tested", "instantaneous", and blanket caching durations unless the task justifies them.
6. **Keep generated testimonials, prices, and claims clearly marked as placeholder content** — they must not become factual content automatically.

---

## Output format

When activated, respond with:

1. **Blindspot summary** (2–4 bullets): missing data sources, unresolved technical decisions, or scope ambiguities caught during review.
2. **Assumptions list**: what was inferred vs. confirmed.
3. **Complete 24-section specification** following the template in [`references/specification-template.md`](references/specification-template.md).

The specification must include all 24 section headings. Use "Not applicable — [reason]" for irrelevant sections. Never truncate the specification in chat; if the host limits response length, produce it as an artifact.

---

## Recommending next steps

After the specification, you may recommend which skills are relevant for implementation (e.g. `schema-craft` if there is a non-trivial data model, `security-verifier` if there are auth boundaries). Do not activate them. Do not embed unconditional release commands.
