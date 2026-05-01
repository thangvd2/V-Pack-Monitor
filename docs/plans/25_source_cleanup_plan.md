# Plan #25: Source Code Cleanup — Full Audit Fix (VERIFIED)

**Created**: 2026-04-18
**Verified**: 2026-04-19 by 5 parallel explore agents
**Status**: DONE — Closed 2026-04-24. Phase 1 + Phase 2 implemented via PRs #51-53 (v3.4.0).
**Scope**: Fix verified issues found during full source code audit (Phase J)
**Version target**: v3.3.0 → completed in v3.4.0

## DEFERRED (low value, high risk, or cosmetic only)

- Phase 2C: Refactor `_handle_scan_locked` (213 lines) — core scan flow, high risk
- Phase 3A: Test quality (broad exceptions, stale docstrings) — cosmetic
- Phase 3B: Docs cleanup (ROADMAP.md counts, QUALITY_CONTROL.md versions) — cosmetic

## VERIFICATION RESULTS

5 explore agents verified EVERY issue with file:line evidence on 2026-04-19.

### REMOVED from plan (FALSE POSITIVES):
| Issue | Why Removed |
|-------|-------------|
| `_parse_semver` pre-release handling | Already handles via `.split("-")[0]` at api.py:45 |
| SSE queue unbounded | Already bounded: `maxsize=100` per client (routes_records.py:434), `MAX_SSE_CLIENTS=50` (api.py:80) |
| `_login_attempts` no cleanup | Cleanup runs on every login (routes_auth.py:37-43) |
| `window.alert` calls | FIXED — zero remaining in any .jsx file |
| mtx-status interval cleanup | FALSE POSITIVE — one-shot check with proper `active` flag cleanup (App.jsx:340-354) |
| VideoPlayerModal hideTimer cleanup | FIXED — already implemented (VideoPlayerModal.jsx:37-42) |
| test_create_station_empty_name asserts success | FALSE POSITIVE — test correctly asserts 422 (test_api_hardening.py:43), just stale docstring |
| test_export_csv no header check | FALSE POSITIVE — both headers and BOM ARE tested (test_api_routes.py:445-456) |
| FTS5 special chars fallback untested | FALSE POSITIVE — test exists (test_video_search.py:52-58) |
| CORS `allow_methods=["*"]` | FALSE POSITIVE — already restricted to specific methods (api.py:599-600) |
| ESLint varsIgnorePattern | INTENTIONAL — `'^[A-Z_]'` is standard pattern for constants |
| console.log remaining | Only console.error/warn in catch blocks (9 total) — acceptable |

### CORRECTED in plan (inaccurate counts):
| Issue | Plan Said | Actual (Verified) |
|-------|-----------|-------------------|
| `payload.dict()` locations | 1 | **4** (routes_system.py:441, routes_stations.py:67, routes_stations.py:93, routes_auth.py:172) |
| Pydantic `__init__` overrides | 1 | **2** (routes_auth.py:111, routes_auth.py:199) |
| Version inconsistency files | 7 | **22+** files with **6 different** version numbers |
| Test count | 312 | **322** across 13 files |
| print() runtime count | 79 | **48** (excluding build.py); 55 including build.py |
| Version numbers | — | 6 distinct: v3.2.0, v3.0.0, v2.4.2, v2.2.0, v2.1.0 |

### NEW ISSUES discovered during verification:
| Issue | Evidence |
|-------|----------|
| `set_decrement_callback()` zero callers — processing count never decrements | video_worker.py:26 defined, never called; `_decrement_callback` always None |
| AGENTS.md duplicate PROJECT STRUCTURE section | Lines 19-38 and 207-214 overlap |
| CONTRIBUTING.md CI section lists 3 jobs, branch protection references 5 | Line 183-188 vs line 147-165 |
| `%TEMP%/openjarvis/` untracked garbage in working tree | `git status` shows `?? %TEMP%/` |
| ROADMAP.md math error | Says 298 but 84+77+108+28=297 |

