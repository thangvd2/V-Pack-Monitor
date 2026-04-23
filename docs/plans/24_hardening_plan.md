# Plan #24: System Hardening — Round 2 (130 Issues)

**Created**: 2026-04-15
**Status**: DONE — Implemented in v3.x series. D1 (Fernet), D2 (per-concern locks), D3 (PRAGMA + SET NULL) all verified in codebase.
**Scope**: 130 issues across all modules after Round 1 (22 issues fixed in v2.4.2)

## ARCHITECTURAL DECISIONS (Oracle Reviewed ✅)

### D1: XOR → Fernet Encryption ✅
- **Decision**: Use `cryptography.fernet.Fernet` (Option A)
- **Key derivation**: `base64.urlsafe_b64encode(hashlib.sha256(existing_key_material).digest())` — preserves chain
- **Migration**: `_migrate_v1_to_v2()` in `init_db()` — decrypt XOR → re-encrypt Fernet → `enc:v2:` prefix
- **Backward compat**: Keep v1 decryption path in `_decrypt_value()` permanently
- **Important**: Consider separate `ENCRYPTION_KEY` DB setting (not derived from JWT_SECRET) to avoid key rotation issues
- **Effort**: Short (2-4h) | **Priority**: HIGH

### D2: Thread Safety — Per-Concern Locks ✅
- **Decision**: Per-concern locks (Option B) with thin helper
- **Lock groups**:
  - `_recorders_lock` → `active_recorders`, `active_waybills`, `active_record_ids`
  - `_streams_lock` → `stream_managers`, `reconnect_status`
  - Keep `_station_locks` as-is (already correct pattern)
- **Critical**: Fix `video_worker.py import api` backdoor — pass callback for decrement instead
- **Critical**: Never delete from `_station_locks` in `delete_station` — use module-level lock for dict itself
- **FastAPI concurrency**: `def` endpoints run in thread pool → truly concurrent. Race condition is REAL.
- **Effort**: Short (3-4h) | **Priority**: HIGH

### D3: FK Enforcement — PRAGMA + Cleanup + SET NULL ✅
- **Decision**: Enable PRAGMA foreign_keys + orphan cleanup + table reconstruction
- **packing_video.station_id**: `ON DELETE SET NULL` — NEVER destroy packing evidence
- **sessions**: `ON DELETE CASCADE` for user_id — stale sessions should go
- **audit_log.user_id**: `ON DELETE SET NULL` — preserve audit trail
- **Migration order**: (1) Clean orphans (2) Enable PRAGMA (3) Reconstruct tables with updated FK
- **Critical**: PRAGMA must be set PER-CONNECTION via `get_connection()` helper — SQLite resets on every new connection
- **Effort**: Medium (1-1.5 days) | **Priority**: MEDIUM

### D4: JWT in URL — Accept + Harden Downloads ✅
- **Decision**: Accept current approach (LAN-only, minimal risk)
- **Harden**: Switch video downloads to `fetch() + blob` (10-line frontend change, zero backend)
- **SSE**: Keep `?token=` — no clean alternative without polyfill. Not worth the complexity.
- **Effort**: Quick (<1h for download fix) | **Priority**: LOW

### D5: recorder.py Tests — 15-18 Mocked Tests ✅
- **Decision**: Heavy mocking with `unittest.mock.patch` on `subprocess.Popen` and `subprocess.run`
- **Test distribution**: 3 modes × start/stop (9) + stop lifecycle (4) + _detect_hw_encoder (2) + _is_hevc (2) + edge cases (2-3)
- **Focus**: Orchestration logic, not FFmpeg itself
- **Effort**: Short (3-4h) | **Priority**: MEDIUM

---

## PHASE 1: CRITICAL Fixes (9 issues)

### C1. api.py — Thread Safety for Global Dicts
**Severity**: CRITICAL | **Lines**: 61-63, 66, 67, 69

6 global dicts accessed from multiple threads without synchronization:
- `active_recorders` (line 61)
- `active_waybills` (line 62)
- `active_record_ids` (line 63)
- `_station_locks` (line 66)
- `stream_managers` (line 67)
- `reconnect_status` (line 69)

