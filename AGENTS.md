# AGENTS.md — Auto-loaded rules for AI sessions

## BRANCH RULES (MANDATORY)
- NEVER commit directly to `master`. It is protected.
- ALWAYS create a feature branch from `dev`: `git checkout -b {type}/{description} dev`
- Branch naming: `feature/`, `fix/`, `security/`, `refactor/`
- After work is done: `gh pr create --base dev`
- Feature PR → dev: use `--squash` (keep dev history clean: 1 feature = 1 commit)
- Release PR → master: use `--merge` (keep shared history, prevent future conflicts)

## RELEASE RULES (MANDATORY)
- Release PR is ALWAYS `dev` → `master`, merged with `gh pr merge <N> --merge` (NOT --squash)
- ALWAYS update `VERSION`, `api.py` header, and `RELEASE_NOTES.md` ON `dev` BEFORE creating release PR
- NEVER squash or rebase dev → master — this destroys shared history and causes permanent conflicts
- Full process: see `CONTRIBUTING.md` → "Release Process (dev → master)"

## BEFORE EVERY COMMIT
1. `pytest tests/ -v` — must pass
2. `npm run build` in `web-ui/` — must pass (if frontend changed)
3. `npm run lint` in `web-ui/` — must pass (if frontend changed)
4. `lsp_diagnostics` on changed Python files — no new errors
5. No hardcode secrets/credentials
6. No silent `except: pass` — must log the error

## CODE RULES
- Match existing patterns in the codebase
- Files > 300 lines need justification in commit/PR
- No `as any`, `@ts-ignore`, `@ts-expect-error`
- No deleting tests to make them pass
- Bug fixes: fix minimally, never refactor while fixing
- New Python dependencies: add to `requirements-dev.txt` (dev) or `requirements.txt` (prod) AND explain why
- New npm dependencies: add via `npm install` AND explain why
- **Frontend-Backend sync**: When adding SSE event or API response field in backend, MUST add frontend handler in the SAME commit
- **React stale closures**: Variables used inside useEffect/useState callbacks must be in deps array or accessed via ref (enforced by `eslint-plugin-react-hooks`)

## MANDATORY PRE-PUSH REVIEW (EVERY FEATURE)
Before pushing ANY new feature or significant change:
1. **Self-review**: Fire 2+ explore agents in parallel to audit the code for edge cases, race conditions, thread safety, and error handling
2. **Test coverage**: New backend logic MUST have corresponding tests. No exceptions.
3. **No tests = not done**: If you can't write tests for it, explain why in the PR and flag it as untested
4. **Thread safety audit**: Any code using threading, locks, timers, or shared state MUST be reviewed for:
   - Lock ordering (deadlock risk)
   - Race conditions (concurrent access without locks)
   - Resource leaks (timers, threads, connections not cleaned up)
   - Stale references (captured variables in callbacks that may be outdated)

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