---

## PHASE 1: CRITICAL + HIGH Fixes (15 issues)

> These affect correctness, security, or will cause runtime crashes.

### Batch 1A: Frontend Stale Closure + Dependencies (3 agents parallel)

**Agent 1: Fix fetchRecords stale closure** (`App.jsx`)
- **Issue**: `fetchRecords()` reads `dateFrom`/`dateTo`/`statusFilter` from closure (lines 659-661), not refs
- **Impact**: SSE-triggered record refreshes ignore date/status filters → user sees wrong data
- **Mitigating factor**: Separate useEffect (line 634) re-fetches on filter change, so stale data gets quickly overwritten
- **Fix**: Change lines 659-661 to use `dateFromRef.current`, `dateToRef.current`, `statusFilterRef.current`
- **While at it**: `stationsIdStr` (line 384) should be memoized with `useMemo` — currently causes unnecessary SSE reconnects every render
- **Verification**: `npm run build` + `npm run lint` pass

**Agent 2: Fix requirements.txt** (3 issues, all verified DEAD)
- **Issue 2a**: `requests` missing from requirements.txt → `telegram_bot.py:151-155` uses `requests.post()` as fallback
  - Fix: Add `requests>=2.31.0` to requirements.txt
- **Issue 2b**: `SQLAlchemy>=2.0.0` in requirements.txt — ZERO imports anywhere in codebase
  - Fix: Remove from requirements.txt
- **Issue 2c**: `opencv-python>=4.8.0` in requirements.txt — only `test_rtsp.py:25` imports cv2 (standalone CLI tool)
  - Fix: Remove from requirements.txt, optionally add to requirements-dev.txt
- **Verification**: `pip install -r requirements.txt` succeeds

**Agent 3: Fix broken test assertion** (`tests/test_database.py`)
- **Issue**: Line 218: `assert all(r[6] == "S1" or True for r in results)` — `or True` makes assertion always pass
- **Fix**: Remove `or True`, fix assertion to test actual expected value
- **Verification**: `pytest tests/test_database.py::TestRecordQueries::test_get_records_by_station -v`

### Batch 1B: Raw sqlite3 + Version Consistency (2 agents parallel)

**Agent 4: Fix raw sqlite3.connect() bypass** (3 files, verified)
- **Issue**: Production code bypasses `database.get_connection()`, missing PRAGMA foreign_keys=ON, WAL mode
  - `telegram_bot.py:52` → `with sqlite3.connect(database.DB_FILE) as conn:`
  - `cloud_sync.py:63,74` → `with sqlite3.connect(DB_FILE) as conn:` (even has TODO comment at line 62!)
  - `routes_system.py:529-532` → `try: database.get_connection() except AttributeError: sqlite3.connect(database.DB_FILE)`
- **Note**: `database.py:132,148` are INTERNAL (get_connection() implementation) — NOT issues
- **Fix**:
  - All 3 files → use `database.get_connection()` directly
  - Remove `import sqlite3` from files where no longer needed
  - Remove TODO comment from cloud_sync.py
- **Verification**: `pytest tests/ -q` + syntax check

**Agent 5: Fix version inconsistency** (22+ files, 6 different versions!)
- **Source of truth**: `VERSION` file = `v3.2.0`
- **Files needing v3.2.0 update** (will bump to v3.3.0 on release):
  - Frontend headers (v2.4.2): `App.jsx`, `VideoPlayerModal.jsx`, `UserManagementModal.jsx`, `SystemHealth.jsx`, `SetupModal.jsx`, `Dashboard.jsx`
  - Frontend header (v2.2.0): `main.jsx`
  - Frontend package (3.0.0): `package.json`
  - Backend headers (v2.1.0): `telegram_bot.py`, `recorder.py`, `database.py`, `auth.py`, `build.py`, `cloud_sync.py`, `network.py`, `video_worker.py`
  - Backend headers (v3.0.0): `routes_system.py`, `routes_auth.py`, `routes_records.py`, `routes_stations.py`
  - README.md (v2.1.0): lines 1, 7, 25
  - Standalone (v2.1.0): `test_rtsp.py`
