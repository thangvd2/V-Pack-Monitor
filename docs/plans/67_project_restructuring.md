# Plan 67: Full Project Restructuring — Root Cleanup to `vpack/` Package

> **Status:** READY
> **Priority:** HIGH — Code organization
> **Scope:** Meta-plan, broken into 4 sub-plans (68-71)

---

## Problem

Root folder has 40 files. Python modules, configs, scripts, docs all mixed.

## Sub-Plans (execute in order)

| Plan | Title | Scope | Risk | Effort |
|------|-------|-------|------|--------|
| **68** | Create `vpack/` package skeleton | pyproject.toml, ruff.toml, __init__.py | LOW | 10 min |
| **69** | Extract shared state from `api.py` | state.py + update 4 route modules | HIGH | 45 min |
| **70** | Move all modules into `vpack/` | 12 files move + ~63 import updates | HIGH | 60 min |
| **71** | Update configs, scripts, docs, cleanup | 10+ external files | MEDIUM | 30 min |

## Target Structure

```
V-Pack-Monitor/
├── vpack/                    ← Python package
│   ├── __init__.py
│   ├── app.py                ← FastAPI app (from api.py)
│   ├── state.py              ← Shared state (extracted from api.py)
│   ├── auth.py, database.py, network.py, recorder.py
│   ├── video_worker.py, cloud_sync.py, telegram_bot.py
│   └── routes/
│       ├── __init__.py
│       ├── auth.py, records.py, stations.py, system.py
├── migrations/               ← Stays, update imports
├── tests/                    ← Stays, update imports
├── scripts/                  ← Stays, update paths
├── build.py, Dockerfile, docker-compose.yml, ...
├── pyproject.toml            ← NEW
```

## Critical Dependency: Plan 69 must come BEFORE Plan 70

`api.py` holds ~30 shared state variables accessed by routes via `api.X`. Must extract to `state.py` first, or file moves will break everything.

## Verification (after ALL sub-plans complete)

- [ ] `pytest tests/ -v` all pass
- [ ] `ruff check .` no errors
- [ ] `python -m uvicorn vpack.app:app` server starts
- [ ] `docker build .` succeeds
- [ ] Root folder < 25 files
