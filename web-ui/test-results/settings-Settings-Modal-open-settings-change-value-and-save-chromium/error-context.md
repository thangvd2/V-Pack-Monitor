# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: settings.spec.ts >> Settings Modal >> open settings, change value and save
- Location: e2e\settings.spec.ts:4:3

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('h3:has-text("Cài đặt Trạm Đóng Gói")')
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 5000ms
  - waiting for locator('h3:has-text("Cài đặt Trạm Đóng Gói")')

```

# Page snapshot

```yaml
- generic [ref=e3]:
  - generic [ref=e5]:
    - generic [ref=e6]:
      - img [ref=e8]
      - generic [ref=e11]:
        - generic [ref=e12]:
          - heading "Thêm Trạm Ghi Hình Mới" [level=2] [ref=e13]
          - paragraph [ref=e14]: Thiết lập kết nối Camera và Hệ thống
        - button "✕" [ref=e16]
    - generic [ref=e17]:
      - generic [ref=e18]:
        - heading "Cấu hình Trạm" [level=3] [ref=e19]
        - generic [ref=e20]:
          - generic [ref=e21]: Tên Trạm Đóng Hàng
          - textbox [ref=e22]
        - generic [ref=e23]:
          - generic [ref=e24]: IP Camera Chính (Luồng Web)
          - generic [ref=e25]:
            - 'textbox "VD: 192.168.1.10 hoặc fe80::1" [ref=e26]'
            - button "Test" [disabled] [ref=e27]:
              - img [ref=e28]
              - text: Test
        - generic [ref=e35]:
          - generic [ref=e36]: Hãng Camera / RTSP Profile
          - combobox [ref=e37]:
            - option "Imou / Dahua (Mặc định)" [selected]
            - option "Tenda (Series CH/TD)"
            - option "EZVIZ (Hikvision)"
            - option "TP-Link Tapo"
        - generic [ref=e38]:
          - generic [ref=e39]: Mật khẩu RTSP / Safety Code
          - generic [ref=e40]:
            - textbox "Mật khẩu thiết bị" [ref=e41]
            - button [ref=e42]:
              - img [ref=e43]
        - generic [ref=e46]:
          - generic [ref=e47]: MAC Address (Tự động tìm lại Camera khi đổi IP)
          - 'textbox "VD: AA:BB:CC:DD:EE:FF" [ref=e49]'
          - paragraph [ref=e50]: Để trống nếu không cần tự động tìm lại IP khi mạng thay đổi.
        - generic [ref=e51]:
          - generic [ref=e52]: Chế độ ghi Video
          - combobox [ref=e53]:
            - option "SINGLE — Ghi 1 luồng" [selected]
            - option "PIP — Ghép 2 camera (hoặc 1 camera 2 mắt)"
            - option "DUAL FILE — 2 file từ 2 camera"
          - paragraph [ref=e54]: Ghi 1 luồng từ 1 camera
      - generic [ref=e55]:
        - button "Hệ thống chung" [ref=e56]:
          - heading "Hệ thống chung" [level=3] [ref=e57]
          - img [ref=e58]
        - generic [ref=e60]:
          - generic [ref=e61]:
            - generic [ref=e62]: Tự động xoá Video cũ hơn
            - combobox [ref=e63]:
              - option "3 Ngày"
              - option "7 Ngày"
              - option "15 Ngày"
              - option "30 Ngày" [selected]
              - option "60 Ngày"
              - option "90 Ngày"
              - option "150 Ngày"
              - option "365 Ngày"
              - option "Không bao giờ xoá"
          - generic [ref=e64]:
            - generic [ref=e65]: Dịch vụ Lưu Trữ Đám Mây
            - combobox [ref=e66]:
              - option "Chưa Kích Hoạt" [selected]
              - option "Google Drive (Khuyên Dùng)"
              - option "S3 / R2 (Amazon / Cloudflare)"
      - generic [ref=e67]:
        - button "Thông Báo Telegram" [ref=e68]:
          - heading "Thông Báo Telegram" [level=3] [ref=e69]
          - img [ref=e70]
        - generic [ref=e72]:
          - generic [ref=e73]:
            - generic [ref=e74]: Bot Token
            - 'textbox "VD: 123456789:ABCdefGHIjklmNOPqrstuv" [ref=e75]'
          - generic [ref=e76]:
            - generic [ref=e77]: Chat ID
            - 'textbox "VD: -4029419241" [ref=e78]'
    - generic [ref=e79]:
      - button "HỦY BỎ" [ref=e80]
      - button "LƯU TRẠM NÀY" [ref=e81]:
        - img [ref=e82]
        - text: LƯU TRẠM NÀY
  - banner [ref=e86]:
    - generic [ref=e87]:
      - generic [ref=e88]:
        - img [ref=e90]
        - generic [ref=e95]:
          - heading "V-Pack Monitor" [level=1] [ref=e96]
          - paragraph [ref=e97]: Hệ thống Camera Đóng hàng E-Commerce
      - generic [ref=e98]:
        - generic [ref=e99]:
          - button "📹 Vận hành" [ref=e100]
          - button "📊 Tổng quan" [ref=e101]
        - button "v3.4.0" [ref=e102]:
          - img [ref=e103]
          - text: v3.4.0
        - generic [ref=e108]:
          - generic:
            - img
          - textbox "Tìm mã vận đơn..." [ref=e109]
        - button "E2E Admin ADMIN" [ref=e111]:
          - img [ref=e112]
          - generic [ref=e115]:
            - generic [ref=e116]: E2E Admin
            - generic [ref=e117]: ADMIN
          - img [ref=e118]
  - generic [ref=e120]:
    - generic [ref=e123]:
      - heading "Live Cameras Toàn Hệ Thống" [level=2] [ref=e125]:
        - img [ref=e126]
        - text: Live Cameras Toàn Hệ Thống
      - generic [ref=e135] [cursor=pointer]:
        - generic:
          - generic: e2e_station_1
          - generic: Sẵn sàng
        - generic [ref=e137]:
          - generic [ref=e138]: 📡
          - paragraph [ref=e139]: MediaMTX chưa khởi động
          - paragraph [ref=e140]: Live view cần MediaMTX chạy ở port 8889
    - generic [ref=e142]:
      - generic:
        - heading "Lịch sử ghi hình" [level=2]:
          - img
          - text: Lịch sử ghi hình
        - generic: 32 video
      - generic [ref=e143]:
        - combobox [ref=e144]:
          - option "Tất cả trạm" [selected]
          - option "(trạm đã xoá)"
          - option "e2e_station_1"
        - textbox [ref=e145]
        - generic [ref=e146]: →
        - textbox [ref=e147]
        - combobox [ref=e148]:
          - option "Tất cả trạng thái" [selected]
          - option "✅ READY"
          - option "🔴 RECORDING"
          - option "⏳ PROCESSING"
          - option "❌ FAILED"
        - generic [ref=e149]: 32 video
      - generic [ref=e150]:
        - generic [ref=e151] [cursor=pointer]:
          - generic [ref=e152]:
            - generic [ref=e153]:
              - heading "6934839106982" [level=3] [ref=e154]
              - generic [ref=e155]: PIP
              - generic [ref=e156]: "Trạm: Mặc định"
            - button "Xoá bản ghi lưu trữ dọn ổ đĩa" [ref=e157]:
              - img [ref=e158]
          - generic [ref=e162]: 00:15:47 22/4/2026
          - button "6934839106982_20260422_001547_PIP.mp4" [ref=e164]:
            - img [ref=e165]
            - generic [ref=e168]: 6934839106982_20260422_001547_PIP.mp4
        - generic [ref=e169] [cursor=pointer]:
          - generic [ref=e170]:
            - generic [ref=e171]:
              - heading "CR XY 00 2006001720" [level=3] [ref=e172]
              - generic [ref=e173]: PIP
              - generic [ref=e174]: "Trạm: Mặc định"
            - button "Xoá bản ghi lưu trữ dọn ổ đĩa" [ref=e175]:
              - img [ref=e176]
          - generic [ref=e180]: 00:15:29 22/4/2026
          - button "CR_XY_00_2006001720_20260422_001529_PIP.mp4" [ref=e182]:
            - img [ref=e183]
            - generic [ref=e186]: CR_XY_00_2006001720_20260422_001529_PIP.mp4
        - generic [ref=e187] [cursor=pointer]:
          - generic [ref=e188]:
            - generic [ref=e189]:
              - heading "6934839106982" [level=3] [ref=e190]
              - generic [ref=e191]: PIP
              - generic [ref=e192]: "Trạm: Mặc định"
            - button "Xoá bản ghi lưu trữ dọn ổ đĩa" [ref=e193]:
              - img [ref=e194]
          - generic [ref=e198]: 00:14:07 22/4/2026
          - button "6934839106982_20260422_001407_PIP.mp4" [ref=e200]:
            - img [ref=e201]
            - generic [ref=e204]: 6934839106982_20260422_001407_PIP.mp4
        - generic [ref=e205] [cursor=pointer]:
          - generic [ref=e206]:
            - generic [ref=e207]:
              - heading "VN264916416227I" [level=3] [ref=e208]
              - generic [ref=e209]: PIP
              - generic [ref=e210]: Lỗi
              - generic [ref=e211]: "Trạm: Mặc định"
            - button "Xoá bản ghi lưu trữ dọn ổ đĩa" [ref=e212]:
              - img [ref=e213]
          - generic [ref=e217]: 23:47:09 13/4/2026
        - generic [ref=e218] [cursor=pointer]:
          - generic [ref=e219]:
            - generic [ref=e220]:
              - heading "VN264916416227I" [level=3] [ref=e221]
              - generic [ref=e222]: PIP
              - generic [ref=e223]: Lỗi
              - generic [ref=e224]: "Trạm: Mặc định"
            - button "Xoá bản ghi lưu trữ dọn ổ đĩa" [ref=e225]:
              - img [ref=e226]
          - generic [ref=e230]: 18:49:02 12/4/2026
        - generic [ref=e231] [cursor=pointer]:
          - generic [ref=e232]:
            - generic [ref=e233]:
              - heading "VN264916416227I" [level=3] [ref=e234]
              - generic [ref=e235]: PIP
              - generic [ref=e236]: Lỗi
              - generic [ref=e237]: "Trạm: Mặc định"
            - button "Xoá bản ghi lưu trữ dọn ổ đĩa" [ref=e238]:
              - img [ref=e239]
          - generic [ref=e243]: 18:44:39 12/4/2026
        - generic [ref=e244] [cursor=pointer]:
          - generic [ref=e245]:
            - generic [ref=e246]:
              - heading "VN264916416227I" [level=3] [ref=e247]
              - generic [ref=e248]: PIP
              - generic [ref=e249]: "Trạm: Mặc định"
            - button "Xoá bản ghi lưu trữ dọn ổ đĩa" [ref=e250]:
              - img [ref=e251]
          - generic [ref=e255]: 18:29:08 12/4/2026
          - button "VN264916416227I_20260412_182908_PIP.mp4" [ref=e257]:
            - img [ref=e258]
            - generic [ref=e261]: VN264916416227I_20260412_182908_PIP.mp4
        - generic [ref=e262] [cursor=pointer]:
          - generic [ref=e263]:
            - generic [ref=e264]:
              - heading "VN264916416227I" [level=3] [ref=e265]
              - generic [ref=e266]: PIP
              - generic [ref=e267]: "Trạm: Mặc định"
            - button "Xoá bản ghi lưu trữ dọn ổ đĩa" [ref=e268]:
              - img [ref=e269]
          - generic [ref=e273]: 18:23:35 12/4/2026
          - button "VN264916416227I_20260412_182336_PIP.mp4" [ref=e275]:
            - img [ref=e276]
            - generic [ref=e279]: VN264916416227I_20260412_182336_PIP.mp4
        - generic [ref=e280] [cursor=pointer]:
          - generic [ref=e281]:
            - generic [ref=e282]:
              - heading "VN264916416227I" [level=3] [ref=e283]
              - generic [ref=e284]: PIP
              - generic [ref=e285]: "Trạm: Mặc định"
            - button "Xoá bản ghi lưu trữ dọn ổ đĩa" [ref=e286]:
              - img [ref=e287]
          - generic [ref=e291]: 18:14:44 12/4/2026
          - button "VN264916416227I_20260412_181444_PIP.mp4" [ref=e293]:
            - img [ref=e294]
            - generic [ref=e297]: VN264916416227I_20260412_181444_PIP.mp4
        - generic [ref=e298] [cursor=pointer]:
          - generic [ref=e299]:
            - generic [ref=e300]:
              - heading "VN264916416227I" [level=3] [ref=e301]
              - generic [ref=e302]: PIP
              - generic [ref=e303]: "Trạm: Mặc định"
            - button "Xoá bản ghi lưu trữ dọn ổ đĩa" [ref=e304]:
              - img [ref=e305]
          - generic [ref=e309]: 17:43:26 12/4/2026
          - button "VN264916416227I_20260412_174326_PIP.mp4" [ref=e311]:
            - img [ref=e312]
            - generic [ref=e315]: VN264916416227I_20260412_174326_PIP.mp4
        - generic [ref=e316] [cursor=pointer]:
          - generic [ref=e317]:
            - generic [ref=e318]:
              - heading "VN264916416227I" [level=3] [ref=e319]
              - generic [ref=e320]: PIP
              - generic [ref=e321]: "Trạm: Mặc định"
            - button "Xoá bản ghi lưu trữ dọn ổ đĩa" [ref=e322]:
              - img [ref=e323]
          - generic [ref=e327]: 17:35:53 12/4/2026
          - button "VN264916416227I_20260412_173553_PIP.mp4" [ref=e329]:
            - img [ref=e330]
            - generic [ref=e333]: VN264916416227I_20260412_173553_PIP.mp4
        - generic [ref=e334] [cursor=pointer]:
          - generic [ref=e335]:
            - generic [ref=e336]:
              - heading "VN264916416227I" [level=3] [ref=e337]
              - generic [ref=e338]: PIP
              - generic [ref=e339]: "Trạm: Mặc định"
            - button "Xoá bản ghi lưu trữ dọn ổ đĩa" [ref=e340]:
              - img [ref=e341]
          - generic [ref=e345]: 17:32:57 12/4/2026
          - button "VN264916416227I_20260412_173257_PIP.mp4" [ref=e347]:
            - img [ref=e348]
            - generic [ref=e351]: VN264916416227I_20260412_173257_PIP.mp4
        - generic [ref=e352] [cursor=pointer]:
          - generic [ref=e353]:
            - generic [ref=e354]:
              - heading "VN264916416227I" [level=3] [ref=e355]
              - generic [ref=e356]: PIP
              - generic [ref=e357]: "Trạm: Mặc định"
            - button "Xoá bản ghi lưu trữ dọn ổ đĩa" [ref=e358]:
              - img [ref=e359]
          - generic [ref=e363]: 17:25:58 12/4/2026
          - button "VN264916416227I_20260412_172558_PIP.mp4" [ref=e365]:
            - img [ref=e366]
            - generic [ref=e369]: VN264916416227I_20260412_172558_PIP.mp4
        - generic [ref=e370] [cursor=pointer]:
          - generic [ref=e371]:
            - generic [ref=e372]:
              - heading "VN264916416227I" [level=3] [ref=e373]
              - generic [ref=e374]: PIP
              - generic [ref=e375]: Lỗi
              - generic [ref=e376]: "Trạm: Mặc định"
            - button "Xoá bản ghi lưu trữ dọn ổ đĩa" [ref=e377]:
              - img [ref=e378]
          - generic [ref=e382]: 17:24:23 12/4/2026
        - generic [ref=e383] [cursor=pointer]:
          - generic [ref=e384]:
            - generic [ref=e385]:
              - heading "85257BJPBVD2228" [level=3] [ref=e386]
              - generic [ref=e387]: SINGLE
              - generic [ref=e388]: "Trạm: Mặc định"
            - button "Xoá bản ghi lưu trữ dọn ổ đĩa" [ref=e389]:
              - img [ref=e390]
          - generic [ref=e394]: 03:03:06 12/4/2026
          - button "85257BJPBVD2228_20260412_030306.mp4" [ref=e396]:
            - img [ref=e397]
            - generic [ref=e400]: 85257BJPBVD2228_20260412_030306.mp4
        - generic [ref=e401] [cursor=pointer]:
          - generic [ref=e402]:
            - generic [ref=e403]:
              - heading "ADASDADQE" [level=3] [ref=e404]
              - generic [ref=e405]: PIP
              - generic [ref=e406]: "Trạm: Mặc định"
            - button "Xoá bản ghi lưu trữ dọn ổ đĩa" [ref=e407]:
              - img [ref=e408]
          - generic [ref=e412]: 06:33:07 9/4/2026
          - button "ADASDADQE_20260409_063259_PIP.mp4" [ref=e414]:
            - img [ref=e415]
            - generic [ref=e418]: ADASDADQE_20260409_063259_PIP.mp4
        - generic [ref=e419] [cursor=pointer]:
          - generic [ref=e420]:
            - generic [ref=e421]:
              - heading "DASDADAD" [level=3] [ref=e422]
              - generic [ref=e423]: SINGLE
              - generic [ref=e424]: "Trạm: Mặc định"
            - button "Xoá bản ghi lưu trữ dọn ổ đĩa" [ref=e425]:
              - img [ref=e426]
          - generic [ref=e430]: 05:20:30 9/4/2026
          - button "DASDADAD_20260409_051230.mp4" [ref=e432]:
            - img [ref=e433]
            - generic [ref=e436]: DASDADAD_20260409_051230.mp4
        - generic [ref=e437] [cursor=pointer]:
          - generic [ref=e438]:
            - generic [ref=e439]:
              - heading "FGDF2423FSV32412SDFSDFSDFSDF" [level=3] [ref=e440]
              - generic [ref=e441]: SINGLE
              - generic [ref=e442]: "Trạm: Mặc định"
            - button "Xoá bản ghi lưu trữ dọn ổ đĩa" [ref=e443]:
              - img [ref=e444]
          - generic [ref=e448]: 05:11:34 9/4/2026
          - button "FGDF2423FSV32412SDFSDFSDFSDF_20260409_051020.mp4" [ref=e450]:
            - img [ref=e451]
            - generic [ref=e454]: FGDF2423FSV32412SDFSDFSDFSDF_20260409_051020.mp4
        - generic [ref=e455] [cursor=pointer]:
          - generic [ref=e456]:
            - generic [ref=e457]:
              - heading "R2SDFSDF23243423423423" [level=3] [ref=e458]
              - generic [ref=e459]: SINGLE
              - generic [ref=e460]: "Trạm: Mặc định"
            - button "Xoá bản ghi lưu trữ dọn ổ đĩa" [ref=e461]:
              - img [ref=e462]
          - generic [ref=e466]: 05:10:12 9/4/2026
          - button "R2SDFSDF23243423423423_20260409_051007.mp4" [ref=e468]:
            - img [ref=e469]
            - generic [ref=e472]: R2SDFSDF23243423423423_20260409_051007.mp4
        - generic [ref=e473] [cursor=pointer]:
          - generic [ref=e474]:
            - generic [ref=e475]:
              - heading "B5555555555555554674222222222222222222222" [level=3] [ref=e476]
              - generic [ref=e477]: SINGLE
              - generic [ref=e478]: "Trạm: Mặc định"
            - button "Xoá bản ghi lưu trữ dọn ổ đĩa" [ref=e479]:
              - img [ref=e480]
          - generic [ref=e484]: 04:53:20 9/4/2026
          - button "B5555555555555554674222222222222222222222_20260409_045107.mp4" [ref=e486]:
            - img [ref=e487]
            - generic [ref=e490]: B5555555555555554674222222222222222222222_20260409_045107.mp4
        - generic [ref=e491]:
          - button "← Trước" [disabled] [ref=e492]
          - generic [ref=e493]: Trang 1/2
          - button "Sau →" [ref=e494]
