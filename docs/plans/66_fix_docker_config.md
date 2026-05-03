# Plan 66: Fix Docker Config (docker-compose.yml + Dockerfile)

> **Status:** DONE
> **Priority:** MEDIUM — Docker deployment broken
> **Scope:** 2 files
> **Estimated Effort:** 15 min

---

## Bug 1: docker-compose.yml — DB path completely wrong

**File:** `docker-compose.yml:12`

**Current:**
```yaml
volumes:
  - ./vpack.db:/app/vpack.db
```

**Actual DB location** (`database.py`): `recordings/packing_records.db`

The volume mount references a non-existent `vpack.db`. Docker users lose all data on container restart because the real DB is not persisted.

**Fix:**
```yaml
volumes:
  - ./recordings:/app/recordings
```

---

## Bug 2: docker-compose.yml — Missing WebRTC & MediaMTX ports

**File:** `docker-compose.yml:8-9`

**Current:** Only maps port `8001`
**Dockerfile exposes:** `8001 8889 9997`

Without ports 8889 (WebRTC live view) and 9997 (MediaMTX API), camera live view does not work in Docker.

**Fix:**
```yaml
ports:
  - "8001:8001"
  - "8889:8889"
  - "9997:9997"
```

---

## Bug 3: Dockerfile — Python version mismatch

**File:** `Dockerfile:2`

**Current:** `FROM python:3.14-slim`
**CI (`ci.yml`):** Python 3.13
**Docs:** Python 3.13

Python 3.14 is not yet stable. Should match CI.

**Fix:** `FROM python:3.13-slim`

---

## Bug 4: Dockerfile — Unnecessary OpenCV system libraries

**File:** `Dockerfile:13`

**Current:** Installs `libsm6 libxext6 libgl1` (OpenCV deps)
**But:** `opencv-python` is only in `requirements-dev.txt`, NOT in `requirements.txt` (which Dockerfile installs)

These 3 libraries are dead weight in production image.

**Fix:** Remove `libsm6 libxext6 libgl1` from apt-get install line.

---

## Bug 5: docker-compose.yml — Deprecated `version: '3.8'`

**File:** `docker-compose.yml:1`

Docker Compose v2 ignores this field and shows deprecation warning.

**Fix:** Remove `version: '3.8'` line entirely.

---

## Files Summary

| # | File | Change |
|---|------|--------|
| 1 | `docker-compose.yml` | Fix DB path, add ports 8889+9997, remove deprecated version |
| 2 | `Dockerfile` | Python 3.14 → 3.13, remove OpenCV libs |

## Verification

1. `docker compose config` validates without errors
2. `docker build .` succeeds
3. DB persists at `./recordings/packing_records.db` after container restart
4. WebRTC live view accessible on port 8889
5. MediaMTX API accessible on port 9997
