# Plan 71B: Update Runtime Configs

> **Status:** READY
> **Priority:** HIGH — Step 4B of restructuring
> **Scope:** 5 config files
> **Estimated Effort:** 10 min

---

## Prerequisites

- Plans 70A-C MUST be done (files moved to `vpack/`)

---

## Goal

Update all config files that reference `api:app` or `api.py` to use `vpack.app:app`.

---

## Changes

### 1. Dockerfile (line 33)

```dockerfile
# BEFORE:
CMD ["sh", "-c", "... python -m uvicorn api:app ..."]

# AFTER:
CMD ["sh", "-c", "... python -m uvicorn vpack.app:app ..."]
```

### 2. `.github/workflows/ci.yml`

- Add `pip install -e .` step after `pip install -r requirements-dev.txt`
- Verify no hardcoded `api.py` references remain
- Verify `pytest` command still works (it should — imports are package-based)

### 3. `web-ui/playwright.config.ts` (line 29)

```typescript
// BEFORE:
python -m uvicorn api:app

// AFTER:
python -m uvicorn vpack.app:app
```

### 4. `alembic.ini`

No change needed — `migrations/` stays at root. Verify `script_location = %(here)s/migrations` is correct.

### 5. `.pre-commit-config.yaml`

Verify no `api.py` or root module references. If using `ruff`, the config in `ruff.toml` (updated in Plan 68 with `src = ["vpack"]`) handles import resolution.

---

## Verification

1. `grep -rn "api:app" Dockerfile .github/workflows/ci.yml web-ui/playwright.config.ts` — returns 0 results
2. `grep -rn "uvicorn.*api" Dockerfile .github/workflows/ci.yml web-ui/playwright.config.ts` — returns 0 results
3. `docker build .` — Docker image builds (if Docker available)
4. CI workflow syntax valid

## After This Plan

All runtime configs reference `vpack.app:app`. No `api:app` references remain in executable configs.
