# Plan 71: Update Configs, Scripts, Docs & Cleanup

> **Status:** READY
> **Priority:** HIGH — Step 4 of restructuring (final)
> **Scope:** 8 scripts moved, 24+ doc/config files updated, 2 deleted
> **Estimated Effort:** 60 min

---

## Prerequisites

- Plans 68, 69, 70 MUST be done
- All tests pass with modules in `vpack/`

---

## Goal

Update all external references to use new `vpack.app:app` entry point. Move 8 root scripts into `scripts/`. Update ALL documentation and config files. Final cleanup.

---

## Part A: Move Scripts to `scripts/`

### 1. `start_windows.bat` → `scripts/start_windows.bat`

Move from root to `scripts/`. Update uvicorn reference:

```batch
REM BEFORE:
python -m uvicorn api:app --host 0.0.0.0 --port 8001

REM AFTER:
python -m uvicorn vpack.app:app --host 0.0.0.0 --port 8001
```

**Important**: Add `cd /d "%~dp0.."` at top to ensure project root is cwd. All `%CD%` paths in the file will then resolve correctly.

### 2. `start.sh` → `scripts/start.sh`

Move from root to `scripts/`. Update uvicorn reference:

```bash
# BEFORE:
python3 -m uvicorn api:app --host 0.0.0.0 --port 8001 &

# AFTER:
python3 -m uvicorn vpack.app:app --host 0.0.0.0 --port 8001 &
```

**Important**: Add `cd "$(dirname "$0")/.."` at top to ensure project root is cwd.

### 3. `build.py` → `scripts/build.py`

Move from root to `scripts/`. Update PyInstaller entry point and hidden imports:

```python
# BEFORE:
a = Analysis(["api.py"], ...)

# AFTER:
a = Analysis(["vpack/app.py"], ...)
```

Also update ALL `--hidden-import` flags: `auth` → `vpack.auth`, `database` → `vpack.database`, etc.

**Important**: Add `PROJECT_ROOT = Path(__file__).resolve().parent.parent` at top. Change `os.chdir("web-ui")` to `os.chdir(PROJECT_ROOT / "web-ui")`. Fix ALL relative paths to use `PROJECT_ROOT / ...`.

### 4. `Install V-Pack Monitor.command` → `scripts/Install V-Pack Monitor.command`

Move from root to `scripts/`. No content changes needed (it calls `install_macos.sh`).

**Important**: `.command` files double-clicked on macOS set cwd to user's home. Verify the script handles this — may need `cd "$(dirname "$0")/.."`.

### 5. `Start V-Pack Monitor.command` → `scripts/Start V-Pack Monitor.command`

Move from root to `scripts/`. Update uvicorn reference:

```bash
# BEFORE:
python3 -m uvicorn api:app

# AFTER:
python3 -m uvicorn vpack.app:app
```

Same cwd considerations as above.

### 6. `install_windows.bat` → `scripts/install_windows.bat`

Move from root to `scripts/`. Add `pip install -e .` step after `pip install -r requirements.txt`.

**Important**: Add `cd /d "%~dp0.."` at top. Verify all `%CD%` path references still resolve.

### 7. `install_macos.sh` → `scripts/install_macos.sh`

Move from root to `scripts/`. Add `pip install -e .` step after `pip install -r requirements.txt`.

**Important**: Add `cd "$(dirname "$0")/.."` at top.

### 8. `inno_setup.iss` → `scripts/inno_setup.iss`

Move from root to `scripts/`. This is the Inno Setup config for Windows installer.

**Important**: Update file paths inside the ISS file that reference root-level files (e.g., `OutputDir=.\installer`, source executable path, icon path). These may use relative paths from the ISS file location.

---

## Part B: Runtime Config Files

### 9. Dockerfile (line 33)

```dockerfile
# BEFORE:
CMD ["sh", "-c", "... python -m uvicorn api:app ..."]

# AFTER:
CMD ["sh", "-c", "... python -m uvicorn vpack.app:app ..."]
```

### 10. `scripts/bump_version.py` (line 26)

```python
# BEFORE:
api_file = root_dir / "api.py"

# AFTER:
api_file = root_dir / "vpack" / "app.py"
```

### 11. `scripts/check_version_consistency.py` (line 21)

```python
# BEFORE:
api_file = root_dir / "api.py"

# AFTER:
api_file = root_dir / "vpack" / "app.py"
```

### 12. `.github/workflows/ci.yml`

Add `pip install -e .` step before pytest. Verify no hardcoded `api.py` references remain.

### 13. `web-ui/playwright.config.ts` (line 29)