**Fix approach** (pending D2):
- Wrap all access in threading.RLock()
- OR consolidate into a single dataclass with lock

**Risk if not fixed**: Data corruption, lost recordings, crashes during concurrent operations

### C2. api.py — JWT Token Leakage via Query Parameters
**Severity**: CRITICAL | **Lines**: 517-519, 1499-1501

Token exposed in browser history, server logs, referrer headers via:
- Video download: `?token=<jwt>`
- SSE EventSource: `&token=<jwt>`

**Fix approach** (pending D4):
- Option A: Short-lived one-time tokens for downloads
- Option B: Accept risk for LAN-only deployment

**Risk if not fixed**: Token theft via log files or shared URLs

### C3. api.py — Error Response Leaks Internal Details
**Severity**: CRITICAL | **Lines**: 671, 1360, 1878, 1911, 2046, 2085

Raw exception messages returned to client, potentially leaking:
- File paths, DB schema, git branch names, internal network topology

**Fix approach**:
- Replace all `f"...{e}"` in error responses with generic messages
- Log detailed error server-side only
- Estimated: 6 lines to change

### C4. api.py — Video Download Path Traversal
**Severity**: CRITICAL | **Lines**: 543-546

File path from DB `video_paths` column served without validation.
If DB is compromised, arbitrary files could be served.

**Fix approach**:
```python
filepath = os.path.abspath(filepath)
if not filepath.startswith(os.path.abspath("recordings")):
    raise HTTPException(status_code=403, detail="Access denied")
```

### C5. database.py — XOR "Encryption" Replacement
**Severity**: CRITICAL | **Lines**: 32-48

Repeating-key XOR is trivially breakable. Protects S3_SECRET_KEY, S3_ACCESS_KEY, TELEGRAM_BOT_TOKEN.

**Fix approach** (pending D1):
- Replace with `cryptography.fernet.Fernet`
- Add migration step in init_db() to re-encrypt existing values
- New prefix: `enc:v2:` to distinguish from old `enc:v1:`

### C6. database.py — Enable Foreign Key Enforcement
**Severity**: CRITICAL | **Line**: N/A (PRAGMA never set)

All FOREIGN KEY declarations are inert. Orphaned records may exist.

**Fix approach** (pending D3):
1. Add orphan cleanup in init_db()
2. Set `PRAGMA foreign_keys = ON` in connection factory
3. Add ON DELETE SET NULL for packing_video.station_id
4. Add ON DELETE CASCADE for sessions.user_id, audit_log.user_id

### C7. database.py — Hardcoded Fallback Encryption Key
**Severity**: CRITICAL | **Line**: 28

```python
fallback = os.environ.get("VPACK_SECRET", "vpack-default-encryption-key")
```

**Fix approach**:
- Remove hardcoded fallback
- If no env var and no DB value, generate random key and warn user
- Log a warning on startup if using generated key

### C8. Frontend — JWT Token in URL (mirrors C2)
**Severity**: CRITICAL | **App.jsx**: 309, 1704

Same as C2 — frontend constructs URLs with token in query params.

### C9. Test Coverage — recorder.py Zero Tests
**Severity**: CRITICAL | **recorder.py**: 403 lines, 0 tests

**Fix approach** (pending D5):
- Create tests/test_recorder.py
- Mock subprocess.Popen for ffmpeg/ffprobe
- Test all 3 recording modes + stop + transcode
- Target: ~20 tests

---

## PHASE 2: HIGH Fixes (35 issues)

### Backend — database.py (10 HIGH)

