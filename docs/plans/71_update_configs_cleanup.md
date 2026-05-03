# Plan 71: Update Configs, Scripts, Docs & Cleanup

> **Status:** READY
> **Priority:** HIGH — Step 4 of restructuring (final)
> **Scope:** 10+ external files updated, 2 deleted
> **Estimated Effort:** 30 min

---

## Prerequisites

- Plans 68, 69, 70 MUST be done
- All tests pass with modules in `vpack/`

---

## Goal

Update all external references (Dockerfile, scripts, CI, docs) to use new `vpack.app:app` entry point. Final cleanup.

---

## Changes

### 1. Dockerfile (line 33)

```dockerfile
# BEFORE:
CMD ["python", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8001"]

# AFTER:
CMD ["python", "-m", "uvicorn", "vpack.app:app", "--host", "0.0.0.0", "--port", "8001"]
```

### 2. `start_windows.bat` (line 60)

```batch
REM BEFORE:
python -m uvicorn api:app --host 0.0.0.0 --port 8001

REM AFTER:
python -m uvicorn vpack.app:app --host 0.0.0.0 --port 8001
```

### 3. `start.sh` (line 44)

```bash
# BEFORE:
python3 -m uvicorn api:app --host 0.0.0.0 --port 8001 &

# AFTER:
python3 -m uvicorn vpack.app:app --host 0.0.0.0 --port 8001 &
```

### 4. `build.py` (line 59)

```python
# BEFORE:
a = Analysis(["api.py"], ...)

# AFTER:
a = Analysis(["vpack/app.py"], ...)
```

Also update any `--hidden-import` flags if they reference root module names.

### 5. Install scripts

Add `pip install -e .` step after `pip install -r requirements.txt`:
- `install_windows.bat` — add `pip install -e .` after pip install
- `install_macos.sh` — add `pip install -e .` after pip install

### 6. `alembic.ini` (line 8)

```ini
# BEFORE:
script_location = %(here)s/migrations

# AFTER: (unchanged — migrations/ stays at root)
script_location = %(here)s/migrations
```

No change needed — `migrations/` stays at root level.

### 7. `scripts/bump_version.py` (line 26)

```python
# BEFORE:
api_file = root_dir / "api.py"

# AFTER:
api_file = root_dir / "vpack" / "app.py"
```

### 8. `scripts/check_version_consistency.py` (line 21)

```python
# BEFORE:
api_file = root_dir / "api.py"

# AFTER:
api_file = root_dir / "vpack" / "app.py"
```

### 9. `.github/workflows/ci.yml`

Add `pip install -e .` step before pytest. Update any hardcoded `api.py` references.

### 10. `CONTRIBUTING.md` — Project Structure section

Update the project structure tree to reflect new layout:
```
vpack/                    ← Python package
  app.py                  ← FastAPI app (DO NOT add routes here)
  state.py                ← Shared state
  routes/                 ← Route modules
  ...
```

### 11. `README.md` (line 68)

```bash
# BEFORE:
python -m uvicorn api:app --host 0.0.0.0 --port 8001

# AFTER:
python -m uvicorn vpack.app:app --host 0.0.0.0 --port 8001
```

### 12. `AGENTS.md` — Project Structure section

Update to reflect `vpack/` layout. Update `.ai-sync/RULES.md` source.

### 13. `docs/BEST_PRACTICES.md`, `docs/DESIGN_PATTERNS.md`, `docs/QUALITY_CONTROL.md`

Update file path references: `api.py` → `vpack/app.py`, `routes_*.py` → `vpack/routes/*.py`, etc.

---

## Cleanup

### Delete `install_log.txt`
Tracked artifact that should not be in repo. Add to `.gitignore`.

### Delete `scratch/` directory (local only)
Already in `.gitignore`. Contains 11 one-off scripts. Just `rm -rf scratch/`.

---

## Verification

1. `pytest tests/ -v` — ALL tests pass
2. `ruff check .` — no errors
3. `python -m uvicorn vpack.app:app --host 0.0.0.0 --port 8001` — server starts
4. `docker build .` — Docker image builds
5. `python build.py` — PyInstaller executable builds
6. Root folder count < 25 files
7. No `.py` source files in root (except `build.py`)
8. `grep -r "api:app" .` returns 0 results (all updated to `vpack.app:app`)
9. `grep -r "sys.path.insert" tests/ migrations/` returns 0 results

## After This Plan

Restructuring complete. Root folder clean. All Python code in `vpack/`.
