# =============================================================================
# V-Pack Monitor - CamDongHang v3.5.0
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Copyright (c) 2024-2026 VDT - Vu Duc Thang (thangvd2)
# All rights reserved. Unauthorized copying or distribution is prohibited.
# =============================================================================

import asyncio
import json
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from vpack import cloud_sync, database, network, recorder, state, telegram_bot, video_worker


def _mtx_cleanup_orphaned_paths(station_ids):
    """Remove MediaMTX paths for stations that no longer exist in DB."""
    import re

    try:
        req = urllib.request.Request(f"{state.MTX_API}/v3/paths/list", method="GET")
        resp = urllib.request.urlopen(req, timeout=5)
        paths = json.loads(resp.read())
        items = paths.get("items", [])
        pattern = re.compile(r"^station_(\d+)(?:_cam2)?$")
        for p in items:
            name = p.get("name", "")
            m = pattern.match(name)
            if m and int(m.group(1)) not in station_ids:
                suffix = name.removeprefix(f"station_{m.group(1)}")
                state._mtx_remove_path(int(m.group(1)), suffix=suffix)
                logger.info(f"[MTX] Cleaned orphaned path: {name}")
    except Exception as e:
        logger.debug(f"[MTX] Cleanup scan skipped (MediaMTX not available): {e}")


