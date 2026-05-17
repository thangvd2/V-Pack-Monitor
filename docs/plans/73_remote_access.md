# Plan 73: Remote Access Support

> **Status:** READY
> **Priority:** HIGH — User-requested feature
> **Scope:** Backend (3 files), Frontend (2 files), Docs
> **Estimated Effort:** 2-3 hours (code changes) + reverse proxy setup guide

---

## Background

V-Pack Monitor runs on a Windows PC in a warehouse. Currently works perfectly on LAN. User wants remote access — from another office, home, or mobile. Requires fixing several hardcoded localhost/LAN assumptions.

## Current State

### Already Remote-Ready (no changes needed):

| Component | Status | Detail |
|---|---|---|
| Uvicorn bind | `0.0.0.0:8001` | Already listens on all interfaces |
| Frontend API_BASE | `window.location` | Dynamic, works from any origin |
| Frontend SSE | Uses `API_BASE` | Same-origin, works remotely |
| MediaMTX iframe hostname | `window.location.hostname` | Dynamic, works remotely |
| JWT authentication | All routes protected | Full auth system exists |
| Docker ports | All exposed | 8001, 8889, 9997 mapped |

### Must Fix for Remote Access:

| # | Issue | File(s) | Line(s) |
|---|---|---|---|
| 1 | CORS only allows localhost + 1 LAN IP | `vpack/app.py` | 374-387 |
| 2 | MediaMTX iframe protocol hardcoded `http://` | `App.tsx`, `AdminDashboard.tsx` | Multiple |
| 3 | `MTX_HOST` env var defaults to `127.0.0.1` | `vpack/routes/records.py` | 434, 442 |
| 4 | No HTTPS/TLS — everything is plain HTTP | All traffic | Everywhere |
| 5 | No documentation for remote access setup | — | — |

## Architecture Decision: Reverse Proxy Approach

**Do NOT build TLS into the Python app.** Use a reverse proxy (Caddy recommended):

```
Remote Client
    │
    ▼
[Caddy Reverse Proxy with TLS]
    │
    ├── /           → FastAPI :8001 (API + frontend)
    ├── /api/*      → FastAPI :8001
    └── /stream/*   → MediaMTX :8889 (WebRTC)

Internal only:
    ├── MediaMTX API :9997 (127.0.0.1 only)
    └── FastAPI ↔ MediaMTX (127.0.0.1:9997)
```

Why Caddy: Automatic HTTPS, single binary, easy Windows install, simple config.

## Implementation Steps

### Step 1: Make CORS configurable

In `vpack/app.py`, update `_get_cors_origins()` to support `CORS_ORIGINS` env var:

```python
def _get_cors_origins():
    origins = [
        "http://localhost:8001",
        "http://127.0.0.1:8001",
    ]
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        origins.append(f"http://{local_ip}:8001")
    except Exception:
        pass
    custom = os.environ.get("CORS_ORIGINS", "")
    if custom:
        for origin in custom.split(","):
            origin = origin.strip()
            if origin and origin not in origins:
                origins.append(origin)
    return origins
```

Example: `CORS_ORIGINS=https://vpack.example.com,https://192.168.1.100:8443`

### Step 2: Fix MediaMTX iframe protocol — make dynamic

In `web-ui/src/App.tsx` and `web-ui/src/AdminDashboard.tsx`, change hardcoded `http://` to use page protocol:

```typescript
// Before:
src={`http://${MTX_HOST}:8889/station_${station.id}...`}

// After:
src={`${window.location.protocol}//${MTX_HOST}:8889/station_${station.id}...`}
```

This ensures WebRTC iframes use same protocol as main page (HTTP on LAN, HTTPS behind reverse proxy).

### Step 3: Fix MTX_HOST in backend API endpoints

In `vpack/routes/records.py`, fix `/api/live` and `/api/live-cam2`:

```python
# Before:
mtx_host = os.environ.get("MTX_HOST", "127.0.0.1")

# After — remove hardcoded URL, let frontend construct it
mtx_host = os.environ.get("MTX_HOST", "")
# Return empty/omit webrtc_url if MTX_HOST not set
# Frontend already constructs iframe URLs using window.location.hostname
```

### Step 4: Add remote access setup guide

Create `docs/REMOTE_ACCESS.md` with:
1. **LAN access** (already works): use server's LAN IP
2. **VPN/tunnel** (recommended): Tailscale, Cloudflare Tunnel, WireGuard
3. **Reverse proxy**: Caddy example Caddyfile config
4. **Port forwarding**: If using direct NAT, forward ports 8001 + 8889
5. **Security**: Always use HTTPS, don't expose port 9997 to WAN

### Step 5 (Optional): Add remote access settings to UI

In SetupModal, add "Remote Access" section:
- Display current LAN IP and server URL
- CORS origins field (comma-separated)
- MTX WebRTC port field
- Link to documentation

## Security Considerations

1. **JWT auth already protects all API routes** — no unauthenticated access
2. **HTTPS mandatory for remote access** — plain HTTP exposes credentials
3. **MediaMTX admin API (9997) must NOT be exposed to WAN** — no auth
4. **VPN/tunnel preferred over port forwarding** — Tailscale/Cloudflare Tunnel are safer

## Testing

- Test CORS with custom origins via env var
- Test MediaMTX iframe with both HTTP and HTTPS protocols
- Test with `MTX_HOST` env var set to various values
- Test reverse proxy setup (Caddy)

## Files Changed (estimated)

| File | Change |
|---|---|
| `vpack/app.py` | Configurable CORS origins |
| `vpack/routes/records.py` | Fix MTX_HOST to be dynamic |
| `web-ui/src/App.tsx` | Dynamic protocol for MediaMTX iframes |
| `web-ui/src/AdminDashboard.tsx` | Dynamic protocol for MediaMTX iframes |
| `docs/REMOTE_ACCESS.md` | New setup guide |
