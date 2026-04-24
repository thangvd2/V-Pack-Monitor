import { test, expect } from './test-helpers';

test.describe('Settings Modal', () => {
  test('open settings, change value and save', async ({ adminPage }) => {
    test.setTimeout(60000); // This test does two full page reloads, needs more time
    // 1. Make sure we are on the Grid tab (Vận hành)
    await adminPage.click('button:has-text("Vận hành")');
    const stationCard = adminPage.locator('div.group:has-text("e2e_station_1")');
    await expect(stationCard).toBeVisible();

    // 2. Click the station card to enter single view, so activeStationId is set
    await stationCard.click();
    
    // Wait for single view to load (we should see the station name in the header or dropdown)
    await expect(adminPage.locator('h2:has-text("Chế Độ Quan Sát Live")')).toBeVisible();

    // 3. Open user dropdown and click Settings
    await adminPage.click('button:has-text("E2E Admin")');
    const settingsBtn = adminPage.locator('button:has-text("Cài đặt Trạm")');
    await settingsBtn.waitFor({ state: 'visible' });
    await settingsBtn.click();

    // 4. Verify Modal opened
    await expect(adminPage.locator('h2:has-text("Cài đặt Trạm")')).toBeVisible();

    // 5. Fill form - Update IP instead of Name so we don't break other parallel tests
    const ipInput = adminPage.locator('input[placeholder*="VD: 192.168.1.10"]');
    await ipInput.fill('192.168.1.100');

    // 6. Save and wait for reload
    await Promise.all([
      adminPage.waitForNavigation(),
      adminPage.click('button:has-text("LƯU TRẠM NÀY")')
    ]);

    // 7. Verify page reloaded and we are back on the grid
    const stationCard2 = adminPage.locator('div.group:has-text("e2e_station_1")');
    await expect(stationCard2).toBeVisible({ timeout: 10000 });

    // To click settings again, we must click the station card again!
    await stationCard2.click();
    await expect(adminPage.locator('h2:has-text("Chế Độ Quan Sát Live")')).toBeVisible();

    // 8. Reset back to original to not break other tests
    await adminPage.click('button:has-text("E2E Admin")');
    const settingsBtn2 = adminPage.locator('button:has-text("Cài đặt Trạm")');
    await settingsBtn2.waitFor({ state: 'visible' });
    await settingsBtn2.click();
    await ipInput.fill('192.168.1.99');
    
    await Promise.all([
      adminPage.waitForNavigation(),
      adminPage.click('button:has-text("LƯU TRẠM NÀY")')
    ]);
    
    await expect(adminPage.locator('div.group:has-text("e2e_station_1")')).toBeVisible({ timeout: 10000 });
  });
});
