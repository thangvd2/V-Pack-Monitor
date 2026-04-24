import { test, expect } from './test-helpers';

test.describe('Operator Scan Flow', () => {
  test('mock scan START, verify status, mock scan STOP', async ({ operatorPage, page }) => {
    // 0. Route mock for /api/scan to simulate backend success
    await page.route('**/api/scan', async (route) => {
      const request = route.request();
      const postData = JSON.parse(request.postData() || '{}');
      
      if (postData.barcode === 'STOP') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ status: 'processing', message: 'Lưu video thành công' })
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ status: 'recording', record_id: 999 })
        });
      }
    });

    // Ensure it shows idle state first
    await expect(operatorPage.locator('text=Sẵn sàng')).toBeVisible();

    // 1. Mock Scan START
    await operatorPage.keyboard.type('E2E_WAYBILL_TEST');
    await operatorPage.keyboard.press('Enter');

    // Verify status changes to recording
    await expect(operatorPage.locator('text=Đang đóng hàng: E2E_WAYBILL_TEST')).toBeVisible();

    // Wait a bit to simulate packing
    await operatorPage.waitForTimeout(2000);

    // 2. Mock Scan STOP via Dev Mode manual simulator
    await operatorPage.fill('input[placeholder*="Nhập mã vận đơn"]', 'STOP');
    await operatorPage.click('button:has-text("Bắt Đầu Ghi")');

    // Verify it goes back to ready
    await expect(operatorPage.locator('text=Sẵn sàng')).toBeVisible({ timeout: 10000 });
  });
});
