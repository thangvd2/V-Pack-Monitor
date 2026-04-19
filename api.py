# =============================================================================
# V-Pack Monitor - CamDongHang v3.2.0
from logger import get_logger

logger = get_logger(__name__)

# Copyright (c) 2024-2026 VDT - Vu Duc Thang (thangvd2)
# All rights reserved. Unauthorized copying or distribution is prohibited.
# =============================================================================

import asyncio
import json
import logging
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import database
import network
import recorder
import video_worker

_SERVER_START_TIME = time.time()

_MAX_RECORDING_SECONDS = 600  # 10 minutes hard cap
_RECORDING_WARNING_SECONDS = 540  # 9 minutes — emit warning SSE event


def _read_version():
    try:
        vpath = os.path.join(os.path.dirname(__file__) or ".", "VERSION")
        with open(vpath) as f:
            return f.read().strip()
    except Exception:
        return "unknown"


def _parse_semver(version_str):
    """Parse a version string like 'v2.4.1' or 'v2.4.1-beta' into (major, minor, patch) tuple."""
    try:
        v = version_str.strip().lstrip("vV")
        # Strip pre-release suffix (e.g. '-beta', '-rc1')
        v = v.split("-")[0]
        parts = v.split(".")
        return tuple(int(p) for p in parts[:3])
    except (ValueError, AttributeError):
        return (0, 0, 0)


# --- Quản lý Trạng thái Ghi hình Đa Trạm ---
active_recorders = {}
active_waybills = {}
active_record_ids = {}
_processing_count = {}  # {station_id: int} — counts pending video conversions
_processing_lock = threading.Lock()
_station_locks = {}  # {station_id: threading.Lock} — prevents double-scan per station
stream_managers = {}

reconnect_status = {}

_recording_timers = {}  # {station_id: threading.Timer} — auto-stop timers
_recording_timers_lock = threading.Lock()
_recording_start_times = {}  # {station_id: float} — epoch seconds when recording started
_recording_warning_timers = {}  # {station_id: threading.Timer} — warning timers

# Per-concern locks for shared mutable state
_recorders_lock = threading.Lock()  # guards active_recorders, active_waybills, active_record_ids
_streams_lock = threading.Lock()  # guards stream_managers, reconnect_status
_station_locks_lock = threading.Lock()  # guards _station_locks dict itself
_cache_lock = threading.Lock()  # guards _update_check_cache
_login_attempts_lock = threading.Lock()  # guards _login_attempts

_logger = logging.getLogger("vpack")

MAX_SSE_CLIENTS = 50
MAX_UPLOAD_SIZE = 1 * 1024 * 1024  # 1MB max for credentials JSON

MTX_API = os.environ.get("MTX_API", "http://127.0.0.1:9997")

_sse_clients = []
_sse_lock = threading.Lock()


def notify_sse(event_type, data):
    msg = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
    with _sse_lock:
        dead = []
        for i, q in enumerate(_sse_clients):
            try:
                q.put_nowait(msg)
            except Exception:
                dead.append(i)
        for i in reversed(dead):
            _sse_clients.pop(i)


