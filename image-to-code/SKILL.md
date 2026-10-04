---
name: image-to-code
description: Website image-to-code workflow engine (Forwarding alias to frontend-artisan). Classifies design inputs, inspects visual references, and implements frontend code.
---

# Image-to-Code Engine (Forwarding Alias)

> [!NOTE]
> **Forwarding Alias Notice**: The 5-step image workflow (Classify Input -> Inspect/Generate -> Extract Decisions -> Implement -> Verify) is natively integrated into [`frontend-artisan`](../frontend-artisan/SKILL.md). This skill functions purely as a forwarding alias.

---

## Direct Delegation Routing

When `image-to-code` is invoked:
- Forward directly to [`frontend-artisan`](../frontend-artisan/SKILL.md).
- Classify mode (Supplied reference vs. New concept vs. Existing design vs. Functional edit).
- If reference image is provided, inspect with `view_file` (crop/zoom allowed); if greenfield concept, generate at most 1 overview and 1 detail image via `generate_image`.
- Implement and verify without duplicate planning passes.