| # | Issue | Lines | Fix |
|---|-------|-------|-----|
| H1 | Missing indexes (sessions, audit_log) | 899, 938, 983, 206 | Add 6 indexes in init_db() |
| H2 | No CHECK constraints on enum columns | 86, 152, 173 | Add CHECK for status/role/mode values |
| H3 | config_value NULL crashes _decrypt_value | 92, 297-298 | Add NULL guard |
| H4 | Nested concurrent connections in init_db | 276, 285 | Pass connection to _rebuild_fts_index() |
| H5 | save_record crashes on non-iterable video_paths | 346 | Add type check |
| H6 | Hardcoded default password in source | 183 | Keep but add startup warning |
| H7 | password_hash leaked in get_user_by_username | 767-770 | Remove from returned dict |
| H8 | No ON DELETE CASCADE/SET NULL | 174-175, 199-200 | Add with FK migration |
| H9 | delete_station creates orphaned data | 751-755 | Clean up sessions + reassign videos |
| H10 | delete_user creates orphaned data | 877-881 | Clean up sessions + audit logs |

### Backend — api.py (8 HIGH)

| # | Issue | Lines | Fix |
|---|-------|-------|-----|
| H11 | All errors return HTTP 200 | 698, 702, 704, etc. | Use HTTPException with proper 4xx codes |
| H12 | No password validation on UserCreate | 775-778 | Add min_length=6 |
| H13 | Admin can lock own account | 806-810 | Add self-lock prevention |
| H14 | No file upload size limit | 651-652 | Add MAX_SIZE check |
| H15 | /api/ping is unrestricted SSRF tool | 1679-1698 | Validate IP format + restrict |
| H16 | os._exit(0) bypasses cleanup | 1853 | Use sys.exit(0) or SIGTERM |
| H17 | _is_updating deadlock on restart failure | 2051-2078 | Reset flag in exception handler |
| H18 | Predictable restart script path | 1833, 1844 | Use tempfile.mkstemp() |

### Backend — recorder.py (2 HIGH)

| # | Issue | Lines | Fix |
|---|-------|-------|-----|
| H19 | Path traversal via waybill_code | 148, 172-173, 196-197 | Sanitize: strip /\.., validate format |
| H20 | _stopped flag never reset in start_recording | 134 | Reset self._stopped = False |

### Backend — video_worker.py (1 HIGH)

| # | Issue | Lines | Fix |
|---|-------|-------|-----|
| H21 | Unbounded ThreadPoolExecutor queue | 16 | Add max queue size + rejection |

### Backend — cloud_sync.py (2 HIGH)

| # | Issue | Lines | Fix |
|---|-------|-------|-----|
| H22 | No path validation in zip | 65-68 | Validate paths within recordings/ |
| H23 | GDrive credentials loaded every call | 86 | Cache credentials |

### Backend — auth.py (0 HIGH — all MEDIUM or below)

### Backend — telegram_bot.py (1 HIGH)

| # | Issue | Lines | Fix |
|---|-------|-------|-----|
| H24 | Bot token re-read from DB on every send | 111-112 | Cache token + refresh on change |

### Frontend (9 HIGH)

| # | Issue | Lines | Fix |
|---|-------|-------|-----|
| H25 | Zero AbortController usage | multiple | Add AbortController to all useEffect fetches |
| H26 | 49 useState in single component | 182-246 | Extract sub-components |
| H27 | S3 secret key sent to frontend | SetupModal:106 | Server returns masked value |
| H28 | 16+ silent catch blocks | multiple | Add error logging or toast |
| H29 | No accessibility attributes | all files | Add aria-label, role, focus trap |
| H30 | Station switch race (OPERATOR) | 1109-1133 | Add switchingStation lock flag |
| H31 | Monolithic App.jsx (1767 lines) | entire file | Split into 8+ sub-components |
| H32 | Duplicated password change logic | 955-968, 974-986 | Extract to single function |
| H33 | SSE reconnects on stations array ref change | 304-379 | Use stations ID string as dep |

### Test Coverage (2 HIGH)

| # | Issue | Fix |
|---|-------|-----|
| H34 | Scan flow (POST /api/scan) mostly untested | Add scan flow tests with mock recorder |
| H35 | 23/52 API endpoints untested (44%) | Add endpoint tests for missing ones |

---

## PHASE 3: MEDIUM Fixes (52 issues)

### Backend — database.py (14 MEDIUM)

