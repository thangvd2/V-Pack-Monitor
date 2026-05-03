# Plan 71: Update Configs, Scripts, Docs & Cleanup

> **Status:** READY
> **Priority:** HIGH — Step 4 of restructuring (final)
> **Scope:** 10+ external files updated, 7 scripts moved, 2 deleted
> **Estimated Effort:** 45 min

---

## Prerequisites

- Plans 68, 69, 70 MUST be done
- All tests pass with modules in `vpack/`

---

## Goal

Update all external references (Dockerfile, scripts, CI, docs) to use new `vpack.app:app` entry point. Move 7 root scripts into `scripts/`. Final cleanup.

---

## Changes

### 1. Dockerfile (line 33)

```dockerfile
# BEFORE:
CMD ["python", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8001"]

# AFTER:
CMD ["python", "-m", "uvicorn", "vpack.app:app", "--host", "0.0.0.0", "--port", "8001"]
```

### 2. `start_windows.bat` → `scripts/start_windows.bat`

Move from root to `scripts/`. Update uvicorn reference:

```batch
REM BEFORE:
python -m uvicorn api:app --host 0.0.0.0 --port 8001

REM AFTER:
python -m uvicorn vpack.app:app --host 0.0.0.0 --port 8001
```

**Important**: All paths in this file use `%CD%` (current directory). If user runs from project root, paths still work. Verify `cd` commands inside the script still resolve correctly from new location, or add a `cd ..` at script start to return to project root.

### 3. `start.sh` → `scripts/start.sh`

Move from root to `scripts/`. Update uvicorn reference:

```bash
# BEFORE:
python3 -m uvicorn api:app --host 0.0.0.0 --port 8001 &

# AFTER:
python3 -m uvicorn vpack.app:app --host 0.0.0.0 --port 8001 &
```

**Important**: Same as above — verify relative paths (`recordings/`, `web-ui/`, `bin/`) still resolve. Add `cd "$(dirname "$0")/.."` at top to ensure project root is cwd.

### 4. `build.py` → `scripts/build.py`

Move from root to `scripts/`. Update PyInstaller entry point:

```python
# BEFORE:
a = Analysis(["api.py"], ...)

# AFTER:
a = Analysis(["vpack/app.py"], ...)
```

Also update any `--hidden-import` flags if they reference root module names.
**Important**: `build.py` uses `os.chdir("web-ui")` and other relative paths. Add `os.chdir(PROJECT_ROOT)` at the top where `PROJECT_ROOT = Path(__file__).resolve().parent.parent`.

### 5. `Install V-Pack Monitor.command` → `scripts/Install V-Pack Monitor.command`

Move from root to `scripts/`. No content changes needed (it calls `install_macos.sh`).
**Important**: `.command` files double-clicked on macOS set cwd to user's home. Verify the script handles this (likely calls `cd "$(dirname "$0")/.."` already).

### 6. `Start V-Pack Monitor.command` → `scripts/Start V-Pack Monitor.command`

Move from root to `scripts/`. Same considerations as above.

### 7. `install_windows.bat` → `scripts/install_windows.bat`

Move from root to `scripts/`. Add `pip install -e .` step after `pip install -r requirements.txt`.
**Important**: Verify all `%CD%` path references still resolve from new location.

### 8. `install_macos.sh` → `scripts/install_macos.sh`

Move from root to `scripts/`. Add `pip install -e .` step after `pip install -r requirements.txt`.
**Important**: Same cwd considerations.

### 9. `inno_setup.iss` → `scripts/inno_setup.iss`

Move from root to `scripts/`. This is the Inno Setup config for Windows installer.
**Important**: Update any file paths inside the ISS file that reference root-level files (e.g., `OutputDir`, source executable path).

### 10. `alembic.ini` (line 8)

```ini
# BEFORE:
script_location = %(here)s/migrations

# AFTER: (unchanged — migrations/ stays at root)
script_location = %(here)s/migrations
```

No change needed — `migrations/` stays at root level.

### 11. `scripts/bump_version.py` (line 26)

```python
# BEFORE:
api_file = root_dir / "api.py"

# AFTER:
api_file = root_dir / "vpack" / "app.py"
```