```typescript
// BEFORE:
python -m uvicorn api:app

// AFTER:
python -m uvicorn vpack.app:app
```

### 14. `alembic.ini`

No change needed — `migrations/` stays at root level. The `script_location = %(here)s/migrations` path is correct.

---

## Part C: `.ai-sync/` Source Files (EDIT FIRST, then sync)

**CRITICAL WORKFLOW**: Edit `.ai-sync/` files FIRST, then run `python .ai-sync/sync.py` to regenerate `AGENTS.md` and `.agents/rules/project-rules.md`. DO NOT edit `AGENTS.md` or `.agents/` files directly.

### 15. `.ai-sync/RULES.md`

Update ALL module path references (lines 32, 87, 89, 174, 180, 183-188):
- `api.py` → `vpack/app.py`
- `routes_*.py` → `vpack/routes/*.py`
- `database.py` → `vpack/database.py`
- `auth.py` → `vpack/auth.py`
- `video_worker.py` → `vpack/video_worker.py`
- `recorder.py` → `vpack/recorder.py`
- Project Structure section: full rewrite

### 16. `.ai-sync/CONTEXT.md` (line 24)

Update `api.py header` → `vpack/app.py header`

### 17. `.ai-sync/MEMORY.md` (lines 44, 54-58, 82)

Update all 6 module path references.

### 18. `.ai-sync/TASKS.md` (line 27)

Update `api.py header` → `vpack/app.py header`

### 19. `.ai-sync/HANDOFF.md` (lines 40-41)

Update `routes_records.py` → `vpack/routes/records.py`, `api.py` → `vpack/app.py`

### 20. `.ai-sync/README.md` (line 319)

Update `routes_*.py` → `vpack/routes/*.py`

### 21. `.ai-sync/workflows/release.md` (lines 18, 71, 79, 100)

Update 4x `api.py` references → `vpack/app.py`

### After editing all `.ai-sync/` files:

```bash
python .ai-sync/sync.py
git add AGENTS.md .agents/ .ai-sync/
```

This auto-regenerates `AGENTS.md` and `.agents/rules/project-rules.md` from the `.ai-sync/` sources.

---

## Part D: Developer & User Documentation

### 22. `CONTRIBUTING.md`

- **Project tree** (lines 208-219): Full rewrite to reflect `vpack/` layout and `scripts/` layout
- **Release process** (lines 117, 179): `VERSION/api.py/RELEASE_NOTES` → `VERSION/vpack/app.py/RELEASE_NOTES`
- **Script paths** (lines 225-228): Update `install_windows.bat` → `scripts/install_windows.bat`, etc.

### 23. `README.md`

- **Developer setup command** (line 68): `python -m uvicorn api:app` → `python -m uvicorn vpack.app:app`
- **Build command** (line 86): `python build.py` → `python scripts/build.py`
- **Script paths** (lines 37-43, 75-81, 115): Update all script paths to `scripts/` prefix
- **Troubleshooting** section: Update `install_windows.bat` → `scripts/install_windows.bat`

### 24. `README_SETUP.md`

Update script paths:
- `install_windows.bat` (line 16) → `scripts/install_windows.bat`
- `install_macos.sh` (lines 23-24) → `scripts/install_macos.sh`
- `start_windows.bat` (line 33) → `scripts/start_windows.bat`
- `start.sh` (line 39) → `scripts/start.sh`

### 25. `docs/DESIGN_PATTERNS.md`

**30+ references** to `module.py:line` format. Update ALL:
- `api.py:NNN` → `vpack/app.py:NNN` (line numbers may shift — update to best approximation)
- `database.py:NNN` → `vpack/database.py:NNN`
- `recorder.py:NNN` → `vpack/recorder.py:NNN`
- `auth.py:NNN` → `vpack/auth.py:NNN`
- `video_worker.py:NNN` → `vpack/video_worker.py:NNN`
- `routes_records.py:NNN` → `vpack/routes/records.py:NNN`
- `routes_system.py:NNN` → `vpack/routes/system.py:NNN`
- `routes_stations.py:NNN` → `vpack/routes/stations.py:NNN`
- `telegram_bot.py:NNN` → `vpack/telegram_bot.py:NNN`
- `cloud_sync.py:NNN` → `vpack/cloud_sync.py:NNN`
- `network.py:NNN` → `vpack/network.py:NNN`

### 26. `docs/BEST_PRACTICES.md`

**15+ references** — same pattern as DESIGN_PATTERNS.md. Update ALL module path references.

### 27. `docs/QUALITY_CONTROL.md`

- **Module dependency diagram** (lines 152-158): Redraw with `vpack/` package structure
- Any other module path references

