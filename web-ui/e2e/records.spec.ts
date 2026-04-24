import { test, expect } from './test-helpers';

test.describe('Records List', () => {
  test('search and filter records', async ({ adminPage }) => {
    // The user should see the record list on the Operations tab (default for Admin)
    await expect(adminPage.locator('text=Lịch sử ghi hình')).toBeVisible();

    // The user should see the record list. Search for a specific waybill.
    // In our seed data, we might not have a specific E2E waybill created initially,
    await adminPage.fill('input[placeholder="Tìm mã vận đơn..."]', 'E2E_WAYBILL_TEST');

    // Select the station filter for Records List specifically
    const select = adminPage.locator('select:has(option[value="orphaned"])');
    await select.selectOption({ label: 'e2e_station_1' });

    // The list should show "Chưa có mã vận đơn nào" if it's empty, or show results.
    // Because we just cleared E2E_WAYBILL_ records in seed, it should be empty.
    await expect(adminPage.locator('text=Chưa có mã vận đơn nào được ghi lại tại Trạm này.')).toBeVisible();
  });
});
