# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: admin_grid.spec.ts >> Admin Grid View >> verify grid layout, tabs, and single view
- Location: e2e\admin_grid.spec.ts:4:3

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('h3:has-text("e2e_station_1")')
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 5000ms
  - waiting for locator('h3:has-text("e2e_station_1")')

```

# Page snapshot

```yaml
- generic [ref=e3]:
    - banner [ref=e4]:
        - generic [ref=e5]:
            - generic [ref=e6]:
                - img [ref=e8]
                - generic [ref=e13]:
                    - heading "V-Pack Monitor" [level=1] [ref=e14]
                    - paragraph [ref=e15]: Hệ thống Camera Đóng hàng E-Commerce
            - generic [ref=e16]:
                - generic [ref=e17]:
                    - button "📹 Vận hành" [ref=e18]
                    - button "📊 Tổng quan" [ref=e19]
                - button "v3.4.0" [ref=e20]:
                    - img [ref=e21]
                    - text: v3.4.0
                - generic [ref=e26]:
                    - generic:
                        - img
                    - textbox "Tìm mã vận đơn..." [ref=e27]
                - button "E2E Admin ADMIN" [ref=e29]:
                    - img [ref=e30]
                    - generic [ref=e33]:
                        - generic [ref=e34]: E2E Admin
                        - generic [ref=e35]: ADMIN
                    - img [ref=e36]
    - generic [ref=e38]:
        - generic [ref=e41]:
            - heading "Live Cameras Toàn Hệ Thống" [level=2] [ref=e43]:
                - img [ref=e44]
                - text: Live Cameras Toàn Hệ Thống
            - generic [ref=e53] [cursor=pointer]:
                - generic:
                    - generic: e2e_station_1
                    - generic: Sẵn sàng
                - generic [ref=e55]:
                    - generic [ref=e56]: 📡
                    - paragraph [ref=e57]: MediaMTX chưa khởi động
                    - paragraph [ref=e58]: Live view cần MediaMTX chạy ở port 8889
        - generic [ref=e60]:
            - generic:
                - heading "Lịch sử ghi hình" [level=2]:
                    - img
                    - text: Lịch sử ghi hình
                - generic: 32 video
            - generic [ref=e61]:
                - combobox [ref=e62]:
                    - option "Tất cả trạm" [selected]
                    - option "(trạm đã xoá)"
                    - option "e2e_station_1"
                - textbox [ref=e63]
                - generic [ref=e64]: →
                - textbox [ref=e65]
                - combobox [ref=e66]:
                    - option "Tất cả trạng thái" [selected]
                    - option "✅ READY"
                    - option "🔴 RECORDING"
                    - option "⏳ PROCESSING"
                    - option "❌ FAILED"
                - generic [ref=e67]: 32 video
            - generic [ref=e68]:
                - generic [ref=e69] [cursor=pointer]:
                    - generic [ref=e70]:
                        - generic [ref=e71]:
                            - heading "6934839106982" [level=3] [ref=e72]
                            - generic [ref=e73]: PIP
                            - generic [ref=e74]: 'Trạm: Mặc định'
                        - button "Xoá bản ghi lưu trữ dọn ổ đĩa" [ref=e75]:
                            - img [ref=e76]
                    - generic [ref=e80]: 00:15:47 22/4/2026
                    - button "6934839106982_20260422_001547_PIP.mp4" [ref=e82]:
                        - img [ref=e83]
                        - generic [ref=e86]: 6934839106982_20260422_001547_PIP.mp4
                - generic [ref=e87] [cursor=pointer]:
                    - generic [ref=e88]:
                        - generic [ref=e89]:
                            - heading "CR XY 00 2006001720" [level=3] [ref=e90]
                            - generic [ref=e91]: PIP
                            - generic [ref=e92]: 'Trạm: Mặc định'
                        - button "Xoá bản ghi lưu trữ dọn ổ đĩa" [ref=e93]:
                            - img [ref=e94]
                    - generic [ref=e98]: 00:15:29 22/4/2026
                    - button "CR_XY_00_2006001720_20260422_001529_PIP.mp4" [ref=e100]:
                        - img [ref=e101]
                        - generic [ref=e104]: CR_XY_00_2006001720_20260422_001529_PIP.mp4
                - generic [ref=e105] [cursor=pointer]:
                    - generic [ref=e106]:
                        - generic [ref=e107]:
                            - heading "6934839106982" [level=3] [ref=e108]
                            - generic [ref=e109]: PIP
                            - generic [ref=e110]: 'Trạm: Mặc định'
                        - button "Xoá bản ghi lưu trữ dọn ổ đĩa" [ref=e111]:
                            - img [ref=e112]
                    - generic [ref=e116]: 00:14:07 22/4/2026
                    - button "6934839106982_20260422_001407_PIP.mp4" [ref=e118]:
                        - img [ref=e119]
                        - generic [ref=e122]: 6934839106982_20260422_001407_PIP.mp4
                - generic [ref=e123] [cursor=pointer]:
                    - generic [ref=e124]:
                        - generic [ref=e125]:
                            - heading "VN264916416227I" [level=3] [ref=e126]
                            - generic [ref=e127]: PIP
                            - generic [ref=e128]: Lỗi
                            - generic [ref=e129]: 'Trạm: Mặc định'
                        - button "Xoá bản ghi lưu trữ dọn ổ đĩa" [ref=e130]:
                            - img [ref=e131]
                    - generic [ref=e135]: 23:47:09 13/4/2026
                - generic [ref=e136] [cursor=pointer]:
                    - generic [ref=e137]:
                        - generic [ref=e138]:
                            - heading "VN264916416227I" [level=3] [ref=e139]
                            - generic [ref=e140]: PIP
                            - generic [ref=e141]: Lỗi
                            - generic [ref=e142]: 'Trạm: Mặc định'
                        - button "Xoá bản ghi lưu trữ dọn ổ đĩa" [ref=e143]:
                            - img [ref=e144]
                    - generic [ref=e148]: 18:49:02 12/4/2026
                - generic [ref=e149] [cursor=pointer]:
                    - generic [ref=e150]:
                        - generic [ref=e151]:
                            - heading "VN264916416227I" [level=3] [ref=e152]
                            - generic [ref=e153]: PIP
                            - generic [ref=e154]: Lỗi
                            - generic [ref=e155]: 'Trạm: Mặc định'
                        - button "Xoá bản ghi lưu trữ dọn ổ đĩa" [ref=e156]:
                            - img [ref=e157]
                    - generic [ref=e161]: 18:44:39 12/4/2026
                - generic [ref=e162] [cursor=pointer]:
                    - generic [ref=e163]:
                        - generic [ref=e164]:
                            - heading "VN264916416227I" [level=3] [ref=e165]
                            - generic [ref=e166]: PIP
                            - generic [ref=e167]: 'Trạm: Mặc định'
                        - button "Xoá bản ghi lưu trữ dọn ổ đĩa" [ref=e168]:
                            - img [ref=e169]
                    - generic [ref=e173]: 18:29:08 12/4/2026
                    - button "VN264916416227I_20260412_182908_PIP.mp4" [ref=e175]:
                        - img [ref=e176]
                        - generic [ref=e179]: VN264916416227I_20260412_182908_PIP.mp4
                - generic [ref=e180] [cursor=pointer]:
                    - generic [ref=e181]:
                        - generic [ref=e182]:
                            - heading "VN264916416227I" [level=3] [ref=e183]
                            - generic [ref=e184]: PIP
                            - generic [ref=e185]: 'Trạm: Mặc định'
                        - button "Xoá bản ghi lưu trữ dọn ổ đĩa" [ref=e186]:
                            - img [ref=e187]
                    - generic [ref=e191]: 18:23:35 12/4/2026
                    - button "VN264916416227I_20260412_182336_PIP.mp4" [ref=e193]:
                        - img [ref=e194]
                        - generic [ref=e197]: VN264916416227I_20260412_182336_PIP.mp4
                - generic [ref=e198] [cursor=pointer]:
                    - generic [ref=e199]:
                        - generic [ref=e200]:
                            - heading "VN264916416227I" [level=3] [ref=e201]
                            - generic [ref=e202]: PIP
                            - generic [ref=e203]: 'Trạm: Mặc định'
                        - button "Xoá bản ghi lưu trữ dọn ổ đĩa" [ref=e204]:
                            - img [ref=e205]
                    - generic [ref=e209]: 18:14:44 12/4/2026
                    - button "VN264916416227I_20260412_181444_PIP.mp4" [ref=e211]:
                        - img [ref=e212]
                        - generic [ref=e215]: VN264916416227I_20260412_181444_PIP.mp4
                - generic [ref=e216] [cursor=pointer]:
                    - generic [ref=e217]:
                        - generic [ref=e218]:
                            - heading "VN264916416227I" [level=3] [ref=e219]
                            - generic [ref=e220]: PIP
                            - generic [ref=e221]: 'Trạm: Mặc định'
                        - button "Xoá bản ghi lưu trữ dọn ổ đĩa" [ref=e222]:
                            - img [ref=e223]
                    - generic [ref=e227]: 17:43:26 12/4/2026
                    - button "VN264916416227I_20260412_174326_PIP.mp4" [ref=e229]:
                        - img [ref=e230]
                        - generic [ref=e233]: VN264916416227I_20260412_174326_PIP.mp4
                - generic [ref=e234] [cursor=pointer]:
                    - generic [ref=e235]:
                        - generic [ref=e236]:
                            - heading "VN264916416227I" [level=3] [ref=e237]
                            - generic [ref=e238]: PIP
                            - generic [ref=e239]: 'Trạm: Mặc định'
                        - button "Xoá bản ghi lưu trữ dọn ổ đĩa" [ref=e240]:
                            - img [ref=e241]
                    - generic [ref=e245]: 17:35:53 12/4/2026
                    - button "VN264916416227I_20260412_173553_PIP.mp4" [ref=e247]:
                        - img [ref=e248]
                        - generic [ref=e251]: VN264916416227I_20260412_173553_PIP.mp4
                - generic [ref=e252] [cursor=pointer]:
                    - generic [ref=e253]:
                        - generic [ref=e254]:
                            - heading "VN264916416227I" [level=3] [ref=e255]
                            - generic [ref=e256]: PIP
                            - generic [ref=e257]: 'Trạm: Mặc định'
                        - button "Xoá bản ghi lưu trữ dọn ổ đĩa" [ref=e258]:
                            - img [ref=e259]
                    - generic [ref=e263]: 17:32:57 12/4/2026
                    - button "VN264916416227I_20260412_173257_PIP.mp4" [ref=e265]:
                        - img [ref=e266]
                        - generic [ref=e269]: VN264916416227I_20260412_173257_PIP.mp4
                - generic [ref=e270] [cursor=pointer]:
                    - generic [ref=e271]:
                        - generic [ref=e272]:
                            - heading "VN264916416227I" [level=3] [ref=e273]
                            - generic [ref=e274]: PIP
                            - generic [ref=e275]: 'Trạm: Mặc định'
                        - button "Xoá bản ghi lưu trữ dọn ổ đĩa" [ref=e276]:
                            - img [ref=e277]
                    - generic [ref=e281]: 17:25:58 12/4/2026
                    - button "VN264916416227I_20260412_172558_PIP.mp4" [ref=e283]:
                        - img [ref=e284]
                        - generic [ref=e287]: VN264916416227I_20260412_172558_PIP.mp4
                - generic [ref=e288] [cursor=pointer]:
                    - generic [ref=e289]:
                        - generic [ref=e290]:
                            - heading "VN264916416227I" [level=3] [ref=e291]
                            - generic [ref=e292]: PIP
                            - generic [ref=e293]: Lỗi
                            - generic [ref=e294]: 'Trạm: Mặc định'
                        - button "Xoá bản ghi lưu trữ dọn ổ đĩa" [ref=e295]:
                            - img [ref=e296]
                    - generic [ref=e300]: 17:24:23 12/4/2026
                - generic [ref=e301] [cursor=pointer]:
                    - generic [ref=e302]:
                        - generic [ref=e303]:
                            - heading "85257BJPBVD2228" [level=3] [ref=e304]
                            - generic [ref=e305]: SINGLE
                            - generic [ref=e306]: 'Trạm: Mặc định'
                        - button "Xoá bản ghi lưu trữ dọn ổ đĩa" [ref=e307]:
                            - img [ref=e308]
                    - generic [ref=e312]: 03:03:06 12/4/2026
                    - button "85257BJPBVD2228_20260412_030306.mp4" [ref=e314]:
                        - img [ref=e315]
                        - generic [ref=e318]: 85257BJPBVD2228_20260412_030306.mp4
                - generic [ref=e319] [cursor=pointer]:
                    - generic [ref=e320]:
                        - generic [ref=e321]:
                            - heading "ADASDADQE" [level=3] [ref=e322]
                            - generic [ref=e323]: PIP
                            - generic [ref=e324]: 'Trạm: Mặc định'
                        - button "Xoá bản ghi lưu trữ dọn ổ đĩa" [ref=e325]:
                            - img [ref=e326]
                    - generic [ref=e330]: 06:33:07 9/4/2026
                    - button "ADASDADQE_20260409_063259_PIP.mp4" [ref=e332]:
                        - img [ref=e333]
                        - generic [ref=e336]: ADASDADQE_20260409_063259_PIP.mp4
                - generic [ref=e337] [cursor=pointer]:
                    - generic [ref=e338]:
                        - generic [ref=e339]:
                            - heading "DASDADAD" [level=3] [ref=e340]
                            - generic [ref=e341]: SINGLE
                            - generic [ref=e342]: 'Trạm: Mặc định'
                        - button "Xoá bản ghi lưu trữ dọn ổ đĩa" [ref=e343]:
                            - img [ref=e344]
                    - generic [ref=e348]: 05:20:30 9/4/2026
                    - button "DASDADAD_20260409_051230.mp4" [ref=e350]:
                        - img [ref=e351]
                        - generic [ref=e354]: DASDADAD_20260409_051230.mp4
                - generic [ref=e355] [cursor=pointer]:
                    - generic [ref=e356]:
                        - generic [ref=e357]:
                            - heading "FGDF2423FSV32412SDFSDFSDFSDF" [level=3] [ref=e358]
                            - generic [ref=e359]: SINGLE
                            - generic [ref=e360]: 'Trạm: Mặc định'
                        - button "Xoá bản ghi lưu trữ dọn ổ đĩa" [ref=e361]:
                            - img [ref=e362]
                    - generic [ref=e366]: 05:11:34 9/4/2026
                    - button "FGDF2423FSV32412SDFSDFSDFSDF_20260409_051020.mp4" [ref=e368]:
                        - img [ref=e369]
                        - generic [ref=e372]: FGDF2423FSV32412SDFSDFSDFSDF_20260409_051020.mp4
                - generic [ref=e373] [cursor=pointer]:
                    - generic [ref=e374]:
                        - generic [ref=e375]:
                            - heading "R2SDFSDF23243423423423" [level=3] [ref=e376]
                            - generic [ref=e377]: SINGLE
                            - generic [ref=e378]: 'Trạm: Mặc định'
                        - button "Xoá bản ghi lưu trữ dọn ổ đĩa" [ref=e379]:
                            - img [ref=e380]
                    - generic [ref=e384]: 05:10:12 9/4/2026
                    - button "R2SDFSDF23243423423423_20260409_051007.mp4" [ref=e386]:
                        - img [ref=e387]
                        - generic [ref=e390]: R2SDFSDF23243423423423_20260409_051007.mp4
                - generic [ref=e391] [cursor=pointer]:
                    - generic [ref=e392]:
                        - generic [ref=e393]:
                            - heading "B5555555555555554674222222222222222222222" [level=3] [ref=e394]
                            - generic [ref=e395]: SINGLE
                            - generic [ref=e396]: 'Trạm: Mặc định'
                        - button "Xoá bản ghi lưu trữ dọn ổ đĩa" [ref=e397]:
                            - img [ref=e398]
                    - generic [ref=e402]: 04:53:20 9/4/2026
                    - button "B5555555555555554674222222222222222222222_20260409_045107.mp4" [ref=e404]:
                        - img [ref=e405]
                        - generic [ref=e408]: B5555555555555554674222222222222222222222_20260409_045107.mp4
                - generic [ref=e409]:
                    - button "← Trước" [disabled] [ref=e410]
                    - generic [ref=e411]: Trang 1/2
                    - button "Sau →" [ref=e412]
