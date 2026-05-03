# Plan 70: Move All Modules into `vpack/` Package

> **Status:** READY
> **Priority:** HIGH — Step 3 of restructuring
> **Scope:** 12 files move + ~63 import updates in 20+ files
> **Estimated Effort:** 60 min

---

## Prerequisites

- Plan 68 (skeleton) MUST be done
- Plan 69 (state extraction) MUST be done

---

## Goal

Move all Python source files from root into `vpack/` package. Update every import statement across the entire codebase.

---

## File Moves

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

## Import Changes

### Pattern: all bare imports change to package imports

```python
# BEFORE (root-level imports):
import database
import auth
from api import get_rtsp_url
import routes_auth

# AFTER (package imports):
from vpack import database
from vpack import auth
from vpack.state import get_rtsp_url
from vpack.routes import auth as routes_auth
```

### Files that need import updates:

**Production modules (inside vpack/):**
- `vpack/app.py` (was api.py) — imports of cloud_sync, database, network, recorder, telegram_bot, video_worker, routes_*
- `vpack/auth.py` — import database
- `vpack/cloud_sync.py` — import database, telegram_bot
- `vpack/video_worker.py` — import database, recorder, telegram_bot
- `vpack/telegram_bot.py` — import database
- `vpack/state.py` — any module-level imports
- `vpack/routes/auth.py` — import auth, database, state
- `vpack/routes/records.py` — import auth, database, network, video_worker, recorder, state
- `vpack/routes/stations.py` — import database, network, state
- `vpack/routes/system.py` — import cloud_sync, database, video_worker, telegram_bot, network, state

**Test files:**
- `tests/conftest.py` — import auth, database, vpack.app, vpack.routes.auth
- `tests/test_auth.py`
- `tests/test_database.py`
- `tests/test_database_edge_cases.py`
- `tests/test_video_search.py`
- `tests/test_api_helpers.py`
- `tests/test_api_hardening.py`
- `tests/test_api_routes.py`
- `tests/test_auto_stop_timer.py`
- `tests/test_recorder.py`
- `tests/test_video_worker.py`
- `tests/test_cloud_sync.py`
- `tests/test_telegram.py`
- `tests/test_network.py`
- `tests/test_security_regression.py`
- `tests/seed_e2e.py`

**Migration files:**
- `migrations/env.py` — import database → from vpack import database
- `migrations/versions/crypto_v1_to_v2_crypto_v1_to_v2.py` — same

**Build/script files (file-path references, NOT Python imports — will break silently):**
- `build.py` — Line 59: `"api.py"` PyInstaller entry point → must update to `"vpack/app.py"` or use package entry. **CRITICAL: build will hard-fail if not updated.**
- `scripts/bump_version.py` — Line 26: `root_dir / "api.py"` → `root_dir / "vpack" / "app.py"`. Will silently fail to update version header.
- `scripts/check_version_consistency.py` — Line 21: `root_dir / "api.py"` → `root_dir / "vpack" / "app.py"`. Will silently stop checking version consistency — CI always green even when broken.

---

## Special Cases

### `vpack/app.py` route registration

```python
# BEFORE:
import routes_auth
import routes_records
import routes_stations
import routes_system

routes_auth.register_routes(app)
routes_records.register_routes(app)
routes_stations.register_routes(app)
routes_system.register_routes(app)

# AFTER:
from vpack.routes import auth as routes_auth
from vpack.routes import records as routes_records
from vpack.routes import stations as routes_stations
from vpack.routes import system as routes_system

routes_auth.register_routes(app)
routes_records.register_routes(app)
routes_stations.register_routes(app)
routes_system.register_routes(app)
```

### Remove all `sys.path.insert()` hacks

These files have manual `sys.path` manipulation. Remove them (editable install handles this):
- `tests/conftest.py` — remove `sys.path.insert(0, ...)`
- `migrations/env.py` — remove `sys.path.insert(0, ...)`
- `migrations/versions/crypto_v1_to_v2_crypto_v1_to_v2.py` — remove `sys.path.insert(0, ...)`
- `tests/seed_e2e.py` — remove `sys.path.insert(0, ...)`

### `database.py` imports `auth`

Currently: `from auth import verify_token` (inside function)
After: `from vpack.auth import verify_token`

### `vpack/state.py` cross-references

After Plan 69, `state.py` already imports from other modules (e.g., `database`, `network`). After Plan 70 moves those modules into `vpack/`, `state.py` needs relative imports updated:
- `import database` → `from vpack import database`
- Any other module-level imports in `state.py` need `vpack.` prefix

### `build.py` PyInstaller hidden imports

Check ALL `--hidden-import` flags in `build.py` that reference root module names:
- `--hidden-import=auth` → `--hidden-import=vpack.auth`
- `--hidden-import=database` → `--hidden-import=vpack.database`
- `--hidden-import=routes_auth` → `--hidden-import=vpack.routes.auth`
- etc. (verify exact list in build.py)

Also update the `Analysis` entry point from `"api.py"` to `"vpack/app.py"`.

---

## Verification

1. `pytest tests/ -v` — ALL tests pass
2. `ruff check .` — no errors
3. `python -c "from vpack.app import app; print(app.title)"` — works
4. `python -c "from vpack import database; print(database.DB_FILE)"` — works
5. No `.py` source files remain in root
6. No `sys.path.insert` hacks remain anywhere
7. `python build.py` — PyInstaller build succeeds (entry point updated)
8. `python scripts/bump_version.py --check` — version consistency check works

## After This Plan

All Python source code in `vpack/`. Root has only configs, scripts, docs. **`build.py` and version scripts MUST be updated in this plan** or they will break. Server still starts with `python -m uvicorn api:app` (old way) — Plan 71 updates start scripts/Dockerfile to `vpack.app:app`.