### 12. `scripts/check_version_consistency.py` (line 21)

```python
# BEFORE:
api_file = root_dir / "api.py"

# AFTER:
api_file = root_dir / "vpack" / "app.py"
```

### 13. `.github/workflows/ci.yml`

Add `pip install -e .` step before pytest. Update any hardcoded `api.py` references.

### 14. `CONTRIBUTING.md` — Project Structure section

Update the project structure tree to reflect new layout:
```
vpack/                    ← Python package
  app.py                  ← FastAPI app (DO NOT add routes here)
  state.py                ← Shared state
  routes/                 ← Route modules
  ...
```

### 15. `README.md` (line 68)

```bash
# BEFORE:
python -m uvicorn api:app --host 0.0.0.0 --port 8001

# AFTER:
python -m uvicorn vpack.app:app --host 0.0.0.0 --port 8001
```

### 16. `AGENTS.md` — Project Structure section

Update to reflect `vpack/` layout. Update `.ai-sync/RULES.md` source.

### 17. `docs/BEST_PRACTICES.md`, `docs/DESIGN_PATTERNS.md`, `docs/QUALITY_CONTROL.md`

Update file path references: `api.py` → `vpack/app.py`, `routes_*.py` → `vpack/routes/*.py`, etc.

---

## Cleanup

### Delete `install_log.txt`
Tracked artifact that should not be in repo. Add to `.gitignore`.

### Delete `scratch/` directory (local only)
Already in `.gitignore`. Contains 11 one-off scripts. Just `rm -rf scratch/`.

### Delete `scripts/__pycache__/`
Cleanup artifact inside `scripts/`.

---

## Scripts Move Summary

| Root File | Destination | Key Risk |
|-----------|-------------|----------|
| `start_windows.bat` | `scripts/start_windows.bat` | `%CD%` paths must still resolve → add `cd /d "%~dp0.."` at top |
| `start.sh` | `scripts/start.sh` | relative paths → add `cd "$(dirname "$0")/.."` at top |
| `build.py` | `scripts/build.py` | `os.chdir("web-ui")` → set `PROJECT_ROOT` first |
| `Install V-Pack Monitor.command` | `scripts/Install V-Pack Monitor.command` | macOS .command cwd = home → verify cd logic |
| `Start V-Pack Monitor.command` | `scripts/Start V-Pack Monitor.command` | same as above |
| `install_windows.bat` | `scripts/install_windows.bat` | `%CD%` paths → add `cd /d "%~dp0.."` |
| `install_macos.sh` | `scripts/install_macos.sh` | relative paths → add `cd "$(dirname "$0")/.."` |
| `inno_setup.iss` | `scripts/inno_setup.iss` | update source/output paths inside ISS file |

**Total: 8 scripts moved from root to `scripts/`**

---

## Verification

1. `pytest tests/ -v` — ALL tests pass
2. `ruff check .` — no errors
3. `python -m uvicorn vpack.app:app --host 0.0.0.0 --port 8001` — server starts
4. `docker build .` — Docker image builds
5. `python scripts/build.py` — PyInstaller executable builds
6. Root folder has only: mandatory configs (`Dockerfile`, `docker-compose.yml`, `pyproject.toml`, `ruff.toml`, `alembic.ini`), mandatory docs (`README.md`, `CONTRIBUTING.md`, `LICENSE`, `AGENTS.md`), dotfiles (`.gitignore`, `.env.example`, `.pre-commit-config.yaml`, `.secrets.baseline`, `.gitattributes`), `VERSION`, `requirements.txt`, `requirements-dev.txt`, and folders (`vpack/`, `tests/`, `migrations/`, `scripts/`, `docs/`, `web-ui/`, `bin/`, `.github/`)
7. No `.py` source files in root
8. `grep -r "api:app" .` returns 0 results (all updated to `vpack.app:app`)
9. `grep -r "sys.path.insert" tests/ migrations/` returns 0 results
10. Each moved script correctly resolves to project root before executing

## After This Plan

Restructuring complete. Root folder clean (~20 items: configs + docs + folders). All Python code in `vpack/`, all scripts in `scripts/`.
