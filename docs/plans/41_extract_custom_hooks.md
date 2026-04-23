# Plan 41: Extract Custom Hooks from App.jsx

**Ngày**: 2026-04-24
**Mức độ**: High — App.jsx 2238 lines, 60 useState, 11 refs, khó maintain/debug/test
**Loại**: Refactor (no behavior change)

---

## Problem

App.jsx là một "mega-component" duy nhất chứa toàn bộ logic:
- 60+ `useState` hooks
- 11 `useRef` + useEffect sync pairs
- SSE event handling (3 event types, 140+ lines)
- Auth flow (login/logout/token restore)
- Records fetching + filtering + pagination
- Toast notifications + confirm dialogs
- Barcode scanner listener
- Station polling + heartbeat

File này khó:
- **Debug**: Scroll 2000+ lines để tìm bug
- **Test**: Không thể unit test hook logic riêng biệt
- **Reuse**: Logic SSE, toast, auth bị lock trong 1 component
- **Review**: PR thay đổi App.jsx rất khó review

---

## Scope

### Hooks cần extract (theo dependency order):

| # | Hook | Extract từ | Lines ~ | Dependencies |
|---|------|------------|---------|-------------|
| 1 | `useAuth` | Login, logout, token restore, interceptor, role checks | ~120 | axios, API_BASE |
| 2 | `useSSE` | EventSource setup, event handlers, cleanup | ~150 | activeStationId, isGlobalSSE |
| 3 | `useRecords` | fetchRecords, filters, pagination, AbortController | ~80 | API_BASE, searchTerm, activeStationId |
| 4 | `useToast` | showToast, toastTimeoutRef, TOAST_DURATIONS | ~30 | None |
| 5 | `useConfirmDialog` | showConfirmDialog, confirmDialog state | ~25 | None |
| 6 | `useBarcodeScanner` | Barcode listener, buffer timeout, scan handler | ~60 | packingStatusRef |

### Files to change:
- `web-ui/src/hooks/useAuth.js` — NEW
- `web-ui/src/hooks/useSSE.js` — NEW
- `web-ui/src/hooks/useRecords.js` — NEW
- `web-ui/src/hooks/useToast.js` — NEW
- `web-ui/src/hooks/useConfirmDialog.js` — NEW
- `web-ui/src/hooks/useBarcodeScanner.js` — NEW
- `web-ui/src/hooks/index.js` — barrel export
- `web-ui/src/App.jsx` — import hooks, remove extracted logic

---

## Constraints

- **NO behavior change** — pure refactor
- App.jsx nên còn ~1200-1400 lines sau refactor (render logic + state declaration)
- Mỗi hook phải standalone — không import other custom hooks (trừ useToast trong useSSE nếu cần)
- Tất cả refs cần đi cùng hook sở hữu nó
- SSE hook cần nhận callbacks parameter (onRecordingStart, onRecordingStop, etc.)

---

## Verification

- [ ] `npm run build` pass
- [ ] `npm run lint` pass
- [ ] Operator flow unchanged: scan START → RECORDING → STOP → PROCESSING → READY
- [ ] Admin flow unchanged: grid view, tab switch, card click, records filter
- [ ] SSE events still update UI in real-time
- [ ] Toast notifications still appear
- [ ] Barcode scanner still works
- [ ] Auth flow: login, logout, 401 auto-logout, token restore all work
