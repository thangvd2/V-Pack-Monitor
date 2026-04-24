import { test, expect } from './test-helpers';

test.describe('Admin Grid View', () => {
  test('verify grid layout, tabs, and single view', async ({ adminPage }) => {
    // 1. Verify Grid is visible
    await expect(adminPage.locator('text=Live Cameras Toàn Hệ Thống')).toBeVisible();

    // 2. Verify we have station cards
    const stationCard = adminPage.locator('h3:has-text("e2e_station_1")');
    await expect(stationCard).toBeVisible();

    // 3. Switch to Settings/System Health tab
    await adminPage.click('button:has-text("Hệ thống")');
    await expect(adminPage.locator('text=Trạng Thái Hệ Thống')).toBeVisible();

    // 4. Switch back to Operations tab
    await adminPage.click('button:has-text("Vận hành")');
    await expect(stationCard).toBeVisible();

    // 5. Click on station to go to Single View
    await stationCard.click();
    
    // 6. Verify single view
    await expect(adminPage.locator('text=Chế độ Camera:')).toBeVisible();

    // 7. Click back to grid
    await adminPage.click('button[title="Trở về danh sách"]');
    await expect(adminPage.locator('text=Live Cameras Toàn Hệ Thống')).toBeVisible();
  });
});