```

# Test source

```ts
  1  | import { test, expect } from './test-helpers';
  2  | 
  3  | test.describe('Settings Modal', () => {
  4  |   test('open settings, change value and save', async ({ adminPage }) => {
  5  |     // 1. Open User menu
  6  |     await adminPage.click('button:has-text("e2e_admin")');
  7  | 
  8  |     // 2. Click settings
  9  |     await adminPage.click('button:has-text("Cài đặt Trạm")');
  10 | 
  11 |     // 3. Verify Modal opened
> 12 |     await expect(adminPage.locator('h3:has-text("Cài đặt Trạm Đóng Gói")')).toBeVisible();
     |                                                                             ^ Error: expect(locator).toBeVisible() failed
  13 | 
  14 |     // 4. Fill form
  15 |     await adminPage.fill('input[placeholder="Nhập tên trạm..."]', 'e2e_station_1_updated');
  16 | 
  17 |     // 5. Save
  18 |     await adminPage.click('button:has-text("Lưu cài đặt")');
  19 | 
  20 |     // 6. Verify toast
  21 |     await expect(adminPage.locator('text=Cập nhật trạm thành công')).toBeVisible();
  22 | 
  23 |     // 7. Reset back to original to not break other tests
  24 |     await adminPage.click('button:has-text("e2e_admin")');
  25 |     await adminPage.click('button:has-text("Cài đặt Trạm")');
  26 |     await adminPage.fill('input[placeholder="Nhập tên trạm..."]', 'e2e_station_1');
  27 |     await adminPage.click('button:has-text("Lưu cài đặt")');
  28 |     await expect(adminPage.locator('text=Cập nhật trạm thành công')).toBeVisible();
  29 |   });
  30 | });
  31 | 
```