# Plan: Extend Cleanup Options + Default 365 Days

## Goal
Add more auto-delete options (60, 90, 150, 365 days + "never delete") and change default from 7→365 days.

## Changes

### 1. Frontend: `web-ui/src/SetupModal.jsx`

**Line 106** — Default value:
```jsx
// BEFORE
const [keepDays, setKeepDays] = useState(initialSettings.RECORD_KEEP_DAYS || 7);
// AFTER
const [keepDays, setKeepDays] = useState(initialSettings.RECORD_KEEP_DAYS || 365);
```

**Lines 657-662** — Add options:
```jsx
// BEFORE
<option value="3">3 Ngày</option>
<option value="7">7 Ngày</option>
<option value="15">15 Ngày</option>
<option value="30">30 Ngày</option>

// AFTER
<option value="3">3 Ngày</option>
<option value="7">7 Ngày</option>
<option value="15">15 Ngày</option>
<option value="30">30 Ngày</option>
<option value="60">60 Ngày</option>
<option value="90">90 Ngày</option>
<option value="150">150 Ngày</option>
<option value="365">365 Ngày</option>
<option value="0">Không bao giờ xoá</option>
```

### 2. Backend: `api.py`

**Line 654** — Default + skip when keep_days==0:
```python
# BEFORE
keep_days = int(database.get_setting("RECORD_KEEP_DAYS", 7))
database.cleanup_old_records(keep_days)

# AFTER
keep_days = int(database.get_setting("RECORD_KEEP_DAYS", 365))
if keep_days > 0:
    logger.info(f"[STARTUP] Auto-cleanup: removing records older than {keep_days} days")
    database.cleanup_old_records(keep_days)
else:
    logger.info("[STARTUP] Auto-cleanup: disabled (keep_days=0, never delete)")
```

### 3. Backend: `database.py`

**Function `cleanup_old_records` (line 716)** — Add early return for days==0:
```python
def cleanup_old_records(days=7):
    """Xóa các video và bản ghi cũ hơn X ngày để giải phóng dung lượng ổ cứng."""
    if days <= 0:
        logger.info("[DB] cleanup_old_records: skipped (keep_days=%s, never delete)", days)
        return
    # ... rest unchanged
```

Also add summary log after loop:
```python
    conn.commit()
    if old_records:
        logger.info("[DB] cleanup_old_records: deleted %d old records (older than %d days)", len(old_records), days)
```

### 4. Backend: `routes_system.py`

**Line 402-403** — Add validation:
```python
class SettingsUpdate(BaseModel):
    RECORD_KEEP_DAYS: int
    RECORD_STREAM_TYPE: str = "main"
    # ... rest unchanged

    @field_validator("RECORD_KEEP_DAYS")
    @classmethod
    def validate_keep_days(cls, v):
        if v not in (0, 3, 7, 15, 30, 60, 90, 150, 365):
            raise ValueError("RECORD_KEEP_DAYS must be one of: 0, 3, 7, 15, 30, 60, 90, 150, 365")
        return v
```

Need to add import: `from pydantic import field_validator`

### 5. Tests: `tests/test_database.py`

Add test for `cleanup_old_records(days=0)` — should not delete anything.

Add test for `cleanup_old_records(days=365)` — should only delete records older than 365 days.

## Files Modified
1. `web-ui/src/SetupModal.jsx` — dropdown options + default
2. `api.py` — startup default + skip when 0
3. `database.py` — early return when days<=0 + summary log
4. `routes_system.py` — validate RECORD_KEEP_DAYS values
5. `tests/test_database.py` — new test cases

## Risks
- None. This is purely additive — existing behavior (7-day default) is simply changed to 365-day default. The "never delete" option is a new feature that doesn't affect existing data.
- Existing DB with `RECORD_KEEP_DAYS=30` will continue to use 30 until admin changes it in UI.
