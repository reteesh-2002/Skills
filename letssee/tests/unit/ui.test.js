// Unit Tests for Workstream B: Anti-Slop & Industrial Telemetry HUD
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const UI_DIR = path.resolve(__dirname, '../../src/ui');

test('Anti-Slop & Frontend Artisan Verification Suite', async (t) => {
  const htmlPath = path.join(UI_DIR, 'dashboard.html');
  const cssPath = path.join(UI_DIR, 'dashboard.css');
  const jsPath = path.join(UI_DIR, 'dashboard.js');

  const htmlContent = fs.readFileSync(htmlPath, 'utf-8');
  const cssContent = fs.readFileSync(cssPath, 'utf-8');
  const jsContent = fs.readFileSync(jsPath, 'utf-8');

  await t.test('1. Enforces Anti-Slop negative constraints on styling', () => {
    // Ban purple/cyan SaaS gradients
    assert.ok(!cssContent.includes('#6366f1'), 'Must not contain generic indigo #6366f1');
    assert.ok(!cssContent.includes('#a855f7'), 'Must not contain generic purple #a855f7');
    assert.ok(!cssContent.includes('linear-gradient'), 'Must not contain generic AI gradient cards');

    // Ban Inter and Roboto
    assert.ok(!/\binter\b/i.test(cssContent), 'Must not use generic Inter font');
    assert.ok(!/\broboto\b/i.test(cssContent), 'Must not use generic Roboto font');

    // Strict 0px border-radius
    assert.ok(cssContent.includes('border-radius: 0 !important;'), 'Must enforce strict 0px border-radius');
  });

  await t.test('2. Enforces Industrial Telemetry HUD visual archetype & high-contrast palette', () => {
    // Color tokens
    assert.ok(cssContent.includes('--color-phosphor: #ffb000;'), 'Must define amber phosphor CRT token');
    assert.ok(cssContent.includes('--color-laser: #00e676;'), 'Must define laser green token');
    assert.ok(cssContent.includes('--color-crimson: #ff3d00;'), 'Must define alert crimson token');

    // Monospace font stack
    assert.ok(cssContent.includes('ui-monospace'), 'Must include monospace stack for technical data');
  });

  await t.test('3. Enforces WCAG AA and semantic ARIA accessibility', () => {
    assert.ok(htmlContent.includes('role="banner"'), 'Header must have banner role');
    assert.ok(htmlContent.includes('role="main"'), 'Main grid must have main role');
    assert.ok(htmlContent.includes('role="meter"'), 'Segmented LED meter must have meter role');
    assert.ok(htmlContent.includes('role="log"'), 'Telemetry stream must have log role');
    assert.ok(htmlContent.includes('aria-live="polite"'), 'Log stream must announce polite updates');
    assert.ok(cssContent.includes(':focus-visible'), 'CSS must include focus-visible accessibility styling');
  });

  await t.test('4. Tactile interactive components and stream ledger integrity', () => {
    assert.ok(htmlContent.includes('id="btn-manual-flush"'), 'Manual flush tactile button must exist');
    assert.ok(htmlContent.includes('id="toggle-zero-trust"'), 'Mechanical toggle switch must exist');
    assert.ok(htmlContent.includes('id="telemetry-log-stream"'), 'Telemetry stream element must exist');
    assert.ok(jsContent.includes('AudioContext'), 'Must synthesize tactile mechanical click audio');
    assert.ok(jsContent.includes('renderLedMeter'), 'Must dynamically drive 20-tick LED bar');
  });
});
