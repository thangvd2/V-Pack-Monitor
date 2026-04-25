# Plan 61: Fix 422 Errors When Viewing Orphaned Records

**Ngày**: 2026-04-25
**Mức độ**: Medium — API errors khi admin chọn "(trạm đã xóa)" filter
**Loại**: Bug fix (frontend)

---

**Status**: Done — PR #69 merged to dev

## Problem

Khi admin chọn option "(trạm đã xóa)" trong records filter, `activeStationId` được set thành string `'orphaned'`. Giá trị này được pass cho các API endpoints expect `station_id: int | None` → 422 Unprocessable Content.

```
GET /api/reconnect-status?station_id=orphaned  → 422
GET /api/status?station_id=orphaned             → 422
GET /api/analytics/today?station_id=orphaned    → 422
GET /api/records?orphaned=true&limit=20          → 200 OK (records endpoint handled correctly)
```

## Root Cause

`activeStationId` có thể là `null`, `number`, `''`, hoặc `'orphaned'`. Khi `'orphaned'`:
- Line 335: `if (activeStationId)` → truthy → proceeds
- Line 336: `fetchStatus('orphaned')` → API call với string thay vì int
- Line 339: `fetchAnalytics('orphaned' || '')` → `'orphaned'` truthy → pass string
- Line 344: `if (!activeStationId)` → falsy → proceeds to reconnect polling
- Line 350: `station_id=${activeStationId}` → pass `'orphaned'` string

## Scope

### File to change: `web-ui/src/App.jsx`

### Fix: Guard tất cả call sites không accept `'orphaned'`

#### 1. useEffect fetch status + analytics (line 334-341)

```javascript
// BEFORE:
useEffect(() => {
    if (activeStationId) {
      fetchStatus(activeStationId);
    }
    if (currentUser) {
      fetchAnalytics(activeStationId || '');
    }
}, [activeStationId, currentUser]);

// AFTER:
useEffect(() => {
    // Only fetch status for real station IDs (number), not 'orphaned' or ''
    if (activeStationId && activeStationId !== 'orphaned') {
      fetchStatus(activeStationId);
    }
    if (currentUser) {
      // Analytics: pass station ID only for real stations
      const sid = (activeStationId && activeStationId !== 'orphaned') ? activeStationId : '';
      fetchAnalytics(sid);
    }
}, [activeStationId, currentUser]);
```

#### 2. useEffect reconnect polling (line 343-374)

```javascript
// BEFORE:
useEffect(() => {
    if (!activeStationId) return;
    ...

// AFTER:
useEffect(() => {
    if (!activeStationId || activeStationId === 'orphaned') return;
    ...
```

### Behavior sau fix:

| `activeStationId` | fetchStatus | fetchAnalytics | fetchReconnect |
|-------------------|-------------|----------------|----------------|
| `null` | Skip | fetch all | Skip |
| `''` (Tất cả trạm) | Skip | fetch all | Skip |
| `37` (station ID) | ✅ fetch | ✅ fetch by station | ✅ poll |
| `'orphaned'` | Skip | fetch all | Skip |

---

## Constraints

- Records endpoint (`/api/records?orphaned=true`) đã hoạt động đúng — không cần sửa
- Không thay đổi backend — chỉ fix frontend guards
- `'orphaned'` chỉ xuất hiện khi ADMIN chọn filter, operator không thấy option này

---

## Verification

- [ ] `npm run build` pass
- [ ] `npm run lint` pass
- [ ] Admin chọn "(trạm đã xóa)" → không có 422 errors trong console/logs
- [ ] Admin chọn station bình thường → status, analytics, reconnect vẫn hoạt động
- [ ] Admin chọn "Tất cả trạm" → analytics fetch all stations
