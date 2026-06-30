import { test, expect } from '@playwright/test';

test.use({ storageState: { cookies: [], origins: [] } });

test('GrsAI Provider Test', async ({ page }) => {
  await page.goto('http://localhost:8000/login', { waitUntil: 'networkidle' });

  await page.fill('input[type="text"]', 'admin');
  await page.fill('input[type="password"]', 'admin123');
  await page.click('button:has-text("登录")');
  await page.waitForTimeout(3000);

  await page.goto('http://localhost:8000/settings?t=' + Date.now(), { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);

  await page.getByRole('tab', { name: /图片模型配置/ }).click();
  await page.waitForTimeout(1500);

  const providerLabel = page.locator('label').filter({ hasText: /封面图片.*Provider/ });
  await expect(providerLabel).toBeVisible();

  const formItem = providerLabel.locator('..').locator('..').locator('..');
  const dropdown = formItem.locator('.ant-select').first();

  await dropdown.click();
  await page.waitForTimeout(1500);

  // Use .ant-select-item instead of [role="option"]
  const options = page.locator('.ant-select-dropdown .ant-select-item');
  const count = await options.count();
  console.log('Options count:', count);

  const texts = await options.allTextContents();
  console.log('Options:', texts);

  // Check for GrsAI
  const hasGrsAI = texts.some(t => t && t.includes('GrsAI'));
  console.log('Has GrsAI:', hasGrsAI);

  await page.screenshot({ path: 'grsai-success.png' });

  expect(hasGrsAI).toBeTruthy();
});