def _mtx_add_path(station_id, rtsp_url, suffix=""):
    name = f"station_{station_id}{suffix}"
    conf = {
        "name": name,
        "source": rtsp_url,
        "rtspTransport": "tcp",
    }
    try:
        data = json.dumps(conf).encode()
        req = urllib.request.Request(
            f"{MTX_API}/v3/config/paths/replace/{name}",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=5)
        return
    except Exception as e:
        logger.error(f"[MTX] replace {name} failed: {e}")
    try:
        req = urllib.request.Request(
            f"{MTX_API}/v3/config/paths/delete/{name}",
            method="POST",
        )
        urllib.request.urlopen(req, timeout=3)
    except Exception:
        pass
    try:
        data = json.dumps(conf).encode()
        req = urllib.request.Request(
            f"{MTX_API}/v3/config/paths/add/{name}",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        logger.error(f"[MTX] ERROR: add {name} failed after all retries: {e}")


def _mtx_remove_path(station_id, suffix=""):
    name = f"station_{station_id}{suffix}"
    try:
        req = urllib.request.Request(
            f"{MTX_API}/v3/config/paths/delete/{name}",
            method="POST",
        )
        urllib.request.urlopen(req, timeout=5)
    except urllib.error.HTTPError as e:
        if e.code != 404:
            logger.error(f"[MTX] delete {name} failed: {e}")
    except Exception:
        pass


class CameraStreamManager:
    def __init__(self, url, station_id=None, cam2_url=None):
        self.url = url
        self.station_id = station_id
        self.cam2_url = cam2_url
        self.is_running = False
        self.thread = None
        self._fail_count = 0
        self._lock = threading.Lock()

    def start(self):
        if not self.is_running and self.url:
            self.is_running = True
            self._fail_count = 0
            self._mtx_register()
            if self.cam2_url:
                _mtx_add_path(self.station_id, self.cam2_url, suffix="_cam2")
            self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.thread.start()

    def stop(self):
        self.is_running = False
        if self.station_id:
            _mtx_remove_path(self.station_id)
            if self.cam2_url:
                _mtx_remove_path(self.station_id, suffix="_cam2")
        if self.thread:
            self.thread.join()

    def _mtx_register(self):
        if self.station_id and self.url:
            _mtx_add_path(self.station_id, self.url)

    def _try_rediscover_camera(self):
        if not self.station_id:
            return None
        station = database.get_station(self.station_id)
        if not station or not station.get("mac_address"):
            return None
        mac = station.get("mac_address", "")
        if not network.validate_mac(mac):
            return None
        new_ip = network.scan_lan_for_mac(mac)
        if new_ip and new_ip != station["ip_camera_1"]:
            database.update_station_ip(self.station_id, "ip_camera_1", new_ip)
            brand = station.get("camera_brand", "imou")
            code = station.get("safety_code", "")
            live_quality = database.get_setting("LIVE_VIEW_STREAM", "sub")
            url_fn = get_rtsp_url if live_quality == "main" else get_rtsp_sub_url
            new_url = url_fn(new_ip, code, channel=1, brand=brand)
            self.url = new_url
            self._mtx_register()
            with _streams_lock:
                reconnect_status[self.station_id] = {
                    "status": "found",
                    "new_ip": new_ip,
                    "old_ip": station["ip_camera_1"],
                }
            return new_ip
        if new_ip:
            with _streams_lock:
                reconnect_status[self.station_id] = {"status": "same_ip", "ip": new_ip}
        return None

    def _monitor_loop(self):
        while self.is_running:
            time.sleep(15)
            if not self.is_running:
                break
            if not self.station_id:
                continue
            try:
                req = urllib.request.Request(
                    f"{MTX_API}/v3/paths/list",
                    method="GET",
                )
                resp = urllib.request.urlopen(req, timeout=3)
                paths_data = json.loads(resp.read())
                items = paths_data.get("items", [])
                path_name = f"station_{self.station_id}"
                found = any(p.get("name") == path_name for p in items)
                if not found:
                    self._mtx_register()
                # Also check cam2 path
                if self.cam2_url:
                    cam2_path_name = f"station_{self.station_id}_cam2"
                    cam2_found = any(p.get("name") == cam2_path_name for p in items)
                    if not cam2_found:
                        _mtx_add_path(self.station_id, self.cam2_url, suffix="_cam2")
            except Exception as e:
                logger.error(f"[MTX] monitor loop error for station_{self.station_id}: {e}")

    def update_url(self, new_url):
        with self._lock:
            self.url = new_url
        if self.station_id:
            _mtx_remove_path(self.station_id)
            self._mtx_register()

    def update_cam2_url(self, new_url):
        with self._lock:
            old_cam2 = self.cam2_url
            self.cam2_url = new_url
        if old_cam2 and self.station_id:
            _mtx_remove_path(self.station_id, suffix="_cam2")
        if new_url and self.station_id:
            _mtx_add_path(self.station_id, new_url, suffix="_cam2")
        self._mtx_register()


def get_rtsp_url(ip, safety_code, channel=1, brand="imou"):
    if not ip or not safety_code:
        return ""
    if brand == "tenda":
        return f"rtsp://admin:{safety_code}@{ip}:554/ch={channel}&subtype=0"
    elif brand == "ezviz":
        return f"rtsp://admin:{safety_code}@{ip}:554/ch{channel}/main"
    elif brand == "tapo":
        stream_id = 1 if channel == 1 else 2
        return f"rtsp://admin:{safety_code}@{ip}:554/stream{stream_id}"
    else:
        return f"rtsp://admin:{safety_code}@{ip}:554/cam/realmonitor?channel={channel}&subtype=0"


def get_rtsp_sub_url(ip, safety_code, channel=1, brand="imou"):
    if not ip or not safety_code:
        return ""
    if brand == "tenda":
        return f"rtsp://admin:{safety_code}@{ip}:554/ch={channel}&subtype=1"
    elif brand == "ezviz":
        return f"rtsp://admin:{safety_code}@{ip}:554/ch{channel}/sub"
    elif brand == "tapo":
        return f"rtsp://admin:{safety_code}@{ip}:554/stream2"
    else:
        return f"rtsp://admin:{safety_code}@{ip}:554/cam/realmonitor?channel={channel}&subtype=1"


import telegram_bot


def _cancel_recording_timer(station_id):
    with _recording_timers_lock:
        timer = _recording_timers.pop(station_id, None)
        warning_timer = _recording_warning_timers.pop(station_id, None)
    if timer:
        timer.cancel()
    if warning_timer:
        warning_timer.cancel()


def _auto_stop_recording(station_id, expected_record_id):
    with _station_locks_lock:
        lock = _station_locks.setdefault(station_id, threading.Lock())
    with lock:
        with _recorders_lock:
            recorder_inst = active_recorders.get(station_id)
            waybill = active_waybills.get(station_id)
            record_id = active_record_ids.get(station_id)

        if not recorder_inst or not record_id or record_id != expected_record_id:
            # Recording already stopped or different recording — bail out
            with _recording_timers_lock:
                _recording_timers.pop(station_id, None)
                _recording_start_times.pop(station_id, None)
            return

        database.update_record_status(record_id, "PROCESSING")
        notify_sse(
            "video_status",
            {
                "station_id": station_id,
                "status": "PROCESSING",
                "record_id": record_id,
                "auto_stopped": True,
            },
        )
        with _processing_lock:
            _processing_count[station_id] = _processing_count.get(station_id, 0) + 1
        with _recorders_lock:
            active_recorders.pop(station_id, None)
            active_waybills.pop(station_id, None)
            active_record_ids.pop(station_id, None)

        _cancel_recording_timer(station_id)
        with _recording_timers_lock:
            _recording_start_times.pop(station_id, None)

        submitted = video_worker.submit_stop_and_save(record_id, recorder_inst, waybill, station_id, save=True)
        if not submitted:
            database.update_record_status(record_id, "FAILED")
            with _processing_lock:
                _processing_count.pop(station_id, None)
            notify_sse(
                "video_status",
                {
                    "station_id": station_id,
                    "status": "FAILED",
                    "record_id": record_id,
                },
            )

        database.log_audit(0, "AUTO_STOP", f"Station {station_id} - max duration reached")


def _emit_recording_warning(station_id):
    with _recorders_lock:
        if station_id not in active_recorders:
            return
    remaining = _MAX_RECORDING_SECONDS - _RECORDING_WARNING_SECONDS
    notify_sse(
        "recording_warning",
        {
            "station_id": station_id,
            "remaining_seconds": remaining,
        },
    )


def _preflight_checks(station_id):
    with _recorders_lock:
        if station_id in active_recorders:
            return (
                False,
                "Trạm đang ghi hình. Quét STOP trước.",
            )
    _, _, free = shutil.disk_usage("recordings")
    if free < 500 * 1024 * 1024:
        return (
            False,
            f"\u1ed4 c\u1ee9ng qu\u00e1 \u0111\u1ea7y! Ch\u1ec9 c\u00f2n {free // (1024 * 1024)} MB tr\u1ed1ng. C\u1ea7n \u00edt nh\u1ea5t 500 MB.",
        )
    ffmpeg_path = recorder._ffmpeg_bin("ffmpeg")
    if not os.path.exists(ffmpeg_path) and ffmpeg_path != "ffmpeg":
        return (
            False,
            "Kh\u00f4ng t\u00ecm th\u1ea5y FFmpeg. Vui l\u00f2ng ch\u1ea1y l\u1ea1i installer.",
        )
    if ffmpeg_path == "ffmpeg" and not shutil.which("ffmpeg"):
        return (
            False,
            "Kh\u00f4ng t\u00ecm th\u1ea5y FFmpeg. Vui l\u00f2ng c\u00e0i \u0111\u1eb7t.",
        )
    return True, ""


def _verify_video_external(filepath):
    if not filepath or not os.path.exists(filepath):
        return False
    if os.path.getsize(filepath) == 0:
        return False
    try:
        cmd = [
            recorder._ffmpeg_bin("ffprobe"),
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "csv=p=0",
            filepath,
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        dur = r.stdout.strip()
        return bool(dur and float(dur) > 0)
    except Exception:
        return False


def _recover_pending_records():
    pending = database.get_pending_records()
    if not pending:
        return
    logger.info(f"Crash recovery: found {len(pending)} pending records")
    for rec in pending:
        rid = rec["id"]
        paths = rec["video_paths"]
        waybill = rec["waybill_code"]
        recovered = False
        if paths:
            for path in paths.split(","):
                ts_path = path + ".tmp.ts"
                if os.path.exists(ts_path):
                    is_hevc = recorder._is_hevc(ts_path)
                    try:
                        if is_hevc:
                            cmd = recorder._build_transcode_cmd(ts_path, path)
                        else:
                            cmd = [
                                recorder._ffmpeg_bin("ffmpeg"),
                                "-y",
                                "-i",
                                ts_path,
                                "-c",
                                "copy",
                                "-movflags",
                                "+faststart",
                                path,
                            ]
                        subprocess.run(
                            cmd,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            timeout=120,
                        )
                        try:
                            os.remove(ts_path)
                        except Exception:
                            pass
                        if _verify_video_external(path):
                            recovered = True
                            break
                    except Exception as e:
                        logger.error(f"[RECOVERY] transcode failed for record {rid}: {e}")
                elif os.path.exists(path) and _verify_video_external(path):
                    recovered = True
                    break

        if recovered:
            database.update_record_status(rid, "READY", video_paths=paths)
            logger.info(f"Recovered record {rid} ({waybill}) \u2192 READY")
        else:
            database.update_record_status(rid, "FAILED", video_paths=paths)
            logger.error(f"Failed to recover record {rid} ({waybill}) \u2192 FAILED")
            try:
                msg = (
                    f"\u26a0\ufe0f <b>PH\u1ee4C H\u1ed2I VIDEO L\u1ed6I</b>\n\n"
                    f"\U0001f4e6 M\u00e3 v\u1eadn \u0111\u01a1n: <b>{waybill}</b>\n"
                    f"\U0001f194 Record ID: {rid}\n"
                    f"\u274c Kh\u00f4ng th\u1ec3 ph\u1ee5c h\u1ed3i video sau khi kh\u1edfi \u0111\u1ed9ng l\u1ea1i server.\n\n"
                    f"Vui l\u00f2ng ki\u1ec3m tra th\u1ee7 c\u00f4ng."
                )
                telegram_bot.send_telegram_message(msg)
            except Exception:
                pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_event_loop()
    orig_handler = loop.get_exception_handler()

    def _suppress_conn_reset(loop, ctx):
        exc = ctx.get("exception")
        if isinstance(exc, (ConnectionResetError, ConnectionAbortedError)):
            _logger.debug("Suppressed connection reset error")
            return
        if orig_handler:
            orig_handler(loop, ctx)
        else:
            loop.default_exception_handler(ctx)

    loop.set_exception_handler(_suppress_conn_reset)

    database.init_db()
    recovery_thread = threading.Thread(target=_recover_pending_records, daemon=True)
    recovery_thread.start()
    stations = database.get_stations()
    live_quality = database.get_setting("LIVE_VIEW_STREAM", "sub")
    for st in stations:
        brand = st.get("camera_brand", "imou")
        code = st["safety_code"]
        if live_quality == "main":
            live_url = get_rtsp_url(
                st["ip_camera_1"],
                code,
                channel=1,
                brand=brand,
            )
        else:
            live_url = get_rtsp_sub_url(
                st["ip_camera_1"],
                code,
                channel=1,
                brand=brand,
            )
        cam2_url = None
        if st.get("ip_camera_2"):
            cam2_ip = st["ip_camera_2"]
            if live_quality == "main":
                cam2_url = get_rtsp_url(cam2_ip, code, channel=2, brand=brand)
            else:
                cam2_url = get_rtsp_sub_url(cam2_ip, code, channel=2, brand=brand)
        manager = CameraStreamManager(live_url, station_id=st["id"], cam2_url=cam2_url)
        with _streams_lock:
            stream_managers[st["id"]] = manager
        manager.start()

    # Kích hoạt Telegram Bot 2 chiều (Lắng nghe)
    telegram_bot.start_polling()

    async def _periodic_audit_cleanup():
        while True:
            await asyncio.sleep(86400)  # 24 hours
            database.cleanup_audit_log()

    cleanup_task = asyncio.create_task(_periodic_audit_cleanup())

    yield
    cleanup_task.cancel()
    with _recording_timers_lock:
        for timer in _recording_timers.values():
            timer.cancel()
        _recording_timers.clear()
        for timer in _recording_warning_timers.values():
            timer.cancel()
        _recording_warning_timers.clear()
        _recording_start_times.clear()
    with _streams_lock:
        managers = list(stream_managers.values())
    for manager in managers:
        manager.stop()
    with _recorders_lock:
        recorders = list(active_recorders.values())
    for rec in recorders:
        rec.stop_recording()
    video_worker.shutdown()
    telegram_bot.stop_polling()


app = FastAPI(title="CamDongHang API Multi-Station", lifespan=lifespan)


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
    return origins


app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

if not os.path.exists("recordings"):
    os.makedirs("recordings")

# Tự động dọn dẹp các video cũ
try:
    keep_days = int(database.get_setting("RECORD_KEEP_DAYS", 7))
    database.cleanup_old_records(keep_days)
except Exception:
    pass


# --- REGISTER ROUTE MODULES ---
import routes_auth
import routes_records
import routes_stations
import routes_system

routes_auth.register_routes(app)
routes_stations.register_routes(app)
routes_records.register_routes(app)
routes_system.register_routes(app)


# --- SERVE FRONTEND (PRODUCTION BUILD) ---
dist_dir = os.path.join(os.getcwd(), "web-ui", "dist")
if getattr(sys, "frozen", False):
    dist_dir = os.path.join(sys._MEIPASS, "web-ui", "dist")

if os.path.exists(dist_dir):
    app.mount("/", StaticFiles(directory=dist_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn

    bind_host = os.environ.get("VPACK_HOST", "0.0.0.0")
    uvicorn.run(app, host=bind_host, port=8001)
