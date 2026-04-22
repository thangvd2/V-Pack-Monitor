# Plan: Admin UI Revamp

## Status: READY FOR DETAILED PLAN

## Problem

Admin login → auto-select station đầu tiên (App.jsx line 537-538) → hiển thị layout giống OPERATOR. Không có overview toàn hệ thống. Orphaned records (station đã xoá) hiển thị "Mặc định" mà không filter được.

## Architecture Decisions (confirmed)

| Decision | Choice | Reason |
|----------|--------|--------|
| Component | **AdminDashboard.jsx mới** | Sạch, không conflict operator flow. App.jsx đã 2100 dòng. |
| Grid view | **Luôn hiện** cho admin | Bất kể số stations (1 station = 1 camera card) |
| Priority | **Cả 2 cùng lúc** | Dashboard + Records all-stations liên quan chặt |

## Layout

```
┌─────────────────────────────────────────────────────────┐
│  V-Pack Monitor    [Tổng quan] [Trạm] [Cài đặt] [👤]   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  📊 TỔNG QUAN HỆ THỐNG                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │ 3 Trạm   │ │ 156 Video│ │ 42 GB    │ │ 99.2%    │   │
│  │ Hoạt động│ │ Hôm nay  │ │ Đã dùng  │ │ Tỉ lệ OK │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
│                                                         │
│  📹 LIVE CAMERAS (luôn hiện, bất kể số stations)        │
│  ┌─────────────────┐ ┌─────────────────┐               │
│  │ Trạm: Số 1      │ │ Trạm: Số 2      │               │
│  │ [live view]     │ │ [live view]     │               │
│  └─────────────────┘ └─────────────────┘               │
│                                                         │
│  📋 TẤT CẢ PLAYBACK (toàn hệ thống)                     │
│  [Search] [Date range] [Status] [Trạm: Tất cả ▼]       │
│  ┌───────────────────────────────────────────────┐      │
│  │ SPX123  │ Số 1  │ PIP  │ 15:30 │ ✅ READY  │▶️🗑️│      │
│  │ SPX456  │ Số 2  │ SGL  │ 15:25 │ ✅ READY  │▶️🗑️│      │
│  │ SPX789  │ (xoá) │ PIP  │ 14:10 │ ✅ READY  │▶️🗑️│      │
│  └───────────────────────────────────────────────┘      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Key Changes

| Hiện tại | Đề xuất |
|----------|---------|
| Admin login → auto-select station đầu tiên | Admin login → AdminDashboard.jsx (overview) |
| Records chỉ filter theo 1 station | Records filter "Tất cả trạm" mặc định cho admin |
| Orphaned records hiển thị "Mặc định" | Hiển thị "(trạm đã xoá)" + filter được |
| Grid view ẩn khi < 2 stations | Luôn hiện live cameras overview cho admin |
| ~~Cleanup options: 3/7/15/30 ngày~~ | ~~Thêm: 60/90/150/365/Ngừng xoá~~ → DONE ✅ |

## Codebase Analysis

### Frontend Branch Points (19 total — App.jsx)

Key points that need change for admin:

| # | Line | What | Change needed |
|---|------|------|---------------|
| 1 | 327-328 | Login → `setStationAssigned(true)` | Render AdminDashboard instead |
| 2 | 537-538 | `setActiveStationId(stations[0].id)` | Skip for admin, let dashboard handle |
| 3 | 1041 | Station selection gate | Admin → AdminDashboard, not gate |
| 4 | 1386 | Grid toggle `stations >= 2 && ADMIN` | AdminDashboard always shows cameras |
| 5 | 1645 | "Tổng quan" button | Navigate to AdminDashboard instead |
| 6 | 659 | `fetchRecords(station_id)` | Admin default: `station_id=None` |

### Backend — Already Built ✅

| Endpoint | Station-id=None? | Note |
|----------|-------------------|------|
| `GET /api/records` | ✅ Yes | All-stations records with FTS5 search |
| `GET /api/analytics/hourly` | ✅ Optional | Aggregated when omitted |
| `GET /api/analytics/trend` | ✅ No param needed | Already system-wide |
| `GET /api/analytics/stations-comparison` | ✅ No param | Per-station counts |
| `GET /api/system/health` | ✅ Admin-only | CPU/RAM/Disk |
| `GET /api/system/network-info` | ✅ Admin-only | Camera reachability |
| `GET /api/storage/info` | ✅ Yes | Storage size + file count |

### Backend — Gaps ❌

| Gap | Impact | Fix |
|-----|--------|-----|
| `/api/analytics/today` requires `station_id` | Admin dashboard needs system-wide count | Make `station_id` optional, return only `total_today` |
| Orphaned records show "Mặc định" | Admin needs to know which records belong to deleted stations | Change label + filter in frontend (backend returns `station_name` from JOIN) |
| No status breakdown aggregation | Dashboard stat cards need READY/FAILED counts | Add new endpoint or extend `/analytics/today` |

### Existing Components to Reuse

| Component | What it has | Reuse in AdminDashboard? |
|-----------|-------------|-------------------------|
| `Dashboard.jsx` | BarChart, LineChart, PieChart (recharts), stat cards | ✅ Reuse chart section |
| `SystemHealth.jsx` | CPU/RAM/Disk/FFmpeg/Camera status, auto-refresh 5s | ✅ Reuse health section |
| `VideoPlayerModal.jsx` | Video playback with download/snapshot | ✅ No change needed |

## Scope

### IN Scope
- **AdminDashboard.jsx**: New component with overview stats + live cameras + all-stations records
- **App.jsx**: Route admin to AdminDashboard instead of auto-selecting station
- **Records filter**: "Tất cả trạm" dropdown + orphaned record label
- **Grid view**: Always show for admin in AdminDashboard (even 1 station)
- **Backend**: Make `/api/analytics/today` station_id optional
- **Operator flow**: UNCHANGED

### OUT of Scope
- New backend endpoints (use existing ones)
- Operator UI changes
- New DB columns
- Analytics redesign (reuse Dashboard.jsx)

## Files to Change

### New
- `web-ui/src/AdminDashboard.jsx` — Admin landing page

### Modified
- `web-ui/src/App.jsx` — Admin routing, records filter default
- `routes_system.py` — `/api/analytics/today` make station_id optional

### Unchanged
- `database.py` — `get_records_v2()` already supports `station_id=None`
- `Dashboard.jsx` — Reused as sub-section
- `SystemHealth.jsx` — Reused as sub-section
- `VideoPlayerModal.jsx` — No change
- All operator flow — No change
