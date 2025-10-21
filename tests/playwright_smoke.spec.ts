/**
 * idempotency_key: playwright-smoke-2025-10-21-v1
 * E2E básico para validar latência e status de páginas críticas
 * Requer: Docker Playwright ou Node+@playwright/test local
 */
import { test, expect } from '@playwright/test';

const BASE_URL = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3001';

test('OpenWebUI home responde < 1.5s e status 200', async ({ page }) => {
  const start = Date.now();
  const res = await page.goto(BASE_URL, { waitUntil: 'domcontentloaded', timeout: 10000 });
  const dur = Date.now() - start;
  expect(res?.status(), 'status 200').toBe(200);
  expect(dur, 'pseudop95<1500ms').toBeLessThan(1500);
  await expect(page.locator('body')).toBeVisible();
});

test('/v1/models responde < 1200ms e contém "data"', async ({ request }) => {
  const start = Date.now();
  const res = await request.get('http://localhost:8082/v1/models', { timeout: 10000 });
  const dur = Date.now() - start;
  expect(res.status(), 'status 200').toBe(200);
  const json = await res.json();
  expect(json).toHaveProperty('data');
  expect(dur, 'pseudop95<1200ms').toBeLessThan(1200);
});
