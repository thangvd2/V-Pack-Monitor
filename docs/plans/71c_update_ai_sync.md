# Plan 71C: Update `.ai-sync/` Source Files + Sync

> **Status:** READY
> **Priority:** HIGH — Step 4C of restructuring
> **Scope:** 7 `.ai-sync/` files + sync.py regeneration
> **Estimated Effort:** 15 min

---

## Prerequisites

- Plans 70A-C MUST be done (files moved to `vpack/`)

---

## Goal

Update all `.ai-sync/` source files to reflect new `vpack/` layout. Run `sync.py` to regenerate `AGENTS.md` and `.agents/`.

---

## CRITICAL WORKFLOW

1. **Edit** `.ai-sync/` files (source of truth)
2. **Run** `python .ai-sync/sync.py` (auto-generates AGENTS.md, .agents/)
3. **Commit** both `.ai-sync/` changes AND regenerated files together

**DO NOT** edit `AGENTS.md` or `.agents/` files directly — they get overwritten by sync.

---

## Changes

### 1. `.ai-sync/RULES.md`

Update ALL module path references:

**Search-replace patterns** (apply globally):
- `api.py` → `vpack/app.py`
- `routes_auth.py` → `vpack/routes/auth.py`
- `routes_records.py` → `vpack/routes/records.py`
- `routes_stations.py` → `vpack/routes/stations.py`
- `routes_system.py` → `vpack/routes/system.py`
- `auth.py` → `vpack/auth.py`
- `database.py` → `vpack/database.py`
- `recorder.py` → `vpack/recorder.py`
- `video_worker.py` → `vpack/video_worker.py`
- `cloud_sync.py` → `vpack/cloud_sync.py`
- `telegram_bot.py` → `vpack/telegram_bot.py`
- `network.py` → `vpack/network.py`
- `build.py` → `scripts/build.py`
- `start_windows.bat` → `scripts/start_windows.bat`
- `start.sh` → `scripts/start.sh`
- `install_windows.bat` → `scripts/install_windows.bat`
- `install_macos.sh` → `scripts/install_macos.sh`

**Project Structure section**: Full rewrite to reflect new layout:
```
vpack/                    ← Python package
  __init__.py
  app.py                  ← FastAPI app (DO NOT add routes here)
  state.py                ← Shared state (extracted from api.py)
  auth.py, database.py, network.py, recorder.py
  video_worker.py, cloud_sync.py, telegram_bot.py
  routes/
    __init__.py
    auth.py, records.py, stations.py, system.py
scripts/                  ← ALL scripts
  build.py, start.sh, start_windows.bat
  install_macos.sh, install_windows.bat
  inno_setup.iss
  bump_version.py, check_version_consistency.py, test_rtsp.py
```

Key lines: 32, 87, 89, 174, 180, 183-188 + Project Structure section.

### 2. `.ai-sync/CONTEXT.md` (line 24)

`api.py header` → `vpack/app.py header`

### 3. `.ai-sync/MEMORY.md` (lines 44, 54-58, 82)

Update all 6 module path references using same search-replace patterns.

### 4. `.ai-sync/TASKS.md` (line 27)

`api.py header` → `vpack/app.py header`

### 5. `.ai-sync/HANDOFF.md` (lines 40-41)

`routes_records.py` → `vpack/routes/records.py`
`api.py` → `vpack/app.py`

### 6. `.ai-sync/README.md` (line 319)

`routes_*.py` → `vpack/routes/*.py`

### 7. `.ai-sync/workflows/release.md` (lines 18, 71, 79, 100)

4x `api.py` references → `vpack/app.py`
`routes_*.py` → `vpack/routes/*.py`

---

## Sync Step

```bash
python .ai-sync/sync.py
git add .ai-sync/ AGENTS.md .agents/
```

Verify:
- `AGENTS.md` reflects new project structure
- `.agents/rules/project-rules.md` reflects new module paths
- `.agents/workflows/release.md` reflects new module paths

---

## Verification

1. `python .ai-sync/sync.py` — exits 0, no errors
2. `grep -n "api.py" AGENTS.md` — no old `api.py` references (only `vpack/app.py`)
3. `grep -n "routes_" AGENTS.md | grep -v "vpack/routes"` — 0 results
4. `grep -n "api.py" .agents/rules/project-rules.md` — no old references
5. Pre-commit hook will auto-run sync on commit — verify it passes

## After This Plan

`.ai-sync/` source files updated. `AGENTS.md` and `.agents/` auto-regenerated. All AI agent configs reflect new layout.
