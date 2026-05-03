# Plan 63: IP → MAC Auto-Discovery (Reverse ARP Lookup)

> **Status:** READY
> **Priority:** MEDIUM — UX improvement
> **Scope:** 3 files + tests
> **Estimated Effort:** 30-45 min

---

## Background

When setting up a camera station, the user can enter a MAC address and click "Quét IP" to auto-discover the camera's IP. However, when entering an IP address and clicking "Test", the system only checks reachability without discovering the MAC. This is an unnecessary asymmetry since the ARP table already contains both IP↔MAC pairs after a ping.

---

## Current Behavior

```
MAC → IP:  User enters MAC → "Quét IP" → /api/discover-mac → scan LAN → auto-fill IP ✅
IP → MAC:  User enters IP → "Test" → /api/ping → reachable/unreachable only ❌
```

## Target Behavior

```
MAC → IP:  (unchanged) ✅
IP → MAC:  User enters IP → "Test" → /api/ping → reachable + MAC auto-fill ✅
```

---

## Changes

### 1. `network.py` — Add `get_mac_for_ip()` function

**Location:** After `scan_lan_all()` (line ~181)

**New function:**
```python
def get_mac_for_ip(target_ip: str) -> str | None:
    """Look up the MAC address for a given IP from the ARP table.

    If not found in cache, pings the IP to populate the ARP table first,
    then looks up again.

    Args:
        target_ip: IPv4 address string.

    Returns:
        Normalized MAC address string if found, None otherwise.
    """
    # Step 1: Check ARP table first
    for entry in _parse_arp_table():
        if entry["ip"] == target_ip:
            return entry["mac"]

    # Step 2: Ping the IP to populate ARP table
    _ping_host(target_ip)
    time.sleep(0.3)  # Brief wait for ARP table update

    # Step 3: Re-read ARP table
    for entry in _parse_arp_table():
        if entry["ip"] == target_ip:
            return entry["mac"]

    return None
```

**Why this approach:**
- Reuses existing `_parse_arp_table()` and `_ping_host()` — no new dependencies
- No full /24 ping sweep needed (unlike `scan_lan_for_mac`) — we already know the IP, just need to ping it once
- Same 2-step pattern as `scan_lan_for_mac` (check cache → ping → re-check)

### 2. `routes_system.py` — Enhance `/api/ping` response

**Location:** `ping_ip()` function (lines 788-814)

**Change:** After determining `alive`, if reachable, look up MAC:

```python
@app.get("/api/ping")
def ping_ip(ip: str, admin: AdminUser):
    if not ip:
        return {"reachable": False}
    if not _validate_ping_ip(ip):
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "IP không hợp lệ."},
        )
    alive = False
    try:
        if _platform.system() == "Windows":
            result = subprocess.run(
                ["ping", "-n", "1", "-w", "2000", ip],
                capture_output=True,
                timeout=5,
            )
        else:
            result = subprocess.run(
                ["ping", "-c", "1", "-W", "2", ip],
                capture_output=True,
                timeout=5,
            )
        alive = result.returncode == 0
    except Exception:
        pass

    # --- NEW: Look up MAC from ARP table when reachable ---
    mac = None
    if alive:
        try:
            mac = network.get_mac_for_ip(ip)
        except Exception:
            pass

    return {"ip": ip, "reachable": alive, "mac": mac}
```

**Response shape change:**
```json
// Before:
{"ip": "192.168.1.10", "reachable": true}

// After:
{"ip": "192.168.1.10", "reachable": true, "mac": "AA:BB:CC:DD:EE:FF"}

// When MAC not found in ARP table:
{"ip": "192.168.1.10", "reachable": true, "mac": null}
```

**Backward compatible:** The `mac` field is additive. Existing consumers ignore unknown fields.

### 3. `web-ui/src/SetupModal.tsx` — Auto-fill MAC from ping result

**Location:** `handleTestIp()` function (lines 214-230)

**Change:** After checking `res.data.reachable`, auto-fill MAC if provided and MAC field is empty:

```typescript
const handleTestIp = async () => {
    if (!ip1 || !isValidIP(ip1)) return;
    setTestingIp(true);
    setTestIpResult(null);
    try {
      const res = await axios.get(`${API_BASE}/api/ping?ip=${encodeURIComponent(ip1)}`);
      if (res.data.reachable) {
        setTestIpResult({ ok: true, msg: `Reachable (${ip1})` });
        // --- NEW: Auto-fill MAC if available and field is empty ---
        if (res.data.mac && !macAddress?.trim()) {
          setMacAddress(res.data.mac);
          markDirty();
        }
      } else {
        setTestIpResult({ ok: false, msg: 'Unreachable — camera không phản hồi' });
      }
    } catch {
      setTestIpResult({ ok: false, msg: 'Lỗi kết nối server' });
    } finally {
      setTestingIp(false);
    }
  };
```

