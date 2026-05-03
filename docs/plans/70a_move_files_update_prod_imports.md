# Plan 70A: Move ALL Modules into `vpack/` + Update Production Imports

> **Status:** READY
> **Priority:** HIGH — Step 3A of restructuring (ATOMIC)
> **Scope:** 12 files moved + 10 production import updates
> **Estimated Effort:** 30 min

---

## Prerequisites

- Plan 68 (skeleton) MUST be done
- Plans 69A/69B/69C (state extraction) MUST be done

---

## Goal

Move ALL 12 Python source files from root into `vpack/` package in a single atomic commit. Update all production module imports to use `vpack.` prefix.

**This commit must be atomic** — after this step, no root-level `.py` source files remain (except `build.py` which Plan 70C handles).

---

## File Moves (ALL at once)

### Root → `vpack/`
| Source | Destination |
|--------|-------------|
| `api.py` | `vpack/app.py` |
| `auth.py` | `vpack/auth.py` |
| `database.py` | `vpack/database.py` |
| `network.py` | `vpack/network.py` |
| `recorder.py` | `vpack/recorder.py` |
| `video_worker.py` | `vpack/video_worker.py` |
| `cloud_sync.py` | `vpack/cloud_sync.py` |
| `telegram_bot.py` | `vpack/telegram_bot.py` |

### Root → `vpack/routes/`
| Source | Destination |
|--------|-------------|
| `routes_auth.py` | `vpack/routes/auth.py` |
| `routes_records.py` | `vpack/routes/records.py` |
| `routes_stations.py` | `vpack/routes/stations.py` |
| `routes_system.py` | `vpack/routes/system.py` |

---

## Import Updates (production modules only)

### Pattern

```python
# BEFORE:
import database
import auth
from api import get_rtsp_url
import routes_auth

# AFTER:
from vpack import database
from vpack import auth
from vpack.state import get_rtsp_url
from vpack.routes import auth as routes_auth
```

### File-by-file changes:

#### `vpack/app.py` (was api.py)
- `import routes_auth` → `from vpack.routes import auth as routes_auth`
- `import routes_records` → `from vpack.routes import records as routes_records`
- `import routes_stations` → `from vpack.routes import stations as routes_stations`
- `import routes_system` → `from vpack.routes import system as routes_system`
- `import cloud_sync` → `from vpack import cloud_sync`
- `import database` → `from vpack import database`
- `import network` → `from vpack import network`
- `import recorder` → `from vpack import recorder`
- `import telegram_bot` → `from vpack import telegram_bot`
- `import video_worker` → `from vpack import video_worker`
- `from vpack import state` (already done in Plan 69A)
- Keep `routes_*.register_routes(app)` calls unchanged

#### `vpack/auth.py`
- `import database` → `from vpack import database`

#### `vpack/database.py`
- `from auth import SECRET_KEY` (lazy, inside `_get_enc_key()` line 30) → `from vpack.auth import SECRET_KEY`
- `from auth import SECRET_KEY` (lazy, inside `_decrypt_value()` line 86) → `from vpack.auth import SECRET_KEY`
**NOTE**: Plan previously said `verify_token` but actual import is `SECRET_KEY` (appears twice).

#### `vpack/cloud_sync.py`
- `import database` → `from vpack import database`
- `import telegram_bot` → `from vpack import telegram_bot`
- `from database import get_setting` → `from vpack.database import get_setting`

#### `vpack/video_worker.py`
- `import database` → `from vpack import database`
- `import recorder` → `from vpack import recorder`
- `import telegram_bot` → `from vpack import telegram_bot`
- `import api` (lazy, inside `_decrement_processing()` line 58) → `from vpack import state` (already done in Plan 69B)
- `import api` (lazy, inside `_notify_sse_safe()` line 72) → `from vpack import state` (already done in Plan 69B)

#### `vpack/telegram_bot.py`
- `import database` → `from vpack import database`

#### `vpack/state.py`
- Check ALL module-level imports for root module references
- `import database` → `from vpack import database` (if present)
- `import network` → `from vpack import network` (if present)
- Any other root imports need `vpack.` prefix

#### `vpack/routes/auth.py`
- **`import api`** (line 13) → **remove** (already migrated to `from vpack import state` in Plan 69B)
- `import auth` → `from vpack import auth`
- `import database` → `from vpack import database`
- `from auth import AdminUser, CurrentUser` → `from vpack.auth import AdminUser, CurrentUser`

#### `vpack/routes/records.py`
- **`import api`** (line 24) → **remove** (already migrated to `from vpack import state` in Plan 69B)
- `import auth` → `from vpack import auth`
- `from auth import AdminUser, CurrentUser` → `from vpack.auth import AdminUser, CurrentUser`
- `import database` → `from vpack import database`
- `import network` → `from vpack import network`
- `import video_worker` → `from vpack import video_worker`
- `from recorder import CameraRecorder` → `from vpack.recorder import CameraRecorder`

#### `vpack/routes/stations.py`
- **`import api`** (line 13) → **remove** (already migrated to `from vpack import state` in Plan 69B)
- `import database` → `from vpack import database`
- `import network` → `from vpack import network`
- `from auth import AdminUser, CurrentUser` → `from vpack.auth import AdminUser, CurrentUser`

#### `vpack/routes/system.py`
- **`import api`** (line 32) → **remove** (already migrated to `from vpack import state` in Plan 69B)
- `import cloud_sync` → `from vpack import cloud_sync`
- `import database` → `from vpack import database`
- `import video_worker` → `from vpack import video_worker`
- `import telegram_bot` (lazy, inside function line 511) → `from vpack import telegram_bot` (can keep lazy pattern)
- `import network` (lazy, inside function line 819) → `from vpack import network` (can keep lazy pattern)
- `from auth import AdminUser, CurrentUser` → `from vpack.auth import AdminUser, CurrentUser`

#### Files with NO cross-module imports (just move, no import changes):
- `vpack/network.py` — no root module imports
- `vpack/recorder.py` — no root module imports

---

## Verification

1. `ruff check vpack/` — no errors (import resolution works)
2. `python -c "from vpack.app import app; print(app.title)"` — works
3. `python -c "from vpack import database; print(database.DB_FILE)"` — works
4. `python -c "from vpack import state; print(state.active_recorders)"` — works
5. No `.py` source files remain in root (except `build.py`)
6. Tests will NOT pass yet (test imports not updated — Plan 70B handles this)

## After This Plan

All production code in `vpack/`. Root has no `.py` source files (except `build.py`). Tests are broken until Plan 70B. Server can start with `python -m uvicorn vpack.app:app`.
