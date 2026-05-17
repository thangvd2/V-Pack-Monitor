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

**Do NOT build TLS into the Python app.** Use a reverse proxy (Caddy recommended).

### Why NOT proxy MediaMTX via subpath `/stream/*`

MediaMTX serves a full web player page (HTML + JS + CSS) with relative paths. Proxying via subpath breaks these relative resource references. Instead, **Caddy should listen on a dedicated TLS port (e.g., 8443) and proxy directly to MediaMTX :8889**. The frontend constructs MediaMTX URLs using `MTX_HOST` and `MTX_WEBRTC_PORT` env vars (or build-time Vite vars).

### Target Architecture

```
Remote Client
    │
    ▼
[Caddy Reverse Proxy with TLS]
    │
    ├── :443  → FastAPI :8001 (API + frontend static)
    └── :8443 → MediaMTX :8889 (WebRTC — dedicated TLS port)

Internal only:
    ├── MediaMTX API :9997 (127.0.0.1 only — never expose)
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

### Step 2: Make MediaMTX iframe URL configurable

**Problem**: Frontend hardcodes port 8889 and protocol `http://` for MediaMTX iframes. This breaks when behind reverse proxy (wrong protocol) or when MediaMTX is on a different port.

**Solution**: Use Vite build-time env var `VITE_MTX_WEBRTC_URL` for full URL override, with sensible defaults:

In `web-ui/src/App.tsx` and `web-ui/src/AdminDashboard.tsx`:

```typescript
// Default: same hostname, same protocol, port 8889
const MTX_BASE = import.meta.env.VITE_MTX_WEBRTC_URL
  || `${window.location.protocol}//${window.location.hostname}:8889`;

// Usage:
src={`${MTX_BASE}/station_${station.id}?controls=false&muted=true&autoplay=true`}
```

- **LAN (no reverse proxy)**: Default works — `http://{hostname}:8889`
- **HTTPS behind Caddy**: Set `VITE_MTX_WEBRTC_URL=https://vpack.example.com:8443` at build time
- **VPN/Tailscale**: Default works if ports are accessible

Also update `web-ui/vite.config.ts` to support the env var, and add it to `web-ui/.env.example`.

### Step 3: Deprecate unused `/api/live` and `/api/live-cam2` endpoints

**Finding**: The frontend never calls `/api/live` or `/api/live-cam2`. It constructs MediaMTX iframe URLs directly using `window.location.hostname`. These endpoints contain hardcoded `MTX_HOST=127.0.0.1` and are dead code.

**Action**: Remove or deprecate these endpoints from `vpack/routes/records.py`. If removed, also remove any tests that reference them. Mark as deprecated in API docs if full removal is too risky.

### Step 4: Add remote access setup guide

Create `docs/REMOTE_ACCESS.md` with:
1. **LAN access** (already works): use server's LAN IP
2. **VPN/tunnel** (recommended): Tailscale, Cloudflare Tunnel, WireGuard
3. **Reverse proxy**: Caddy example Caddyfile config with two listeners:
   - `:443` → FastAPI `:8001`
   - `:8443` → MediaMTX `:8889` (dedicated TLS port, NOT subpath proxy)
4. **Port forwarding**: If using direct NAT, forward ports 8001 + 8889
5. **Security**: Always use HTTPS, don't expose port 9997 to WAN
6. **Build-time config**: Document `VITE_MTX_WEBRTC_URL` env var

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
| `vpack/routes/records.py` | Deprecate/remove unused `/api/live` endpoints |
| `web-ui/src/App.tsx` | Configurable MediaMTX URL via env var |
| `web-ui/src/AdminDashboard.tsx` | Configurable MediaMTX URL via env var |
| `docs/REMOTE_ACCESS.md` | New setup guide |