- **Verification**: `grep -r "v2\.\|v3\.0" *.py web-ui/src/*.jsx README.md` shows no stale versions

### Batch 1C: Remaining HIGH Issues (3 agents parallel)

**Agent 6: Delete dead files + dependencies** (all verified DEAD with zero callers)
- Delete `web-ui/src/App.css` (182 lines dead Vite boilerplate, zero imports)
- `npm uninstall react-router-dom` (zero imports in any .jsx/.js file)
- Remove unused `import sqlite3` from `routes_system.py:21` (if not needed after Agent 4)
- **Verification**: `npm run build` + `npm run lint` pass

**Agent 7: Add missing dev dependencies + fix CI** (all verified missing)
- Add `pytest-cov` and `pytest-timeout` to `requirements-dev.txt` (currently only has pre-commit, ruff, pytest, httpx)
- Fix CI cache key `.github/workflows/ci.yml:86`:
  ```yaml
  # FROM:
  key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
  # TO:
  key: v1-${{ runner.os }}-pip-${{ hashFiles('requirements.txt', 'requirements-dev.txt') }}
  ```
- Add security lint rules to `ruff.toml` (currently only E, F, W):
  ```toml
  select = ["E", "F", "W", "S", "B", "SIM", "UP", "I"]
  ignore = ["E501", "E402", "F811", "F541", "W291", "E741", "S101"]
  ```
- **Verification**: `ruff check .` — expect new findings, fix or ignore as needed

**Agent 8: Create tests/test_recorder.py** (422 lines, ZERO test coverage verified)
- Mock `subprocess.Popen` and `subprocess.run` for FFmpeg
- Test cases (~15-18):
  - 3 recording modes × start/stop (9)
  - Stop lifecycle (4): already stopped, double stop, stop without start
  - `_detect_hw_encoder` (2): mock subprocess result
  - `_is_hevc` (2): mock ffprobe output
  - Edge cases (2-3): empty waybill, long filename, special chars
- **Verification**: `pytest tests/test_recorder.py -v` all pass

---

## PHASE 2: MEDIUM Fixes (20 issues)

### Batch 2A: Backend Code Quality (3 agents parallel)

**Agent 9: Replace print() with logging** (48 runtime calls verified)
- Replace with `logging.info/debug/warning/error` as appropriate
- Add `logger = logging.getLogger(__name__)` to each module
- Skip test files (print acceptable in tests)
- Skip `test_rtsp.py` (standalone CLI tool)
- Optionally skip `build.py` (build script, 7 prints)
- **Exact counts**:
  - routes_system.py: 11 (lines 93,131,162,171,172,216,273,387,519,833,882)
  - database.py: 10 (lines 40,115,117,269,306,308,395,771,773,794)
  - api.py: 8 (lines 120,139,152,247,429,469,476,479)
  - recorder.py: 7 (lines 64,69,302,304,327,389,406)
  - build.py: 7 (lines 11,14,21,25,29,58,59) — optional
  - cloud_sync.py: 4 (lines 104,141,143,157)
  - video_worker.py: 4 (lines 64,135,164,202)
  - telegram_bot.py: 2 (lines 98,102)
  - auth.py: 1 (line 47)
  - routes_records.py: 1 (line 361)
- **Verification**: `ruff check .` + `pytest tests/ -q`

**Agent 10: Pydantic v2 migration + code cleanup** (4 dict() + 2 __init__)
- **`payload.dict()` → `payload.model_dump()`** (4 verified locations):
  - `routes_system.py:441`: `data = payload.dict()`
  - `routes_stations.py:67`: `new_id = database.add_station(payload.dict())`
  - `routes_stations.py:93`: `database.update_station(station_id, payload.dict())`
  - `routes_auth.py:172`: `kwargs = {k: v for k, v in payload.dict().items() if v is not None}`
    → Can simplify to `payload.model_dump(exclude_none=True)`
