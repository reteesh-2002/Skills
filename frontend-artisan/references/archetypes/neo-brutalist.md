# Archetype: Neo-Brutalist

The **Neo-Brutalist** aesthetic draws inspiration from high-contrast print posters, brutalist architecture, and early web optimism. It rejects subtle blurs in favor of raw graphic confidence: bold black borders, hard cast shadows, and punchy accent colors.

**Best for**: Creative portfolios, developer landing pages, developer tools with personality, Hackathon projects, and Web3/indie products.

---

## 1. Palette & Surface Tokens

High-saturation color pops grounded by stark black borders:

| Role | Utility Class | Value Description |
| :--- | :--- | :--- |
| **Canvas** | `bg-[#fbf7ee]` / `bg-amber-50/40` | Warm vintage newsprint / cream |
| **Dark Canvas** | `bg-[#121212]` | Ink-black |
| **Card Surface** | `bg-white` / `dark:bg-[#1e1e1e]` | Crisp stark card |
| **Borders** | `border-2 border-black` / `dark:border-white` | Non-negotiable 2px solid hairline |
| **Hard Shadow** | `shadow-[4px_4px_0px_#000]` / `dark:shadow-[4px_4px_0px_#fff]` | Crisp offset block shadow (no blur) |
| **Accent Primary** | `bg-[#ff5a36]` (Vermilion) or `bg-[#ffe600]` (Electric Yellow) | Saturated, energetic pop |
| **Accent Secondary**| `bg-[#00f0ff]` (Cyan) or `bg-[#00e575]` (Acid Green) | Retro-futuristic punch |

---

## 2. The Hard-Offset Card

Neo-brutalist cards feature distinct 2px borders and sharp 4px shadows:

```html
<!-- Neo-Brutalist Card -->
<div class="bg-white dark:bg-[#1e1e1e] border-2 border-black dark:border-white rounded-lg p-6 shadow-[4px_4px_0px_#000] dark:shadow-[4px_4px_0px_#fff] transition-all duration-150">
  <div class="inline-block px-2.5 py-1 mb-3 text-xs font-black uppercase tracking-wider bg-[#ffe600] text-black border border-black rounded">
    Beta Release
  </div>
  <h3 class="text-xl font-black text-black dark:text-white mb-2">Instant Orchestration</h3>
  <p class="text-sm font-medium text-stone-700 dark:text-stone-300">
    Parallelize tasks without merge conflicts using isolated git worktrees.
  </p>
</div>
```

---

## 3. The Physical "Stamp" Button

Buttons physically snap down into their shadow when clicked:

```html
<!-- Hard-Press Button -->
<button class="px-5 py-2.5 bg-[#ff5a36] text-white font-black text-sm uppercase tracking-wider border-2 border-black rounded-lg shadow-[4px_4px_0px_#000] hover:bg-[#ff421a] hover:translate-x-[-1px] hover:translate-y-[-1px] hover:shadow-[5px_5px_0px_#000] active:translate-x-[4px] active:translate-y-[4px] active:shadow-none transition-all duration-100 motion-reduce:transform-none">
  Launch Mission →
</button>
```

---

## 4. Mobile Responsiveness Guardrail

Neo-Brutalist cards have prominent borders and shadows. On small screens (<640px), excessive shadows can cause horizontal overflow.

**Rule**:
- Use `shadow-[3px_3px_0px_#000]` on mobile, scaling to `md:shadow-[5px_5px_0px_#000]` on desktop.
- Always use `grid-cols-1 md:grid-cols-2` with `gap-6` to provide sufficient breathing room around hard shadows.