| # | Issue | Lines |
|---|-------|-------|
| M1 | F-string SQL column injection (whitelist-protected) | 723, 858 |
| M2 | No WAL journal mode | init_db |
| M3 | set_settings uses loop instead of executemany | 330-341 |
| M4 | No connection factory for shared PRAGMA | all functions |
| M5 | Empty path segments from comma-split | 616, 636 |
| M6 | No input length validation | 345, 828, 302 |
| M7 | Duplicate end_session functions | 925, 1051 |
| M8 | Near-duplicate save_record/create_record | 345-356, 359-369 |
| M9 | get_records returns raw tuples | 411-431 |
| M10 | get_hourly_stats uses datetime.now() without tz | 1069 |
| M11 | Inconsistent timestamp type names | 69, 155, 171, 200 |
| M12 | UTC/localtime boundary bug near midnight | 354, 512 |
| M13 | init_db not thread-safe | 56 |
| M14 | password_hash returned to caller | 767-770 |

### Backend — api.py (9 MEDIUM)

| # | Issue | Lines |
|---|-------|-------|
| M15 | No input validation on StationPayload | 844-851 |
| M16 | Audit log limit/offset not bounded | 1119-1129 |
| M17 | Raw sqlite3.connect in get_analytics_today | 1390-1406 |
| M18 | _update_check_cache not thread-safe | 1705, 1735-1736 |
| M19 | No audit trail for failed logins | 700-702 |
| M20 | Unbounded SSE client accumulation | 73, 1519 |
| M21 | Live preview leaks localhost:8889 | 1471-1474 |
| M22 | _recover_pending_records blocks startup | 338-405 |
| M23 | git stash can lose changes | 1863-1882 |

### Backend — other files (8 MEDIUM)

| # | File | Issue | Lines |
|---|------|-------|-------|
| M24 | video_worker.py | Lazy import of api internals | 47-56 |
| M25 | video_worker.py | submit/shutdown race condition | 139-144 |
| M26 | recorder.py | transcode error silently swallowed | 364-369 |
| M27 | network.py | 254 threads for LAN scan | 154-155 |
| M28 | network.py | No private IP validation for scan | 154-155 |
| M29 | cloud_sync.py | No concurrency protection | 125-174 |
| M30 | cloud_sync.py | Direct sqlite3.connect | 28-34 |
| M31 | telegram_bot.py | Polling with no backoff | 70-74 |

### Frontend (12 MEDIUM)

| # | Issue | Lines |
|---|-------|-------|
| M32 | 15 alert() calls blocking UI | App.jsx, UserManagementModal |
| M33 | 6 window.confirm() calls | App.jsx, SetupModal, UserManagementModal |
| M34 | DOM direct access (getElementById) | App.jsx:1559 |
| M35 | fetchStorageInfo called on every records fetch | App.jsx:518 |
| M36 | Inline arrow functions in JSX (50+) | multiple |
| M37 | API_BASE duplicated in 5 files | multiple |
| M38 | Version numbers inconsistent in comments | App.jsx, SetupModal, Dashboard |
| M39 | Magic numbers (no named constants) | App.jsx multiple |
| M40 | console.error remaining (10 calls) | multiple files |
| M41 | fetchStationStatus dep missing | App.jsx:37-46 |
| M42 | Recharts heavy import | Dashboard.jsx:10-13 |
| M43 | Grid mode fires N concurrent requests | App.jsx:472-487 |

### Auth + Telegram (3 MEDIUM)

| # | File | Issue |
|---|------|-------|
| M44 | auth.py | SECRET_KEY loaded once, never refreshed |
| M45 | auth.py | int(user_id) can throw ValueError → 500 |
| M46 | telegram_bot.py | Direct sqlite3.connect in /baocao handler |

---

## PHASE 4: LOW Fixes (34 issues)

### Backend (22 LOW)

