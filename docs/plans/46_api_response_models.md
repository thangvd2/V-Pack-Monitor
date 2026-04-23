# Plan 46: API Response Models (Pydantic)

**Ngày**: 2026-04-24
**Mức độ**: Medium — Backend trả dict tự do, frontend không biết field nào tồn tại
**Loại**: Refactor (backward compatible)

---

## Problem

Backend routes trả `dict` trực tiếp:
```python
return {"stations": stations, "processing_counts": processing_counts}
```

Frontend phải guess field names. Không có:
- Self-documenting API (phải đọc code để biết response shape)
- Response validation (field missing → frontend crash)
- Consistent naming (snake_case backend → camelCase frontend)

---

## Scope

### Files to change:
- `web-ui/src/types/api.ts` — Frontend types (if Plan #45 done) hoặc inline JSDoc
- `routes_*.py` — Add Pydantic response models

### Response models cần define:

| Endpoint | Current | Response Model |
|----------|---------|----------------|
| `GET /api/stations` | `{"stations": [...]}` | `StationsResponse` |
| `GET /api/records` | `{"records": [...], "total": N}` | `RecordsResponse` |
| `GET /api/records/{id}/download` | File response | No change needed |
| `GET /api/settings` | `{"settings": {...}}` | `SettingsResponse` |
| `GET /api/analytics/today` | `{"total_records": N, ...}` | `AnalyticsResponse` |
| `GET /api/system/health` | `{"status": "...", ...}` | `HealthResponse` |
| `POST /api/auth/login` | `{"token": "...", "user": {...}}` | `LoginResponse` |
| `GET /api/users` | `{"users": [...]}` | `UsersResponse` |
| `POST /api/stations/{id}/scan` | `{"status": "...", ...}` | `ScanResponse` |

### Example:
```python
class StationResponse(BaseModel):
    id: int
    name: str
    ip: str | None
    brand: str | None
    camera_mode: str | None
    # ...

class StationsResponse(BaseModel):
    stations: list[StationResponse]
    processing_counts: dict[int, int]
```

### FastAPI `response_model`:
```python
@router.get("/api/stations", response_model=StationsResponse)
async def get_stations(current_user: CurrentUser):
    ...
```

---

## Constraints

- **Backward compatible** — response shape không đổi, chỉ thêm validation
- Không đổi field names (giữ snake_case cho consistency)
- Response models optional — FastAPI filter out extra fields automatically
- Nếu Plan #45 chưa làm → dùng JSDoc comments cho frontend types

---

## Verification

- [ ] `pytest tests/ -q` pass
- [ ] `npm run build` pass
- [ ] All API responses match their response_model
- [ ] FastAPI /docs shows response schemas
- [ ] Frontend không bị break
