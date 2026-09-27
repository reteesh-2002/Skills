# Vercel Web Interface Guidelines Reference

The production engineering standard for web interfaces, micro-interactions, layout, animations, and forms.

## 1. Interaction Invariants

- **Keyboard Works Everywhere**: All interactive flows must be operable by keyboard alone following WAI-ARIA authoring patterns.
- **Visible, Clear Focus Rings**:
  - Prefer `:focus-visible` over `:focus` to prevent distracting pointer users.
  - Set `:focus-within` for composite controls.
  - Sticky headers, floating banners, and navigation bars must NEVER obscure the focused element (`scroll-padding-top`).
- **Hit Target Sizing**:
  - Desktop minimum hit target is 24px (expand hit area with pseudo-elements if visual icon is smaller).
  - Mobile minimum hit target is **44px × 44px**.
- **Mobile Input Font Size**:
  - `<input>` and `<textarea>` must have font size $\ge 16\text{px}$ on mobile (`text-base` or `1rem`) to prevent iOS Safari auto-zooming and viewport panning.
- **Respect User Zoom**:
  - Never disable browser zoom (`user-scalable=no` is strictly forbidden).
- **Don't Block Paste**:
  - Never intercept or disable paste events on form fields.
- **Touch Action Manipulation**:
  - Apply `touch-action: manipulation` to interactive controls and buttons to eliminate the 300ms double-tap zoom delay on mobile devices.
- **Design Forgiving Interactions**:
  - Controls should have generous click padding. For dropdowns and submenus, implement hover prediction cones to prevent menu dismissal when moving diagonally.

## 2. Loading & State Discipline

- **Loading Buttons Retain Labels**:
  - When a button triggers an async action, show an inline spinner or loader while **keeping the original button label visible** (e.g. `[ ⟳ Deploying... ]` or `[ ⟳ Save ]`). Never swap the button out for an ambiguous blank spinner.
- **Flicker-Free Loading Skeletons**:
  - Add a short delay (**150–300ms**) before showing a skeleton/spinner on fast API responses.
  - Once visible, enforce a minimum display duration (**300–500ms**) so the UI does not violently flash between skeleton and content.
- **URL as State**:
  - Persist filters, active tabs, search terms, and pagination in URL query parameters (`searchParams` / `nuqs`). Refreshing, sharing, or hitting browser Back/Forward must preserve the user's view state.
- **Optimistic UI Updates**:
  - Update UI immediately upon user action when success is highly probable. Reconcile upon server response. On error, roll back gracefully with a toast notification and "Undo" affordance.
- **Ellipsis Etiquette**:
  - Menu options or buttons that require subsequent user input before executing (e.g. "Rename…", "Export…") must end with a typographical ellipsis (`…`).

## 3. Layout, Scroll & Motion Polish

- **Overscroll Containment**:
  - Apply `overscroll-behavior: contain` to modal dialogs, slide-over sheets, and drawer panels to prevent scroll chaining to the underlying document body.
- **Scroll Position Restoration**:
  - Ensure navigating back restores prior scroll position.
- **Inert During Drag**:
  - While dragging elements (e.g. reordering lists, kanban cards), apply `inert` and disable text selection (`select-none`) so hover and text highlights don't trigger erratically.
- **Motion Safety**:
  - All transitions, transforms, and animations must respect `@media (prefers-reduced-motion: reduce)` (`motion-reduce:transition-none motion-reduce:transform-none`).
