# Plan 70B: Update Test + Migration File Imports

> **Status:** READY
> **Priority:** HIGH — Step 3B of restructuring
> **Scope:** 16 test files + 2 migration files
> **Estimated Effort:** 20 min

---

## Prerequisites

- Plan 70A (files moved, production imports updated) MUST be done

---

## Goal

Update all Python import statements in test and migration files from root module names to `vpack.` package imports. Remove `sys.path.insert()` hacks.

---

## Test Files (16 files)

### Pattern

```python
# BEFORE:
import api
import auth
import database
from api import get_rtsp_url
from auth import verify_token
from database import init_db

# AFTER:
import vpack.app as api              # For app and remaining api.py functions
from vpack import auth
from vpack import database
from vpack.state import get_rtsp_url
from vpack.auth import verify_token
from vpack.database import init_db
```

### File-by-file:

#### `tests/conftest.py`
- `import auth` (line 11, top-level) → `from vpack import auth`
- `import database` (line 12, top-level) → `from vpack import database`
- `import api` (line 88, inside fixture) → `import vpack.app as api` (needs api.app FastAPI object)
- `import routes_auth` (line 89, inside fixture) → `from vpack.routes import auth as routes_auth`
- `from vpack import state` (already done in Plan 69C)
- Remove `sys.path.insert(0, ...)` hack (line 7)

#### `tests/test_auth.py`
- `import auth` → `from vpack import auth`
- `import database` → `from vpack import database`

#### `tests/test_database.py`
- `import database` → `from vpack import database`
- `from database import (...)` → `from vpack.database import (...)`

#### `tests/test_database_edge_cases.py`
- `import database` → `from vpack import database`
- `from database import (...)` → `from vpack.database import (...)`

#### `tests/test_video_search.py`
- `import database` → `from vpack import database`

#### `tests/test_api_helpers.py`
- `from vpack.state import get_rtsp_sub_url, get_rtsp_url` (already done in Plan 69C, verify)

#### `tests/test_api_hardening.py`
- `import auth` → `from vpack import auth`
- `import database` → `from vpack import database`
- `import routes_system` → `from vpack.routes import system as routes_system`

#### `tests/test_api_routes.py`
- `import auth` → `from vpack import auth`
- `import database` → `from vpack import database`

#### `tests/test_auto_stop_timer.py`
- **`import api`** (line 5, top-level) → `import vpack.app as api`
- `import database` → `from vpack import database`
- `import video_worker` → `from vpack import video_worker`
- `from vpack import state` (already done in Plan 69C, verify)
- **IMPORTANT**: Patch targets also need updating (done in Plan 69C, verify):
  - `patch.object(api, "_preflight_checks", ...)` → `patch.object(state, "_preflight_checks", ...)`
  - `patch.object(api, "notify_sse", ...)` → `patch.object(state, "notify_sse", ...)`

#### `tests/test_recorder.py`
- `import recorder` → `from vpack import recorder`
- `from recorder import CameraRecorder, _detect_hw_encoder` → `from vpack.recorder import CameraRecorder, _detect_hw_encoder`

#### `tests/test_video_worker.py`
- `import database` → `from vpack import database`
- `import video_worker` → `from vpack import video_worker`
- Patches `"api._get_video_info_external"` → `"vpack.app._get_video_info_external"` (function stays in app.py)
- **Also update these patch targets:**
  - `patch("video_worker._process_stop_and_save")` (line 37) → `patch("vpack.video_worker._process_stop_and_save")`
  - `patch("video_worker._get_video_info")` (line 128) → `patch("vpack.video_worker._get_video_info")`
- `api._recover_pending_records()` → `vpack.app._recover_pending_records()` or keep `import vpack.app as api`

#### `tests/test_cloud_sync.py`
- `import cloud_sync` → `from vpack import cloud_sync`

#### `tests/test_telegram.py`
- `import telegram_bot` → `from vpack import telegram_bot`

#### `tests/test_network.py`
- `import database` → `from vpack import database`
- `import network` → `from vpack import network`

#### `tests/test_security_regression.py`
- `import auth` → `from vpack import auth`
- `import database` → `from vpack import database`

#### `tests/seed_e2e.py`
- `import database` → `from vpack import database`
- Remove `sys.path.insert(0, ...)` hack if present

---

## Migration Files (2 files)

#### `migrations/env.py`
- `import database` → `from vpack import database`
- Remove `sys.path.insert(0, ...)` hack

#### `migrations/versions/crypto_v1_to_v2_crypto_v1_to_v2.py`
- `import database` → `from vpack import database`
- Remove `sys.path.insert(0, ...)` hack

---

## sys.path.insert Removal

These 4 files have manual `sys.path` manipulation. Remove ALL of them (editable install handles this):
1. `tests/conftest.py`
2. `tests/seed_e2e.py`
3. `migrations/env.py`
4. `migrations/versions/crypto_v1_to_v2_crypto_v1_to_v2.py`

---

## Verification

1. `pytest tests/ -v` — ALL tests pass
2. `ruff check tests/ migrations/` — no errors
3. `grep -rn "sys.path.insert" tests/ migrations/` — returns 0 results
4. `grep -rn "^import api$\|^import auth$\|^import database$\|^import recorder$\|^import video_worker$\|^import cloud_sync$\|^import telegram_bot$\|^import network$" tests/` — returns 0 results (no bare root imports remain)

## After This Plan

All test and migration imports updated. Tests pass. No `sys.path.insert` hacks remain. All Python code uses `vpack.` package imports.
