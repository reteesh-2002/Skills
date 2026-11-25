# Frontend Anti-Patterns & AI Clichés Reference

Categorized inventory of default AI UI traps and uncurated web patterns. Replace these occurrences with handcrafted artisan alternatives during design, implementation, and review.

---

## 1. Palette & Atmospheric Depth

| Anti-Pattern | Why It Fails | Artisan Replacement |
|---|---|---|
| **Unprompted Purple-on-Slate Default** (`bg-slate-900` + generic purple/indigo gradients) | Universal hallmark of unprompted AI templates when no brand palette is chosen. | Use deliberate presets from `design-presets.md` (e.g. `#08090a` true dark with `#5e6ad2` Linear accent, deep obsidian with emerald, or warm editorial ivory). |
| **CSS Radial "Sun Blobs"** (giant blurry radial gradient in page center) | Creates a muddy, low-contrast smear across background text without adding real lighting depth. | Clean linear gradients, subtle noise/grain texture, authentic SVG mesh geometry, or crisp photography. |
| **Muddy Navy + Neon Glow** (generic blue/cyan neon borders) | Dated, high-friction aesthetic that distracts from core content. | Linear true dark (`#08090a`), Vercel monochrome, or subtle 1px hairline borders (`border-white/10`). |
| **Solid Bright Cyan/Blue Walls** | Overwhelming visual weight that washes out primary call-to-actions. | Restrained neutral canvas with targeted accent color reserved for interactive elements. |

---

## 2. Layout & Composition

| Anti-Pattern | Why It Fails | Artisan Replacement |
|---|---|---|
| **Cookie-Cutter 3-Card Grid** (3 identical square cards with centered icons) | Monotonous visual rhythm; communicates zero content hierarchy or narrative flow. | **Bento Grid**: Asymmetric layout varying column spans (e.g. 2-col interactive preview + 1-col metric counter + full-width timeline). |
| **Cards Inside Cards (3+ Levels)** | Recursive nesting creates claustrophobic boxes, visual noise, and confusing container boundaries. | Hairline 1px dividers, tabular columns, subtle background shifts, and generous whitespace. |
| **Obligatory 4-Card KPI Stat Row** (Active Keys, Latency, etc. at top of tools) | Obscures the primary user workflow; pushes the actual table, form, or editor below the fold. | Put the core utility, data table, or editor front and center. Reserve stat summaries for dedicated analytics views. |
| **Centered Hero Cliché** (Pill badge → 48px title → subtitle → 2 centered buttons) | Homogeneous layout that feels like a generic marketing theme. | Off-axis split layouts: bold left-aligned typography with an interactive live widget or live code editor on the right. |

---

## 3. Interaction & Affordance

| Anti-Pattern | Why It Fails | Artisan Replacement |
|---|---|---|
| **Flat, Non-Tactile Buttons** (`bg-blue-600 hover:bg-blue-700` without depth) | Feels like flat static paper; lacks mechanical feedback or physical affordance. | Micro-spring feedback: subtle elevation (`shadow-sm hover:shadow`), slight lift (`hover:-translate-y-0.5`), and active compression (`active:scale-[0.98]`). |
| **Fake Gimmick Controls** (mock "Simulate Pulse" buttons, fake animated terminals) | Superficial theater over utility; adds noise without functional substance. | Real state management: optimistic updates, instant clipboard copy with toast confirmation, and keyboard shortcuts (`⌘K`, `Esc`). |
| **Unlabeled Icon-Only Buttons** | Screen readers cannot discern intent; difficult for users with cognitive impairments. | Always provide descriptive `aria-label` or `title` attributes with tooltip explanations. |
| **Unstyled System Scrollbars** | Heavy OS default scrollbars clash with custom dark or polished themes. | Custom thin scrollbars (`scrollbar-thin scrollbar-thumb-zinc-700`) and parent `overflow-x-hidden` containers. |

---

## 4. Accessibility & Typography

| Anti-Pattern | Why It Fails | Artisan Replacement |
|---|---|---|
| **Low-Contrast Muted Text** (`text-zinc-400` on white or `text-zinc-600` on black) | Violates WCAG AA contrast (drops below 3:1); unreadable in bright environments or on low-end screens. | Maintain strict 4.5:1 contrast: use `text-zinc-600` for secondary text in light mode, and `text-zinc-300` in dark mode. |
| **Jittering Metric Counters** | Changing numbers shift character widths, causing surrounding layout jitter. | Apply `font-variant-numeric: tabular-nums` or clean monospace fonts (Geist Mono, JetBrains Mono). |
| **Mobile `<input>` Font < 16px** | Causes iOS Safari to automatically zoom and pan the viewport on focus, breaking responsive layout. | Always enforce `text-base` (`font-size: 16px` minimum) on mobile inputs and selects. |
| **Tiny Touch Targets (< 44px on Mobile)** | Causes high tap-error rates and frustration on touch devices. | Expand clickable hit area with padding or pseudo-elements to ensure minimum 44px × 44px touch targets. |

---

## 5. Visual Styling & Polish

| Anti-Pattern | Why It Fails | Artisan Replacement |
|---|---|---|
| **Excessive Rounded Corners** (`rounded-3xl` on small cards or buttons) | Gives the interface a toy-like, cartoonish aesthetic. | Disciplined radii: `rounded-md` (6px) or `rounded-lg` (8px) for buttons/inputs; `rounded-xl` (12px) for cards. |
| **Colored Pill Badge Inflation** (every table cell has a bright pill badge) | Desensitizes the user to actual status changes; creates carnival of competing colors. | Plain text with `tabular-nums`, monochrome typography, or subtle 6px status dots. |
| **Flickering Loading Skeletons** | Showing skeletons for fast requests (<150ms) creates jarring flashes. | Delay skeleton display by 150–300ms, and maintain skeleton visible for at least 300ms if displayed. |
| **Missing `:focus-visible` Outlines** | Leaves keyboard navigators unable to determine active cursor position. | High-contrast, unobscured outline (`focus-visible:ring-2 focus-visible:ring-offset-2`). |
