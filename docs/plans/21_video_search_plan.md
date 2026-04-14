# Plan #21: Video Search Nâng Cao — Pagination, FTS5, Date Range Filter

**Created:** 2026-04-14
**Status:** PLANNING
**Priority:** P1 (UX Critical)

---

## Mục tiêu

Nâng cấp hệ thống tìm kiếm và liệt kê video records từ trạng thái hiện tại (LIMIT 100 cứng, LIKE search, không filter) lên production-grade với:
1. **Pagination** — duyệt tất cả records, không giới hạn 100
2. **FTS5 Full-Text Search** — tìm waybill_code nhanh (thay thế LIKE '%query%')
3. **Date Range Filter** — lọc theo khoảng thời gian (từ → đến)
4. **Status Filter** — lọc theo trạng thái (READY, RECORDING, PROCESSING, FAILED)
5. **Sorting** — sắp xếp theo ngày, trạm, trạng thái

---

## Phân tích hiện trạng

### Database (`database.py:344-362`)

```python
def get_records(search="", station_id=None):
    query = "SELECT ... FROM packing_video p LEFT JOIN stations s ... WHERE 1=1"
    if search:
        query += " AND p.waybill_code LIKE ?"  # Full table scan
        params.append(f"%{search}%")
    else:
        if station_id:
            query += " AND p.station_id = ?"
    query += " ORDER BY p.id DESC LIMIT 100"  # Hard limit, no offset
```

### API (`api.py:1314-1331`)

```python
@app.get("/api/records")
def get_records(current_user: CurrentUser, station_id: int = None, search: str = ""):
    # Chỉ nhận station_id + search
    # Trả về {"data": [...]} — không có total, page, has_more
```

### Frontend (`App.jsx:461-473, 1536-1654`)

```javascript
// Fetch — không gửi page/limit/date
const res = await axios.get(`${API_BASE}/api/records?search=${query}&station_id=${sid}`);

// "Pagination" = slice(0, 3) + show all toggle
{(showAllRecords ? records : records.slice(0, 3)).map(...)}
```

### Vấn đề hiện tại

| Vấn đề | Chi tiết |
|---|---|
| **LIMIT 100 cứng** | Không duyệt được records cũ hơn |
| **LIKE '%query%'** | Full table scan, chậm khi DB lớn |
| **Không có index** | `packing_video` không có index nào |
| **Không filter ngày** | Không tìm được "video tuần trước" |
| **Không filter status** | Không lọc được video lỗi |
| **Search override station** | Khi search, station_id bị bỏ qua hoàn toàn |
| **Không có total count** | Frontend không biết tổng bao nhiêu records |
| **SSE refetch toàn bộ** | Mỗi video_status event refetch lại cả list |

---

## Kiến trúc mới

### 1. Database Schema Changes

#### A. Thêm indexes cho `packing_video`

```sql
-- Index cho date range queries (phổ biến nhất)
CREATE INDEX IF NOT EXISTS idx_pv_recorded_at ON packing_video(recorded_at DESC);

-- Index cho station filter
CREATE INDEX IF NOT EXISTS idx_pv_station_id ON packing_video(station_id);

-- Index cho status filter
CREATE INDEX IF NOT EXISTS idx_pv_status ON packing_video(status);

-- Composite index cho query phổ biến: station + date
CREATE INDEX IF NOT EXISTS idx_pv_station_date ON packing_video(station_id, recorded_at DESC);
```

#### B. FTS5 Virtual Table (external content)

```sql
-- FTS5 bảng ảo, liên kết với packing_video qua rowid
CREATE VIRTUAL TABLE IF NOT EXISTS packing_video_fts USING fts5(
    waybill_code,
    content='packing_video',
    content_rowid='id',
    tokenize='unicode61'  -- Hỗ trợ ký tự đặc biệt, không cần porter stemmer cho mã vạch
);
```

#### C. Triggers auto-sync FTS5

```sql
-- INSERT trigger
CREATE TRIGGER IF NOT EXISTS packing_video_fts_insert AFTER INSERT ON packing_video BEGIN
    INSERT INTO packing_video_fts(rowid, waybill_code) VALUES (new.id, new.waybill_code);
END;

-- UPDATE trigger
CREATE TRIGGER IF NOT EXISTS packing_video_fts_update AFTER UPDATE ON packing_video BEGIN
    INSERT INTO packing_video_fts(packing_video_fts, rowid, waybill_code)
        VALUES ('delete', old.id, old.waybill_code);
    INSERT INTO packing_video_fts(rowid, waybill_code) VALUES (new.id, new.waybill_code);
END;

-- DELETE trigger
CREATE TRIGGER IF NOT EXISTS packing_video_fts_delete AFTER DELETE ON packing_video BEGIN
    INSERT INTO packing_video_fts(packing_video_fts, rowid, waybill_code)
        VALUES ('delete', old.id, old.waybill_code);
END;
```

