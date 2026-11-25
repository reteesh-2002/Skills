# Framework Adapters & Multi-Stack Guide

`frontend-artisan` is 100% framework-agnostic. It translates curated design system presets, typography, and micro-interactions into the idiomatic patterns of your target stack:

---

## 1. Vanilla HTML5 & Modern CSS (Zero Build Steps)

Use when building static sites, light widgets, or environments without Node.js/Vite.

### Core Invariants:
- Use **CSS Custom Properties** (variables) scoped on `:root` or container elements.
- Use **Modern CSS Grid**: `grid-template-columns: repeat(auto-fit, minmax(min(100%, 280px), 1fr))` for fluid zero-overflow layouts.
- Use **Fluid Typography**: `font-size: clamp(1rem, 0.9rem + 0.5vw, 1.25rem)`.
- Use **Native Spring Transitions**: `transition: transform 0.15s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.15s ease`.

### Example: Tactile Button in Vanilla CSS
```html
<button class="artisan-btn-tactile">Save Project</button>

<style>
.artisan-btn-tactile {
  --btn-bg: #1c1917;
  --btn-text: #fafaf9;
  --btn-border: #292524;
  
  padding: 0.625rem 1.25rem;
  font-family: inherit;
  font-size: 0.875rem;
  font-weight: 500;
  background-color: var(--btn-bg);
  color: var(--btn-text);
  border: 1px solid var(--btn-border);
  border-radius: 0.5rem;
  box-shadow: 0 1px 2px rgba(0,0,0,0.08);
  cursor: pointer;
  transition: transform 0.12s ease-out, background-color 0.12s ease;
}

.artisan-btn-tactile:hover {
  background-color: #292524;
  transform: translateY(-1px);
}

.artisan-btn-tactile:active {
  transform: translateY(0.5px) scale(0.98);
}

.artisan-btn-tactile:focus-visible {
  outline: 2px solid #78716c;
  outline-offset: 2px;
}

@media (prefers-reduced-motion: reduce) {
  .artisan-btn-tactile {
    transition: none;
    transform: none !important;
  }
}
</style>
```

---

## 2. React / Next.js (TSX & JSX)

Use component encapsulation and variant props to enforce archetype rules across your codebase.

### Idiomatic Principles:
- Expose a `preset` prop (`"linear"` | `"vercel"` | `"stripe"`) matching [`design-presets.md`](design-presets.md) or theme context.
- Never hardcode arbitrary inline styles; use Tailwind or CSS Modules.
- Ensure strict keyboard access: always spread standard button/input props (`aria-label`, `disabled`, `onClick`).
- For Next.js: Keep visual presentational components as **Server Components** where possible, isolating interactive state (`onClick`, micro-press) to client leaf components (`"use client"`).

### Example: Preset-Driven React Button (TypeScript)
```tsx
import React from 'react';

type ButtonPreset = 'linear' | 'vercel' | 'stripe';

interface ArtisanButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  preset?: ButtonPreset;
  children: React.ReactNode;
}

export const ArtisanButton: React.FC<ArtisanButtonProps> = ({
  preset = 'vercel',
  className = '',
  children,
  ...props
}) => {
  const styles: Record<ButtonPreset, string> = {
    linear:
      'bg-[#5e6ad2] text-white border border-white/10 rounded-lg hover:bg-[#6b77e0] active:scale-[0.98] transition-all duration-150',
    vercel:
      'bg-black text-white dark:bg-white dark:text-black border border-black/10 rounded-md hover:opacity-90 active:scale-[0.98] transition-all duration-150',
    stripe:
      'bg-[#635bff] text-white rounded-lg shadow-sm hover:bg-[#5850ec] active:scale-[0.98] transition-all duration-150',
  };

  return (
    <button
      className={`px-4 py-2 text-sm font-medium focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-stone-900 motion-reduce:transform-none cursor-pointer ${styles[preset]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
};
```

---

## 3. Vue 3 (Single File Components - `<script setup>`)

### Idiomatic Principles:
- Use Vue's built-in `<Transition>` and `<TransitionGroup>` for layout animations with CSS transitions.
- Use `computed()` properties to derive archetype styling classes dynamically.
- Leverage scoped CSS (`<style scoped>`) or Tailwind utilities.

### Example: Vue 3 Bento Card Component
```vue
<script setup lang="ts">
import { computed } from 'vue';