```

# Test source

```ts
  1  | import { test, expect } from './test-helpers';
  2  |
  3  | test.describe('Admin Grid View', () => {
  4  |   test('verify grid layout, tabs, and single view', async ({ adminPage }) => {
  5  |     // 1. Verify Grid is visible
  6  |     await expect(adminPage.locator('text=Live Cameras Toàn Hệ Thống')).toBeVisible();
  7  |
  8  |     // 2. Verify we have station cards
  9  |     const stationCard = adminPage.locator('h3:has-text("e2e_station_1")');
> 10 |     await expect(stationCard).toBeVisible();
     |                               ^ Error: expect(locator).toBeVisible() failed
  11 |
  12 |     // 3. Switch to Settings/System Health tab
  13 |     await adminPage.click('button:has-text("Hệ thống")');
  14 |     await expect(adminPage.locator('text=Trạng Thái Hệ Thống')).toBeVisible();
  15 |
  16 |     // 4. Switch back to Operations tab
  17 |     await adminPage.click('button:has-text("Vận hành")');
  18 |     await expect(stationCard).toBeVisible();
  19 |
  20 |     // 5. Click on station to go to Single View
  21 |     await stationCard.click();
  22 |
  23 |     // 6. Verify single view
  24 |     await expect(adminPage.locator('text=Chế độ Camera:')).toBeVisible();
  25 |
  26 |     // 7. Click back to grid
  27 |     await adminPage.click('button[title="Trở về danh sách"]');
  28 |     await expect(adminPage.locator('text=Live Cameras Toàn Hệ Thống')).toBeVisible();
  29 |   });
  30 | });
  31 |
```