### 28. `docs/ROADMAP.md` (line 34)

Update `database.py + auth.py` → `vpack/database.py + vpack/auth.py`

### 29. `docs/USER_GUIDE_ADMIN.md` (line 545)

Update `start.sh` / `start_windows.bat` → `scripts/start.sh` / `scripts/start_windows.bat`

### 30. `docs/HARDWARE_REQUIREMENTS.md` (line 96)

Update `recorder.py` → `vpack/recorder.py`

---

## Part E: Files That Do NOT Need Updates

### DO NOT UPDATE (historical records):
- `RELEASE_NOTES.md` — historical changelog, do not rewrite history
- `docs/plans/*.md` (Plans 02-70) — completed historical plans, reference old paths intentionally
- `docs/plans/67-71` — these are the restructuring plans themselves, will be marked DONE after implementation

### No changes needed (verified):
- `alembic.ini` — no module path references
- `ruff.toml` — no module path references (updated in Plan 68 with `src = ["vpack"]`)
- `.pre-commit-config.yaml` — no module path references
- `.env.example` — no module path references
- `LICENSE` — no module path references
- `VERSION` — no module path references

---

## Part F: Cleanup

### Delete `install_log.txt`
Tracked artifact that should not be in repo. Add to `.gitignore`.

### Delete `scratch/` directory (local only)
Already in `.gitignore`. Contains one-off scripts. `rm -rf scratch/`.

### Delete `scripts/__pycache__/`
Cleanup artifact.

---

## Scripts Move Summary

| Root File | Destination | Key Risk |
|-----------|-------------|----------|
| `start_windows.bat` | `scripts/start_windows.bat` | `%CD%` paths → add `cd /d "%~dp0.."` at top |
| `start.sh` | `scripts/start.sh` | relative paths → add `cd "$(dirname "$0")/.."` at top |
| `build.py` | `scripts/build.py` | `os.chdir("web-ui")` → use `PROJECT_ROOT` |
| `Install V-Pack Monitor.command` | `scripts/Install V-Pack Monitor.command` | macOS .command cwd = home → verify cd logic |
| `Start V-Pack Monitor.command` | `scripts/Start V-Pack Monitor.command` | update uvicorn + cwd |
| `install_windows.bat` | `scripts/install_windows.bat` | `%CD%` paths → add `cd /d "%~dp0.."` |
| `install_macos.sh` | `scripts/install_macos.sh` | relative paths → add `cd "$(dirname "$0")/.."` |
| `inno_setup.iss` | `scripts/inno_setup.iss` | update source/output paths inside ISS file |

**Total: 8 scripts moved from root to `scripts/`**

---

## Doc Update Summary

| Category | Count | Files |
|----------|-------|-------|
| `.ai-sync/` source files | 7 | RULES, CONTEXT, MEMORY, TASKS, HANDOFF, README, workflows/release |
| Developer/user docs | 9 | CONTRIBUTING, README, README_SETUP, DESIGN_PATTERNS, BEST_PRACTICES, QUALITY_CONTROL, ROADMAP, USER_GUIDE_ADMIN, HARDWARE_REQUIREMENTS |
| Runtime configs | 5 | Dockerfile, bump_version.py, check_version_consistency.py, ci.yml, playwright.config.ts |
| Auto-generated (via sync) | 2 | AGENTS.md, .agents/rules/project-rules.md |
| **DO NOT update** | — | RELEASE_NOTES.md, docs/plans/ (historical) |

**Total: 24 files manually updated + 2 auto-generated**

---

## Verification

1. `pytest tests/ -v` — ALL tests pass
2. `ruff check .` — no errors
3. `python -m uvicorn vpack.app:app --host 0.0.0.0 --port 8001` — server starts
4. `docker build .` — Docker image builds
5. `python scripts/build.py` — PyInstaller executable builds
6. Root folder has only: mandatory configs + mandatory docs + dotfiles + `VERSION` + `requirements*.txt` + folders
7. No `.py` source files in root
8. `grep -r "api:app" . --include="*.sh" --include="*.bat" --include="*.yml" --include="*.ts"` returns 0 results
9. `grep -r "sys.path.insert" tests/ migrations/` returns 0 results
10. Each moved script correctly resolves to project root before executing
11. `python .ai-sync/sync.py` succeeds, `AGENTS.md` reflects new structure
12. `grep -r "routes_.*\.py" docs/ --include="*.md" --exclude-dir=plans` — no old path references remain in active docs

## After This Plan

Restructuring complete. Root folder clean (~20 items: configs + docs + folders). All Python code in `vpack/`, all scripts in `scripts/`, all docs updated.