**Key constraint:** Only auto-fill when `macAddress` is empty/blank. Never overwrite a user-provided MAC.

---

### 4. `tests/test_network.py` — Add tests for `get_mac_for_ip()`

**Add new test class:**

```python
class TestGetMacForIp:
    """Tests for network.get_mac_for_ip()."""

    @patch("network._parse_arp_table")
    def test_found_immediately(self, mock_arp):
        mock_arp.return_value = [
            {"ip": "192.168.1.42", "mac": "AA:BB:CC:DD:EE:FF"},
        ]
        result = network.get_mac_for_ip("192.168.1.42")
        assert result == "AA:BB:CC:DD:EE:FF"

    @patch("network._ping_host")
    @patch("network._parse_arp_table")
    def test_found_after_ping(self, mock_arp, mock_ping):
        mock_arp.side_effect = [
            [],
            [{"ip": "192.168.1.42", "mac": "AA:BB:CC:DD:EE:FF"}],
        ]
        result = network.get_mac_for_ip("192.168.1.42")
        assert result == "AA:BB:CC:DD:EE:FF"
        mock_ping.assert_called_once_with("192.168.1.42")

    @patch("network._ping_host")
    @patch("network._parse_arp_table")
    def test_not_found(self, mock_arp, mock_ping):
        mock_arp.return_value = []
        result = network.get_mac_for_ip("192.168.1.42")
        assert result is None

    def test_different_ip_not_matched(self):
        """Ensure we match exact IP, not partial."""
        with patch("network._parse_arp_table") as mock_arp:
            mock_arp.return_value = [
                {"ip": "192.168.1.4", "mac": "AA:BB:CC:DD:EE:FF"},  # .4 not .42
            ]
            result = network.get_mac_for_ip("192.168.1.42")
            # First call returns .4, then ping, then second call also returns .4
            assert result is None or result != "AA:BB:CC:DD:EE:FF"
```

**Also add API-level test for enhanced `/api/ping` response:**

```python
class TestPingWithMac:
    """Tests for /api/ping enhanced with MAC lookup."""

    @patch("network.get_mac_for_ip", return_value="AA:BB:CC:DD:EE:FF")
    @patch("subprocess.run")
    def test_ping_reachable_with_mac(self, mock_run, mock_get_mac, client, admin_headers):
        mock_run.return_value = MagicMock(returncode=0)
        r = client.get("/api/ping", headers=admin_headers, params={"ip": "192.168.1.10"})
        assert r.json()["reachable"] is True
        assert r.json()["mac"] == "AA:BB:CC:DD:EE:FF"

    @patch("network.get_mac_for_ip", return_value=None)
    @patch("subprocess.run")
    def test_ping_reachable_no_mac(self, mock_run, mock_get_mac, client, admin_headers):
        mock_run.return_value = MagicMock(returncode=0)
        r = client.get("/api/ping", headers=admin_headers, params={"ip": "192.168.1.10"})
        assert r.json()["reachable"] is True
        assert r.json()["mac"] is None

    @patch("subprocess.run")
    def test_ping_unreachable_no_mac_lookup(self, mock_run, client, admin_headers):
        mock_run.return_value = MagicMock(returncode=1)
        r = client.get("/api/ping", headers=admin_headers, params={"ip": "192.168.1.10"})
        assert r.json()["reachable"] is False
        assert "mac" not in r.json() or r.json()["mac"] is None
```

---

## Files Summary

| # | File | Action |
|---|------|--------|
| 1 | `network.py` | Add `get_mac_for_ip()` function (~20 lines) |
| 2 | `routes_system.py` | Enhance `/api/ping` response with MAC field (~5 lines) |
| 3 | `web-ui/src/SetupModal.tsx` | Auto-fill MAC in `handleTestIp()` (~4 lines) |
| 4 | `tests/test_network.py` | Add `TestGetMacForIp` + `TestPingWithMac` (~50 lines) |

---

## Verification

1. `ruff check .` passes
2. `pytest tests/ -v` passes (all new + existing tests)
3. `npm run build && npm run lint` passes
4. Manual test: Enter IP in SetupModal → click "Test" → verify MAC auto-fills when reachable
5. Manual test: Enter IP → "Test" when MAC already filled → MAC NOT overwritten
6. Manual test: Enter unreachable IP → "Test" → no MAC auto-fill, shows "Unreachable"
