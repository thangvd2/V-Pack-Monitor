# AGENTS.md — Auto-loaded rules for AI sessions

## BRANCH RULES (MANDATORY)
- NEVER commit directly to `master`. It is protected.
- ALWAYS create a feature branch from `dev`: `git checkout -b {type}/{description} dev`
- Branch naming: `feature/`, `fix/`, `security/`, `refactor/`
- After work is done: `gh pr create --base dev`
- When dev is stable: create PR `dev` → `master` for release

## BEFORE EVERY COMMIT
1. `pytest tests/ -v` — must pass
2. `npm run build` in `web-ui/` — must pass (if frontend changed)
3. `lsp_diagnostics` on changed Python files — no new errors
4. No hardcode secrets/credentials
5. No silent `except: pass` — must log the error

## CODE RULES
- Match existing patterns in the codebase
- Files > 300 lines need justification in commit/PR
- No `as any`, `@ts-ignore`, `@ts-expect-error`
- No deleting tests to make them pass
- Bug fixes: fix minimally, never refactor while fixing
- New Python dependencies: add to `requirements.txt` AND explain why
- New npm dependencies: add via `npm install` AND explain why

## PROJECT STRUCTURE
- `api.py` — FastAPI app, shared state, lifespan, helpers (DO NOT add routes here)
- `routes_*.py` — Route modules, each exports `register_routes(app)`
- `database.py` — DB layer, Fernet encryption, FTS5 search
- `auth.py` — JWT, password hashing, token revocation
- `video_worker.py` — Video processing queue (bounded, max 10 pending)
- `recorder.py` — FFmpeg recording
- `tests/` — Pytest suite with tmp_path isolation

## VERSIONING
- PATCH (x.x.Z): bugfix only
- MINOR (x.Y.0): new feature, backward-compatible
- MAJOR (X.0.0): breaking change (API format, DB schema, response structure)
- Update `VERSION` file + `RELEASE_NOTES.md` on release

## LANGUAGE
- User communicates in Vietnamese
- Code, comments, commit messages in English
- Respond in Vietnamese unless user uses English
