import { chromium } from '@playwright/test';

(async () => {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  // Clear storage
  await page.goto('http://localhost:8000/login');
  await page.evaluate(() => {
    localStorage.clear();
    sessionStorage.clear();
  });

  // Login
  await page.fill('input[type="text"]:visible', 'admin');
  await page.fill('input[type="password"]:visible', 'admin123');
  await page.click('button:has-text("登录")');
  await page.waitForTimeout(3000);

  // Navigate to settings
  await page.goto('http://localhost:8000/settings');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(2000);

  // Click the "图片模型配置" tab
  const tabs = await page.locator('[role="tab"]').all();
  console.log('Found tabs:', tabs.length);
  for (let i = 0; i < tabs.length; i++) {
    const text = await tabs[i].textContent();
    console.log(`Tab ${i}:`, text);
  }

  await tabs[1].click(); // 图片模型配置
  await page.waitForTimeout(2000);

  // Find the dropdown
  const dropdown = page.locator('[name="cover_api_provider"]');
  await dropdown.click();
  await page.waitForTimeout(1000);

  // Now execute JavaScript to find what React is seeing
  const result = await page.evaluate(() => {
    // Find all Option elements in the DOM
    const options = Array.from(document.querySelectorAll('[role="option"]'));
    return {
      count: options.length,
      options: options.map(o => ({
        label: o.textContent,
        id: o.id,
        ariaLabel: o.getAttribute('aria-label'),
        visible: o.offsetParent !== null
      }))
    };
  });

  console.log('Dropdown options:', JSON.stringify(result, null, 2));

  // Take screenshot
  await page.screenshot({ path: 'debug-dropdown.png', fullPage: true });
  console.log('Screenshot saved to debug-dropdown.png');

  // Keep browser open for manual inspection
  console.log('Browser open - press Ctrl+C to exit');
  await new Promise(() => {});
})();
