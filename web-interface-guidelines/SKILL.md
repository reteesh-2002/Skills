---
name: web-interface-guidelines
description: Web Interface Guidelines (Forwarding alias to frontend-artisan). Production engineering standards covering keyboard navigation, touch ergonomics, hit targets, and loading stability.
---

# Web Interface Guidelines (Forwarding Alias)

> [!NOTE]
> **Forwarding Alias Notice**: Interactive accessibility, touch ergonomics, and loading stability standards are natively integrated into [`frontend-artisan`](../frontend-artisan/SKILL.md) and [`frontend-artisan/references/interface-guidelines.md`](../frontend-artisan/references/interface-guidelines.md). This skill functions purely as a forwarding alias.

---

## Direct Delegation Routing

When `web-interface-guidelines` is invoked:
- Forward directly to [`frontend-artisan`](../frontend-artisan/SKILL.md).
- Apply target ergonomic checks (keyboard `:focus-visible`, hit target $\ge 44$px mobile / $\ge 24$px desktop, mobile input $\ge 16$px, tabular numbers, CLS-free skeletons).
- No duplicate checklist or second planning pass is executed.
