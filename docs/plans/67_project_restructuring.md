# Plan 67: Full Project Restructuring — Root Cleanup to `vpack/` Package

> **Status:** READY
> **Priority:** HIGH — Code organization
> **Scope:** Meta-plan, broken into 11 atomic sub-plans (68 + 69A-C + 70A-C + 71A-D)

---

## Problem

Root folder has 40 files. Python modules, configs, scripts, docs all mixed.

## Sub-Plans (execute in order)

| Plan | Title | Scope | Risk | Effort |
|------|-------|-------|------|--------|
| **68** | Create `vpack/` package skeleton | pyproject.toml, ruff.toml, __init__.py | LOW | 10 min |
| **69A** | Create `state.py` + backward-compat re-exports | 1 new file + api.py update | HIGH | 20 min |
| **69B** | Migrate routes + video_worker to `state.X` | 5 files, ~70 api.X refs | MED | 20 min |
| **69C** | Migrate test files + remove re-exports | 5 files, cleanup compat layer | MED | 20 min |
| **70A** | Move ALL 12 modules into `vpack/` + prod imports | 12 moves + 10 import updates | HIGH | 30 min |
| **70B** | Update test + migration imports | 16 tests + 2 migrations | MED | 20 min |
| **70C** | Update build + version scripts | 3 files (file-path refs) | MED | 10 min |
| **71A** | Move 8 scripts to `scripts/` + cwd fixes | 8 scripts moved | MED | 20 min |
| **71B** | Update runtime configs (Dockerfile, CI, playwright) | 5 config files | LOW | 10 min |
| **71C** | Update `.ai-sync/` + sync → AGENTS.md | 7 source files + sync | LOW | 15 min |
| **71D** | Update developer docs + cleanup | 9 docs + 2 deletions | LOW | 20 min |

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
├── scripts/                  ← ALL scripts
│   ├── build.py, start.sh, start_windows.bat
│   ├── install_macos.sh, install_windows.bat
│   ├── inno_setup.iss, bump_version.py, check_version_consistency.py
│   ├── Install V-Pack Monitor.command, Start V-Pack Monitor.command
├── migrations/               ← Stays, imports updated
├── tests/                    ← Stays, imports updated
├── docs/                     ← Updated path references
├── web-ui/                   ← Unchanged
├── .ai-sync/                 ← Updated + sync.py
├── Dockerfile, docker-compose.yml, pyproject.toml, ruff.toml
├── README.md, CONTRIBUTING.md, AGENTS.md, LICENSE, VERSION
└── .github/, bin/, .gitignore, .env.example, ...
```

## Critical Dependencies

```
68 → 69A → 69B → 69C → 70A → 70B → 70C → 71A → 71B → 71C → 71D
```

Each plan depends on ALL previous plans being done. No parallelism within the chain.

## Key Risk: Plan 69A-C (State Extraction)

`api.py` holds ~30 shared state variables accessed via `api.X` by 4 routes + video_worker + 4 test files. Extraction uses backward-compat strategy:
- 69A: Create state.py, api.py re-exports everything
- 69B: Migrate production consumers to state.X
- 69C: Migrate test consumers, remove re-exports

## Verification (after ALL sub-plans complete)

- [ ] `pytest tests/ -v` all pass
- [ ] `ruff check .` no errors
- [ ] `python -m uvicorn vpack.app:app` server starts
- [ ] `docker build .` succeeds
- [ ] `python scripts/build.py` PyInstaller build succeeds
- [ ] Root folder < 25 items
- [ ] No `api:app` references remain anywhere
