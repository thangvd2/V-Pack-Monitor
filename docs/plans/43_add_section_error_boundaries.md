# Plan 43: Add Section-Level Error Boundaries

**Ngày**: 2026-04-24
**Mức độ**: Medium — Hiện chỉ có 1 ErrorBoundary wrap toàn App, section crash = toàn UI trắng
**Loại**: Reliability improvement (frontend)

---

## Problem

Hiện `ErrorBoundary` (App.jsx:179-202) chỉ wrap App root. Khi bất kỳ section nào crash:
- SSE handler throw → toàn app trắng
- Video player crash → toàn app trắng
- Dashboard chart render error → toàn app trắng

React best practice: wrap từng risky section riêng để isolate failures.

---

## Scope

### Files to change:
- `web-ui/src/ErrorBoundary.jsx` — NEW (extract from App.jsx, make reusable)
- `web-ui/src/App.jsx` — remove ErrorBoundary class, import from new file

### Sections cần wrap:

| Section | Risk | Fallback |
|---------|------|----------|
| SSE event handler | Network error, malformed JSON | "Mất kết nối thời gian thực. Đang thử lại..." |
| VideoPlayerModal | Video codec unsupported, browser error | "Không thể phát video. Tải lại trang." |
| Dashboard charts | Chart.js render error, bad data | "Lỗi hiển thị biểu đồ. Nhấn để thử lại." |
| SystemHealth | API timeout, malformed response | "Không thể tải thông tin hệ thống." |
| AdminDashboard (live cameras) | iframe crash, MediaMTX error | "Lỗi hiển thị camera. Nhấn để thử lại." |

### ErrorBoundary component features:
- `fallback` prop — custom fallback UI per section
- `onReset` prop — optional retry callback
- `sectionName` prop — for error logging
- Wrap `componentDidCatch` to log errors (console.warn)

---

## Constraints

- ErrorBoundary class phải reusable — nhận props, không hardcode UI
- Mỗi section's fallback phải có "Thử lại" button
- SSE handler errors cần auto-reconnect (nếu plan #47 implemented)
- Không thay đổi ErrorBoundary behavior ở App root level

---

## Verification

- [ ] `npm run build` pass
- [ ] `npm run lint` pass
- [ ] Throw error in video player → only video section shows fallback, rest of UI intact
- [ ] Throw error in chart → only dashboard section shows fallback
- [ ] "Thử lại" button resets error state correctly
