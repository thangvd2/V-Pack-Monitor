# Plan 53: Cloud Sync Scheduler (Daily Auto-Backup)

**Ngày**: 2026-04-24
**Mức độ**: High — README advertise "Backup dữ liệu hàng ngày" nhưng chỉ có manual trigger
**Loại**: Feature completion

---

## Problem

README ghi: "☁️ Đồng Bộ Hoá Điện Toán Đám Mây (Cloud Sync): Backup dữ liệu hàng ngày lên Google Drive hoặc S3"

Thực tế:
- Cloud sync chỉ chạy khi admin bấm nút "Sync Now" (gọi `POST /api/cloud-sync`)
- Không có scheduled/periodic auto-backup
- Pattern đã có sẵn: `_periodic_audit_cleanup()` chạy mỗi 24h trong `api.py:610`

---

## Scope

### Files to change:
- `api.py` — Add `_periodic_cloud_sync()` async task
- `routes_system.py` — Add `CLOUD_SYNC_SCHEDULE` setting + toggle
- `web-ui/src/SetupModal.jsx` — Add schedule UI (time picker + enable toggle)
- `database.py` — No change (settings table already supports arbitrary keys)

### Backend implementation:

#### 1. Periodic task (api.py)
```python
async def _periodic_cloud_sync():
    """Auto cloud sync based on configured schedule."""
    while True:
        await asyncio.sleep(3600)  # check every hour
        provider = database.get_setting("CLOUD_PROVIDER")
        enabled = database.get_setting("CLOUD_SYNC_SCHEDULED")
        schedule_time = database.get_setting("CLOUD_SYNC_TIME")  # "02:00"

        if provider and provider != "NONE" and enabled == "true":
            # Check if current hour matches scheduled time
            now = datetime.now()
            scheduled_hour = int(schedule_time.split(":")[0]) if schedule_time else 2
            if now.hour == scheduled_hour and now.minute < 60:
                cloud_sync.process_cloud_sync()
```

#### 2. Settings (routes_system.py)
Add to settings model:
```python
"CLOUD_SYNC_SCHEDULED": str  # "true" / "false"
"CLOUD_SYNC_TIME": str       # "02:00" (HH:MM)
```

#### 3. Frontend UI (SetupModal.jsx)
Add to Cloud Sync section:
- Toggle: "Tự động đồng bộ hàng ngày" (switch)
- Time picker: "Giờ đồng bộ" (dropdown: 00:00 - 23:00, default 02:00)
- Display: last sync time + next scheduled sync

### Startup flow:
1. App starts → `lifespan()` creates `_periodic_cloud_sync` task
2. Task checks every hour: is provider configured? is schedule enabled?
3. If current hour matches scheduled time → trigger `process_cloud_sync()`
4. Telegram notification on success/failure (already implemented)

---

## Constraints

- Reuse `_periodic_audit_cleanup` pattern exactly (asyncio.create_task)
- Only run if CLOUD_PROVIDER != "NONE" AND CLOUD_SYNC_SCHEDULED == "true"
- Default: disabled (CLOUD_SYNC_SCHEDULED = "false"), user must opt-in
- Don't re-run if already synced this hour (add _last_sync_hour guard)
- Cancel task on shutdown (same pattern as cleanup_task)
- Process in thread (cloud_sync uses synchronous I/O) — use `asyncio.to_thread()`

---

## Verification

- [ ] `pytest tests/ -q` pass
- [ ] Manual trigger `POST /api/cloud-sync` still works
- [ ] Set CLOUD_SYNC_SCHEDULED=true, CLOUD_SYNC_TIME=next hour → sync runs
- [ ] Set CLOUD_SYNC_SCHEDULED=false → no auto sync
- [ ] Telegram notification sent after auto sync
- [ ] Frontend shows schedule toggle + time picker
- [ ] No double-sync within same hour
