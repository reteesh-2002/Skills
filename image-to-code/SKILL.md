---
name: image-to-code
description: Website image-to-code workflow engine. Classifies design inputs, inspects or generates visual references, extracts concrete design decisions, implements frontend code, and verifies rendering. Explicit only.
---

# Image-to-Code Engine

Transform visual design concepts and reference imagery into production-quality, accessible frontend code. The workflow enforces disciplined extraction of design decisions before implementation, eliminating guesswork and generic AI templates.

---

## The 5-Step Workflow

Follow this sequence for all image-to-code tasks:

```
[1. Classify Input] ──> [2. Inspect / Generate] ──> [3. Extract Decisions] ──> [4. Implement] ──> [5. Verify]
```

---

## Step 1: Classify Input

Before taking action, classify the task to determine the appropriate reference workflow:

| Mode | Condition | Visual Reference Action |
|---|---|---|
| **Supplied Reference** | User provided a screenshot, mockup, wireframe, or URL | Inspect existing reference; crop/zoom into details as needed. No generation. |
| **New Concept** | Greenfield page, feature, or layout without existing design | Generate at most 1 overview and 1 detail image via `generate_image`. |
| **Existing Design** | Modifying an existing codebase with established styling | No image generation. Inspect existing tokens, components, and `DESIGN.md`. |
| **Functional Edit** | Bug fix, accessibility fix, or logic change | Preserve existing appearance. Skip image generation entirely. |

---

## Step 2: Inspect or Generate Reference

### A. Supplied Reference Mode
When the user provides a reference image or mockup:
1. View the reference image using `view_file`.
2. **Crop or zoom** into specific sections, components, navigation bars, or typographic lockups whenever closer inspection of spacing, fonts, or subtle borders is required.
3. Do not generate alternative images unless explicitly instructed by the user.

### B. New Concept Mode
When designing a new page or visual layout from scratch:
1. Call `generate_image` to establish a visual baseline:
   - **Overview Image**: Use `AspectRatio: '16:9'` for hero sections or desktop layouts, or `'3:2'` for content sections.
   - **Detail Image** (optional, maximum 1): Use `AspectRatio: '1:1'` or `'3:2'` to zoom in on a complex widget, table, or interactive card.
2. **Hard Ceiling**: Generate at most **one overview and one detail image**. Do not generate an image per section or spam multiple generation calls.
3. If after two attempts the direction remains uncertain, proceed with the best available reference or surface the specific design question to the user.
4. **Hero Discipline**: Ensure the generated concept features a clean, spacious hero that remains fully visible on standard laptop viewports without drowning in nested containers.

---

## Step 3: Extract Design Decisions

Do not jump straight into coding. Inspect the reference image and explicitly extract the core design tokens:

### 1. Color Palette & Atmospheric Depth
- **Canvas / Background**: Identify the primary canvas color (e.g. neutral dark `#090a0f`, deep slate `#0f172a`, clean white `#ffffff`, warm ivory `#faf9f6`).
- **Surfaces & Cards**: Note surface elevations, background opacities (e.g. `bg-white/5`, `backdrop-blur-xl`), and hair-line border treatments (`border-white/10`).
- **Text Hierarchy**: Identify high-contrast headline color, readable secondary muted color, and subtle meta/timestamp color.
- **Accent / Brand**: Extract the primary brand color for active states, indicators, and primary action buttons.

### 2. Typography Scale & Density
- **Font Families**: Distinguish font styles (modern sans-serif like Inter/Geist, editorial serif, or high-density monospace for metrics).
- **Scale**: Establish hero heading size, section title, card heading, body text, and small label styling.
- **Micro-Typography**: Note letter-spacing (`tracking-tight` on large titles, `tracking-wider` on uppercase labels) and numeric formatting (`tabular-nums`).

### 3. Spacing, Layout Primitives & Rhythm
- **Page Container**: Set max width (`max-w-6xl`, `max-w-7xl`) and horizontal padding (`px-4 sm:px-6 lg:px-8`).
- **Vertical Rhythm**: Generous section spacing (`py-16 md:py-24`), avoiding claustrophobic compression.
- **Grid Architecture**: Asymmetric bento grids, balanced 2-column or 3-column splits. Avoid monotonous identical card rows.

### 4. Tactility & Shape Discipline
- **Corner Radii**: Use disciplined radii (`rounded-lg` or `rounded-xl`). Avoid excessive ballooned corners (`rounded-3xl` everywhere).
- **Elevation & Borders**: Combine 1px hairline borders with layered subtle shadows rather than harsh single-layer drop shadows.
- **Button Affordance**: Buttons must feel physical with hover lift and active compression.

---

## Step 4: Implement Frontend Code

Translate the extracted design tokens into production-ready semantic HTML and CSS/Tailwind:

### Layout Anti-Patterns to Avoid
- **No Cards-Inside-Cards-Inside-Cards**: Replace deep nesting with hairline dividers, subtle background contrast, or negative space.
- **No Unsolicited 4-Card KPI Stat Grids**: If building a utility, tool, or table view, place the primary workflow front and center rather than pushing content down with generic metric cards.
- **No Muddy Radial Glows**: Avoid cheap CSS radial gradients ("sun blobs"). Use clean gradients, crisp photography, or clean SVG geometry.
- **No Fake Controls**: Interactive elements must have real state handlers, keyboard focus, and accessible labels.

### Code Craft Standards
1. **Semantic Structure**: Use `<header>`, `<main>`, `<section>`, `<nav>`, and `<footer>` rather than soup of `<div>`s.
2. **Responsive by Default**: Build mobile-first or fluid layouts that gracefully adapt from 375px mobile to ultra-wide screens.
3. **Typography**: Enforce `font-size: 16px` minimum on mobile `<input>` elements to prevent iOS Safari auto-zoom.
4. **Touch & Click Targets**: Ensure interactive targets meet minimum sizes (≥ 44px mobile, ≥ 24px desktop).

---

## Step 5: Verify & Audit

Validate the implemented code against the design reference and accessibility standards:

1. **Visual Parity Check**:
   - Compare implemented layout against reference image: headline hierarchy, padding proportions, alignment.
2. **Multi-Viewport Audit**:
   - Verify layout integrity at 375px (mobile), 768px (tablet), and 1440px (desktop).
   - Confirm zero horizontal scrollbar or unintended overflow (`document.documentElement.scrollWidth <= window.innerWidth`).
3. **Accessibility & Contrast**:
   - Verify WCAG AA compliance (contrast ratio ≥ 4.5:1 for normal text, ≥ 3:1 for large text).
   - Ensure all interactive controls have visible `:focus-visible` indicators.
4. **Browser Tools**:
   - Use Playwright (`playwright-cli screenshot`) or browser DevTools when available for real rendering checks. If browser tools are unavailable, disclose the verification limitation.

---

## Output Format & Source Record

Follow [`references/output-policy.md`](../references/output-policy.md):
- **Source & Budget Record**: `Source: [Supplied Reference (<file/url>) | New Concept] | Image Budget: [N used / 2 max default]`
- **Key Design Decisions**: Palette, typography scale, container widths, and layout primitives.
- **Copy Discipline**: Existing content and user-provided claims preserved; placeholder content explicitly tagged `[PLACEHOLDER]`; zero invented pricing or fake customer testimonials.
- **Verification**: Viewports and accessibility checks conducted across 375px/768px/1440px.
- **Evidence / Location**: Link to implemented files and captured screenshots.