| # | File | Issue |
|---|------|-------|
| L1 | database.py | Dynamic SQL construction in get_records_v2 (safe but fragile) |
| L2 | database.py | days param concatenated via \|\| (parameterized, safe) |
| L3 | database.py | FTS5 fallback runs 2 separate queries |
| L4 | database.py | Relative DB path (works but fragile) |
| L5 | database.py | datetime.now() without timezone |
| L6 | database.py | Repeated import bcrypt inside functions |
| L7 | database.py | is_synced column never read |
| L8 | api.py | Redundant imports (asyncio, telegram_bot, FileResponse) |
| L9 | api.py | import re inside loop |
| L10 | api.py | import subprocess repeated 9 times |
| L11 | api.py | import socket duplicated |
| L12 | api.py | All logging uses print() — no structured logging |
| L13 | api.py | Dead code in _preflight_checks |
| L14 | api.py | No username length/char validation |
| L15 | api.py | _suppress_conn_reset swallows errors |
| L16 | api.py | days parameter allows negative values |
| L17 | api.py | Non-atomic _login_attempts cleanup |
| L18 | auth.py | revoke_token silently swallows exceptions |
| L19 | auth.py | 8-hour token expiry (design choice) |
| L20 | recorder.py | Windows file delete retry is fragile |
| L21 | network.py | get_local_subnet fails without internet |
| L22 | cloud_sync.py | Zip deleted but videos remain |

### Frontend (5 LOW)

| # | Issue |
|---|-------|
| L23 | sendScanAction not memoized |
| L24 | useEffect cleanup missing for mtx-status |
| L25 | VideoPlayerModal hideTimer not cleaned on unmount |
| L26 | Hardcoded Vietnamese strings (no i18n) |
| L27 | Missing useMemo for derived values |

### Test Coverage (5 LOW)

| # | Issue |
|---|-------|
| L28 | test_update_user doesn't verify DB change |
| L29 | test_analytics_today_with_data only checks >= 1 |
| L30 | test_create_station_empty_name asserts success (documents bug) |
| L31 | test_error_response_no_stack_trace_leak trivially passes |
| L32 | test_export_csv doesn't verify headers/encoding |
| L33 | FTS5 MATCH fallback not tested for real special chars |
| L34 | _parse_semver not tested directly |

---

## EXECUTION PLAN

### Step 1: Get Oracle feedback on D1-D5
### Step 2: User reviews plan + Oracle recommendations → confirm/deny each phase
### Step 3: Phase 1 — CRITICAL fixes (9 issues)
### Step 4: Phase 2 — HIGH fixes (35 issues)
### Step 5: Phase 3 — MEDIUM fixes (52 issues)
### Step 6: Phase 4 — LOW fixes (34 issues)
### Step 7: Run full test suite + build verification
### Step 8: Version bump + release

**Estimated test impact**: 304 → ~370+ tests (recorder.py + scan flow + endpoint coverage)

---

## REVIEW NOTES (Per-Issue Scrutiny)

### Issues that may be FALSE POSITIVES or LOW PRIORITY:

1. **C2/C8 (JWT in URL)**: System runs on internal LAN only. Real risk may be negligible.
2. **H29 (No accessibility)**: Important but not a "security" issue. Separate workstream.
3. **H31 (Monolithic App.jsx)**: Large refactor, high regression risk. Should be separate PR.
4. **M12 (UTC/localtime midnight)**: Theoretical bug, extremely rare occurrence.
5. **M2 (WAL mode)**: Single-user system, concurrent access is rare. Low actual benefit.
6. **L12 (print vs logging)**: Style preference, not a bug. Low priority for production.

### Issues that may be DUPLICATES or OVERLAPPING:

- C2/C8 are the same issue (api.py + frontend) — should fix together
- H7/H8/H9/H10 are all part of the FK migration (D3) — fix as one unit
- H20 (_stopped flag) is a real bug but only manifests if recorder is reused — rare in practice
- M7/M8 (duplicate functions) are code smells, not bugs

### Issues that need MORE INVESTIGATION before fixing:

- C1 (race conditions): Need to understand FastAPI's actual concurrency model
- C6 (PRAGMA foreign_keys): Need to audit existing data for orphans before enabling
- M22 (recovery blocks startup): Need to test with real pending records

---

*Oracle review pending for D1-D5. Plan will be updated with recommendations.*
