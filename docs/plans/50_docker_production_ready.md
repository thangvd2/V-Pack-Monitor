# Plan 50: Docker Compose Production-Ready

**Ngày**: 2026-04-24
**Mức độ**: Low — Docker đang work cho dev, production cần thêm hardening
**Loại**: Infrastructure improvement

---

**Status**: Plan created, not yet implemented

## Problem

Docker Compose hiện tại minimal:
- Không có reverse proxy (Nginx)
- Không có health checks
- Không có restart policies
- Không có log management
- Không có resource limits

---

## Scope

### Files to change:
- `docker-compose.yml` — Add services + hardening
- `nginx.conf` — NEW reverse proxy config
- `Dockerfile` — Add health check

### Changes:

#### 1. Nginx reverse proxy
```
Client → Nginx (:80/:443) → FastAPI (:8000)
                               → MediaMTX (:8888)
                               → Static files (web-ui/dist)
```
- SSL termination
- Gzip compression
- Static file caching
- Rate limiting per IP

#### 2. Health checks
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/api/system/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

#### 3. Restart policies
```yaml
restart: unless-stopped
```

#### 4. Resource limits
```yaml
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '2.0'
```

#### 5. Log management
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

---

## Constraints

- Nginx config phải support WebSocket upgrade (for future WebSocket migration)
- Health check endpoint `GET /api/system/health` phải trả 200 khi healthy
- SSL certs: self-signed for dev, Let's Encrypt for production
- Không thay đổi Dockerfile logic hiện tại (chỉ thêm HEALTHCHECK)
- `docker-compose.yml` phải backward compatible (không break existing deployment)

---

## Verification

- [ ] `docker compose up` start tất cả services
- [ ] Health check pass after 30s
- [ ] Nginx proxy FastAPI + MediaMTX + static files correctly
- [ ] `docker compose down` clean up properly
- [ ] Log rotation works (verify after 10m of logs)
