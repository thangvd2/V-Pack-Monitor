import { test, expect } from './test-helpers';

test.describe('Records List', () => {
  test('search and filter records', async ({ adminPage }) => {
    // Navigate to Dashboard (which has records)
    await adminPage.click('button:has-text("Hệ thống")');
    // Wait for Dashboard to load
    await expect(adminPage.locator('text=Thống kê')).toBeVisible();

    // The user should see the record list. Search for a specific waybill.
    // In our seed data, we might not have a specific E2E waybill created initially,
    // but we can type in the search box to verify it's working.
    await adminPage.fill('input[placeholder="Tìm kiếm mã vận đơn..."]', 'E2E_WAYBILL_TEST');

    // Select the station filter
    const select = adminPage.locator('select');
    await select.selectOption({ label: 'e2e_station_1' });

    // The list should show "Không tìm thấy bản ghi nào" if it's empty, or show results.
    // Because we just cleared E2E_WAYBILL_ records in seed, it should be empty.
    await expect(adminPage.locator('text=Không tìm thấy bản ghi nào')).toBeVisible();
  });
});
