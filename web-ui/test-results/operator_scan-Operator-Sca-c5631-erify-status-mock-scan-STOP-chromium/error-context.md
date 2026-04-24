# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: operator_scan.spec.ts >> Operator Scan Flow >> mock scan START, verify status, mock scan STOP
- Location: e2e\operator_scan.spec.ts:4:3

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('text=Thống kê')
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 5000ms
  - waiting for locator('text=Thống kê')

```

# Page snapshot

```yaml
- generic [ref=e3]:
    - generic [ref=e4]:
        - generic [ref=e5]:
            - img [ref=e7]
            - generic [ref=e12]:
                - heading "V-Pack Monitor" [level=1] [ref=e13]
                - paragraph [ref=e14]: Chọn trạm làm việc
        - button "Đăng xuất" [ref=e15]:
            - img [ref=e16]
            - text: Đăng xuất
    - generic [ref=e19]:
        - generic [ref=e20]:
            - img [ref=e22]
            - heading "Chọn Trạm Làm Việc" [level=2] [ref=e24]
            - paragraph [ref=e25]: Xin chào E2E Operator, vui lòng chọn trạm để bắt đầu
        - 'button "🟢 Trống e2e_station_1 ID: 25 Nhấn để chọn →" [ref=e27] [cursor=pointer]':
            - generic [ref=e28]:
                - img [ref=e30]
                - generic [ref=e32]:
                    - generic [ref=e33]: 🟢
                    - text: Trống
            - heading "e2e_station_1" [level=3] [ref=e34]
            - paragraph [ref=e35]: 'ID: 25'
            - paragraph [ref=e37]: Nhấn để chọn →
        - paragraph [ref=e38]: Trạng thái tự động cập nhật mỗi 10 giây
```

# Test source

```ts
  1  | import { test as base, expect } from '@playwright/test';
  2  |
  3  | type AuthFixtures = {
  4  |   adminPage: import('@playwright/test').Page;
  5  |   operatorPage: import('@playwright/test').Page;
  6  | };
  7  |
  8  | export const test = base.extend<AuthFixtures>({
  9  |   adminPage: async ({ page }, use) => {
  10 |     await page.goto('/');
  11 |     await page.fill('input[type="text"]', 'e2e_admin');
  12 |     await page.fill('input[type="password"]', 'admin123');
  13 |     await page.click('button:has-text("Đăng Nhập")');
  14 |     await expect(page.locator('text=Live Cameras Toàn Hệ Thống')).toBeVisible();
  15 |     await use(page);
  16 |   },
  17 |   operatorPage: async ({ page }, use) => {
  18 |     await page.goto('/');
  19 |     await page.fill('input[type="text"]', 'e2e_operator');
  20 |     await page.fill('input[type="password"]', 'operator123');
  21 |     await page.click('button:has-text("Đăng Nhập")');
  22 |     // Operator will see Dashboard (which contains Thống kê)
> 23 |     await expect(page.locator('text=Thống kê')).toBeVisible();
     |                                                 ^ Error: expect(locator).toBeVisible() failed
  24 |     await use(page);
  25 |   }
  26 | });
  27 |
  28 | export { expect } from '@playwright/test';
  29 |
```
