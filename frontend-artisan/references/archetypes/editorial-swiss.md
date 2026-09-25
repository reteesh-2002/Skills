# Archetype: Editorial / Swiss Style

The **Editorial / Swiss** aesthetic translates international typographic style and print magazine layout into modern web design. It prioritizes stark contrast, deliberate asymmetric columns, expressive serif or geometric sans titles, and generous negative space.

**Best for**: Content platforms, documentation, architectural portfolios, long-form landing pages, and luxury/curated brands.

---

## 1. Palette & Surface Tokens

Stark high-contrast monochromes with intentional typographic tinting:

| Role | Utility Class | Value Description |
| :--- | :--- | :--- |
| **Canvas** | `bg-[#fafaf9]` / `bg-stone-50` | Warm gallery white / ivory |
| **Dark Canvas** | `bg-[#0a0a0a]` | Deep void black |
| **Divider Hairlines** | `border-stone-300 dark:border-neutral-800` | Crisp 1px structural grid lines |
| **Headline Type** | `text-stone-950 dark:text-neutral-50` | Maximum contrast ink |
| **Body Type** | `text-stone-700 dark:text-neutral-400` | Highly legible editorial gray (WCAG AAA) |
| **Accent Rule** | Deep Vermilion (`text-[#c2410c]`) | Subtle, sparing editorial mark |

---

## 2. Layout Structure & Hairlines

Swiss design uses visible structural hairline rules and asymmetrical grid columns:

```html
<div class="border-t border-b border-stone-300 dark:border-neutral-800 py-8 my-6">
  <div class="grid grid-cols-1 md:grid-cols-12 gap-8">
    <div class="md:col-span-4">
      <span class="text-xs uppercase tracking-widest font-mono text-stone-500">Vol. 01 / Architecture</span>
      <h2 class="text-3xl font-serif tracking-tight text-stone-900 dark:text-neutral-100 mt-2">
        Typographic Precision in Generative Interfaces
      </h2>
    </div>
    <div class="md:col-span-8 text-stone-700 dark:text-neutral-300 text-base leading-relaxed space-y-4">
      <p>
        Swiss style removes ornamental shadows and artificial glows, relying on the intrinsic rhythm of letterforms and negative space to guide the reader.
      </p>
    </div>
  </div>
</div>
```

---

## 3. Responsive Collapse

On mobile (<640px), the 12-column asymmetric split collapses gracefully to a single fluid column, maintaining proportional headline sizing with `clamp()`.
