# Plan 71D: Update Developer Docs + Cleanup

> **Status:** READY
> **Priority:** MEDIUM — Step 4D of restructuring (final)
> **Scope:** 9 doc files + 2 deletions
> **Estimated Effort:** 20 min

---

## Prerequisites

- Plans 71A-C MUST be done
- All `.ai-sync/` files synced

---

## Goal

Update all developer/user documentation to reflect new file paths. Final cleanup of obsolete files.

---

## Doc Updates

### 1. `CONTRIBUTING.md`

- **Project tree** (lines 208-219): Rewrite to show `vpack/` + `scripts/` layout
- **Release process** (lines 117, 179): `VERSION/api.py/RELEASE_NOTES` → `VERSION/vpack/app.py/RELEASE_NOTES`
- **Script paths** (lines 225-228): `install_windows.bat` → `scripts/install_windows.bat`, etc.

### 2. `README.md`

- **Developer setup** (line 68): `python -m uvicorn api:app` → `python -m uvicorn vpack.app:app`
- **Build command** (line 86): `python build.py` → `python scripts/build.py`
- **Script paths** (lines 37-43, 75-81, 115): All script paths get `scripts/` prefix
- **Troubleshooting**: `install_windows.bat` → `scripts/install_windows.bat`, `build.py` → `scripts/build.py`

### 3. `README_SETUP.md`

- `install_windows.bat` (line 16) → `scripts/install_windows.bat`
- `install_macos.sh` (lines 23-24) → `scripts/install_macos.sh`
- `start_windows.bat` (line 33) → `scripts/start_windows.bat`
- `start.sh` (line 39) → `scripts/start.sh`

### 4. `docs/DESIGN_PATTERNS.md` (30+ references)

**Search-replace ALL** `module.py:NNN` patterns:
- `api.py:NNN` → `vpack/app.py:NNN`
- `database.py:NNN` → `vpack/database.py:NNN`
- `recorder.py:NNN` → `vpack/recorder.py:NNN`
- `auth.py:NNN` → `vpack/auth.py:NNN`
- `video_worker.py:NNN` → `vpack/video_worker.py:NNN`
- `routes_records.py:NNN` → `vpack/routes/records.py:NNN`
- `routes_system.py:NNN` → `vpack/routes/system.py:NNN`
- `routes_stations.py:NNN` → `vpack/routes/stations.py:NNN`
- `routes_auth.py:NNN` → `vpack/routes/auth.py:NNN`
- `telegram_bot.py:NNN` → `vpack/telegram_bot.py:NNN`
- `cloud_sync.py:NNN` → `vpack/cloud_sync.py:NNN`
- `network.py:NNN` → `vpack/network.py:NNN`

**NOTE**: Line numbers (NNN) may have shifted after restructuring. Update to best approximation or remove line numbers if uncertain.

### 5. `docs/BEST_PRACTICES.md` (15+ references)

Same search-replace patterns as DESIGN_PATTERNS.md.

### 6. `docs/QUALITY_CONTROL.md`

- **Module dependency diagram** (lines 152-158): Redraw with `vpack/` package structure
- Any other module path references — same search-replace patterns

### 7. `docs/ROADMAP.md` (line 34)

`database.py + auth.py` → `vpack/database.py + vpack/auth.py`

### 8. `docs/USER_GUIDE_ADMIN.md` (line 545)

`start.sh` / `start_windows.bat` → `scripts/start.sh` / `scripts/start_windows.bat`

### 9. `docs/HARDWARE_REQUIREMENTS.md` (line 96)

`recorder.py` → `vpack/recorder.py`

---

## Cleanup

### Delete `install_log.txt`
Already in `.gitignore` (line 15). If tracked by git, remove: `git rm install_log.txt`.

### Delete `scratch/` directory (local only)
Already in `.gitignore`. Just `rm -rf scratch/` locally.

### Delete `scripts/__pycache__/`
Add `__pycache__/` to `.gitignore` if not already there.

---

## Files That Do NOT Need Updates

- `RELEASE_NOTES.md` — historical changelog, do not rewrite history
- `docs/plans/*.md` (Plans 02-70) — completed historical plans
- `LICENSE`, `VERSION`, `.env.example` — no module path references

---

## Verification

1. `grep -rn "api\.py\|routes_auth\.py\|routes_records\.py\|routes_stations\.py\|routes_system\.py" docs/ README.md README_SETUP.md CONTRIBUTING.md --include="*.md" | grep -v "docs/plans/"` — returns 0 old references
2. `grep -rn "install_windows\.bat\|start_windows\.bat\|start\.sh\|install_macos\.sh\|build\.py" README.md README_SETUP.md CONTRIBUTING.md docs/USER_GUIDE_ADMIN.md` — all use `scripts/` prefix
3. `grep -rn "api:app" README.md CONTRIBUTING.md docs/` — returns 0 results
4. Root folder has only mandatory configs + docs + folders
5. `git status` — `install_log.txt` removed from tracking

## After This Plan

**Restructuring COMPLETE.** Root folder clean (~20 items). All Python code in `vpack/`, all scripts in `scripts/`, all docs updated, all configs updated.
