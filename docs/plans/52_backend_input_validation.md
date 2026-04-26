# Plan 52: Backend Input Validation (3 TODOs)

**Ngày**: 2026-04-24
**Mức độ**: Medium — Invalid data enters system, causes downstream errors
**Loại**: Bugfix / Hardening

---

**Status**: Done — PR #78 merged to dev

## Problem

3 backend validation gaps documented in `tests/test_api_hardening.py`:

| # | File:Line | Issue | Impact |
|---|-----------|-------|--------|
| 1 | `test_api_hardening.py:42` | Station name > 50 chars accepted | UI overflow, DB bloat, FFmpeg path issues |
| 2 | `test_api_hardening.py:88` | IP format not validated ("not-an-ip-address" accepted) | FFmpeg crash when trying to connect RTSP |
| 3 | `test_api_hardening.py:214` | RECORD_STREAM_TYPE accepts any value (not just main/sub) | FFmpeg wrong stream, recording fails |

---

## Scope

### Files to change:
- `routes_stations.py` — Add validation to `StationPayload` model
- `routes_system.py` — Add validation to settings update

### Fix 1: Station name length

**Location**: `StationPayload` model in `routes_stations.py`

```python
class StationPayload(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    ip_camera_1: str = Field(..., min_length=7)
    safety_code: str = Field(..., min_length=1)
    # ...
```

Add `max_length=50` to name field.

### Fix 2: IP address format

**Location**: `StationPayload` model in `routes_stations.py`

```python
import re

IP_PATTERN = re.compile(
    r'^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$'
)

def _validate_ip(v: str) -> str:
    if not IP_PATTERN.match(v):
        raise ValueError(f'Invalid IP address format: {v}')
    return v
```

Add Pydantic `@field_validator` for `ip_camera_1` and `ip_camera_2`.

### Fix 3: RECORD_STREAM_TYPE validation

**Location**: Settings update in `routes_system.py`

```python
VALID_STREAM_TYPES = {"main", "sub"}

# In settings update handler:
if "RECORD_STREAM_TYPE" in updates:
    if updates["RECORD_STREAM_TYPE"] not in VALID_STREAM_TYPES:
        raise HTTPException(400, "RECORD_STREAM_TYPE must be 'main' or 'sub'")
```

### Tests to update:
- `test_api_hardening.py` — Change 3 tests from `assert status == 200` to `assert status == 422`
- Remove `# TODO(Plan #19)` and `# TODO(Plan #16)` comments

---

## Constraints

- Use Pydantic validators (not manual if/raise) for station fields
- Error messages phải tiếng Anh, descriptive
- Backward compatible: existing valid data unaffected
- Test changes: flip assertions from 200 → 422, remove TODO comments

---

## Verification

- [ ] `pytest tests/test_api_hardening.py -v` — 3 tests now expect 422
- [ ] `pytest tests/ -q` — all pass, no regressions
- [ ] Name "X" * 100 → 422
- [ ] IP "not-an-ip-address" → 422
- [ ] RECORD_STREAM_TYPE "INVALID_TYPE" → 400/422
- [ ] Valid inputs still work (normal station CRUD, settings save)
