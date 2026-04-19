# =============================================================================
# V-Pack Monitor - CamDongHang v3.2.0
import logging

logger = logging.getLogger(__name__)

# Copyright (c) 2024-2026 VDT - Vu Duc Thang (thangvd2)
# All rights reserved. Unauthorized copying or distribution is prohibited.
# =============================================================================

import csv
import io
import ipaddress
import json
import os
import platform as _platform
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request

import psutil
from fastapi import File, HTTPException, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

import api
import cloud_sync
import database
import video_worker
from auth import AdminUser, CurrentUser

_SENSITIVE_KEYS = {"S3_SECRET_KEY", "S3_ACCESS_KEY", "TELEGRAM_BOT_TOKEN"}


_update_lock = threading.Lock()
_is_updating = False
_update_check_cache = {"result": None, "timestamp": 0}
_UPDATE_CHECK_TTL = 3600


def _get_git_branch():
    try:
        import subprocess as _sp

        r = _sp.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if r.returncode == 0:
            branch = r.stdout.strip()
            if branch and branch != "HEAD":
                return branch
        r2 = _sp.run(
            ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if r2.returncode == 0:
            return r2.stdout.strip().replace("refs/remotes/origin/", "")
    except Exception:
        pass
    return "master"


def _notify_update_progress(stage, message, progress=0):
    api.notify_sse(
        "update_progress",
        {
            "stage": stage,
            "message": message,
            "progress": progress,
        },
    )


def _do_graceful_restart():
    global _is_updating
    time.sleep(1.5)
    try:
        with api._recorders_lock:
            recorders = list(api.active_recorders.values())
        for rec in recorders:
            try:
                rec.stop_recording()
            except Exception as e:
                logger.error(f"[RESTART] stop recorder failed: {e}")
        video_worker.shutdown()
        _notify_update_progress("restarting", "Đang khởi động lại...", 100)
        time.sleep(1.5)
        if _platform.system() == "Windows":
            bat_content = "@echo off\r\n"
            bat_content += "timeout /t 3 /nobreak >nul\r\n"
            bat_content += 'cd /d "' + os.getcwd() + '"\r\n'
            bat_content += "call start_windows.bat\r\n"
            bat_content += 'del "%~f0"\r\n'
            bat_fd, bat_path = tempfile.mkstemp(suffix=".bat", prefix="vpack_restart_")
            try:
                with os.fdopen(bat_fd, "w") as f:
                    f.write(bat_content)
                subprocess.Popen(["cmd", "/c", bat_path], creationflags=0x00000008)
            finally:
                try:
                    os.unlink(bat_path)
                except Exception:
                    pass
        else:
            sh_content = "#!/bin/bash\n"
            sh_content += "sleep 3\n"
            sh_content += 'cd "' + os.getcwd() + '"\n'
            sh_content += "bash start.sh\n"
            sh_content += 'rm -- "$0"\n'
            sh_fd, sh_path = tempfile.mkstemp(suffix=".sh", prefix="vpack_restart_")
            try:
                with os.fdopen(sh_fd, "w") as f:
                    f.write(sh_content)
                subprocess.run(["chmod", "+x", sh_path])
                subprocess.Popen(["bash", sh_path], start_new_session=True)
            finally:
                try:
                    os.unlink(sh_path)
                except Exception:
                    pass
    except Exception as e:
        logger.error(f"[RESTART] CRITICAL: graceful restart failed: {e}")
        _is_updating = False
    finally:
        sys.exit(0)


def _update_dev():
    import subprocess as _sp

    try:
        _notify_update_progress("checking", "Đang kiểm tra bản cập nhật...", 10)
        branch = _get_git_branch()

        stash_result = _sp.run(
            ["git", "stash"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        had_stash = "No local changes" not in (stash_result.stdout or "")

        _notify_update_progress("downloading", "Đang tải bản cập nhật (git pull)...", 30)
        r = _sp.run(
            ["git", "pull", "origin", branch],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if r.returncode != 0:
            if had_stash:
                _sp.run(["git", "stash", "pop"], capture_output=True, timeout=30)
            logger.error(f"[UPDATE] git pull failed: {r.stderr[:200]}")
            return {
                "status": "error",
                "message": "Cập nhật thất bại.",
            }

        if had_stash:
            pop_result = _sp.run(["git", "stash", "pop"], capture_output=True, text=True, timeout=30)
            if pop_result.returncode != 0:
                logger.error("[UPDATE] WARNING: git stash pop failed. Changes preserved in stash.")
                logger.info("[UPDATE] Run 'git stash list' and 'git stash pop' manually.")
                return {
                    "status": "error",
                    "message": "Cập nhật thành công nhưng có xung đột. Xem log.",
                }

        _notify_update_progress("installing", "Đang cài đặt npm dependencies...", 50)
        if _platform.system() == "Windows":
            _sp.run(
                ["cmd", "/c", "npm", "install"],
                cwd="web-ui",
                capture_output=True,
                timeout=120,
            )
        else:
            _sp.run(
                ["npm", "install"],
                cwd="web-ui",
                capture_output=True,
                timeout=120,
            )

        _notify_update_progress("building", "Đang build frontend...", 70)
        if _platform.system() == "Windows":
            _sp.run(
                ["cmd", "/c", "npm", "run", "build"],
                cwd="web-ui",
                capture_output=True,
                timeout=120,
            )
        else:
            _sp.run(
                ["npm", "run", "build"],
                cwd="web-ui",
                capture_output=True,
                timeout=120,
            )

        _notify_update_progress("restarting", "Đang chuẩn bị khởi động lại...", 90)
        return {
            "status": "restarting",
            "message": "Cập nhật thành công. Đang khởi động lại...",
        }
    except Exception as e:
        logger.error(f"[UPDATE] Error: {e}")
        return {"status": "error", "message": "Lỗi cập nhật."}


def _update_production():
    import subprocess as _sp
    import tempfile
    import zipfile

    try:
        _notify_update_progress("checking", "Đang kiểm tra GitHub Release...", 5)
        req = urllib.request.Request(
            "https://api.github.com/repos/thangvd2/V-Pack-Monitor/releases/latest",
            headers={"User-Agent": "V-Pack-Monitor"},
        )
        resp = urllib.request.urlopen(req, timeout=10)
        release = json.loads(resp.read())
        tag = release.get("tag_name", "")
        if not tag:
            return {"status": "error", "message": "Không tìm thấy bản release."}

        _notify_update_progress("downloading", f"Đang tải {tag}...", 20)
        zip_url = f"https://github.com/thangvd2/V-Pack-Monitor/archive/refs/tags/{tag}.zip"
        zip_resp = urllib.request.urlopen(zip_url, timeout=120)
        tmp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(tmp_dir, f"{tag}.zip")
        with open(zip_path, "wb") as f:
            while True:
                chunk = zip_resp.read(65536)
                if not chunk:
                    break
                f.write(chunk)

        _notify_update_progress("extracting", "Đang giải nén...", 40)
        # Verify zip integrity before extraction
        try:
            with zipfile.ZipFile(zip_path, "r") as test_zf:
                bad_file = test_zf.testzip()
                if bad_file:
                    shutil.rmtree(tmp_dir, ignore_errors=True)
                    return {
                        "status": "error",
                        "message": f"Zip file corrupted at entry: {bad_file}",
                    }
        except zipfile.BadZipFile:
            shutil.rmtree(tmp_dir, ignore_errors=True)
            return {
                "status": "error",
                "message": "Downloaded file is not a valid zip archive.",
            }
        with zipfile.ZipFile(zip_path, "r") as zf:
            for member in zf.infolist():
                # Prevent Zip Slip (path traversal)
                member_path = os.path.realpath(os.path.join(tmp_dir, member.filename))
                if not member_path.startswith(os.path.realpath(tmp_dir) + os.sep) and member_path != os.path.realpath(
                    tmp_dir
                ):
                    logger.info(f"[UPDATE] Zip Slip detected: skipping {member.filename}")
                    continue
                zf.extract(member, tmp_dir)
        tag_ver = tag[1:] if tag.startswith("v") else tag
        src_dir = os.path.join(tmp_dir, f"V-Pack-Monitor-{tag_ver}")
        if not os.path.isdir(src_dir):
            for d in os.listdir(tmp_dir):
                dp = os.path.join(tmp_dir, d)
                if os.path.isdir(dp) and "V-Pack" in d:
                    src_dir = dp
                    break
        if not os.path.isdir(src_dir):
            shutil.rmtree(tmp_dir, ignore_errors=True)
            return {"status": "error", "message": "Không tìm thấy thư mục giải nén."}

        _notify_update_progress("backup", "Đang sao lưu database...", 50)
        db_path = os.path.join("recordings", "packing_records.db")
        if os.path.exists(db_path):
            shutil.copy2(db_path, db_path + ".bak")

        _notify_update_progress("installing", "Đang cài đặt...", 60)
        excludes = {
            "recordings",
            "venv",
            "bin",
            "credentials.json",
            ".env",
            "install_log.txt",
            "__pycache__",
            ".git",
            "_update_restart.bat",
            "_update_restart.sh",
        }
        for item in os.listdir(src_dir):
            if item in excludes:
                continue
            src = os.path.join(src_dir, item)
            dst = os.path.join(".", item)
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)

        _notify_update_progress("dependencies", "Đang cài đặt dependencies...", 75)
        _sp.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-q"],
            capture_output=True,
            timeout=120,
        )

        _notify_update_progress("building", "Đang build frontend...", 85)
        has_npm = False
        if _platform.system() == "Windows":
            has_npm = (
                _sp.run(
                    ["cmd", "/c", "where", "npm"],
                    capture_output=True,
                    timeout=5,
                ).returncode
                == 0
            )
        else:
            has_npm = shutil.which("npm") is not None
        if has_npm:
            if _platform.system() == "Windows":
                _sp.run(
                    ["cmd", "/c", "npm", "install"],
                    cwd="web-ui",
                    capture_output=True,
                    timeout=120,
                )
                _sp.run(
                    ["cmd", "/c", "npm", "run", "build"],
                    cwd="web-ui",
                    capture_output=True,
                    timeout=120,
                )
            else:
                _sp.run(
                    ["npm", "install"],
                    cwd="web-ui",
                    capture_output=True,
                    timeout=120,
                )
                _sp.run(
                    ["npm", "run", "build"],
                    cwd="web-ui",
                    capture_output=True,
                    timeout=120,
                )
        else:
            _notify_update_progress(
                "building",
                "Bỏ qua npm build (không có Node.js). Dùng dist/ có sẵn.",
                85,
            )

        shutil.rmtree(tmp_dir, ignore_errors=True)
        db_bak = os.path.join("recordings", "packing_records.db.bak")
        if os.path.exists(db_bak):
            try:
                os.remove(db_bak)
            except OSError:
                pass

        _notify_update_progress("restarting", "Đang chuẩn bị khởi động lại...", 95)
        return {
            "status": "restarting",
            "message": "Cập nhật thành công. Đang khởi động lại...",
        }
    except Exception as e:
        db_path = os.path.join("recordings", "packing_records.db")
        if os.path.exists(db_path + ".bak"):
            shutil.copy2(db_path + ".bak", db_path)
        logger.error(f"[UPDATE] Error: {e}")
        return {"status": "error", "message": "Lỗi cập nhật."}


def _validate_ping_ip(ip_str):
    """Validate that IP is a valid IPv4 address."""
    try:
        addr = ipaddress.ip_address(ip_str)
        return isinstance(addr, ipaddress.IPv4Address)
    except ValueError:
        return False


class SettingsUpdate(BaseModel):
    RECORD_KEEP_DAYS: int
    RECORD_STREAM_TYPE: str = "main"
    CLOUD_PROVIDER: str = "NONE"
    GDRIVE_FOLDER_ID: str = ""
    S3_ENDPOINT: str = ""
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_BUCKET_NAME: str = ""
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""


def register_routes(app):
    # --- SYSTEM HEALTH API ---

    @app.get("/api/system/disk")
    def get_disk_health(current_user: CurrentUser):
        total, used, free = shutil.disk_usage("recordings")
        return {
            "status": "success",
            "total": total,
            "used": used,
            "free": free,
            "percentage": round(used / total * 100, 2),
        }

    # --- SYSTEM SETTINGS API ---

    @app.get("/api/settings")
    def get_settings(admin: AdminUser):
        settings = database.get_all_settings()
        for k in _SENSITIVE_KEYS:
            if k in settings and settings[k]:
                settings[k] = "****"
        return {"data": settings}

    @app.post("/api/settings")
    def update_settings(payload: SettingsUpdate, admin: AdminUser):
        data = payload.dict()
        current = database.get_all_settings()
        for k in _SENSITIVE_KEYS:
            if k in data and data[k] == "****":
                data[k] = current.get(k, "")
        database.set_settings(data)
        database.log_audit(admin["id"], "SETTINGS_UPDATE", f"keys={list(data.keys())}")

        # Restart Telegram Bot polling if tokens change
        if payload.TELEGRAM_BOT_TOKEN and payload.TELEGRAM_CHAT_ID:
            # Import dynamic if not already
            import telegram_bot

            telegram_bot.start_polling()

        return {"status": "success", "message": "Đã lưu cài đặt hệ thống."}

    @app.post("/api/live-stream-quality")
    def set_live_stream_quality(payload: dict, admin: AdminUser):
        quality = payload.get("quality", "sub")
        if quality not in ("main", "sub"):
            quality = "sub"
        database.set_setting("LIVE_VIEW_STREAM", quality)
        with api._streams_lock:
            sm_items = list(api.stream_managers.items())
        for sid, sm in sm_items:
            station = database.get_station(sid)
            if not station:
                continue
            ip = station["ip_camera_1"]
            code = station["safety_code"]
            brand = station.get("camera_brand", "imou")
            if quality == "main":
                new_url = api.get_rtsp_url(ip, code, channel=1, brand=brand)
            else:
                new_url = api.get_rtsp_sub_url(ip, code, channel=1, brand=brand)
            sm.update_url(new_url)
            if sm.cam2_url is not None:
                cam2_ip = station.get("ip_camera_2") or ip
                if quality == "main":
                    new_cam2 = api.get_rtsp_url(cam2_ip, code, channel=2, brand=brand)
                else:
                    new_cam2 = api.get_rtsp_sub_url(cam2_ip, code, channel=2, brand=brand)
                sm.update_cam2_url(new_cam2)
        label = "1080p (main)" if quality == "main" else "480p (sub)"
        return {"status": "success", "message": f"Live view: {label}"}

    @app.get("/api/live-stream-quality")
    def get_live_stream_quality(current_user: CurrentUser):
        quality = database.get_setting("LIVE_VIEW_STREAM", "sub")
        return {"quality": quality}

    # --- CLOUD BACKUP API ---

    @app.post("/api/credentials")
    async def upload_credentials(admin: AdminUser, file: UploadFile = File(...)):
        contents = await file.read(api.MAX_UPLOAD_SIZE + 1)
        if len(contents) > api.MAX_UPLOAD_SIZE:
            return JSONResponse(
                status_code=413,
                content={"status": "error", "message": "File quá lớn (tối đa 1MB)."},
            )
        try:
            data = json.loads(contents)
            if not isinstance(data, dict) or "type" not in data:
                raise ValueError("Not a valid service account JSON")
        except (json.JSONDecodeError, ValueError) as e:
            raise HTTPException(status_code=400, detail=f"File không hợp lệ: {e}")
        with open("credentials.json", "wb") as f:
            f.write(contents)
        return {"status": "success", "message": "Đã cập nhật credentials.json"}

    @app.post("/api/cloud-sync")
    def trigger_cloud_sync(admin: AdminUser):
        try:
            msg = cloud_sync.process_cloud_sync()
            return {"status": "success", "message": msg}
        except Exception as e:
            logger.error(f"[CLOUD] sync failed: {e}")
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": "Lỗi đồng bộ cloud."},
            )

    # --- ANALYTICS DASHBOARD API ---

    @app.get("/api/analytics/today")
    def get_analytics_today(station_id: int, current_user: CurrentUser):
        conn = database.get_connection()
        with conn:
            cursor = conn.cursor()

            # Đếm tổng đơn toàn hệ thống kho hôm nay (SQLite local time)
            cursor.execute(
                "SELECT COUNT(*) FROM packing_video WHERE date(recorded_at, 'localtime') = date('now', 'localtime')"
            )
            total_today = cursor.fetchone()[0]

            # Đếm số đơn riêng của trạm đang chọn
            cursor.execute(
                "SELECT COUNT(*) FROM packing_video WHERE date(recorded_at, 'localtime') = date('now', 'localtime') AND station_id = ?",
                (station_id,),
            )
            station_today = cursor.fetchone()[0]

            return {"data": {"total_today": total_today, "station_today": station_today}}

    # --- ANALYTICS PRO API ---

    @app.get("/api/analytics/hourly")
    def get_hourly_stats_api(
        current_user: CurrentUser,
        date: str | None = None,
        station_id: int | None = None,
    ):
        data = database.get_hourly_stats(date=date, station_id=station_id)
        return {"data": data}

    @app.get("/api/analytics/trend")
    def get_daily_trend_api(current_user: CurrentUser, days: int = 7):
        days = max(min(days, 30), 1)
        data = database.get_daily_trend(days=days)
        return {"data": data}

    @app.get("/api/analytics/stations-comparison")
    def get_stations_comparison_api(current_user: CurrentUser):
        data = database.get_stations_comparison()
        return {"data": data}

    @app.get("/api/export/csv")
    def export_csv(
        current_user: CurrentUser,
        date: str | None = None,
        station_id: int | None = None,
    ):
        records = database.get_records_for_export(date=date, station_id=station_id)

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Mã vận đơn", "Trạm", "Thời gian ghi", "Trạng thái", "File video"])
        for r in records:
            video_files = (
                "; ".join(r.get("video_paths", []))
                if isinstance(r.get("video_paths"), list)
                else (r.get("video_paths") or "")
            )
            writer.writerow(
                [
                    r["waybill_code"],
                    r.get("station_name", ""),
                    r.get("recorded_at", ""),
                    r.get("status", ""),
                    video_files,
                ]
            )

        output.seek(0)
        csv_bytes = ("\ufeff" + output.getvalue()).encode("utf-8-sig")
        filename = f"vpack_export_{date or 'all'}.csv"
        return StreamingResponse(
            iter([csv_bytes]),
            media_type="text/csv; charset=utf-8-sig",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    # --- SYSTEM HEALTH PRO API ---

    @app.get("/api/system/health")
    def get_system_health(admin: AdminUser):
        cpu_percent = psutil.cpu_percent(interval=0.5)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("recordings")

        def _status(value, warn_threshold, crit_threshold):
            if value >= crit_threshold:
                return "critical"
            if value >= warn_threshold:
                return "warning"
            return "ok"

        uptime_seconds = int(time.time() - api._SERVER_START_TIME)
        days, remainder = divmod(uptime_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{days}d {hours}h {minutes}m {seconds}s" if days > 0 else f"{hours}h {minutes}m {seconds}s"

        return {
            "cpu": {
                "percent": cpu_percent,
                "count": psutil.cpu_count(),
                "status": _status(cpu_percent, 80, 95),
            },
            "memory": {
                "total_gb": round(memory.total / (1024**3), 1),
                "used_gb": round(memory.used / (1024**3), 1),
                "percent": memory.percent,
                "status": _status(memory.percent, 85, 95),
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 1),
                "used_gb": round(disk.used / (1024**3), 1),
                "percent": disk.percent,
                "status": _status(disk.percent, 80, 95),
            },
            "uptime": uptime_str,
            "uptime_seconds": uptime_seconds,
        }

    @app.get("/api/system/processes")
    def get_system_processes(admin: AdminUser):
        import re as _re

        ffmpeg_procs = []
        for proc in psutil.process_iter(["pid", "name", "cmdline", "cpu_percent", "memory_percent", "create_time"]):
            try:
                name = proc.info["name"] or ""
                if "ffmpeg" in name.lower():
                    cmdline = proc.info.get("cmdline") or []
                    cmdline_str = " ".join(cmdline)[:120] if cmdline else ""
                    cmdline_str = _re.sub(r"://[^@]+@", "://***@", cmdline_str)
                    ffmpeg_procs.append(
                        {
                            "pid": proc.info["pid"],
                            "name": name,
                            "cmdline_short": cmdline_str,
                            "cpu_percent": proc.info.get("cpu_percent") or 0,
                            "memory_percent": round(proc.info.get("memory_percent") or 0, 1),
                        }
                    )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return {
            "ffmpeg_count": len(ffmpeg_procs),
            "ffmpeg_processes": ffmpeg_procs,
        }

    @app.get("/api/system/network-info")
    def get_network_info(admin: AdminUser):
        hostname = socket.gethostname()
        local_ip = "unknown"
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except Exception:
            pass

        camera_status = []
        stations = database.get_stations()
        for st in stations:
            ip = st.get("ip_camera_1", "")
            alive = False
            if ip:
                try:
                    if _platform.system() == "Windows":
                        result = subprocess.run(
                            ["ping", "-n", "1", "-w", "1000", ip],
                            capture_output=True,
                            timeout=3,
                        )
                    else:
                        result = subprocess.run(
                            ["ping", "-c", "1", "-W", "1", ip],
                            capture_output=True,
                            timeout=3,
                        )
                    alive = result.returncode == 0
                except Exception:
                    pass
            camera_status.append(
                {
                    "station_id": st["id"],
                    "station_name": st["name"],
                    "ip": ip,
                    "reachable": alive,
                }
            )

        return {
            "hostname": hostname,
            "local_ip": local_ip,
            "cameras": camera_status,
        }

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
        return {"ip": ip, "reachable": alive}

    # --- AUTO-UPDATE API ---

    @app.get("/api/system/update-check")
    def check_update(admin: AdminUser):
        now = time.time()
        with api._cache_lock:
            if _update_check_cache["result"] and (now - _update_check_cache["timestamp"]) < _UPDATE_CHECK_TTL:
                return _update_check_cache["result"]

        import subprocess as _sp

        current = api._read_version()
        mode = "dev" if os.path.exists(".git") else "production"
        latest = current
        update_available = False
        changelog = ""

        try:
            if mode == "dev":
                branch = _get_git_branch()
                _sp.run(
                    ["git", "fetch", "origin", branch],
                    capture_output=True,
                    timeout=30,
                )
                r = _sp.run(
                    ["git", "describe", "--tags", "--abbrev=0", f"origin/{branch}"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if r.returncode == 0 and r.stdout.strip():
                    latest = r.stdout.strip()
                else:
                    r2 = _sp.run(
                        ["git", "rev-parse", "--short", f"origin/{branch}"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    if r2.returncode == 0:
                        latest = r2.stdout.strip()
                r3 = _sp.run(
                    ["git", "rev-parse", "HEAD"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                local_head = r3.stdout.strip() if r3.returncode == 0 else ""
                r4 = _sp.run(
                    ["git", "rev-parse", f"origin/{branch}"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                remote_head = r4.stdout.strip() if r4.returncode == 0 else ""
                update_available = local_head != remote_head and remote_head != ""
                # In dev mode, if local is ahead of or equal to remote, show VERSION as latest
                if not update_available:
                    latest = current
            else:
                import urllib.request as _ur

                req = _ur.Request(
                    "https://api.github.com/repos/thangvd2/V-Pack-Monitor/releases/latest",
                    headers={"User-Agent": "V-Pack-Monitor"},
                )
                resp = _ur.urlopen(req, timeout=10)
                release = json.loads(resp.read())
                tag = release.get("tag_name", "")
                if tag:
                    latest = tag
                    changelog = release.get("body", "")
                update_available = api._parse_semver(latest) > api._parse_semver(current) and latest != "unknown"
        except Exception as e:
            logger.error(f"[UPDATE] check failed: {e}")

        result = {
            "current_version": current,
            "latest_version": latest,
            "update_available": update_available,
            "mode": mode,
            "changelog": changelog,
        }
        with api._cache_lock:
            _update_check_cache["result"] = result
            _update_check_cache["timestamp"] = now
        return result

    @app.post("/api/system/update")
    def perform_update(admin: AdminUser):
        global _is_updating

        if not _update_lock.acquire(blocking=False):
            return {"status": "error", "message": "Cập nhật đang chạy. Vui lòng đợi..."}

        if _is_updating:
            _update_lock.release()
            return {"status": "error", "message": "Cập nhật đang chạy. Vui lòng đợi..."}

        _is_updating = True
        try:
            with api._cache_lock:
                _update_check_cache["result"] = None
                _update_check_cache["timestamp"] = 0
            mode = "dev" if os.path.exists(".git") else "production"
            if mode == "dev":
                result = _update_dev()
            else:
                result = _update_production()

            if result.get("status") == "error":
                _is_updating = False
                _update_lock.release()
                return result

            restart_thread = threading.Thread(target=_do_graceful_restart, daemon=False)
            restart_thread.start()

            _update_lock.release()
            return result
        except Exception as e:
            _is_updating = False
            _update_lock.release()
            logger.error(f"[UPDATE] Update failed: {e}")
            import traceback

            traceback.print_exc()
            return {"status": "error", "message": "Lỗi cập nhật."}
