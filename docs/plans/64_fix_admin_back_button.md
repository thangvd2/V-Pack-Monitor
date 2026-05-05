# Plan 64: Fix Admin Back Button Navigation

> **Status:** DONE
> **Priority:** LOW — UX bugs (2 issues)
> **Scope:** 1 file (`App.tsx`), 4 changes
> **Estimated Effort:** 10 min

---

## Bug 1: Back button ép sai tab

Khi Admin drill-down vào chi tiết 1 trạm (từ grid camera), nút back trong header luôn chuyển về tab **Vận hành** thay vì giữ nguyên tab trước đó.

### Root Cause

`App.tsx` line ~1153 — Header back button hardcode `setAdminTab('operations')`:

```typescript
// lines 1148-1159
{viewMode === 'single' && currentUser?.role === 'ADMIN' && (
  <button
    onClick={() => {
      setViewMode('grid');
      setAdminTab('operations');  // ← BUG: luôn ép về tab Vận hành
    }}
    title="Quay lại giao diện tổng quan"
  >
    ← Tổng quan
  </button>
)}
```

### Fix 1a: Xóa `setAdminTab('operations')`

Xóa dòng `setAdminTab('operations')` khỏi header back button. Sau khi fix, nút back chỉ gọi `setViewMode('grid')` — preserve tab state, consistent với nút back thứ 2 (content area, line ~1451).

```typescript
onClick={() => {
  setViewMode('grid');
  // Xóa: setAdminTab('operations');
}}
```

### Fix 1b: Đổi label nút back

Vì chỉ có thể drill-down từ tab "📹 Vận hành" (tab "📊 Tổng quan" không có `onStationClick`), nút back phải hiển thị "← Vận hành" thay vì "← Tổng quan":

**Line ~1155**: `title="Quay lại giao diện tổng quan"` → `title="Quay lại giao diện vận hành"`
**Line ~1157**: `← Tổng quan` → `← Vận hành`

---

## Bug 2: Nút dashboard toggle thừa khi Admin xem single station

Khi Admin đang ở `viewMode === 'single'` (xem 1 trạm), header hiển thị nút toggle dashboard (BarChart3 icon) với title "Quay lại giao diện chính" / "Bảng điều khiển". Nút này thừa vì Admin đã có nút back "← Vận hành" riêng.

### Root Cause

`App.tsx` lines 1187-1194 — Điều kiện hiện nút:

```typescript
{!(currentUser?.role === 'ADMIN' && viewMode === 'grid') && (
  <button
    onClick={() => setShowDashboard((prev) => !prev)}
    title={showDashboard ? 'Quay lại giao diện chính' : 'Bảng điều khiển'}
  >
    <BarChart3 className="w-5 h-5" />
  </button>
)}
```

Điều kiện `!(ADMIN && grid)` = hiện cho OPERATOR bất kỳ + **ADMIN ở single view**. Nút này chỉ cần cho OPERATOR (để toggle dashboard mini bên cạnh camera). Với ADMIN ở single view, nó là thừa và gây nhầm lẫn.

### Fix 2: Ẩn nút dashboard toggle khi ADMIN ở single view

Đổi điều kiện từ:
```typescript
{!(currentUser?.role === 'ADMIN' && viewMode === 'grid') && (
```

Sang:
```typescript
{!(currentUser?.role === 'ADMIN') && (
```

Hoặc rõ nghĩa hơn:
```typescript
{currentUser?.role !== 'ADMIN' && (
```

Giải thích: ADMIN không cần nút dashboard toggle vì:
- Ở grid view: ADMIN có 2 tab riêng (Vận hành/Tổng quan) thay thế
- Ở single view: ADMIN có nút back "← Vận hành" riêng
- Nút này chỉ dùng cho OPERATOR ở single view (toggle dashboard mini)

---

## Files Summary

| # | File | Change | Lines |
|---|------|--------|-------|
| 1a | `App.tsx` | Xóa `setAdminTab('operations')` | ~1153 |
| 1b | `App.tsx` | Đổi label "← Tổng quan" → "← Vận hành" + title | ~1155, 1157 |
| 2 | `App.tsx` | Ẩn nút BarChart3 cho ADMIN | ~1187 |

## Verification

1. `npm run build && npm run lint` pass
2. Manual test:
   - Admin ở tab "📹 Vận hành" → click camera card → drill-down → nút back hiển thị "← Vận hành" → click → quay lại tab Vận hành ✅
   - Admin ở tab "📊 Tổng quan" → (không thể drill-down từ tab này) ✅
   - Admin ở single view → KHÔNG thấy nút BarChart3 dashboard toggle ✅
   - Operator ở single view → VẪN thấy nút BarChart3 dashboard toggle ✅
