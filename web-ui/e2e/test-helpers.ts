import { test as base, expect } from '@playwright/test';

type AuthFixtures = {
  adminPage: import('@playwright/test').Page;
  operatorPage: import('@playwright/test').Page;
};

export const test = base.extend<AuthFixtures>({
  adminPage: async ({ page }, use) => {
    await page.goto('/');
    await page.fill('input[type="text"]', 'e2e_admin');
    await page.fill('input[type="password"]', 'admin123');
    await page.click('button:has-text("Đăng Nhập")');
    await expect(page.locator('text=Live Cameras Toàn Hệ Thống')).toBeVisible();
    await use(page);
  },
  operatorPage: async ({ page }, use) => {
    await page.goto('/');
    await page.fill('input[type="text"]', 'e2e_operator');
    await page.fill('input[type="password"]', 'operator123');
    await page.click('button:has-text("Đăng Nhập")');
    // Select station first
    await expect(page.locator('h2:has-text("Chọn Trạm Làm Việc")')).toBeVisible();
    await page.locator('button:has(h3:has-text("e2e_station_1"))').click();
    // Operator will see Live View
    await expect(page.locator('text=Chế Độ Quan Sát Live')).toBeVisible();
    await use(page);
  },
});

export { expect } from '@playwright/test';
