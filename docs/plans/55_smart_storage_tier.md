# Plan 55: Smart Storage 3-Tier Video Management

**Ngày**: 2026-04-24
**Mức độ**: Low — Feature nâng cao, không urgent
**Loại**: New feature (ROADMAP #2)

---

## Problem

Video hiện lưu tại 1 nơi (`recordings/`), chỉ có auto-cleanup by days. Không có:
- Phân tầng storage (SSD nhanh → HDD archive → compressed deep archive)
- Auto-migrate video cũ sang tier rẻ hơn
- Storage dashboard theo tier
- Compressed archive tiết kiệm ~70% dung lượng

---

## Scope

### Phase 1: Storage Tier Configuration

#### Database:
- New settings: `STORAGE_TIER1_PATH` (default: `recordings/`)
- New settings: `STORAGE_TIER2_PATH` (default: empty = disabled)
- New settings: `STORAGE_TIER2_DAYS` (default: 30 — migrate after 30 days)
- New settings: `STORAGE_TIER3_ENABLED` (default: false)
- New settings: `STORAGE_TIER3_DAYS` (default: 180)

#### Backend:
- `routes_system.py` — Add settings + validation
- `database.py` — Add `storage_tier` column to `packing_video` table (TEXT: "tier1"/"tier2"/"tier3")

### Phase 2: Auto-Migration

#### Periodic task (api.py):
```python
async def _periodic_storage_migration():
    while True:
        await asyncio.sleep(86400)  # daily
        _migrate_tier1_to_tier2()   # Move files > TIER2_DAYS
        _migrate_tier2_to_tier3()   # Compress files > TIER3_DAYS
```

#### Tier 1 → Tier 2 (Move):
- Find videos older than `STORAGE_TIER2_DAYS` still in tier1
- Move file from tier1 path → tier2 path
- Update DB: `storage_tier = "tier2"`, `file_path = new_path`
- Only if tier2 path configured and accessible

#### Tier 2 → Tier 3 (Compress):
- Find videos older than `STORAGE_TIER3_DAYS` in tier2
- FFmpeg re-encode: H.264 CRF 28 (smaller file, ~70% size reduction)
- Save compressed file, delete original
- Update DB: `storage_tier = "tier3"`, `file_size = new_size`

### Phase 3: Storage Dashboard

#### Backend API:
```
GET /api/storage-stats → {
  tier1: {path, total_bytes, used_bytes, file_count},
  tier2: {path, total_bytes, used_bytes, file_count},
  tier3: {total_bytes, file_count, compression_ratio}
}
```

#### Frontend (SystemHealth.jsx or new StorageTab):
- Per-tier: disk usage bar, file count, total size
- Migration status: last run, files migrated, space saved
- Manual trigger: "Migrate Now" button

---

## Constraints

- Tier 2/3 optional — chỉ activate khi path configured
- File move phải atomic: copy → verify checksum → delete original
- Compress chạy trong thread pool (FFmpeg blocking)
- DB update SAU khi file move/convert thành công (prevent orphaned records)
- Auto-cleanup (RECORD_KEEP_DAYS) vẫn hoạt động trên tất cả tiers
- Phải handle: tier path không tồn tại / không writable → skip + log warning
- Tier migration chỉ chạy khi enabled (không auto-migrate nếu chỉ có tier1)

---

## Decision

**Khuyến nghị: KHÔNG LÀM NGAY.** Single-disk setup đang work tốt. Chỉ implement khi:
- Khách hàng có SSD + HDD riêng biệt
- Storage cost trở thành vấn đề
- Video retention > 30 ngày cần tiết kiệm space

Giữ plan này trong backlog.

---

## Verification

- [ ] Tier 1→2 migration moves files correctly
- [ ] Tier 2→3 compression reduces file size ~70%
- [ ] DB records updated with new paths and tiers
- [ ] Video playback works from all tiers
- [ ] Storage dashboard shows accurate per-tier stats
- [ ] Manual trigger works via API
- [ ] `pytest tests/ -q` pass
