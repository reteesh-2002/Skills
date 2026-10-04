# Web Interface Engineering Guidelines

Production standard covering interactions, keyboard navigation, hit targets, mobile ergonomics, and loading stability.

---

## 1. Interactions & Keyboard Navigation
- **Keyboard Operability**: All interactive controls must be reachable and operable via keyboard (`Tab`, `Shift+Tab`, `Enter`, `Space`, `Arrow keys`, `Esc`).
- **Focus Rings**: Every focusable control shows a visible, high-contrast focus ring. Use `:focus-visible` to prevent distracting pointer users. Set `:focus-within` on compound controls.
- **Focus Trapping**: Modals, slide-overs, and popovers must trap focus while open and return focus to trigger upon close.
- **Hit Targets**: Minimum clickable/tappable area is **≥ 24px on desktop** and **≥ 44px on mobile**.
- **Semantic Links**: Use `<a>` or framework `<Link>` for navigation. Never substitute clickable `<div onClick=...>` or `<button>` for URLs so middle-click and open-in-new-tab function naturally.

---

## 2. Touch & Mobile Ergonomics
- **Input Font Size**: All `<input>`, `<select>`, and `<textarea>` elements must have font-size **≥ 16px on mobile viewports** to prevent iOS Safari auto-zoom on focus.
- **Touch Action**: Set `touch-action: manipulation` on buttons to prevent 300ms double-tap zoom delay.
- **Safe Areas**: Use `env(safe-area-inset-bottom)` and `env(safe-area-inset-top)` for mobile fixed toolbars and floating buttons.
- **No Double-Tap Disruption**: Never disable zoom via `user-scalable=no` or `maximum-scale=1` in viewport meta.

---

## 3. Loading Stability & Motion Safety
- **Button Loading States**: Show spinner alongside the original button label (`[Spinner] Saving...`) to prevent button dimensions from collapsing or shifting surrounding elements.
- **Flicker-Free Loading**: Delay showing spinners or skeletons for fast network calls (<150ms). Once shown, maintain for at least 300ms to avoid micro-flicker.
- **CLS Prevention**: Skeleton placeholders must mirror final element height and typography lines to prevent Cumulative Layout Shift.
- **Tabular Numbers**: Apply `font-feature-settings: "tnum"` / Tailwind `tabular-nums` on timers, counters, currency, and table data.
- **Motion Safety**: Wrap animations in `@media (prefers-reduced-motion: reduce)`. Keep interactive motions interruptible.
