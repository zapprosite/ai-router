/**
 * idempotency_key: playwright-config-2025-10-21-v1
 */
import { defineConfig } from '@playwright/test';

export default defineConfig({
  timeout: 10000,
  expect: { timeout: 5000 },
  use: {
    headless: process.env.PLAYWRIGHT_HEADLESS !== 'false',
    actionTimeout: 5000,
  },
  reporter: [['list']]
});
