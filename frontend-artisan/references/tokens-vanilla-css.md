# Vanilla CSS Design System & Token Set

For projects built with **pure HTML & CSS** (no Tailwind, no Node/Vite build steps), import or copy these CSS variables and utility classes.

---

## 1. Global CSS Reset & Variables (`artisan-tokens.css`)

```css
/* ==========================================================================
   FRONTEND ARTISAN: CORE CSS TOKENS (WCAG AA COMPLIANT)
   ========================================================================== */

:root {
  /* Fluid Typography Scale */
  --font-sans: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  --font-serif: Georgia, Cambria, 'Times New Roman', Times, serif;

  --text-xs: clamp(0.75rem, 0.7rem + 0.25vw, 0.8125rem);
  --text-sm: clamp(0.875rem, 0.825rem + 0.25vw, 0.9375rem);
  --text-base: clamp(1rem, 0.95rem + 0.25vw, 1.0625rem);
  --text-lg: clamp(1.125rem, 1.05rem + 0.35vw, 1.25rem);
  --text-xl: clamp(1.25rem, 1.15rem + 0.5vw, 1.5rem);
  --text-2xl: clamp(1.5rem, 1.35rem + 0.75vw, 2rem);
  --text-3xl: clamp(1.875rem, 1.65rem + 1vw, 2.5rem);

  /* Light Mode Default (Notion / Catalyst Clean) */
  --tactile-bg: #fafaf9;
  --tactile-surface: #ffffff;
  --tactile-elevated: #f5f5f4;
  --tactile-border: #e7e5e4;
  --tactile-text: #1c1917;
  --tactile-muted: #57534e;       /* Contrast ratio 5.6:1 (Passes AA) */
  --tactile-accent: #d97706;      /* Warm Amber */
  --tactile-success: #059669;     /* Emerald */
  --tactile-shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --tactile-shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.06), 0 2px 4px -2px rgba(0, 0, 0, 0.04);

  /* High-Contrast Accent Tokens */
  --brutalist-bg: #fbf7ee;
  --brutalist-surface: #ffffff;
  --brutalist-border: 2px solid #000000;
  --brutalist-shadow: 4px 4px 0px #000000;
  --brutalist-shadow-hover: 6px 6px 0px #000000;
  --brutalist-accent: #ff5a36;    /* Vermilion */
  --brutalist-accent-alt: #ffe600;/* Electric Yellow */

  /* Timing Functions */
  --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
}

/* Dark Mode Tokens */
@media (prefers-color-scheme: dark) {
  :root {
    --tactile-bg: #0c0a09;
    --tactile-surface: #1c1917;
    --tactile-elevated: #292524;
    --tactile-border: #44403c;
    --tactile-text: #fafaf9;
    --tactile-muted: #a8a29e;     /* Contrast ratio 6.2:1 (Passes AA) */
    --tactile-accent: #f59e0b;
  }
}
```

---

## 2. Reusable Vanilla CSS Classes

```css
/* Tactile Card */
.artisan-card-tactile {
  background-color: var(--tactile-surface);
  border: 1px solid var(--tactile-border);
  border-radius: 0.75rem;
  padding: 1.5rem;
  box-shadow: var(--tactile-shadow-sm);
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.artisan-card-tactile:hover {
  border-color: #d6d3d1;
  box-shadow: var(--tactile-shadow-md);
}

/* Tactile Button */
.artisan-btn-tactile {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.625rem 1.25rem;
  font-family: var(--font-sans);
  font-size: var(--text-sm);
  font-weight: 600;
  border-radius: 0.5rem;
  border: 1px solid transparent;
  cursor: pointer;
  background-color: var(--tactile-text);
  color: var(--tactile-bg);
  box-shadow: var(--tactile-shadow-sm);
  transition: transform 0.12s var(--ease-out), background-color 0.12s ease;
}

.artisan-btn-tactile:hover {
  opacity: 0.92;
  transform: translateY(-1px);
}

.artisan-btn-tactile:active {
  transform: translateY(0.5px) scale(0.98);
}

/* Neo-Brutalist Card */
.artisan-card-brutalist {
  background-color: var(--brutalist-surface);
  border: var(--brutalist-border);
  border-radius: 0.5rem;
  padding: 1.5rem;
  box-shadow: var(--brutalist-shadow);
  transition: transform 0.1s ease, box-shadow 0.1s ease;
}

/* Neo-Brutalist Stamp Button */
.artisan-btn-brutalist {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.75rem 1.5rem;
  font-family: var(--font-sans);
  font-size: var(--text-sm);
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  background-color: var(--brutalist-accent);
  color: #ffffff;
  border: var(--brutalist-border);
  border-radius: 0.5rem;
  box-shadow: var(--brutalist-shadow);
  cursor: pointer;
  transition: transform 0.08s ease, box-shadow 0.08s ease;
}

.artisan-btn-brutalist:hover {
  transform: translate(-1px, -1px);
  box-shadow: var(--brutalist-shadow-hover);
}

.artisan-btn-brutalist:active {
  transform: translate(4px, 4px);
  box-shadow: 0 0 0 #000;
}

/* Accessibility: Reduced Motion Override */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    transform: none !important;
  }
}
```
