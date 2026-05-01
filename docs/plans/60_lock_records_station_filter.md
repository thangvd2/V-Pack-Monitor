# Plan 60: Lock Records Station Filter in Single View

**Ngày**: 2026-04-25
**Mức độ**: Low — UX improvement
**Loại**: Frontend fix

---

**Status**: Done — PR #68 merged to dev

## Problem

Khi admin click vào station card → chuyển sang single view, dropdown lọc trạm trong "Lịch sử ghi hình" vẫn changeable. Admin có thể đổi filter sang trạm khác → records hiển thị sai với trạm đang xem live.

## Scope

### File to change: `web-ui/src/App.jsx`

### Current code (line 1637-1657):

```jsx
{currentUser?.role === 'ADMIN' && (
  <select
    value={activeStationId || ''}
    onChange={(e) => {
      const val = e.target.value;
      setActiveStationId(val === '' || val === 'orphaned' ? val : Number(val));
    }}
    className="bg-white/10 text-white text-xs rounded px-2 py-1 border border-white/20 focus:outline-none focus:border-blue-400"
    style={{ colorScheme: 'dark' }}
  >
    ...
  </select>
)}
```

### Fix:

1. **Disable dropdown khi ở single view** (`viewMode !== 'grid'`):
   - Thêm `disabled={viewMode !== 'grid'}`
   - Thêm disabled styling: `disabled:opacity-50 disabled:cursor-not-allowed`

2. **Dropdown vẫn hoạt động bình thường trong grid view** (admin tab Operations) — admin vẫn filter tất cả trạm

### Code change:

```jsx
{currentUser?.role === 'ADMIN' && (
  <select
    value={activeStationId || ''}
    onChange={(e) => {
      const val = e.target.value;
      setActiveStationId(val === '' || val === 'orphaned' ? val : Number(val));
    }}
    disabled={viewMode !== 'grid'}
    className="bg-white/10 text-white text-xs rounded px-2 py-1 border border-white/20 focus:outline-none focus:border-blue-400 disabled:opacity-50 disabled:cursor-not-allowed"
    style={{ colorScheme: 'dark' }}
  >
    ...
  </select>
)}
```

---

## Behavior Matrix

| View | Dropdown state | Giá trị | User action |
|------|---------------|---------|-------------|
| Grid (Operations tab) | ✅ Enabled | Tùy chọn | Có thể đổi filter |
| Single view (admin click station) | 🔒 Disabled | Station đang xem | Không đổi được |
| Operator (luôn single view) | 🔒 Disabled | Station đang làm | Không đổi được |

---

## Constraints

- Chỉ thêm `disabled` prop + styling, không thay đổi logic
- Operator luôn ở single view → dropdown luôn disabled (đúng behavior)
- Records fetch logic KHÔNG thay đổi — vẫn dùng `activeStationId`

---

## Verification

- [ ] `npm run build` pass
- [ ] `npm run lint` pass
- [ ] Admin grid view → dropdown enabled, đổi được trạm
- [ ] Admin click station → single view → dropdown disabled, grayed out, đúng tên trạm
- [ ] Operator single view → dropdown disabled
