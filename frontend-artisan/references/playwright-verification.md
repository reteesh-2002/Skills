# Playwright Agent Headless Verification Protocol

Inspired by [Playwright Agent CLI](https://playwright.dev/agent-cli/skills).

When verifying frontend implementations, automated headless browser tests provide physical proof of rendering, responsive layout stability, and accessibility without guessing.

## 1. Automated Verification Checks

Using `playwright-cli` or inline Playwright node scripts routed through `./scripts/exec-proxy.sh`:

### A. Viewport Responsiveness & Layout Clip Check
Verify that layouts adapt from mobile (375px) to desktop (1440px) without horizontal scrollbars:
```javascript
// verify-viewports.js
import { test, expect } from '@playwright/test';

const viewports = [
  { name: 'mobile', width: 375, height: 667 },
  { name: 'tablet', width: 768, height: 1024 },
  { name: 'desktop', width: 1440, height: 900 }
];

for (const vp of viewports) {
  test(`Layout renders cleanly on ${vp.name}`, async ({ page }) => {
    await page.setViewportSize({ width: vp.width, height: vp.height });
    await page.goto('http://localhost:3000');
    
    // Check no horizontal overflow
    const hasHorizontalOverflow = await page.evaluate(() => {
      return document.documentElement.scrollWidth > window.innerWidth;
    });
    expect(hasHorizontalOverflow).toBe(false);

    // Save physical proof screenshot
    await page.screenshot({ path: `.evidence/screenshots/${vp.name}.png`, fullPage: false });
  });
}
```

### B. Accessibility Tree & Interactive Focus Ring Check
```javascript
test('Keyboard navigation and focus visibility', async ({ page }) => {
  await page.goto('http://localhost:3000');
  
  // Tab through interactive elements and verify outline is not 'none'
  await page.keyboard.press('Tab');
  const focusedOutline = await page.evaluate(() => {
    const el = document.activeElement;
    return window.getComputedStyle(el).outlineStyle;
  });
  expect(focusedOutline).not.toBe('none');
});
```

### C. Console Error & Hydration Mismatch Defense
```javascript
test('Zero console errors or unhandled exceptions', async ({ page }) => {
  const errors = [];
  page.on('console', msg => {
    if (msg.type() === 'error') errors.push(msg.text());
  });
  page.on('pageerror', err => errors.push(err.message));

  await page.goto('http://localhost:3000');
  expect(errors).toEqual([]);
});
```

## 2. Headless CLI Execution via Proxy
Route test runs through `scripts/exec-proxy.sh` to record physical receipts:
```bash
./scripts/exec-proxy.sh --label test_frontend_ui npx playwright test
```
If Playwright is not installed in the target workspace, disclose the limitation explicitly and provide the self-contained verification script so the user can execute it.
