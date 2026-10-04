---
name: design-md
description: Design system specification and token manager (Forwarding alias to frontend-artisan). Ingests and enforces DESIGN.md brand guidelines, color palettes, and component styling rules.
---

# Design MD (Forwarding Alias)

> [!NOTE]
> **Forwarding Alias Notice**: Design system token ingestion, brand presets (Linear, Apple, Vercel, Stripe), and aesthetic rules are natively integrated into [`frontend-artisan`](../frontend-artisan/SKILL.md) and [`frontend-artisan/references/design-presets.md`](../frontend-artisan/references/design-presets.md). This skill functions purely as a forwarding alias.

---

## Direct Delegation Routing

When `design-md` is invoked:
- Forward directly to [`frontend-artisan`](../frontend-artisan/SKILL.md).
- Prioritize existing project tokens in `DESIGN.md` if present; otherwise, load contextual brand tokens from [`design-presets.md`](../frontend-artisan/references/design-presets.md).
- No duplicate checklist or second planning pass is executed.
