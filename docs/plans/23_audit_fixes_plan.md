# Plan #23: Source Code Audit — 22 Issues Fix

**Status**: DONE — Implemented in v3.x series.

**Created**: 2026-04-15
**Scope**: Fix all 22 issues found during source code audit across database.py, api.py, App.jsx

## Phase 1: CRITICAL Fixes (database.py + App.jsx)

### Issue #1 — FTS5 MATCH crash (database.py)
- `get_records_v2()` line ~479-484: FTS5 MATCH query crashes on waybill codes with special chars (`+`, `-`, `"`, `*`)
- **Fix**: Wrap MATCH query in try/except, fallback to LIKE on failure
- **File**: `database.py`, function `get_records_v2()`

### Issue #2 — SSE stale closure (App.jsx)
- SSE handler (line ~279-329) captures `fetchRecords`, `activeStationId`, `recordsPage` via closure
- When user changes date/status filter, SSE handler still calls old `fetchRecords` with stale params
- **Fix**: Use refs (`useRef`) for all callbacks and state read inside SSE handler
- **File**: `web-ui/src/App.jsx`

## Phase 2: HIGH Fixes (database.py + api.py)

### Issue #3 — recorded_at returns raw UTC (database.py)
- `get_records_v2()` SELECT returns `p.recorded_at` which is UTC, but date filters use `'localtime'`
- User sees wrong date/time in records list
- **Fix**: Add `datetime(p.recorded_at, 'localtime') AS recorded_at` in SELECT
- **File**: `database.py`, function `get_records_v2()`, line ~460

### Issue #4 — except BaseException (api.py)
- Line 506: `except BaseException:` swallows `KeyboardInterrupt` and `SystemExit`
- **Fix**: Change to `except Exception:`
- **File**: `api.py`, line 506

### Issue #5 — Zip Slip vulnerability (api.py)
- `_update_production()` line ~1942: `zf.extractall(tmp_dir)` doesn't validate paths
- Malicious zip could contain `../../etc/passwd` paths
- **Fix**: Validate each member path doesn't escape `tmp_dir` before extraction
- **File**: `api.py`, function `_update_production()`

### Issue #6 — _login_attempts unbounded (api.py)
- Dict grows without limit; current cleanup only triggers at >1000 entries
- **Fix**: Cleanup expired entries on every login attempt (already partially done, ensure it's correct)
- **File**: `api.py`, function `login()`

### Issue #7 — Production update no signature verification (api.py)
- Downloads zip from GitHub without verifying checksum/signature
- **Fix**: Add SHA256 checksum verification from GitHub release assets (if available). At minimum, add a warning log.
- **File**: `api.py`, function `_update_production()`

## Phase 3: MEDIUM Fixes

### Issue #8 — Silent FTS5 migration failure (database.py)
- Line ~277: `except Exception: pass` silently swallows FTS5 rebuild errors
- **Fix**: Log the exception with `print()` instead of bare `pass`
- **File**: `database.py`, function `init_db()`

### Issue #9 — _parse_semver pre-release tags (api.py)
- `v2.4.1-beta` → strips to `2.4.1-beta` → `int('1-beta')` fails → returns `(0,0,0)`
- **Fix**: Split on `-` first, then parse version parts
- **File**: `api.py`, function `_parse_semver()`

### Issue #10 — SSE queue unbounded per client (api.py)
- `queue.Queue()` with no maxsize → memory leak if client is slow
- **Fix**: Use `queue.Queue(maxsize=100)` — drop old messages if full
- **File**: `api.py`, function `sse_events()`

### Issue #11 — CORS allows all methods/headers (api.py)
- `allow_methods=["*"]` and `allow_headers=["*"]` — too permissive
- **Fix**: Restrict to `["GET", "POST", "PUT", "DELETE", "OPTIONS"]` and specific headers
- **File**: `api.py`, CORS middleware config

### Issue #12 — activeStationId initialized to 1 (App.jsx)
- Line 160: `useState(1)` — may point to non-existent station
- **Fix**: Initialize to `null` and handle null case throughout
- **File**: `web-ui/src/App.jsx`

### Issue #13 — sendScanAction missing packingStatus (App.jsx)
- When scan returns `status: 'recording'`, `packingStatus` is not set (relies on SSE)
- **Fix**: Set `packingStatus('packing')` and `currentWaybill` on recording response
- **File**: `web-ui/src/App.jsx`, function `sendScanAction()`

### Issue #14 — Barcode scanner stale recordsPage (App.jsx)
- Barcode scanner `useEffect` deps include `[searchTerm, activeStationId, currentUser]`
- `sendScanAction` inside captures stale `recordsPage`
- **Fix**: Add `recordsPage` ref and use it inside scanner handler
- **File**: `web-ui/src/App.jsx`

## Phase 4: LOW Fixes

### Issue #15 — Dead code in database.py
- Old `get_records()` function kept for backwards compat — add deprecation comment

### Issue #16 — Hardcoded MTX_API in api.py
- `MTX_API = "http://127.0.0.1:9997"` — make configurable via env var
- **Fix**: `MTX_API = os.environ.get("MTX_API", "http://127.0.0.1:9997")`

### Issue #17 — console.log/console.error cleanup (App.jsx)
- Remove `console.log('Analytics not ready')`, `console.log('Status not ready')`, `console.log('API not reachable yet')`
- Keep `console.error()` for genuine errors but remove noise

### Issue #18 — Duplicate fetchRecords pattern (App.jsx)
- `fetchRecords(searchTerm, activeStationId, recordsPage)` called identically in 3+ SSE branches
- Minor cleanup, not critical

### Issue #19 — No React error boundary
- Add a simple error boundary component to catch render crashes
- **File**: New component in `web-ui/src/App.jsx`

### Issue #20 — No debounce on search input
- Every keystroke triggers `fetchRecords` via `useEffect`
- **Fix**: Add 300ms debounce on `searchTerm` before triggering fetch
- **File**: `web-ui/src/App.jsx`

### Issue #21 — Duplicate FTS5 check code in get_records_v2
- The `has_fts` check can be simplified

### Issue #22 — No request timeout on axios calls
- Frontend axios calls have no timeout — hangs indefinitely on dead server
- **Fix**: Set `axios.defaults.timeout = 15000` after login

## Execution Plan

### Agent 1: Backend database.py (Issues #1, #3, #8, #15, #21)
### Agent 2: Backend api.py (Issues #4, #5, #6, #7, #9, #10, #11, #16)
### Agent 3: Frontend App.jsx (Issues #2, #12, #13, #14, #17, #18, #19, #20, #22)

All 3 agents run in parallel. After completion:
- Run `python -c "import py_compile; py_compile.compile(...)"` on database.py and api.py
- Run `npm run build` in web-ui/
- Run full test suite (304 tests)