**Lưu ý về tokenizer:**
- `unicode61` — phù hợp cho mã vạch (VD: `SPXVN123456789`, `GHN987654321`)
- Mã vạch không cần stemming (porter) vì chúng là mã định danh, không phải ngôn ngữ tự nhiên
- FTS5 match mặc định là token-based, tìm `SPXVN` sẽ match `SPXVN123456789`

### 2. New Database Function: `get_records_v2()`

```python
def get_records_v2(
    search: str = "",
    station_id: int | None = None,
    status: str | None = None,
    date_from: str | None = None,     # "2026-04-01" format
    date_to: str | None = None,       # "2026-04-14" format
    page: int = 1,
    limit: int = 20,
    sort_by: str = "recorded_at",     # recorded_at | waybill_code | station_name | status
    sort_order: str = "desc",         # asc | desc
) -> dict:
    """
    Returns: {
        "records": [...],
        "total": int,
        "page": int,
        "limit": int,
        "total_pages": int,
        "has_more": bool
    }
    """
```

#### Query Strategy

**Khi có search term → dùng FTS5:**
```sql
-- Count query (cho pagination metadata)
SELECT COUNT(*)
FROM packing_video p
JOIN packing_video_fts fts ON fts.rowid = p.id
WHERE fts.waybill_code MATCH ?
  AND (:station_id IS NULL OR p.station_id = :station_id)
  AND (:status IS NULL OR p.status = :status)
  AND (:date_from IS NULL OR date(p.recorded_at) >= :date_from)
  AND (:date_to IS NULL OR date(p.recorded_at) <= :date_to);

-- Data query (với pagination)
SELECT p.id, p.waybill_code, p.video_paths, p.record_mode, p.recorded_at,
       s.name AS station_name, p.status
FROM packing_video p
JOIN packing_video_fts fts ON fts.rowid = p.id
LEFT JOIN stations s ON p.station_id = s.id
WHERE fts.waybill_code MATCH ?
  AND (:station_id IS NULL OR p.station_id = :station_id)
  AND (:status IS NULL OR p.status = :status)
  AND (:date_from IS NULL OR date(p.recorded_at) >= :date_from)
  AND (:date_to IS NULL OR date(p.recorded_at) <= :date_to)
ORDER BY :sort_by :sort_order
LIMIT :limit OFFSET :offset;
```

**Khi không có search term → dùng regular query (có index):**
```sql
-- Tương tự nhưng không JOIN FTS, dùng index trực tiếp
SELECT ...
FROM packing_video p LEFT JOIN stations s ON p.station_id = s.id
WHERE 1=1
  AND (:station_id IS NULL OR p.station_id = :station_id)
  AND (:status IS NULL OR p.status = :status)
  AND (:date_from IS NULL OR date(p.recorded_at) >= :date_from)
  AND (:date_to IS NULL OR date(p.recorded_at) <= :date_to)
ORDER BY :sort_by :sort_order
LIMIT :limit OFFSET :offset;
```

#### Pagination Details

- **Offset-based** (đơn giản, đủ cho use case này — không phải infinite scroll)
- Default: `page=1, limit=20`
- Max limit: 100 (ngăn abuse)
- Return: `total_pages = ceil(total / limit)`, `has_more = page < total_pages`

#### Sort Whitelist

```python
SORT_COLUMNS = {
    "recorded_at": "p.recorded_at",
    "waybill_code": "p.waybill_code",
    "station_name": "s.name",
    "status": "p.status",
}
# Không cho sort theo column tùy ý — chống SQL injection
```

### 3. API Endpoint Update

```python
@app.get("/api/records")
def get_records(
    current_user: CurrentUser,
    station_id: int | None = None,
    search: str = "",
    status: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    page: int = 1,
    limit: int = 20,
    sort_by: str = "recorded_at",
    sort_order: str = "desc",
):
    result = database.get_records_v2(
        search=search,
        station_id=station_id,
        status=status,
        date_from=date_from,
        date_to=date_to,
        page=page,
        limit=min(limit, 100),
        sort_by=sort_by,
        sort_order=sort_order,
    )
    # Transform video_paths từ string → list
    for r in result["records"]:
        r["video_paths"] = [p for p in r["video_paths"].split(",") if p] if r["video_paths"] else []
    return result
```

