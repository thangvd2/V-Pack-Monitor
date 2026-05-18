> **Status:** DONE

# System Stability & Configuration Fixes

## Overview
This PR addresses multiple system stability issues, TypeScript inference errors in the UI, and MediaMTX connectivity bugs. It also introduces critical hardware acceleration for AMD processors lacking dedicated GPUs. Finally, it documents the resolution of Double-NAT and IP mismatch issues causing `401/403` RTSP failures.

## 1. Frontend TypeScript & State Fixes
- **Issue:** Red squiggles and build failures in IDE due to missing typings in `types/api.ts` (e.g., `camera_health.latency_ms`, `CAMERA_DOWN_ALERT_MINUTES`). 
- **Issue:** TypeScript inference broke because `currentStation` was assigned a default `{}` object.
- **Fix:** Added complete types to `api.ts` based on backend outputs. Removed `{}` defaults to let TypeScript correctly infer `undefined`. Added explicit `Number()` type casting in `SetupModal.tsx` for stringly-typed backend config variables.

## 2. MediaMTX API Connection Fix
- **Issue:** The Frontend displayed "MediaMTX chưa khởi động" because the backend's `/api/mtx-status` probe was returning `503 Service Unavailable`.
- **Root Cause:** The `bin/mediamtx/mediamtx.yml` shipped/downloaded by the scripts had `api: false` by default, blocking port 9997.
- **Fix:** Updated both `scripts/install_windows.bat` and `scripts/install_macos.sh` to automatically replace `api: false` with `api: yes` using PowerShell/sed after extraction.

## 3. Hardware Acceleration for AMD (Ryzen 3 3200G/Vega)
- **Issue:** `vpack/recorder.py` was probing `h264_amf` but not assigning any `-hwaccel` decoding flags, causing the CPU to spike to 100% when decoding dual 1080p PIP RTSP streams.
- **Fix:** Enabled Direct3D 11 Video Acceleration (`-hwaccel d3d11va`) for the AMF encoder. Added `cuda` explicitly for NVENC as well. This shifts the decoding load completely to the Vega iGPU, massive performance boost.

## 4. Network Diagnostics (Double NAT & RTSP Authentication)
During deployment, two primary external network issues were analyzed and resolved for the user:
- **MAC Address Autofill Failing:** Diagnosed as a Layer 2 limitation. The PC (`192.168.0.x`) and Cameras (`192.168.1.x`) were separated by a secondary router performing NAT, dropping ARP broadcast frames.
- **RTSP 401/403 Errors:** The app DMSS returned cached IP addresses. Probing the actual IPs (`192.168.1.13` and `192.168.1.16`) proved they worked flawlessly with the assigned Safety Codes, confirming the cameras had rotated IPs via DHCP.

## Affected Files
- `web-ui/src/types/api.ts`
- `web-ui/src/SetupModal.tsx`
- `web-ui/src/App.tsx`
- `web-ui/src/AdminDashboard.tsx`
- `web-ui/src/MtxFallback.tsx`
- `web-ui/src/types/props.ts`
- `vpack/recorder.py`
- `scripts/install_windows.bat`
- `scripts/install_macos.sh`
