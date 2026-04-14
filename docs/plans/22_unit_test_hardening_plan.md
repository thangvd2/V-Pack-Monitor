# Plan #22: Unit Test Hardening — Coverage Gaps & Regression Guards

**Created:** 2026-04-14
**Status:** PLANNING
**Priority:** P1 (CI/CD Readiness)
**Depends on:** Plan #20 (Unit Test Suite — Phase 1-4 DONE)

---

## Mục tiêu

Phân tích tất cả 20 plans trong `docs/plans/` để xác định coverage gaps trong 161 tests hiện tại, sau đó thêm tests để:
1. **Regression guard** — 26 security vulnerabilities (Plan #17) + 9 bugs (Plan #15) sẽ không tái phát
2. **Cover untested paths** — network.py, recorder.py, video_worker.py, cloud_sync.py hiện 0% coverage
3. **Edge case hardening** — boundary conditions, error handling, concurrent access
4. **API contract tests** — verify response format, pagination metadata, status codes

---

## Phân tích hiện trạng

### Tests hiện tại: 161 tests, 4 files

| File | Tests | Coverage |
|---|---|---|
| `test_database.py` | 62 | ~94% database.py |
| `test_auth.py` | 22 | ~93% auth.py |
| `test_api_routes.py` | 55 | ~39% api.py (hardware-dependent paths skipped) |
| `test_api_helpers.py` | 22 | RTSP URLs all brands |
| **conftest.py** | fixtures | isolate_db, client, admin/operator tokens |

### Files CHƯA có test (0% coverage)

| File | Dòng code | Vai trò | Testable? |
|---|---|---|---|
| `network.py` | ~165 | LAN scanner, MAC discovery, IP validation | ✅ Mock subprocess |
| `recorder.py` | ~402 | FFmpeg recording, PIP, transcoding | ⚠️ Mock FFmpeg |
| `video_worker.py` | ~155 | Background video processing queue | ✅ Mock |
| `cloud_sync.py` | ~165 | S3/GDrive cloud backup | ✅ Mock boto3 |
| `telegram_bot.py` | ~135 | Telegram notifications | ✅ Mock requests |
| `build.py` | ~170 | Build/packaging script | ❌ Skip |

---

## Gap Analysis theo Plans

### Từ Plan #15 — Bug Fixes (9 bugs, COMPLETED)

| Bug | Đã có test guard? | Gap |
|---|---|---|
| #1 JWT Secret auto-generate | ❌ | Không test `_generate_secret()` persistence |
| #2 GET /api/stations auth required | ✅ | `test_api_routes.py` đã test |
| #3 Windows ping compatibility | ❌ | Không test `_ping_check()` helper |
| #4 update_url re-register MediaMTX | ❌ | Không test `CameraStreamManager.update_url()` side effects |
| #5 Transcode fail preserve .ts | ❌ | Không test recorder failure path |
| #6 shutdown(wait=True) | ❌ | Không test `video_worker.shutdown()` wait behavior |
| #7 Password in body not URL | ✅ | `test_api_routes.py` đã test |
| #8 UTC/Local timestamp mixing | ❌ | Không test timezone correctness |
| #9 SSE stale closure | ❌ | Frontend-only, cần E2E test (out of scope) |

### Từ Plan #17 — Security Hardening (26 vulns, COMPLETED)

| VULN | Đã có test guard? | Gap |
|---|---|---|
| #01 Unauthenticated video download | ✅ | Test `test_api_routes.py` |
| #02 CORS restrictive | ❌ | Không test CORS headers response |
| #03 Default admin must_change_password | ❌ | Không test force password change flow |
| #04 Safety code hidden from OPERATOR | ❌ | Không test station API field filtering |
| #05 Login rate limiting (5 attempts) | ✅ | Test `test_api_routes.py` |
| #06 JWT token revocation on logout | ✅ | Test `test_auth.py` + `test_api_routes.py` |
| #07 SSE auth required | ⚠️ | Partial — chỉ test connection, không test token rejected |
| #09 SQL injection prevention | ⚠️ | Implicit qua parameterized queries, không test explicit injection |
| #10 Settings masking (sensitive keys) | ✅ | Test `test_api_routes.py` |
| #13 Server-side password validation | ❌ | Không test min_length=6 validation |
| #14 Session heartbeat ownership | ❌ | Không test user A không heartbeat session user B |
| #15 Encrypt settings at rest | ✅ | Test `test_database.py` encryption |
| #18 Generic error messages | ❌ | Không test exception không leak stack trace |
| #20 IP validation before ping | ❌ | Không test malformed IP rejected |
| #25 Input length limits (barcode) | ❌ | Không test barcode max length |

### Từ Plan #16 — Record Stream Toggle

| Feature | Đã có test? | Gap |
|---|---|---|
| RECORD_STREAM_TYPE setting | ❌ | Không test main/sub toggle |
| Toggle chỉ hiệu lực lần ghi tiếp | ❌ | Không test |

### Từ Plan #18 — Auto-Update System

| Feature | Đã có test? | Gap |
|---|---|---|
| Version file read | ❌ | Không test `read_version_file()` |
| Dev mode detection (.git/) | ❌ | Không test |
| Concurrent update protection | ❌ | Không test update lock |
| Exclude list (recordings/, venv/) | ❌ | Không test |

### Từ Plan #19 — Setup Modal Upgrade

| Feature | Đã có test? | Gap |
|---|---|---|
| Station name validation (2-50 chars) | ❌ | Không test |
| IP validation (IPv4 format) | ❌ | Không test |
| MAC validation | ❌ | Không test |
| Duplicate name/IP warning | ❌ | Không test check-conflict endpoint |

### Từ Plan #11 — Auto-Discovery Camera

| Feature | Đã có test? | Gap |
|---|---|---|
| `scan_lan_for_mac()` | ❌ | network.py 0% coverage |
| `validate_mac()` | ❌ | |
| MAC normalize | ❌ | |
| `get_local_subnet()` | ❌ | |

### Từ Plan #12 — v2 Roadmap

| Feature | Đã có test? | Gap |
|---|---|---|
| Record status lifecycle (RECORDING→PROCESSING→READY) | ✅ | test_database.py |
| VideoWorker queue + thread | ❌ | video_worker.py 0% coverage |
| Crash recovery (_recover_pending_records) | ❌ | |

---

## Phased Implementation

### Phase 1: Security Regression Guards — 18 tests mới
**File:** `tests/test_security_regression.py`

| # | Test | Guards Against |
|---|---|---|
| 1 | GET /api/stations without token → 401 | VULN-02 re-regression |
| 2 | GET /api/stations with OPERATOR → no safety_code in response | VULN-04 |
| 3 | GET /api/stations with ADMIN → has safety_code | VULN-04 |
| 4 | GET /api/records/{id}/download without token → 401 | VULN-01 |
| 5 | CORS header — no wildcard origin | VULN-02 |
| 6 | Default admin has must_change_password=1 | VULN-03 |
| 7 | Login with must_change_password → response flag | VULN-03 |
| 8 | Password change with <6 chars → rejected | VULN-13 |
| 9 | Session heartbeat — wrong user → 403 | VULN-14 |
| 10 | Settings GET — sensitive keys masked | VULN-10 |
| 11 | Settings POST — masked values not saved (no overwrite) | VULN-10 |
| 12 | SQL injection attempt in station update → sanitized | VULN-09 |
| 13 | SQL injection in update_station_ip → whitelist enforced | VULN-09 |
| 14 | Generic error on exception (no stack trace leak) | VULN-18 |
| 15 | Malformed IP → rejected by ping helper | VULN-20 |
| 16 | Barcode >100 chars → truncated or rejected | VULN-25 |
| 17 | JWT token with wrong secret → rejected | Bug #1 |
| 18 | UTC timestamp in records — verified consistent | Bug #8 |

### Phase 2: Network Module Tests — 15 tests mới
**File:** `tests/test_network.py`

| # | Test | Function Tested |
|---|---|---|
| 1 | `validate_mac("AA:BB:CC:DD:EE:FF")` → True | validate_mac |
| 2 | `validate_mac("aa-bb-cc-dd-ee-ff")` → True (case insensitive) | validate_mac |
| 3 | `validate_mac("aabb.ccdd.eeff")` → True (Cisco format) | validate_mac |
| 4 | `validate_mac("")` → False (empty) | validate_mac |
| 5 | `validate_mac("00:00:00:00:00:00")` → False | validate_mac |
| 6 | `validate_mac("FF:FF:FF:FF:FF:FF")` → False | validate_mac |
| 7 | `validate_mac("invalid")` → False | validate_mac |
| 8 | `validate_mac("AA:BB:CC:DD")` → False (too short) | validate_mac |
| 9 | `normalize_mac("aa-bb-cc-dd-ee-ff")` → "AA:BB:CC:DD:EE:FF" | normalize_mac |
| 10 | `get_local_subnet()` → returns valid CIDR string | get_local_subnet |
| 11 | `scan_lan_for_mac()` — mock arp output, found | scan_lan_for_mac |
| 12 | `scan_lan_for_mac()` — mock arp output, not found | scan_lan_for_mac |
| 13 | `scan_lan_for_mac()` — MAC case insensitive match | scan_lan_for_mac |
| 14 | `/api/discover-mac` endpoint — valid IP | API integration |
| 15 | `/api/discover/{station_id}` endpoint — auto-update IP | API integration |

### Phase 3: Video Worker Tests — 12 tests mới
**File:** `tests/test_video_worker.py`

| # | Test | Function Tested |
|---|---|---|
| 1 | `submit_task()` — adds to queue | submit_task |
| 2 | `shutdown()` — executor stops | shutdown |
| 3 | `shutdown(wait=True)` — waits for tasks | Bug #6 guard |
| 4 | Concurrent submit + shutdown — no race | thread safety |
| 5 | `submit_task()` when None executor → auto-creates | lazy init |
| 6 | Double shutdown → idempotent | shutdown |
| 7 | Task callback — on_success updates status | callback |
| 8 | Task callback — on_failure sets FAILED | callback |
| 9 | `_recover_pending_records()` — RECORDING → retry | crash recovery |
| 10 | `_recover_pending_records()` — PROCESSING → retry | crash recovery |
| 11 | `_recover_pending_records()` — READY → skip | crash recovery |
| 12 | Worker processes task from queue → status changes | end-to-end mock |

### Phase 4: API Endpoint Hardening — 20 tests mới
**File:** `tests/test_api_hardening.py`

| # | Test | Endpoint / Feature |
|---|---|---|
| 1 | POST /api/stations — name too short (<2 chars) → 400 | Plan #19 |
| 2 | POST /api/stations — name too long (>50 chars) → 400 | Plan #19 |
| 3 | POST /api/stations — empty IP → 400 | Plan #19 |
| 4 | POST /api/stations — invalid IP format → 400 | Plan #19 |
| 5 | POST /api/stations — empty safety code → 400 | Plan #19 |
| 6 | POST /api/stations — safety code <4 chars → 400 | Plan #19 |
| 7 | POST /api/stations — invalid MAC → rejected | Plan #19 |
| 8 | POST /api/stations — duplicate name → warning or accepted | Plan #19 |
| 9 | GET /api/stations/check-conflict?ip=X → duplicate detected | Plan #19 |
| 10 | GET /api/stations/check-conflict?mac=X → duplicate detected | Plan #19 |
| 11 | GET /api/stations/check-conflict — no conflict → empty | Plan #19 |
| 12 | POST /api/settings — RECORD_STREAM_TYPE main/sub | Plan #16 |
| 13 | POST /api/settings — invalid stream type → rejected | Plan #16 |
| 14 | GET /api/system/update-check — returns version info | Plan #18 |
| 15 | POST /api/system/update — concurrent call → second rejected | Plan #18 |
| 16 | POST /api/auth/change-password — same password → accepted | Edge case |
| 17 | DELETE /api/users/{self} → rejected (cannot delete self) | Existing test gap |
| 18 | POST /api/sessions/acquire — station already locked → conflict | Edge case |
| 19 | POST /api/sessions/release — other user's session → 403 | VULN-14 |
| 20 | GET /api/audit-logs — OPERATOR → filtered to own actions | RBAC |

### Phase 5: Database Edge Cases — 10 tests mới
**File:** `tests/test_database_edge_cases.py`

| # | Test | Edge Case |
|---|---|---|
| 1 | `get_records()` — search with SQL injection attempt | SQL injection guard |
| 2 | `get_records()` — search overrides station filter (by design) | Behavioral contract |
| 3 | `cleanup_old_records()` — exactly N days boundary | Off-by-one |
| 4 | `cleanup_old_records()` — video file doesn't exist (already deleted) | Graceful handling |
| 5 | `create_user()` — username with special chars | Input validation |
| 6 | `create_user()` — username max length | Boundary |
| 7 | `update_station()` — invalid field in allow-list → ignored | Whitelist enforcement |
| 8 | `set_settings()` — large value (10KB JSON) | Input limits |
| 9 | `expire_stale_sessions()` — session exactly at timeout boundary | Off-by-one |
| 10 | `get_hourly_stats()` — no records today → all zeros | Zero-fill verification |

### Phase 6: Cloud Sync & Telegram Mocks — 8 tests mới
**File:** `tests/test_cloud_sync.py` + `tests/test_telegram.py`

| # | Test | Module |
|---|---|---|
| 1 | S3 upload — success path (mock boto3) | cloud_sync.py |
| 2 | S3 upload — credentials invalid → graceful error | cloud_sync.py |
| 3 | S3 upload — network timeout → retry | cloud_sync.py |
| 4 | GDrive upload — success path (mock) | cloud_sync.py |
| 5 | Cloud disabled → skip upload | cloud_sync.py |
| 6 | Telegram send — success (mock requests) | telegram_bot.py |
| 7 | Telegram send — invalid token → graceful error | telegram_bot.py |
| 8 | Telegram send — message formatting | telegram_bot.py |

---

## Summary

| Phase | File | Tests | Priority |
|---|---|---|---|
| **1** | Security regression guards | 18 | P0 |
| **2** | Network module | 15 | P1 |
| **3** | Video worker | 12 | P1 |
| **4** | API hardening | 20 | P1 |
| **5** | Database edge cases | 10 | P2 |
| **6** | Cloud + Telegram mocks | 8 | P2 |
| **Total** | **6 new files** | **83 tests mới** | |

### After implementation:
- **Total tests:** 161 + 83 = **~244 tests**
- **Coverage:** database.py ~97%, auth.py ~95%, api.py ~55%, network.py ~80%, video_worker.py ~75%
- **Regression guard:** Tất cả 26 security vulns + 9 bugs có test protection

---

## Test Infrastructure Improvements

### conftest.py additions needed:

```python
# Fixture cho network mocks
@pytest.fixture
def mock_arp_table():
    """Mock subprocess arp -a output"""
    ...

# Fixture cho video worker
@pytest.fixture
def video_worker_instance():
    """VideoWorker with mock executor"""
    ...

# Fixture cho cloud mocks
@pytest.fixture
def mock_s3_client():
    """Mock boto3 S3 client"""
    ...

# Fixture cho FFmpeg mock
@pytest.fixture
def mock_ffmpeg():
    """Mock subprocess.run for FFmpeg commands"""
    ...
```

---

## Success Criteria

- [ ] Tất cả 83 tests mới pass
- [ ] Tổng tests ≥ 240
- [ ] Không test flaky (chạy 3 lần liên tục, tất cả pass)
- [ ] Tests chạy <90 giây
- [ ] Coverage tăng: api.py 39% → 55%, network.py 0% → 80%, video_worker.py 0% → 75%
- [ ] Tất cả security vulnerabilities từ Plan #17 có regression test