**Response format mới:**
```json
{
  "records": [...],
  "total": 1542,
  "page": 1,
  "limit": 20,
  "total_pages": 78,
  "has_more": true
}
```

### 4. Frontend Changes

#### A. State additions (`App.jsx`)

```javascript
const [recordsPage, setRecordsPage] = useState(1);
const [recordsTotal, setRecordsTotal] = useState(0);
const [recordsTotalPages, setRecordsTotalPages] = useState(0);
const [dateFrom, setDateFrom] = useState('');
const [dateTo, setDateTo] = useState('');
const [statusFilter, setStatusFilter] = useState('');
```

#### B. Updated fetchRecords

```javascript
const fetchRecords = async (query = '', sid = activeStationId, page = 1) => {
    try {
        setLoading(true);
        const params = new URLSearchParams();
        if (query) params.set('search', query);
        if (sid) params.set('station_id', sid);
        if (page > 1) params.set('page', page);
        if (dateFrom) params.set('date_from', dateFrom);
        if (dateTo) params.set('date_to', dateTo);
        if (statusFilter) params.set('status', statusFilter);

        const res = await axios.get(`${API_BASE}/api/records?${params}`);
        setRecords(res.data.records);
        setRecordsTotal(res.data.total);
        setRecordsTotalPages(res.data.total_pages);
        setRecordsPage(res.data.page);
    } catch (err) {
        console.error(err);
    } finally {
        setLoading(false);
    }
};
```

#### C. UI Components

**Filter Bar** (thêm phía trên danh sách records):
```
[Tìm mã vận đơn...] [Status ▼] [Từ: 📅] [Đến: 📅] [Tìm]
```

**Pagination** (thay thế "Xem thêm" / "Thu gọn"):
```
[← Trước]  Trang 1/78 (1542 records)  [Sau →]
```

**Record count badge** (cập nhật):
```javascript
<div className="px-3 py-1 bg-white/10 rounded-full text-xs">
    {recordsTotal} videos  {/* Hiện tổng thay vì records.length */}
</div>
```

---

## Files Cần Sửa

| File | Thay đổi | Chi tiết |
|---|---|---|
| `database.py` | Schema migration | Thêm indexes + FTS5 virtual table + triggers trong `init_db()` |
| `database.py` | New function | `get_records_v2()` với pagination, FTS5, date range, status |
| `database.py` | Backfill | `_rebuild_fts_index()` — populate FTS5 từ existing records |
| `api.py` | Update endpoint | `GET /api/records` — thêm params: page, limit, date_from, date_to, status, sort_by, sort_order |
| `api.py` | Update SSE handler | SSE refetch chỉ refetch page hiện tại, không reset |
| `web-ui/src/App.jsx` | Filter UI | Date picker, status dropdown, sort controls |
| `web-ui/src/App.jsx` | Pagination UI | Page controls, total count, page size |
| `web-ui/src/App.jsx` | State management | Thêm page, dateFrom, dateTo, statusFilter states |
| `tests/test_database.py` | New tests | Test get_records_v2 pagination, FTS5, date range |
| `tests/test_api_routes.py` | New tests | Test updated /api/records endpoint params |

---

## Phased Implementation

### Phase 1: Database Foundation — Indexes + FTS5
**Thời gian ước tính:** 30 phút

| # | Task | Chi tiết |
|---|---|---|
| 1 | Thêm indexes vào `init_db()` | 4 indexes: recorded_at, station_id, status, composite |
| 2 | Thêm FTS5 virtual table vào `init_db()` | `packing_video_fts` với external content |
| 3 | Thêm triggers vào `init_db()` | INSERT, UPDATE, DELETE triggers |
| 4 | Thêm `_rebuild_fts_index()` | Populate FTS5 từ existing records (chạy 1 lần) |
| 5 | Test migration trên DB hiện có | Verify indexes tạo, FTS5 populate đúng |

### Phase 2: Backend — `get_records_v2()` + API Update
**Thời gian ước tính:** 45 phút

| # | Task | Chi tiết |
|---|---|---|
| 6 | Implement `get_records_v2()` | FTS5 search + date range + status + pagination + sort |
| 7 | Update `GET /api/records` | Thêm params mới, return pagination metadata |
| 8 | Giữ backward compatibility | `get_records()` cũ vẫn dùng cho internal (pending, export) |
| 9 | Update SSE refetch logic | SSE event chỉ refetch page hiện tại |
| 10 | Update `get_records_for_export()` | Thêm date range support (nâng cấp CSV export) |

### Phase 3: Frontend — Filter UI + Pagination
**Thời gian ước tính:** 60 phút

