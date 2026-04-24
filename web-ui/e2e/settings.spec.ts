import { test, expect } from './test-helpers';

test.describe('Settings Modal', () => {
  test('open settings, change value and save', async ({ adminPage }) => {
    // 1. Open User menu
    await adminPage.click('button:has-text("e2e_admin")');

    // 2. Click settings
    await adminPage.click('button:has-text("Cài đặt Trạm")');

    // 3. Verify Modal opened
    await expect(adminPage.locator('h3:has-text("Cài đặt Trạm Đóng Gói")')).toBeVisible();

    // 4. Fill form
    await adminPage.fill('input[placeholder="Nhập tên trạm..."]', 'e2e_station_1_updated');

    // 5. Save
    await adminPage.click('button:has-text("Lưu cài đặt")');

    // 6. Verify toast
    await expect(adminPage.locator('text=Cập nhật trạm thành công')).toBeVisible();

    // 7. Reset back to original to not break other tests
    await adminPage.click('button:has-text("e2e_admin")');
    await adminPage.click('button:has-text("Cài đặt Trạm")');
    await adminPage.fill('input[placeholder="Nhập tên trạm..."]', 'e2e_station_1');
    await adminPage.click('button:has-text("Lưu cài đặt")');
    await expect(adminPage.locator('text=Cập nhật trạm thành công')).toBeVisible();
  });
});