const props = withDefaults(
  defineProps<{
    span?: '1' | '2' | '3';
    archetype?: 'tactile' | 'brutalist';
  }>(),
  { span: '1', archetype: 'tactile' }
);

const cardClasses = computed(() => {
  const base = props.span === '2' ? 'md:col-span-2' : props.span === '3' ? 'md:col-span-3' : '';
  const style =
    props.archetype === 'brutalist'
      ? 'bg-white border-2 border-black rounded-lg p-6 shadow-[4px_4px_0px_#000]'
      : 'bg-white dark:bg-zinc-900 border border-stone-200 dark:border-zinc-800 rounded-xl p-6 shadow-sm hover:border-stone-300 dark:hover:border-zinc-700 transition-all';
  return `${base} ${style}`;
});
</script>

<template>
  <div :class="cardClasses">
    <slot name="header" />
    <slot />
  </div>
</template>
```

---

## 4. Svelte 5 (Runes & Scoped CSS)

### Idiomatic Principles:
- Leverage Svelte's native spring and tweened motions: `import { spring } from 'svelte/motion'`.
- Use Svelte 5 Runes (`$state`, `$derived`, `$props`) for clean reactive state.
- Component-scoped styles by default prevent styling leaks.

### Example: Svelte 5 Tactile Counter Card
```svelte
<script lang="ts">
  let { title, value, archetype = 'tactile' } = $props<{
    title: string;
    value: number;
    archetype?: 'tactile' | 'brutalist';
  }>();

  let count = $state(value);
</script>

<div class={archetype === 'brutalist' ? 'brutalist-box' : 'tactile-box'}>
  <span class="label">{title}</span>
  <div class="value">{count}</div>
  <button 
    class="inc-btn" 
    onclick={() => count++}
    aria-label="Increment counter"
  >
    + Increment
  </button>
</div>

<style>
  .tactile-box {
    background: #ffffff;
    border: 1px solid #e7e5e4;
    border-radius: 0.75rem;
    padding: 1.25rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  }
  .brutalist-box {
    background: #ffffff;
    border: 2px solid #000000;
    border-radius: 0.5rem;
    padding: 1.25rem;
    box-shadow: 4px 4px 0px #000000;
  }
  .label {
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    color: #78716c;
  }
  .value {
    font-size: 2rem;
    font-weight: 800;
    font-family: monospace;
    margin: 0.5rem 0;
  }
  .inc-btn {
    padding: 0.375rem 0.75rem;
    font-size: 0.75rem;
    font-weight: 600;
    border-radius: 0.375rem;
    cursor: pointer;
    transition: transform 0.12s ease;
  }
  .inc-btn:active {
    transform: scale(0.96);
  }
</style>
```

---

## 5. Summary Matrix Across Stacks

| Feature | Vanilla HTML/CSS | Tailwind CSS | React / Next.js | Vue 3 | Svelte 5 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Styling Engine** | Native CSS Custom Props | Utility classes | Tailwind / CSS Modules | Scoped `<style>` / Tailwind | Scoped `<style>` / Tailwind |
| **Archetypes** | CSS class bundles | Utility strings | Variant props (`cva`/`props`) | Derived classes (`computed`) | Derived props (`$derived`) |
| **Micro-Interactions** | Native CSS transition | `active:scale-[0.98]` | CSS / Motion fallbacks | `<Transition>` / CSS | Svelte `spring()` / CSS |
| **Zero External Deps** | ✅ Built-in | ✅ Built-in | ✅ Built-in | ✅ Built-in | ✅ Built-in |