| # | Task | Chi tiết |
|---|---|---|
| 11 | Thêm filter states | page, dateFrom, dateTo, statusFilter |
| 12 | Cập nhật `fetchRecords()` | Gửi params mới, xử lý pagination response |
| 13 | Filter bar UI | Date picker, status dropdown, clear filters button |
| 14 | Pagination component | Prev/Next buttons, page info, total count |
| 15 | Xóa showAllRecords logic | Thay bằng pagination thật |
| 16 | Debounce search | Throttle fetch khi gõ search term |
| 17 | URL params sync | Push filter state vào URL params (shareable links) |

### Phase 4: Unit Tests
**Thời gian ước tính:** 30 phút

| # | Task | Chi tiết |
|---|---|---|
| 18 | Test indexes + FTS5 creation | Verify schema migration |
| 19 | Test `get_records_v2()` pagination | Page 1, page 2, last page, beyond total |
| 20 | Test FTS5 search | Exact match, prefix match, no match |
| 21 | Test date range filter | From only, to only, both, invalid date |
| 22 | Test status filter | READY, RECORDING, PROCESSING, FAILED |
| 23 | Test combined filters | Search + date + station + status cùng lúc |
| 24 | Test API endpoint | Verify response format, params validation |
| 25 | Test sort | Asc/desc, each sort column, invalid column rejected |

---

## Edge Cases & Considerations

### FTS5 vs LIKE Migration

| Tình huống | LIKE (cũ) | FTS5 (mới) | Ghi chú |
|---|---|---|---|
| Tìm `SPXVN123` | `%SPXVN123%` → scan all | `MATCH 'SPXVN123'` → index | FTS5 nhanh hơn 10-100x |
| Tìm `123` | `%123%` → tìm mọi nơi | `MATCH '123'` → token-based | FTS5 chỉ match token chứa `123` |
| Tìm khoảng trắng | `%ABC DEF%` | `MATCH 'ABC DEF'` = AND | Khác behavior — cần document |
| Ký tự đặc biệt | OK | Cần escape `"` `*` `(` `)` | FTS5 query escaping |

**Quyết định:** Khi search term chứa ký tự đặc biệt FTS5, fallback sang LIKE query. Hoặc dùng `unicode61` tokenizer + escape special chars.

### Date Format

- API nhận: `"2026-04-14"` (ISO date string)
- DB stored: `CURRENT_TIMESTAMP` (UTC `2026-04-14 02:25:37`)
- Filter: `date(p.recorded_at, 'localtime') >= ?` — convert UTC sang local trước khi so sánh
- **Lưu ý:** Bug #8 (Plan #15) đã convert sang UTC storage, nên cần `localtime` khi filter

### SSE Refetch Strategy

Hiện tại: mỗi `video_status` SSE event → `fetchRecords()` refetch toàn bộ.
Mới: SSE event chỉ refetch **page 1** (record mới nhất sẽ hiện ở đầu), hoặc chỉ update record cụ thể trong list.

```javascript
// SSE handler — chỉ refetch nếu record mới có thể xuất hiện ở page hiện tại
case "video_status":
    if (data.status === "READY" && recordsPage === 1) {
        fetchRecords(searchTermRef.current, activeStationId, 1);
    }
    break;
```

### Backward Compatibility

- `get_records()` cũ được giữ lại — dùng cho `get_pending_records()`, `_recover_pending_records()`, internal logic
- `get_records_v2()` là function mới cho API endpoint
- `get_records_for_export()` giữ nguyên (không cần pagination cho CSV export)

---

## Success Criteria

- [ ] Tất cả records có thể duyệt qua pagination (không giới hạn 100)
- [ ] FTS5 search nhanh hơn LIKE 10x trên DB 10,000+ records
- [ ] Date range filter hoạt động chính xác (xét timezone)
- [ ] Status filter hoạt động
- [ ] Frontend pagination UI responsive (mobile + desktop)
- [ ] SSE events không gây full refetch
- [ ] Migration an toàn trên DB hiện có (indexes + FTS5 backfill)
- [ ] Tất cả tests pass
- [ ] `npm run build` thành công
- [ ] Backward compatible — API cũ vẫn hoạt động

---

## Performance Benchmarks (Target)

| Query | Records | LIKE (cũ) | FTS5 + Index (mới) |
|---|---|---|---|
| Search waybill | 10,000 | ~200ms (scan) | ~5ms (index) |
| Date range 1 week | 10,000 | ~150ms (scan) | ~10ms (index) |
| Paginated page 1 | 10,000 | ~50ms | ~5ms |
| Paginated page 50 | 10,000 | N/A (blocked) | ~15ms |
