# Plan 46: API Response Models (Pydantic)

**Ngày**: 2026-04-26
**Mức độ**: Medium — Backend trả dict tự do, frontend không biết field nào tồn tại
**Loại**: Refactor (backward compatible)
**Status**: ✅ Done — PR #72 merged to dev

---

## Problem

Backend routes trả `dict` trực tiếp:
```python
return {"data": stations}
```

Frontend phải guess field names. Không có:
- Self-documenting API (phải đọc code để biết response shape)
- Response validation (field missing → frontend crash)

---

## Scope

### Files changed:
- `routes_stations.py` — StationModel, StationsResponse
- `routes_records.py` — RecordModel, RecordsResponse
- `routes_auth.py` — UserAuthModel, LoginResponse, UserFullModel, UsersResponse
- `routes_system.py` — SettingsResponse, AnalyticsTodayResponse, CpuComponent, MemoryComponent, DiskComponent, HealthResponse
- `database.py` — Added `p.station_id` to get_records_v2() query

### Response models defined:

| Endpoint | Response Shape | Response Model |
|----------|----------------|----------------|
| `GET /api/stations` | `{"data": [{id, name, ip_camera_1, ip_camera_2, safety_code?, camera_mode, camera_brand, mac_address, processing_count?}]}` | `StationsResponse` |
| `GET /api/records` | `{"records": [...], "total", "page", "limit", "total_pages", "has_more"}` | `RecordsResponse` |
| `GET /api/records/{id}/download` | File response | No change needed |
| `GET /api/settings` | `{"data": {key: value, ...}}` | `SettingsResponse` |
| `GET /api/analytics/today` | `{"data": {"total_today": N, "station_today": N}}` | `AnalyticsTodayResponse` |
| `GET /api/system/health` | `{"cpu": {...}, "memory": {...}, "disk": {...}, "uptime", "uptime_seconds"}` | `HealthResponse` |
| `POST /api/auth/login` | `{"status", "access_token", "token_type", "user": {id, username, role, full_name, must_change_password}}` | `LoginResponse` |
| `GET /api/users` | `{"data": [{id, username, role, full_name, is_active, created_at?}]}` | `UsersResponse` |
| `POST /api/scan` | Dynamic (13 return paths) | **Not modeled** — too dynamic, high risk |

### Example:
```python
class StationModel(BaseModel):
    id: int
    name: str
    ip_camera_1: str
    ip_camera_2: str
    safety_code: str | None = None
    camera_mode: str
    camera_brand: str
    mac_address: str
    processing_count: int | None = None

class StationsResponse(BaseModel):
    data: list[StationModel]
```

### FastAPI `response_model`:
```python
@app.get("/api/stations", response_model=StationsResponse, response_model_exclude_none=True)
def get_stations_api(current_user: CurrentUser):
    ...
```

---

## Constraints

- **Backward compatible** — response shape không đổi, chỉ thêm validation
- Không đổi field names (giữ snake_case cho consistency)
- `response_model_exclude_none=True` cho stations để tự động bỏ `safety_code` khi non-ADMIN
- `/api/scan` không modeled vì quá dynamic (13 return paths)
- `database.py` fix: added `p.station_id` to `get_records_v2()` base_select query

---

## Verification

- [x] `pytest tests/ -q` pass
- [x] `npm run build` pass (no frontend changes)
- [x] All API responses match their response_model
- [x] FastAPI /docs shows response schemas
- [x] Frontend không bị break
