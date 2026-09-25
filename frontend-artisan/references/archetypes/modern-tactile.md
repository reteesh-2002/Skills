# Archetype: Modern Tactile

The **Modern Tactile** aesthetic balances physical industrial design with software ergonomics. It treats digital surfaces as physical plates with depth, crisp hairline edges, and satisfying mechanical feedback.

**Best for**: SaaS dashboards, developer tools, financial interfaces, and productivity applications.

---

## 1. Palette & Surface Tokens

Warm, grounded neutrals replace cold clinical blues:

| Role | Light Mode Value | Dark Mode Value |
| :--- | :--- | :--- |
| **Canvas / Background** | `bg-stone-50` / `bg-[#fbfbfa]` | `bg-[#0f1115]` / `bg-zinc-950` |
| **Card Surface** | `bg-white` | `bg-[#16181d]` / `bg-zinc-900` |
| **Elevated Surface** | `bg-stone-100` | `bg-[#1c1f26]` / `bg-zinc-800` |
| **Border (Hairline)** | `border-stone-200` / `border-zinc-200` | `border-zinc-800` / `border-[#262a33]` |
| **Primary Text** | `text-stone-900` / `text-zinc-900` | `text-stone-100` / `text-zinc-100` |
| **Muted Text** | `text-stone-600` (WCAG AA compliant) | `text-zinc-400` (WCAG AA compliant) |
| **Accents** | Warm Amber (`amber-600`) or Forest Emerald (`emerald-600`) | Warm Amber (`amber-500`) or Emerald (`emerald-400`) |

---

## 2. Elevation & Physical Depth

Instead of heavy fuzzy drop-shadows, use **hairline borders + subtle inner bevels**:

```html
<!-- Modern Tactile Card Container -->
<div class="bg-white dark:bg-[#16181d] border border-stone-200 dark:border-zinc-800 rounded-xl p-6 shadow-[0_1px_3px_rgba(0,0,0,0.05),0_1px_2px_rgba(0,0,0,0.03)] hover:border-stone-300 dark:hover:border-zinc-700 transition-all duration-200">
  <!-- Content -->
</div>
```

---

## 3. Interactive Buttons & Controls

Buttons feature micro-depression on click (`active:scale-[0.98] active:translate-y-0.5`):

```html
<!-- Primary Mechanical Button -->
<button class="px-4 py-2 bg-stone-900 dark:bg-stone-100 text-stone-50 dark:text-stone-900 font-medium text-sm rounded-lg shadow-sm hover:bg-stone-800 dark:hover:bg-white active:scale-[0.98] active:translate-y-0.5 transition-all duration-150 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-stone-900 motion-reduce:transform-none">
  Deploy Changes
</button>

<!-- Secondary Tactile Surface Button -->
<button class="px-4 py-2 bg-white dark:bg-zinc-800 text-stone-700 dark:text-zinc-200 border border-stone-200 dark:border-zinc-700 font-medium text-sm rounded-lg hover:bg-stone-50 dark:hover:bg-zinc-750 active:scale-[0.98] active:translate-y-0.5 transition-all duration-150 shadow-sm motion-reduce:transform-none">
  Inspect Logs
</button>
```

---

## 4. High-Density Bento Grid

Replace identical 3-column cards with asymmetrical data blocks:

```html
<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
  <!-- Hero Card: Spans 2 columns on tablet/desktop -->
  <div class="md:col-span-2 bg-white dark:bg-[#16181d] border border-stone-200 dark:border-zinc-800 rounded-xl p-5">
    <div class="flex items-center justify-between mb-4">
      <span class="text-xs font-semibold uppercase tracking-wider text-stone-500">Live Traffic</span>
      <span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">
        <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span> Optimal
      </span>
    </div>
    <!-- Data / Graph Area -->
  </div>

  <!-- Metric Tile: Spans 1 column -->
  <div class="bg-white dark:bg-[#16181d] border border-stone-200 dark:border-zinc-800 rounded-xl p-5 flex flex-col justify-between">
    <span class="text-xs font-semibold uppercase tracking-wider text-stone-500">P99 Latency</span>
    <div class="my-4">
      <span class="text-3xl font-bold font-mono text-stone-900 dark:text-stone-100">18.4ms</span>
      <span class="text-xs text-emerald-600 block mt-1">↓ 4.2ms from baseline</span>
    </div>
    <div class="w-full bg-stone-100 dark:bg-zinc-800 h-1.5 rounded-full overflow-hidden">
      <div class="bg-amber-500 h-full rounded-full" style="width: 28%"></div>
    </div>
  </div>
</div>
```