- **Pydantic `__init__` override → `@field_validator`** (2 verified locations):
  - `routes_auth.py:111-113`: `ChangePasswordPayload.__init__` calls `self._validate_pwd()`
  - `routes_auth.py:199-202`: `ResetPasswordPayload.__init__` with inline length check
- **Verification**: `pytest tests/ -q` + syntax check

**Agent 11: Dead code removal** (all verified DEAD with zero production callers)
- `database.py:457` `save_record()` — only called from tests/test_database.py → remove function + test
- `database.py:550` `get_records()` — only called from tests → remove function + update tests to use v2
- `auth.py:58` `hash_password()` — only called from tests; production uses inline `bcrypt.hashpw()` in database.py → remove function + test
- `video_worker.py:26` `set_decrement_callback()` — ZERO callers anywhere → remove function + `_decrement_callback` variable + dead code at lines 59-61
- `_MAX_RECORDING_SECONDS`: Remove duplicate from `recorder.py:14`, import from `api.py`
- Remove redundant `sys.path.insert` from 12 individual test files (already in conftest.py:6)
- Delete `%TEMP%/` untracked garbage directory
- **Verification**: `pytest tests/ -q` + `grep` confirms no callers

### Batch 2B: Frontend Code Quality (2 agents parallel)

**Agent 12: Replace window.confirm with custom UI** (2 verified instances)
- `UserManagementModal.jsx:183`: `window.confirm(\`Xoá user "${user.username}"?\`)`
- `UserManagementModal.jsx:237`: `window.confirm(\`Kết thúc phiên của "${username}"?\`)`
- Note: App.jsx already has `showConfirmDialog` pattern (line 302) — migrate to use it
- Note: No `window.alert` calls remain (already fixed)
- **Verification**: `npm run build` + `npm run lint`

**Agent 13: Fix Vietnamese diacritics + docs references**
- `VideoPlayerModal.jsx:152`: `Ma van don:` → `Mã vận đơn:`
- `VideoPlayerModal.jsx:267`: `title="Chup khung hinh hien tai"` → `title="Chụp khung hình hiện tại"`
- `VideoPlayerModal.jsx:298`: `title="Tai video xuong"` → `title="Tải video xuống"`
- Fix `AGENTS.md:56`: "see RULES.md" → "see .ai-sync/RULES.md"
- **Verification**: `npm run build` + `npm run lint`

### Batch 2C: Large Refactor Preparation

**Agent 14: Refactor _handle_scan_locked** (`routes_records.py`)
- Current: 213-line monolithic function (lines 98-310, verified exact)
- Break into helper functions:
  - `_validate_scan_input()`
  - `_start_recording()`
  - `_stop_recording()`
  - `_handle_scan_result()`
- Keep same API contract, just reorganize internals
- **Verification**: `pytest tests/ -q` + manual scan flow test

---

## PHASE 3: LOW Fixes + Doc Updates (15 issues)

### Batch 3A: Test Quality (2 agents parallel)

**Agent 15: Fix test quality issues**
- `tests/test_auth.py:70,74,85`: Broad `pytest.raises(Exception)` → specific JWT exception types
- `tests/test_security_regression.py:161`: Fix `assert "exception" not in body or r.status_code == 200` → unconditional assertion
- `tests/test_api_hardening.py:31`: Update stale docstring "Empty name is currently accepted"
- `tests/test_api_routes.py:380-386`: Add DB verification to `test_update_user` API test
- Add direct `_parse_semver` unit test (currently only tested indirectly via update-check endpoint)
- **Verification**: `pytest tests/ -q`

