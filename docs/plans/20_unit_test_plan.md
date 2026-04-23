# Plan #20 — Unit Test Suite

**Status**: DONE — Implemented in v3.x series.

**Created:** 2026-04-14
**Status:** IN PROGRESS
**Priority:** P0 (Production Hardening)

---

## Mục tiêu

Tạo bộ unit test toàn diện cho V-Pack Monitor để:
1. **Regression guard** — 18 bugs đã fix sẽ không tái phát
2. **Safety net** — refactor/Thêm tính năng mới mà không sợ phá vỡ logic cũ
3. **CI/CD readiness** — chạy `pytest` trước mỗi commit/push

## Công nghệ

- **pytest** — test framework chính
- **pytest-asyncio** — test async endpoints (SSE, lifespan)
- **httpx** — FastAPI `TestClient` (sync + async)
- **pytest-cov** — coverage report
- SQLite `:memory:` — test database (không ảnh hưởng production DB)

## Cài đặt

```bash
pip install pytest pytest-asyncio httpx pytest-cov
```

## Cấu trúc thư mục

```
tests/
├── conftest.py              # Shared fixtures (DB, client, auth tokens)
├── test_database.py         # database.py — 44 public functions
├── test_auth.py             # auth.py — 8 functions
├── test_api_routes.py       # api.py — 52 endpoints
└── test_api_helpers.py      # api.py — helper functions (RTSP URLs, etc.)
```

## Phased Approach

### Phase 1: Database Layer (`test_database.py`) — P0
**Lý do:** Database là foundation — mọi thứ khác phụ thuộc nó. Cần test trước.

| # | Test Case | Mức ưu tiên |
|---|-----------|-------------|
| **Encryption/Decryption** | | |
| 1 | `_encrypt_value` → `_decrypt_value` roundtrip | P0 |
| 2 | `_decrypt_value` với corrupted data → return ciphertext gốc | P0 |
| 3 | `_decrypt_value` với non-encrypted string → pass-through | P0 |
| **DB Init & Migration** | | |
| 4 | `init_db` tạo đúng bảng + cột | P0 |
| 5 | `init_db` tạo default admin khi chưa có user | P0 |
| 6 | `init_db` migration — thêm cột mới cho DB cũ | P1 |
| **Settings** | | |
| 7 | `set_setting` / `get_setting` roundtrip | P0 |
| 8 | `set_setting` mã hóa sensitive keys (S3_SECRET_KEY, etc.) | P0 |
| 9 | `get_all_settings` trả tất cả settings, sensitive được mã hóa | P0 |
| 10 | `set_settings` batch upsert | P1 |
| **Records CRUD** | | |
| 11 | `create_record` → status=RECORDING | P0 |
| 12 | `update_record_status` RECORDING→PROCESSING→READY | P0 |
| 13 | `update_record_status` với video_paths | P1 |
| 14 | `get_records` — search by waybill | P0 |
| 15 | `get_records` — filter by station_id | P1 |
| 16 | `get_record_by_id` | P1 |
| 17 | `save_record` | P1 |
| 18 | `get_pending_records` — chỉ trả RECORDING + PROCESSING | P1 |
| 19 | `cleanup_old_records` — xóa record cũ + file | P0 |
| 20 | `delete_record` — xóa 1 record + file | P1 |
| **Stations CRUD** | | |
| 21 | `add_station` → `get_station` roundtrip | P0 |
| 22 | `update_station` tất cả field | P1 |
| 23 | `update_station_ip` — chỉ cho phép ip_camera_1, ip_camera_2 | P0 |
| 24 | `delete_station` | P1 |
| 25 | `get_stations` | P1 |
| **Users CRUD** | | |
| 26 | `create_user` — tạo user mới | P0 |
| 27 | `create_user` — duplicate username → None | P0 |
| 28 | `get_user_by_username` | P1 |
| 29 | `update_user` — allow-list filtering | P0 |
| 30 | `update_user_password` — verify password changed | P1 |
| 31 | `delete_user` | P1 |
| 32 | `clear_must_change_password` | P1 |
| **Sessions** | | |
| 33 | `create_session` → `get_active_session` | P0 |
| 34 | `expire_stale_sessions` — hết hạn session cũ | P0 |
| 35 | `end_session` → status EXPIRED | P1 |
| 36 | `update_session_heartbeat` | P1 |
| **Audit** | | |
| 37 | `log_audit` → `get_audit_logs` roundtrip | P1 |
| 38 | `cleanup_audit_log` — xóa log cũ | P1 |
| **Analytics** | | |
| 39 | `get_hourly_stats` — zero-fill 24h | P0 |
| 40 | `get_daily_trend` — zero-fill N ngày, parameterized query | P0 |
| 41 | `get_stations_comparison` | P1 |
| 42 | `get_records_for_export` | P1 |
| **Token Revocation** | | |
| 43 | `revoke_jti` → `is_jti_revoked` roundtrip | P0 |
| 44 | `is_jti_revoked` — JTI chưa revoke → False | P0 |

