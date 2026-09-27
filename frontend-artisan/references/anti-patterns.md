# Frontend Anti-Patterns & AI Cliches

These patterns identify uninspired, default AI generations. When writing or refactoring UI code, replace every occurrence of these patterns with handcrafted alternatives.

---

## 1. The "Purple-on-Slate" Gradient Trap

* **The Anti-Pattern**: Dark slate background (`bg-slate-900` or `bg-slate-950`) with vibrant purple/indigo text gradients (`bg-gradient-to-r from-purple-500 to-indigo-500 text-transparent bg-clip-text`) and a faint purple blurred radial aura in the center.
* **Why it fails**: Every AI coding model defaults to this exact color scheme. It instantly signals low-effort, uncurated code.
* **The Artisan Fix**:
  - Adopt **deliberate color palettes**: warm stone/sand neutrals, deep charcoal with emerald/forest accents, ink-black with electric amber, or clean editorial ivory with deep vermilion.
  - Use solid typography with deliberate weight contrasts instead of noisy rainbow gradients.

---

## 2. The Cookie-Cutter 3-Card Feature Grid

* **The Anti-Pattern**: Exactly three identically sized cards side-by-side (`grid grid-cols-3 gap-6`), each with an identical rounded icon in a colored square at the top, a 2-word heading, and 2 lines of generic lorem ipsum text.
* **Why it fails**: Monotonous visual rhythm; conveys zero hierarchy or narrative structure.
* **The Artisan Fix**:
  - Use **Bento Grids**: Vary card sizes across a 12-column or 4-column layout (e.g., Card 1 spans 2 columns with an interactive preview; Card 2 spans 1 column with a live metric counter; Card 3 spans full width with a timeline).
  - Give each feature an asymmetric, domain-relevant layout instead of a generic card wrapper.

---

## 3. Flat, Non-Tactile Buttons

* **The Anti-Pattern**: Buttons with `bg-blue-600 hover:bg-blue-700` and no other states.
* **Why it fails**: The button feels like flat printed paper on a screen; no sense of physical affordance or mechanical response.
* **The Artisan Fix**:
  - Add micro-spring compression:
    ```html
    <button class="px-4 py-2 rounded-lg font-medium text-sm transition-all duration-150 ease-out hover:-translate-y-0.5 active:translate-y-0 active:scale-[0.98] shadow-sm hover:shadow active:shadow-none">
      Save Changes
    </button>
    ```

---

## 4. Unstyled System Scrollbars & Layout Overflow

* **The Anti-Pattern**: Long lists or sidebars showing default clunky OS scrollbars, or horizontal scrollbars appearing unexpectedly on mobile.
* **Why it fails**: Destroys visual immersion and signals unpolished code.
* **The Artisan Fix**:
  - Style custom thin scrollbars using Tailwind utilities or subtle pseudo-elements (`scrollbar-thin scrollbar-thumb-zinc-300 dark:scrollbar-thumb-zinc-700`).
  - Always enforce `overflow-x-hidden` on parent containers or design flex/grid items to wrap cleanly.

---

## 5. Low-Contrast Muted Text (Accessibility Hazard)

* **The Anti-Pattern**: Using `text-zinc-400` or `text-gray-400` on white backgrounds, or `text-zinc-600` on dark backgrounds to look "minimal".
* **Why it fails**: Directly violates WCAG 2.1 AA (contrast drops below 3:1), making labels unreadable for many users and failing compliance audits.
* **The Artisan Fix**:
  - In light mode: use `text-zinc-600` for secondary text (contrast ~5.5:1 on white). Never use `text-zinc-400` for readable text on light surfaces.
  - In dark mode: use `text-zinc-300` or `text-zinc-400` on zinc-900 (contrast ~6:1).

---

## 6. Centered Hero Cliché

* **The Anti-Pattern**: Centered small pill badge ("✨ Announcing v2.0") $\rightarrow$ 48px centered bold title $\rightarrow$ 18px centered subtitle $\rightarrow$ two buttons side-by-side ("Get Started" and "View Docs").
* **Why it fails**: Completely homogeneous landing page template used thousands of times.
* **The Artisan Fix**:
  - Off-axis split layouts: bold left-aligned typography with an interactive live widget or code preview pinned on the right.
  - High-density status strip or breadcrumbs rather than the standard pill badge.

---

## 7. The Obligatory 4-Card Metric KPI Grid

* **The Anti-Pattern**: Placing 4 metric cards (`Active Keys`, `Total Volume`, `Latency`, `Errors`) with neon icons in the top-right corner at the top of a utility tool, settings page, or table view.
* **Why it fails**: It screams generic AI-generated template. Real developer tools (Stripe, OpenAI, GitHub, Linear) put the primary workflow—the table, editor, or configuration—front and center.
* **The Artisan Fix**:
  - Eliminate the stat row completely unless the user explicitly requested an analytics dashboard.
  - Give 100% of the viewport to high-density tabular data, search filters, and action controls.

---

## 8. Faux Gimmick Controls & Fake Streamers

* **The Anti-Pattern**: Adding fake "Simulate Traffic Pulse" buttons, glowing animated terminal logs, or unnecessary pulse animations to make a page look "alive".
* **Why it fails**: It's theater over substance. It insults developer intelligence and clutters real utility workflows.
* **The Artisan Fix**:
  - Build real, functional state management: optimistic updates, instant copy-to-clipboard with visual confirmation, keyboard shortcuts (`⌘K`, `Esc`), and crisp empty states.

