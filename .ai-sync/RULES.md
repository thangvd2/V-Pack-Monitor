# Shared Coding Rules

> **AUTO-GENERATED into AGENTS.md and .agents/rules/project-rules.md. DO NOT edit those files directly.**
> Edit this file, then run `python .ai-sync/sync.py`.

---

## BRANCH RULES (MANDATORY)

- NEVER commit directly to `master` or `dev`. Both are protected.
- ALWAYS create a feature branch from `dev`: `git checkout -b {type}/{description} dev`
- Branch naming: `feature/`, `fix/`, `security/`, `refactor/`
- After work is done: `gh pr create --base dev`
- Feature PR → dev: use `--squash` (keep dev history clean: 1 feature = 1 commit)
- Release PR → master: use `--merge` (keep shared history, prevent future conflicts)
- NEVER merge any PR without explicit user confirmation. Always ask first.

## IMPLEMENTATION WORKFLOW (MANDATORY — ALL AGENTS)

```
PLAN → git checkout -b feature/xxx dev → IMPLEMENT → TEST → COMMIT → gh pr create → WAIT FOR REVIEW → USER MERGES
```

1. **CREATE BRANCH BEFORE any code**: `git checkout -b {type}/{desc} dev`. NEVER write code on `dev` or `master`. If already on `dev`, stash → create branch → pop stash.
2. **IMPLEMENT on feature branch**: All changes, tests, fixes on this branch. Run `pytest tests/ -v` and `npm run build && npm run lint` before committing.
3. **CREATE PR AFTER implementation**: `gh pr create --base dev`. PR must include: plan reference, files changed, test results, any deviations. PR enables OpenCode review.
4. **WAIT for review**: OpenCode reviews PR. Fix issues on same branch. ONLY merge after explicit user approval.

## RELEASE RULES (MANDATORY)

- Release PR is ALWAYS `dev` → `master`, merged with `gh pr merge <N> --merge` (NOT --squash)
- ALWAYS update `VERSION`, `api.py` header, and `RELEASE_NOTES.md` ON `dev` BEFORE creating release PR
- NEVER squash or rebase dev → master — this destroys shared history and causes permanent conflicts
- Full process: see `CONTRIBUTING.md` → "Release Process (dev → master)"

## BEFORE EVERY COMMIT

1. `pytest tests/ -v` — must pass
2. `npm run build` in `web-ui/` — must pass (if frontend changed)
3. `npm run lint` in `web-ui/` — must pass (if frontend changed)
4. Linter/diagnostics on changed files — no new errors
5. No hardcode secrets/credentials
6. No silent `except: pass` — must log the error
7. If ANY file in `.ai-sync/` was edited — run `python .ai-sync/sync.py` to regenerate platform configs, then commit the generated files in the SAME commit

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
1. **Self-review**: Audit code for edge cases, race conditions, thread safety, and error handling
2. **Test coverage**: New backend logic MUST have corresponding tests. No exceptions.
3. **No tests = not done**: If you can't write tests for it, explain why in the PR and flag it as untested
4. **Thread safety audit**: Any code using threading, locks, timers, or shared state MUST be reviewed for:
   - Lock ordering (deadlock risk)
   - Race conditions (concurrent access without locks)
   - Resource leaks (timers, threads, connections not cleaned up)
   - Stale references (captured variables in callbacks that may be outdated)

## CODE REVIEW ANTI-FALSE-POSITIVE RULES (MANDATORY)

When flagging a potential issue during code review, you MUST:
1. **Read ALL files in the dependency chain** — not just the immediate file. If issue is in `api.py`, also read callers (`routes_*.py`), callees (`video_worker.py`, `database.py`), and config (`auth.py`).
2. **Trace the FULL call path** — callers, callees, related modules. A lock in one function is only a deadlock risk if another code path acquires locks in reverse order.
3. **Check mitigations FIRST** — before flagging, ask: "Is this already handled elsewhere?" (e.g., a random key fallback in `database.py` is mitigated by `auth.py` persisting SECRET_KEY in DB).
4. **Provide FOR and AGAINST evidence** — every flagged issue MUST include:
   - EVIDENCE FOR: why this seems like a real issue (with file:line)
   - EVIDENCE AGAINST: why this might NOT be a real issue — check guards, related code, production config
   - DEPENDENCY CHAIN: list ALL related files/modules that affect this issue
5. **Classify before reporting** — every issue gets one of:
   - `REAL`: Confirmed with full dependency trace. Has user impact.
   - `SPECULATIVE`: Plausible but unverified. Needs deeper investigation.
   - `FALSE POSITIVE`: Initially seemed real, but mitigated elsewhere.

**Issue without full dependency trace = SPECULATIVE, not actionable.**
**Issue without AGAINST evidence = incomplete review.**