### Phase 2: Auth Layer (`test_auth.py`) — P0
**Lý do:** Auth là security-critical. Test riêng biệt cho dễ debug.

| # | Test Case | Mức ưu tiên |
|---|-----------|-------------|
| 1 | `hash_password` → `verify_password` roundtrip | P0 |
| 2 | `verify_password` sai password → False | P0 |
| 3 | `create_access_token` → `decode_token` roundtrip | P0 |
| 4 | `create_access_token` có `jti` unique | P0 |
| 5 | `create_access_token` có `exp` đúng 8h | P1 |
| 6 | `decode_token` với expired token → raises | P0 |
| 7 | `decode_token` với invalid secret → raises | P0 |
| 8 | `revoke_token` → `is_token_revoked` = True | P0 |
| 9 | `get_current_user` — token hợp lệ + user active → trả user | P0 |
| 10 | `get_current_user` — revoked token → 401 | P0 |
| 11 | `get_current_user` — user inactive → 401 | P0 |
| 12 | `require_admin` — admin user → pass | P0 |
| 13 | `require_admin` — operator → 403 | P0 |

### Phase 3: API Routes (`test_api_routes.py`) — P1
**Lý do:** Endpoints cần DB + Auth working. Test sau khi Phase 1+2 pass.

| # | Test Group | Endpoints | Mức ưu tiên |
|---|-----------|-----------|-------------|
| 1 | **Auth endpoints** | POST /api/auth/login, /logout, /change-password | P0 |
| 2 | **Login rate limiting** | 5 failed attempts → blocked | P0 |
| 3 | **Station CRUD** | GET/POST/PUT/DELETE /api/stations | P0 |
| 4 | **Record listing** | GET /api/records (search, filter, video_paths parsing) | P0 |
| 5 | **Settings** | GET/POST /api/settings (masking, preservation) | P1 |
| 6 | **Sessions** | acquire, heartbeat, release, force-end | P1 |
| 7 | **User CRUD** | create, update, delete, self-delete prevention | P1 |
| 8 | **Scan flow** | POST /api/scan (EXIT, STOP, START barcode) | P1 |
| 9 | **Analytics** | today, hourly, trend, stations-comparison | P1 |
| 10 | **Download auth** | GET /api/records/{id}/download/{idx}?token= | P1 |
| 11 | **SSE auth** | GET /api/events — revoked token rejected | P1 |
| 12 | **Conflict check** | GET /api/stations/check-conflict | P1 |

### Phase 4: API Helpers (`test_api_helpers.py`) — P2
| # | Test Case | Mức ưu tiên |
|---|-----------|-------------|
| 1 | `get_rtsp_url` — tất cả brands (imou, dahua, tenda, ezviz, tapo) | P1 |
| 2 | `get_rtsp_sub_url` — tất cả brands | P1 |
| 3 | `get_rtsp_url` — channel=1 vs channel=2 | P1 |

## Fixtures Strategy (`conftest.py`)

```python
import pytest, tempfile, os
import database, auth

@pytest.fixture(autouse=True)
def tmp_db(tmp_path, monkeypatch):
    """Mỗi test dùng SQLite :memory: riêng biệt"""
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr(database, "DB_FILE", db_path)
    database.init_db()
    yield
    # Cleanup

@pytest.fixture
def admin_token():
    """JWT token cho admin user (default admin)"""
    ...

@pytest.fixture
def operator_token():
    """JWT token cho operator user"""
    ...

@pytest.fixture
def client():
    """FastAPI TestClient"""
    from httpx import TestClient
    from api import app
    return TestClient(app)
```

## Chạy test

```bash
# Chạy tất cả
pytest tests/ -v

# Chạy với coverage
pytest tests/ -v --cov=database --cov=auth --cov=api --cov-report=term-missing

# Chạy chỉ Phase 1
pytest tests/test_database.py -v

# Chạy chỉ P0 tests
pytest tests/ -v -m "p0"
```

## Success Criteria

- [ ] Phase 1: ≥40 test cases cho `database.py`, coverage ≥ 85%
- [ ] Phase 2: ≥13 test cases cho `auth.py`, coverage ≥ 90%
- [ ] Phase 3: ≥30 test cases cho API routes, coverage ≥ 70%
- [ ] Phase 4: ≥3 test cases cho helpers, coverage ≥ 90%
- [ ] Tất cả tests pass trên Windows
- [ ] `pytest` chạy trong <30 giây
