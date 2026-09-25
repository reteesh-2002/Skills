# Tailwind CSS Micro-Tokens & Physics Recipes

These pure Tailwind utility combinations require **zero external npm libraries** (no Framer Motion or GSAP needed).

---

## 1. Mechanical Button States

### Smooth Spring Press (Tactile Modern)
```html
class="transition-all duration-150 ease-out hover:-translate-y-0.5 active:translate-y-0 active:scale-[0.98] motion-reduce:transform-none"
```

### Hard Snap Press (Neo-Brutalist Stamp)
```html
class="border-2 border-black shadow-[4px_4px_0px_#000] hover:-translate-x-0.5 hover:-translate-y-0.5 hover:shadow-[5px_5px_0px_#000] active:translate-x-1 active:translate-y-1 active:shadow-none transition-all duration-100 motion-reduce:transform-none"
```

### Minimal Subsurface Press (Ghost Button)
```html
class="bg-transparent hover:bg-stone-100 dark:hover:bg-zinc-800 text-stone-700 dark:text-zinc-300 active:scale-[0.97] transition-all duration-150"
```

---

## 2. Interactive Card Transitions

### Subtle Border Illumination (Dark Mode)
```html
class="border border-zinc-800 bg-zinc-900/80 hover:border-zinc-700 hover:bg-zinc-900 transition-all duration-200"
```

### Lift & Bevel (Light Mode)
```html
class="border border-stone-200 bg-white shadow-sm hover:shadow-md hover:border-stone-300 hover:-translate-y-0.5 transition-all duration-200 motion-reduce:transform-none"
```

---

## 3. High-Contrast Accessible Color Pairings (WCAG 2.1 AA)

All pairings below guarantee a contrast ratio $\ge 4.5:1$ (pass automated Lighthouse / axe-core audits):

| Background | Safe Text Class | Contrast Ratio |
| :--- | :--- | :--- |
| `bg-white` (Pure Light) | `text-stone-900` / `text-zinc-900` | 19.3:1 (AAA) |
| `bg-white` (Secondary) | `text-stone-600` / `text-zinc-600` | 5.6:1 (AA) |
| `bg-stone-50` (Warm Canvas) | `text-stone-900` | 18.2:1 (AAA) |
| `bg-[#16181d]` (Dark Card) | `text-stone-100` / `text-zinc-100` | 13.8:1 (AAA) |
| `bg-[#16181d]` (Muted Dark)| `text-zinc-400` | 5.4:1 (AA) |
| `bg-amber-500` (Accent) | `text-stone-950` / `text-black` | 9.8:1 (AAA) |
| `bg-emerald-600` (Badge) | `text-white` | 4.8:1 (AA) |

---

## 4. Custom Thin Scrollbar

Apply to overflowing panels:
```html
class="overflow-y-auto [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-stone-300 dark:[&::-webkit-scrollbar-thumb]:bg-zinc-700 [&::-webkit-scrollbar-track]:bg-transparent"
```

---

## 5. Responsive Grid Rules

Always use single-column default with progressive breakpoint expansion:
```html
<!-- Bento 4-block layout -->
<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
  <div class="sm:col-span-2 lg:col-span-2">...</div>
  <div>...</div>
  <div>...</div>
</div>
```
