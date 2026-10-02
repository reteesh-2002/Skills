---
name: web-interface-guidelines
description: Vercel's official Web Interface Guidelines. Production engineering standard covering interactions, keyboard navigation, hit targets, mobile input ergonomics, flicker-free loading states, state persistence, forms, and animation safety. Use when designing, building, or refining web components, flows, and user interfaces.
---

# Web Interface Guidelines

Production engineering standard for full-stack user interfaces, web components, and frontend interactions.

---

## 1. Interactions & Keyboard Navigation

- **Keyboard navigation works everywhere**: All interactive flows must be operable by keyboard and adhere to WAI-ARIA authoring patterns.
- **Clear focus indicators**: Every focusable element shows a visible, high-contrast focus ring. Prefer `:focus-visible` over `:focus` to avoid distracting pointer users. Set `:focus-within` on grouped controls. Overlays, sticky headers, and banners must never obscure the focused element.
- **Focus management**: Trap focus in modals/drawers; move focus to newly mounted modal containers, and restore focus to the trigger element upon dismissal.
- **Hit targets**: Minimum interactive hit target is **≥ 24px on desktop** and **≥ 44px on mobile**. If a visual icon is smaller, expand its clickable padding area.
- **Forgiving interactions**: Controls minimize finickiness with generous hit boundaries, clear hover/active affordances, and predictable behavior.
- **No dead zones**: If any portion of a card or control appears interactive, the entire bounding region must be clickable.
- **Semantic links**: Use `<a>` or framework `<Link>` for navigation so browser behaviors (Cmd/Ctrl+Click, middle click, context menu) function natively. Never substitute clickable `<div onClick=...>` or `<button>` for links.
- **Async announcements**: Use polite `aria-live` for toasts, notifications, and inline validation updates.

---

## 2. Touch & Mobile Ergonomics

- **Mobile input font-size**: `<input>` and `<select>` font size must be **≥ 16px on mobile viewports** to prevent iOS Safari auto-zoom on focus.
- **Prevent double-tap zoom delay**: Set `touch-action: manipulation` on buttons and interactive controls.
- **Respect user zoom**: Never set `maximum-scale=1` or `user-scalable=no` in viewport meta tags.
- **Safe areas**: Account for hardware notches and mobile home indicators using CSS `env(safe-area-inset-*)`.
- **Autofocus discipline**: Avoid autofocusing inputs on mobile devices because unexpected keyboard activation causes disruptive layout shifts.

---

## 3. Loading, States & Feedback

- **Loading button states**: Show a spinner or progress indicator while **retaining the original button label** (e.g. `[Spinner] Saving...`), avoiding button size collapse.
- **Flicker-free loading**: Apply a short delay (~150–300ms) before rendering loading skeletons or spinners, with a minimum visible duration (~300–500ms) to prevent visual flashing on fast networks.
- **Stable skeletons**: Skeleton placeholders must match the exact dimensions and typography layout of final content to prevent Cumulative Layout Shift (CLS).
- **Optimistic updates**: Update UI state immediately upon user action when success is highly probable; reconcile on server response and provide graceful rollback or Undo on failure.
- **Empty & error states**: Every view must gracefully handle empty data, sparse lists, and error states with clear recovery actions.

---

## 4. Forms & Input UX

- **Label association**: Every input control must have an associated `<label>` element with matching `for`/`id` or be wrapped within a `<label>`. Clicking the label must focus the input.
- **Submission rules**: Text inputs submit on `Enter`. In `<textarea>`, `Cmd/Ctrl+Enter` submits while `Enter` inserts a newline. Keep submit buttons enabled so users can trigger submission to surface validation errors; only disable during the in-flight network request.
- **Never block typing**: Do not suppress invalid keystrokes silently; accept input and present immediate inline validation feedback.
- **Never block paste**: Never disable pasting into password, email, or verification code inputs.
- **Autocomplete attributes**: Always specify semantic `autocomplete` attributes (e.g. `email`, `current-password`, `one-time-code`, `name`).
- **Input modes**: Use correct `inputmode` (`numeric`, `email`, `tel`, `url`) to prompt the appropriate virtual keyboard on mobile devices.

---

## 5. Animation Safety & Motion

- **Honor `prefers-reduced-motion`**: Always provide a reduced-motion fallback that disables non-essential animations.
- **Never `transition: all`**: Explicitly specify only the animated properties (e.g. `transition: opacity 150ms ease, transform 150ms ease`). Transitions on layout properties (`width`, `height`, `margin`) cause costly repaints and layout thrashing.
- **GPU-accelerated transforms**: Restrict animations to compositor-friendly properties (`transform`, `opacity`).
- **Interruptible motion**: All animations and modal transitions must be immediately dismissible by user interaction (ESC key, backdrop click).

---

## 6. Layout, Typography & Visual Polish

- **Tabular numbers**: Use `font-variant-numeric: tabular-nums` or monospace fonts for prices, counters, timestamps, and data tables to prevent jitter during updates.
- **Explicit image dimensions**: Specify `width` and `height` or aspect-ratio on all images and media containers to eliminate layout shifts.
- **Layered shadows**: Combine ambient soft shadows with crisp borders and hairlines to achieve physical elevation depth.
- **Contrast compliance**: Verify WCAG AA contrast (≥ 4.5:1 for body text, ≥ 3:1 for large text) across both light and dark themes. Style `<html>` with `color-scheme: dark` in dark themes for proper native control contrast.
