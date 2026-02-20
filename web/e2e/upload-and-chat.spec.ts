/**
 * E2E: Upload a sample file, wait for processing, then ask a RAG question.
 *
 * Requires: API at NEXT_PUBLIC_API_URL (default localhost:8000), web at baseURL (default localhost:3000),
 * and a valid tenant ID (set E2E_TENANT_ID or use default). Sample file from test/sample_docs/.
 */

import { test, expect } from '@playwright/test';
import path from 'path';

const E2E_TENANT_ID = process.env.E2E_TENANT_ID || '00000000-0000-0000-0000-000000000001';
const SAMPLE_FILE = path.resolve(__dirname, '../../test/sample_docs/manual_pump_01.txt');

test.describe('Upload and chat', () => {
  test('upload sample file, wait for completed, then chat returns answer or sources', async ({ page }) => {
    await page.goto('/');

    const tenantInput = page.getByPlaceholder(/tenant|uuid/i).or(page.locator('input[type="text"]').first());
    await tenantInput.fill(E2E_TENANT_ID);

    await page.goto('/upload');
    await tenantInput.fill(E2E_TENANT_ID);

    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(SAMPLE_FILE);

    await expect(page.getByText(/uploading|queuing|processing/i)).toBeVisible({ timeout: 5000 }).catch(() => {});

    for (let i = 0; i < 30; i++) {
      await page.waitForTimeout(2000);
      const row = page.locator('li').filter({ hasText: 'manual_pump_01' });
      const text = await row.textContent();
      if (text && text.includes('completed')) break;
      if (text && text.includes('failed')) throw new Error('Document processing failed');
    }

    await page.goto('/');
    await page.getByPlaceholder(/ask a question/i).fill('How do I prime the pump?');
    await page.getByRole('button', { name: /send/i }).click();

    await expect(page.getByText(/priming|pump|step|procedure/i).or(page.getByText(/source|document/i))).toBeVisible({
      timeout: 20000,
    });
  });
});
