# Bug Fix: Delete station fails with FK constraint error

**Ngày phát hiện**: 2026-04-22
**Mức độ**: High — Không xóa được trạm khi có expired sessions
**Loại**: Data integrity bug (backend)
**Reproduce**: DELETE /api/stations/{id} trả 500 khi trạm có sessions EXPIRED

---

## Root Cause

`database.py` hàm `delete_station()` (line 867-869) chỉ xóa sessions có `status = 'ACTIVE'`:

```python
cursor.execute(
    "DELETE FROM sessions WHERE station_id = ? AND status = 'ACTIVE'",
    (station_id,),
)
```

Sessions EXPIRED bị bỏ sót. Sau đó `DELETE FROM stations` fail vì FK constraint từ table `sessions`:

```
sqlite3.IntegrityError: FOREIGN KEY constraint failed
```

Table `sessions` có FK `ON DELETE CASCADE` nhưng code tự delete một phần sessions trước → để sót EXPIRED → CASCADE không được trigger đúng trong cùng transaction.

**Dữ liệu thực tế**: Station 1 có **9 sessions EXPIRED** (không có ACTIVE nào) → delete fail 100%.

---

## Fix Plan

### 1. Sửa `database.py` — `delete_station()` (line 867-869)

```python
# SỬA TỪ:
cursor.execute(
    "DELETE FROM sessions WHERE station_id = ? AND status = 'ACTIVE'",
    (station_id,),
)

# SỬA THÀNH:
# Delete ALL sessions for this station (both ACTIVE and EXPIRED)
cursor.execute(
    "DELETE FROM sessions WHERE station_id = ?",
    (station_id,),
)
```

### 2. Thêm test case cho edge case này

**File: `tests/test_database.py`** (hoặc file test phù hợp) — Thêm test:

```python
def test_delete_station_with_expired_sessions(tmp_path, monkeypatch):
    """Deleting a station with only EXPIRED sessions should succeed (not FK error)."""
    monkeypatch.setattr(database, "DB_FILE", str(tmp_path / "test.db"))
    database._init_done = False
    database.init_db()

    # Create station
    station_id = database.add_station({
        "name": "Test Station",
        "ip_camera_1": "192.168.1.1",
        "ip_camera_2": "",
        "safety_code": "1234",
        "camera_mode": "single",
        "camera_brand": "imou",
        "mac_address": "",
    })

    # Create user
    database.create_user("op1", "hashed_pw", "OPERATOR", "Operator 1")

    # Create and expire a session
    session_id = database.create_session(2, station_id)  # user_id=2 (op1)
    database.end_session(session_id)  # Set to EXPIRED

    # Verify session is EXPIRED
    session = database.get_session_by_id(session_id)
    assert session["status"] == "EXPIRED"

    # Delete station should NOT raise FK error
    database.delete_station(station_id)

    # Verify station is gone
    assert database.get_station(station_id) is None
```

---

## Files cần sửa

| File | Vị trí | Thay đổi |
|---|---|---|
| `database.py` | Line 867-869 (`delete_station`) | Bỏ `AND status = 'ACTIVE'` |
| `tests/test_database.py` | Thêm test case | Test delete station với expired sessions |

---

## Test Cases

1. **Trạm có sessions EXPIRED** → `delete_station()` thành công, không FK error
2. **Trạm có sessions ACTIVE** → sessions bị xóa, station bị xóa (existing behavior không đổi)
3. **Trạm có packing_video records** → station_id set NULL, video giữ lại (existing behavior không đổi)
4. **Trạm không có sessions hay videos** → xóa thành công (existing behavior không đổi)
5. **`pytest tests/ -v`** pass

---

## KHÔNG sửa

- FK schema (`ON DELETE CASCADE`) — đã đúng, không đụng
- `packing_video` — không có FK constraint, code tự set NULL đã đúng
- `audit_log` — không có FK constraint trên station_id
- `routes_stations.py` — không cần sửa, chỉ gọi `database.delete_station()`