def _get_video_info_external(filepath):
    if not filepath or not os.path.exists(filepath):
        return (False, 0)
    if os.path.getsize(filepath) == 0:
        return (False, 0)
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
        if dur:
            dur_float = float(dur)
            if dur_float > 0:
                return (True, dur_float)
    except Exception:
        pass
    return (False, 0)


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
        total_duration = 0.0
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
                        is_valid, dur = _get_video_info_external(path)
                        if is_valid:
                            recovered = True
                            total_duration = max(total_duration, dur)
                    except Exception as e:
                        logger.error(f"[RECOVERY] transcode failed for record {rid}: {e}")
                elif os.path.exists(path):
                    is_valid, dur = _get_video_info_external(path)
                    if is_valid:
                        recovered = True
                        total_duration = max(total_duration, dur)

        if recovered:
            database.update_record_status(rid, "READY", video_paths=paths, duration=total_duration)
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
        if isinstance(exc, ConnectionResetError | ConnectionAbortedError):
            logger.debug("Suppressed connection reset error")
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

    # Cleanup orphaned MediaMTX paths from previous sessions
    station_ids = {st["id"] for st in stations}
    _mtx_cleanup_orphaned_paths(station_ids)

    live_quality = database.get_setting("LIVE_VIEW_STREAM", "sub")
    for st in stations:
        brand = st.get("camera_brand", "imou")
        code = st["safety_code"]
        if live_quality == "main":
            live_url = state.get_rtsp_url(
                st["ip_camera_1"],
                code,
                channel=1,
                brand=brand,
            )
        else:
            live_url = state.get_rtsp_sub_url(
                st["ip_camera_1"],
                code,
                channel=1,
                brand=brand,
            )
        cam2_url = None
        cam2_ip = st.get("ip_camera_2", "").strip()
        mode = st.get("camera_mode", "SINGLE").upper()
        # Auto-migrate deprecated camera modes
        if mode in ("PIP_SIM", "DUAL_FILE_SIM"):
            migrated = "PIP" if mode == "PIP_SIM" else "DUAL_FILE"
            logger.warning(
                "Station %d has deprecated camera_mode '%s'. Auto-migrated to '%s'.",
                st["id"],
                mode,
                migrated,
            )
            database.update_station_camera_mode(st["id"], migrated)
            mode = migrated
        if cam2_ip:
            if live_quality == "main":
                cam2_url = state.get_rtsp_url(cam2_ip, code, channel=2, brand=brand)
            else:
                cam2_url = state.get_rtsp_sub_url(cam2_ip, code, channel=2, brand=brand)
        elif mode in ("PIP", "DUAL_FILE"):
            cam2_ip = st["ip_camera_1"]
            if live_quality == "main":
                cam2_url = state.get_rtsp_url(cam2_ip, code, channel=2, brand=brand)
            else:
                cam2_url = state.get_rtsp_sub_url(cam2_ip, code, channel=2, brand=brand)
        manager = state.CameraStreamManager(
            live_url, station_id=st["id"], cam2_url=cam2_url, station_name=st.get("name", "")
        )
        with state._streams_lock:
            state.stream_managers[st["id"]] = manager
        manager.start()

    # Kích hoạt Telegram Bot 2 chiều (Lắng nghe)
    telegram_bot.start_polling()

    async def _periodic_audit_cleanup():
        while True:
            await asyncio.sleep(86400)  # 24 hours
            database.cleanup_audit_log()

    cleanup_task = asyncio.create_task(_periodic_audit_cleanup())

    async def _periodic_cloud_sync():
        _last_sync_day = None
        while True:
            await asyncio.sleep(3600)  # 1 hour
            try:
                provider = database.get_setting("CLOUD_PROVIDER")
                enabled = database.get_setting("CLOUD_SYNC_SCHEDULED")
                schedule_time = database.get_setting("CLOUD_SYNC_TIME") or "02:00"

                if provider and provider != "NONE" and enabled == "true":
                    now = datetime.now()
                    try:
                        scheduled_hour = int(schedule_time.split(":")[0])
                    except Exception:
                        scheduled_hour = 2

                    if now.hour == scheduled_hour and _last_sync_day != now.date():
                        _last_sync_day = now.date()
                        await asyncio.to_thread(cloud_sync.process_cloud_sync)
            except Exception as e:
                logger.error(f"[CLOUD] Scheduled sync failed: {e}")

    cloud_sync_task = asyncio.create_task(_periodic_cloud_sync())

    async def _periodic_camera_health_check():
        while True:
            try:
                interval = int(database.get_setting("CAMERA_HEALTH_CHECK_INTERVAL", 60))
            except Exception:
                interval = 60
            await asyncio.sleep(interval)
            try:
                try:
                    alert_minutes = int(database.get_setting("CAMERA_DOWN_ALERT_MINUTES", 5))
                except Exception:
                    alert_minutes = 5

                stations = database.get_stations()
                for st in stations:
                    station_id = str(st["id"])
                    ip = st.get("ip_camera_1")
                    if not ip:
                        continue

                    is_online, latency = await asyncio.to_thread(network.check_ping, ip, 2000)
                    now_ts = int(time.time())

                    with state._camera_health_lock:
                        if station_id not in state._camera_health:
                            state._camera_health[station_id] = {
                                "online": is_online,
                                "last_seen": now_ts if is_online else 0,
                                "latency_ms": latency,
                                "down_alert_sent": False,
                                "down_time": now_ts if not is_online else 0,
                            }
                            state_changed = True
                            prev_online = None
                        else:
                            prev_online = state._camera_health[station_id]["online"]
                            state_changed = prev_online != is_online

                            state._camera_health[station_id]["online"] = is_online
                            state._camera_health[station_id]["latency_ms"] = latency
                            if is_online:
                                state._camera_health[station_id]["last_seen"] = now_ts

                        current_state = dict(state._camera_health[station_id])

                    if state_changed:
                        state.notify_sse("camera_status", {"station_id": station_id, "online": is_online})

                        if is_online and prev_online is False and current_state.get("down_alert_sent"):
                            duration = now_ts - current_state.get("down_time", now_ts)
                            dur_mins = duration // 60
                            telegram_bot.send_telegram_message(
                                f"✅ <b>Camera UP</b>\nTrạm: {st.get('name')}\nThời gian gián đoạn: {dur_mins} phút"
                            )
                            with state._camera_health_lock:
                                state._camera_health[station_id]["down_alert_sent"] = False

                        if not is_online and prev_online is not False:
                            with state._camera_health_lock:
                                state._camera_health[station_id]["down_time"] = now_ts

                    if not is_online:
                        with state._camera_health_lock:
                            down_time = state._camera_health[station_id].get("down_time", now_ts)
                            alert_sent = state._camera_health[station_id].get("down_alert_sent", False)

                        if not alert_sent and (now_ts - down_time) >= alert_minutes * 60:
                            dt_str = datetime.fromtimestamp(down_time).strftime("%Y-%m-%d %H:%M:%S")
                            telegram_bot.send_telegram_message(
                                f"⚠️ <b>Camera DOWN</b>\nTrạm: {st.get('name')}\nIP: {ip}\nThời gian mất kết nối: {dt_str}"
                            )
                            with state._camera_health_lock:
                                state._camera_health[station_id]["down_alert_sent"] = True

            except Exception as e:
                logger.error(f"[HEALTH] Camera health check failed: {e}")

    camera_health_task = asyncio.create_task(_periodic_camera_health_check())

    yield
    cleanup_task.cancel()
    cloud_sync_task.cancel()
    camera_health_task.cancel()
    with state._recording_timers_lock:
        for timer in state._recording_timers.values():
            timer.cancel()
        state._recording_timers.clear()
        for timer in state._recording_warning_timers.values():
            timer.cancel()
        state._recording_warning_timers.clear()
        state._recording_start_times.clear()
    with state._streams_lock:
        managers = list(state.stream_managers.values())
    for manager in managers:
        manager.stop()
    with state._recorders_lock:
        recorders = list(state.active_recorders.values())
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
    keep_days = int(database.get_setting("RECORD_KEEP_DAYS", 365))
    if keep_days > 0:
        logger.info(f"[STARTUP] Auto-cleanup: removing records older than {keep_days} days")
        database.cleanup_old_records(keep_days)
    else:
        logger.info("[STARTUP] Auto-cleanup: disabled (keep_days=0, never delete)")
except Exception:
    pass


# --- REGISTER ROUTE MODULES ---
from vpack.routes import auth as routes_auth
from vpack.routes import records as routes_records
from vpack.routes import stations as routes_stations
from vpack.routes import system as routes_system

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