## REVIEW PROMPT TEMPLATE (USE WHEN DELEGATING REVIEW TASKS)
When firing explore/librarian agents for code review, include this structure in the prompt:

```
For EACH potential issue found, you MUST provide:

1. ISSUE: [one-line description]
2. FILES READ: [list ALL files you actually read to verify this — not just where the issue appears]
3. EVIDENCE FOR: [why this seems like a real issue, with file:line references]
4. EVIDENCE AGAINST: [why this might NOT be a real issue — check mitigations, guards,
   fallbacks, related modules, production config. If you cannot find any against-evidence,
   state "No against-evidence found after checking [files checked]"]
5. DEPENDENCY CHAIN: [list all related files/modules that could affect whether this is real]
6. VERDICT: REAL / SPECULATIVE / FALSE POSITIVE

DO NOT flag issues without reading the full dependency chain.
DO NOT skip AGAINST evidence — it is MANDATORY.
```

## 2-PASS REVIEW PROCESS (FOR RELEASE REVIEWS & SECURITY AUDITS)
For release PRs, security audits, and critical code changes — use this two-pass process:

**Pass 1 — Flag issues (broad scan):**
- Review different areas (backend, frontend, tests)
- Flag potential issues using the evidence template above
- Collect ALL flagged issues — do not filter yet

**Pass 2 — Verify issues (deep investigation):**
- For EACH flagged issue, investigate to verify
- The verifier MUST:
  - Read the FULL dependency chain (not just the file where the issue was found)
  - Trace every lock acquisition, every fallback path, every related module
  - Provide FOR and AGAINST evidence
  - Give final verdict: REAL, SPECULATIVE, or FALSE POSITIVE
- Only REAL issues are reported to the user
- SPECULATIVE issues are reported with clear caveat
- FALSE POSITIVE issues are documented with explanation of why they're safe

**Why 2 passes?** A single pass creates confirmation bias — agents find "evidence" to support their initial concern without checking if it's already mitigated. Two passes separate "detection" (Pass 1) from "verification" (Pass 2), dramatically reducing false positives.

## MANDATORY SELF-VERIFICATION CHECKLIST (BEFORE SAYING "DONE")
You MUST NOT report a task as complete until EVERY item below passes.
No exceptions. If you skip any item, the user WILL find the bug on double-check.

### For EVERY code change (Python, JS, JSX, YAML):
- [ ] NOT on `master` or `dev` — must be on a feature branch (`feature/`, `fix/`, `security/`, `refactor/`)
- [ ] `ruff check .` passes on changed files (or `npm run lint` for frontend)
- [ ] `lsp_diagnostics` shows no NEW errors on changed files
- [ ] No duplicate lines, duplicate comments, or copy-paste artifacts
- [ ] No unused imports, unused variables, or dead code left behind
- [ ] Every new shared state variable has cleanup path on shutdown/exit
- [ ] Git diff reviewed line-by-line — no accidental inclusions (log files, .playwright-mcp, screenshots)

### For backend Python changes:
- [ ] `pytest tests/ -q` passes (or specific test file if targeted)
- [ ] New functions with threading/locks/timers: verify lock ordering, cancel paths, cleanup on error
- [ ] New SSE events: frontend handler exists in the SAME commit
- [ ] New API fields: check all consumers (frontend, tests, docs)

### For frontend changes:
- [ ] `npm run build` passes
- [ ] `npm run lint` passes
- [ ] useEffect deps arrays correct (no stale closures)
- [ ] catch blocks have error handling (alert/toast/setError + console.warn, not bare `catch {}`)

### For CI/YAML changes:
- [ ] YAML syntax valid (no duplicate keys, correct indentation)
- [ ] New jobs added to branch protection required checks
- [ ] Path filters cover all relevant file patterns
- [ ] If adding `if:` conditions — verified that skipped jobs still satisfy branch protection

### For docs/config changes (AGENTS.md, CONTRIBUTING.md, VERSION):
- [ ] VERSION file matches api.py header
- [ ] Cross-references between docs are accurate (section names, file paths)
- [ ] No contradictory rules between AGENTS.md and CONTRIBUTING.md

### For release PRs:
- [ ] `gh pr merge <N> --merge` (NOT --squash)
- [ ] VERSION, api.py header, RELEASE_NOTES.md all updated on dev BEFORE creating PR

## PROJECT STRUCTURE
- `api.py` — FastAPI app, shared state, lifespan, helpers (DO NOT add routes here)
- `routes_*.py` — Route modules, each exports `register_routes(app)`
- `database.py` — DB layer, Fernet encryption, FTS5 search
- `auth.py` — JWT, password hashing, token revocation
- `video_worker.py` — Video processing queue (bounded, max 10 pending)
- `recorder.py` — FFmpeg recording
- `tests/` — Pytest suite with tmp_path isolation
