import { test, expect } from './test-helpers';

test.describe('Operator Scan Flow', () => {
  test('mock scan START, verify status, mock scan STOP', async ({ operatorPage }) => {
    // Select station e2e_station_1
    const select = operatorPage.locator('select');
    await select.selectOption({ label: 'e2e_station_1' });

    // Ensure it shows idle state first
    await expect(operatorPage.locator('text=Sẵn sàng đóng gói')).toBeVisible();

    // 1. Mock Scan START
    await operatorPage.keyboard.type('E2E_WAYBILL_TEST');
    await operatorPage.keyboard.press('Enter');

    // Verify status changes to recording
    await expect(operatorPage.locator('text=Đang đóng gói...')).toBeVisible();
    await expect(operatorPage.locator('text=E2E_WAYBILL_TEST')).toBeVisible();

    // Wait a bit to simulate packing
    await operatorPage.waitForTimeout(2000);

    // 2. Mock Scan STOP
    await operatorPage.keyboard.type('E2E_WAYBILL_TEST');
    await operatorPage.keyboard.press('Enter');

    // Verify it goes back to ready and shows a toast
    await expect(operatorPage.locator('text=Lưu video thành công')).toBeVisible({ timeout: 10000 });
    await expect(operatorPage.locator('text=Sẵn sàng đóng gói')).toBeVisible();
  });
});