**Agent 16: Docs + references cleanup**
- Update `ROADMAP.md` test count: 298 → 322 + fix math error (84+77+108+28=297 not 298)
- Update `QUALITY_CONTROL.md:74` test count: 305 → 322
- Update `QUALITY_CONTROL.md:335` version: v3.0.0 → v3.2.0
- Create `docs/incidents/` directory with `.gitkeep` (referenced in QUALITY_CONTROL.md:326)
- Update `CONTRIBUTING.md` CI section (line 183-188): add ai-sync-check, docs-only-bypass, release-check
- Remove duplicate PROJECT STRUCTURE section from `AGENTS.md` (lines 207-214 duplicate of 19-38)
- **Verification**: Manual review of all updated docs

---

## EXECUTION SUMMARY

| Phase | Batch | Agents | Issues | Files Touched |
|-------|-------|--------|--------|---------------|
| 1 | 1A | 3 parallel | 5 | App.jsx, requirements.txt, test_database.py |
| 1 | 1B | 2 parallel | 25+ | 3 backend .py, 22+ version files |
| 1 | 1C | 3 parallel | 6 | App.css, package.json, requirements-dev.txt, ruff.toml, ci.yml, test_recorder.py |
| 2 | 2A | 3 parallel | 12+ | All backend .py, all test files |
| 2 | 2B | 2 parallel | 5 | UserManagementModal.jsx, VideoPlayerModal.jsx, AGENTS.md |
| 2 | 2C | 1 | 1 | routes_records.py |
| 3 | 3A | 2 parallel | 10+ | test_auth.py, test_security_regression.py, docs/*.md, AGENTS.md |
| **Total** | **7 batches** | **~16 agent runs** | **~50 verified** | **~35 files** |

## VERIFICATION GATES

After each batch:
1. `pytest tests/ -q` — all 322+ tests pass
2. `npm run build` in `web-ui/` — build succeeds (if frontend changed)
3. `npm run lint` in `web-ui/` — 0 errors, 0 warnings (if frontend changed)
4. `ruff check .` — no new issues (if backend changed)
5. `python -c "import py_compile; py_compile.compile('file')"` — syntax OK per changed .py file
6. `lsp_diagnostics` on all changed files — no new errors

## VERSION BUMP

After all phases complete:
1. Update `VERSION` → `v3.3.0`
2. Update `api.py` header → `v3.3.0`
3. Update `package.json` → `3.3.0`
4. Update ALL 22+ file headers → `v3.3.0`
5. Update `RELEASE_NOTES.md` with v3.3.0 entry
6. Run full verification suite
7. Commit + PR to `dev`

## RISK ASSESSMENT

| Change | Risk | Mitigation |
|--------|------|------------|
| fetchRecords refs | Medium — could break SSE record refresh | Test SSE flow manually |
| requirements.txt changes | Low — remove unused, add missing | `pip install -r requirements.txt` fresh test |
| sqlite3 → get_connection() | Medium — different connection semantics | Run full test suite |
| print → logging | Low — behavioral change only | Check log output format |
| _handle_scan_locked refactor | High — core scan flow | Extensive test + manual verification |
| Dead code removal | Low — all verified zero callers | Tests updated accordingly |
| ruff new rules (S, B, SIM, UP) | Medium — may flag many existing issues | Run `ruff check .` first, fix or ignore |

## NOTES

- Phase 1 is the highest priority — addresses correctness and crash risks
- Phase 2 code quality improvements have low regression risk
- Phase 3 is cosmetic and documentation
- `_handle_scan_locked` refactor (Phase 2C) is optional — can defer if user prefers
- `recorder.py` tests (Phase 1C) are the most complex new code — needs careful mocking
- ~48 print() → logging replacement is the largest single change by line count
- `set_decrement_callback()` removal (Phase 2A) silently fixes a bug: processing count never decrements because callback is never wired up
- `%TEMP%/` directory is untracked garbage — add to `.gitignore` or delete
