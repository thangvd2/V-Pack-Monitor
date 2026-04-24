import { test, expect } from './test-helpers';

test.describe('Auth Flow', () => {
  test('login with valid credentials, verify redirect and logout', async ({ page }) => {
    await page.goto('/');

    await expect(page.locator('h1', { hasText: 'V-Pack Monitor' })).toBeVisible();

    await page.fill('input[type="text"]', 'e2e_admin');
    await page.fill('input[type="password"]', 'admin123');

    await page.click('button:has-text("Đăng Nhập")');

    // Should redirect to dashboard
    await expect(page.locator('text=Live Cameras Toàn Hệ Thống')).toBeVisible();

    // Open user menu
    await page.click('button:has-text("e2e_admin")');

    // Click logout
    await page.click('button:has-text("Đăng xuất")');

    // Back to login page
    await expect(page.locator('h1', { hasText: 'V-Pack Monitor' })).toBeVisible();
  });
});
