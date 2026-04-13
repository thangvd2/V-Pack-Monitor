# =============================================================================
# V-Pack Monitor - CamDongHang v2.1.0
# Copyright (c) 2024-2026 VDT - Vu Duc Thang (thangvd2)
# All rights reserved. Unauthorized copying or distribution is prohibited.
# =============================================================================

import os
import sys
import time
import shutil
import threading
import sqlite3
import json
import asyncio
import urllib.request
import urllib.error
import io
import csv
import jwt as _jwt
import platform as _platform
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel, Field
import database
import recorder
from recorder import CameraRecorder
import cloud_sync
import network
import video_worker
import psutil
import auth
from auth import CurrentUser, AdminUser, oauth2_scheme

_SERVER_START_TIME = time.time()


def _read_version():
    try:
        vpath = os.path.join(os.path.dirname(__file__) or ".", "VERSION")
        with open(vpath, "r") as f:
            return f.read().strip()
    except Exception:
        return "unknown"

# --- Quản lý Trạng thái Ghi hình Đa Trạm ---
active_recorders = {}
active_waybills = {}
active_record_ids = {}
_processing_count = {}  # {station_id: int} — counts pending video conversions
_station_locks = {}  # {station_id: threading.Lock} — prevents double-scan per station
stream_managers = {}

reconnect_status = {}

MTX_API = "http://127.0.0.1:9997"

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
        print(f"[MTX] replace {name} failed: {e}")
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
        print(f"[MTX] ERROR: add {name} failed after all retries: {e}")


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
            print(f"[MTX] delete {name} failed: {e}")
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
            reconnect_status[self.station_id] = {
                "status": "found",
                "new_ip": new_ip,
                "old_ip": station["ip_camera_1"],
            }
            return new_ip
        if new_ip:
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
                print(f"[MTX] monitor loop error for station_{self.station_id}: {e}")

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


import telebot
import telegram_bot


def _preflight_checks(station_id):
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
    if os.path.exists(ffmpeg_path):
        pass
    elif ffmpeg_path == "ffmpeg":
        if not shutil.which("ffmpeg"):
            return (
                False,
                "Kh\u00f4ng t\u00ecm th\u1ea5y FFmpeg. Vui l\u00f2ng c\u00e0i \u0111\u1eb7t.",
            )
    else:
        return (
            False,
            "Kh\u00f4ng t\u00ecm th\u1ea5y FFmpeg. Vui l\u00f2ng ch\u1ea1y l\u1ea1i installer.",
        )
    return True, ""


def _verify_video_external(filepath):
    import subprocess

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
    print(f"Crash recovery: found {len(pending)} pending records")
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
                        import subprocess

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
                        print(f"[RECOVERY] transcode failed for record {rid}: {e}")
                elif os.path.exists(path) and _verify_video_external(path):
                    recovered = True
                    break

        if recovered:
            database.update_record_status(rid, "READY", video_paths=paths)
            print(f"Recovered record {rid} ({waybill}) \u2192 READY")
        else:
            database.update_record_status(rid, "FAILED", video_paths=paths)
            print(f"Failed to recover record {rid} ({waybill}) \u2192 FAILED")
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
    import asyncio

    loop = asyncio.get_event_loop()
    orig_handler = loop.get_exception_handler()

    def _suppress_conn_reset(loop, ctx):
        exc = ctx.get("exception")
        if isinstance(exc, (ConnectionResetError, ConnectionAbortedError)):
            return
        if orig_handler:
            orig_handler(loop, ctx)
        else:
            loop.default_exception_handler(ctx)

    loop.set_exception_handler(_suppress_conn_reset)

    database.init_db()
    _recover_pending_records()
    stations = database.get_stations()
    live_quality = database.get_setting("LIVE_VIEW_STREAM", "sub")
    for st in stations:
        brand = st.get("camera_brand", "imou")
        code = st["safety_code"]
        if live_quality == "main":
            live_url = get_rtsp_url(
                st["ip_camera_1"], code, channel=1, brand=brand,
            )
        else:
            live_url = get_rtsp_sub_url(
                st["ip_camera_1"], code, channel=1, brand=brand,
            )
        cam2_url = None
        if st.get("ip_camera_2"):
            cam2_ip = st["ip_camera_2"]
            if live_quality == "main":
                cam2_url = get_rtsp_url(cam2_ip, code, channel=2, brand=brand)
            else:
                cam2_url = get_rtsp_sub_url(cam2_ip, code, channel=2, brand=brand)
        manager = CameraStreamManager(
            live_url, station_id=st["id"], cam2_url=cam2_url
        )
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
    for manager in stream_managers.values():
        manager.stop()
    for recorder in active_recorders.values():
        recorder.stop_recording()
    video_worker.shutdown()
    telegram_bot.stop_polling()


app = FastAPI(title="CamDongHang API Multi-Station", lifespan=lifespan)

def _get_cors_origins():
    origins = [
        "http://localhost:8001",
        "http://127.0.0.1:8001",
    ]
    try:
        import socket
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
    allow_methods=["*"],
    allow_headers=["*"],
)

if not os.path.exists("recordings"):
    os.makedirs("recordings")

# Tự động dọn dẹp các video cũ
try:
    keep_days = int(database.get_setting("RECORD_KEEP_DAYS", 7))
    database.cleanup_old_records(keep_days)
except BaseException:
    pass


# --- VIDEO DOWNLOAD API ---


@app.get("/api/records/{record_id}/download/{file_index}")
def download_record_file(request: Request, record_id: int, file_index: int):
    token = request.query_params.get("token") or request.headers.get(
        "Authorization", ""
    ).replace("Bearer ", "")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = auth.decode_token(token)
        jti = payload.get("jti")
        if jti and auth.is_token_revoked(jti):
            raise HTTPException(status_code=401, detail="Token revoked")
        user_id = payload.get("sub")
        user = database.get_user_by_id(int(user_id)) if user_id else None
        if not user or not user.get("is_active"):
            raise HTTPException(status_code=401, detail="Not authenticated")
    except _jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    from fastapi.responses import FileResponse as _FR

    record = database.get_record_by_id(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    paths_str = record.get("video_paths") or ""
    paths = [p.strip() for p in paths_str.split(",") if p.strip()]
    if file_index < 0 or file_index >= len(paths):
        raise HTTPException(status_code=404, detail="File not found")
    filepath = paths[file_index]
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File deleted")
    return _FR(filepath, media_type="video/mp4", filename=os.path.basename(filepath))


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


_SENSITIVE_KEYS = {"S3_SECRET_KEY", "S3_ACCESS_KEY", "TELEGRAM_BOT_TOKEN"}


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
    database.log_audit(
        admin["id"], "SETTINGS_UPDATE", f"keys={list(data.keys())}"
    )

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
    for sid, sm in stream_managers.items():
        station = database.get_station(sid)
        if not station:
            continue
        ip = station["ip_camera_1"]
        code = station["safety_code"]
        brand = station.get("camera_brand", "imou")
        if quality == "main":
            new_url = get_rtsp_url(ip, code, channel=1, brand=brand)
        else:
            new_url = get_rtsp_sub_url(ip, code, channel=1, brand=brand)
        sm.update_url(new_url)
        if sm.cam2_url is not None:
            cam2_ip = station.get("ip_camera_2") or ip
            if quality == "main":
                new_cam2 = get_rtsp_url(cam2_ip, code, channel=2, brand=brand)
            else:
                new_cam2 = get_rtsp_sub_url(cam2_ip, code, channel=2, brand=brand)
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
    contents = await file.read()
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
        print(f"[CLOUD] sync failed: {e}")
        return {"status": "error", "message": f"Lỗi đồng bộ cloud: {e}"}


# --- AUTH API ---


class LoginPayload(BaseModel):
    username: str
    password: str


_login_attempts = {}
_LOGIN_MAX = 5
_LOGIN_WINDOW = 300


@app.post("/api/auth/login")
def login(payload: LoginPayload, request: Request):
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    attempts = [t for t in _login_attempts.get(ip, []) if now - t < _LOGIN_WINDOW]
    if len(attempts) >= _LOGIN_MAX:
        return {"status": "error", "message": "Quá nhiều lần đăng nhập sai. Thử lại sau 5 phút."}
    user = database.get_user_by_username(payload.username)
    if not user or not auth.verify_password(payload.password, user["password_hash"]):
        _login_attempts.setdefault(ip, []).append(now)
        return {"status": "error", "message": "Sai tên đăng nhập hoặc mật khẩu."}
    if not user.get("is_active"):
        return {"status": "error", "message": "Tài khoản đã bị khóa."}
    token = auth.create_access_token({"sub": str(user["id"]), "role": user["role"]})
    database.log_audit(user["id"], "LOGIN")
    return {
        "status": "success",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
            "full_name": user["full_name"],
            "must_change_password": user.get("must_change_password", 0),
        },
    }


@app.get("/api/auth/me")
def get_me(current_user: CurrentUser):
    return {"status": "success", "user": current_user}


@app.post("/api/auth/logout")
def logout(current_user: CurrentUser, request: Request):
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else ""
    if token:
        auth.revoke_token(token)
    database.log_audit(current_user["id"], "LOGOUT")
    return {"status": "success", "message": "Đã đăng xuất."}


class ChangePasswordPayload(BaseModel):
    old_password: str
    new_password: str

    @staticmethod
    def _validate_pwd(v):
        if len(v) < 6:
            raise ValueError("Mật khẩu phải có ít nhất 6 ký tự.")
        return v

    def __init__(self, **data):
        super().__init__(**data)
        self._validate_pwd(self.new_password)


@app.put("/api/auth/change-password")
def change_password(payload: ChangePasswordPayload, current_user: CurrentUser):
    user = database.get_user_by_id(current_user["id"])
    if not user:
        return {"status": "error", "message": "Người dùng không tồn tại."}
    full_user = database.get_user_by_username(user["username"])
    if not full_user or not auth.verify_password(
        payload.old_password, full_user["password_hash"]
    ):
        return {"status": "error", "message": "Mật khẩu cũ không đúng."}
    database.update_user_password(user["id"], payload.new_password)
    database.clear_must_change_password(user["id"])
    database.log_audit(user["id"], "CHANGE_PASSWORD")
    return {"status": "success", "message": "Đã đổi mật khẩu thành công."}


# --- USER MANAGEMENT API (ADMIN ONLY) ---


@app.get("/api/users")
def list_users(admin: AdminUser):
    return {"data": database.get_all_users()}


class UserCreatePayload(BaseModel):
    username: str
    password: str
    role: str = "OPERATOR"
    full_name: str = ""


@app.post("/api/users")
def create_user(payload: UserCreatePayload, admin: AdminUser):
    if payload.role not in ("ADMIN", "OPERATOR"):
        return {"status": "error", "message": "Role phải là ADMIN hoặc OPERATOR."}
    new_id = database.create_user(
        payload.username, payload.password, payload.role, payload.full_name
    )
    if new_id is None:
        return {"status": "error", "message": "Username đã tồn tại."}
    database.log_audit(admin["id"], "CREATE_USER", f"username={payload.username}")
    return {"status": "success", "id": new_id}


class UserUpdatePayload(BaseModel):
    role: str | None = None
    full_name: str | None = None
    is_active: int | None = None


@app.put("/api/users/{user_id}")
def update_user_api(user_id: int, payload: UserUpdatePayload, admin: AdminUser):
    kwargs = {k: v for k, v in payload.dict().items() if v is not None}
    if not kwargs:
        return {"status": "error", "message": "Không có dữ liệu cập nhật."}
    if payload.is_active is not None:
        old_user = database.get_user_by_id(user_id)
        if old_user and old_user["is_active"] != payload.is_active:
            action = "LOCK_USER" if payload.is_active == 0 else "UNLOCK_USER"
            database.log_audit(admin["id"], action, f"user_id={user_id}")
    database.update_user(user_id, **kwargs)
    database.log_audit(admin["id"], "UPDATE_USER", f"user_id={user_id}")
    return {"status": "success"}


class ResetPasswordPayload(BaseModel):
    password: str

    def __init__(self, **data):
        super().__init__(**data)
        if len(self.password) < 6:
            raise ValueError("Mật khẩu phải có ít nhất 6 ký tự.")


@app.put("/api/users/{user_id}/password")
def reset_password(user_id: int, payload: ResetPasswordPayload, admin: AdminUser):
    database.update_user_password(user_id, payload.password)
    database.log_audit(admin["id"], "RESET_PASSWORD", f"user_id={user_id}")
    return {"status": "success"}


@app.delete("/api/users/{user_id}")
def delete_user_api(user_id: int, admin: AdminUser):
    if user_id == admin["id"]:
        return {"status": "error", "message": "Không thể xoá chính mình."}
    database.delete_user(user_id)
    database.log_audit(admin["id"], "DELETE_USER", f"user_id={user_id}")
    return {"status": "success"}


# --- STATIONS CRUD API ---


class StationPayload(BaseModel):
    name: str
    ip_camera_1: str
    ip_camera_2: str = ""
    safety_code: str
    camera_mode: str
    camera_brand: str = "imou"
    mac_address: str = ""


@app.get("/api/stations")
def get_stations_api(current_user: CurrentUser):
    stations = database.get_stations()
    if current_user.get("role") != "ADMIN":
        for s in stations:
            s.pop("safety_code", None)
    return {"data": stations}


@app.post("/api/stations")
def create_station(payload: StationPayload, admin: AdminUser):
    new_id = database.create_station(payload.dict())
    database.log_audit(admin["id"], "STATION_CREATE", f"station_id={new_id}")
    live_quality = database.get_setting("LIVE_VIEW_STREAM", "sub")
    url_fn = get_rtsp_url if live_quality == "main" else get_rtsp_sub_url
    url = url_fn(
        payload.ip_camera_1,
        payload.safety_code,
        channel=1,
        brand=payload.camera_brand,
    )
    cam2_url = None
    if payload.ip_camera_2:
        cam2_url = url_fn(
            payload.ip_camera_2,
            payload.safety_code,
            channel=2,
            brand=payload.camera_brand,
        )
    cam2_url = None
    if payload.ip_camera_2:
        cam2_url = get_rtsp_sub_url(
            payload.ip_camera_2,
            payload.safety_code,
            channel=2,
            brand=payload.camera_brand,
        )
    sm = CameraStreamManager(url, station_id=new_id, cam2_url=cam2_url)
    stream_managers[new_id] = sm
    sm.start()
    return {"status": "success", "id": new_id}


@app.put("/api/stations/{station_id}")
def update_station(station_id: int, payload: StationPayload, admin: AdminUser):
    database.update_station(station_id, payload.dict())
    database.log_audit(admin["id"], "STATION_UPDATE", f"station_id={station_id}")
    if station_id in stream_managers:
        live_quality = database.get_setting("LIVE_VIEW_STREAM", "sub")
        url_fn = get_rtsp_url if live_quality == "main" else get_rtsp_sub_url
        url = url_fn(
            payload.ip_camera_1,
            payload.safety_code,
            channel=1,
            brand=payload.camera_brand,
        )
        stream_managers[station_id].update_url(url)
        cam2_url = None
        if payload.ip_camera_2:
            cam2_url = url_fn(
                payload.ip_camera_2,
                payload.safety_code,
                channel=2,
                brand=payload.camera_brand,
            )
        stream_managers[station_id].update_cam2_url(cam2_url)
    return {"status": "success"}


@app.delete("/api/stations/{station_id}")
def delete_station(station_id: int, admin: AdminUser):
    database.delete_station(station_id)
    database.log_audit(admin["id"], "STATION_DELETE", f"station_id={station_id}")
    if station_id in stream_managers:
        stream_managers[station_id].stop()
        stream_managers.pop(station_id, None)
    if station_id in active_recorders:
        active_recorders[station_id].stop_recording()
        active_recorders.pop(station_id, None)
        active_waybills.pop(station_id, None)
        active_record_ids.pop(station_id, None)
    _processing_count.pop(station_id, None)
    if station_id in reconnect_status:
        del reconnect_status[station_id]
    return {"status": "success"}


# --- CAMERA DISCOVERY API ---


@app.get("/api/discover-mac")
def discover_camera_by_mac(mac: str, current_user: AdminUser):
    if not mac or not network.validate_mac(mac):
        return {
            "status": "error",
            "message": "MAC Address không hợp lệ.",
        }
    new_ip = network.scan_lan_for_mac(mac)
    if not new_ip:
        return {
            "status": "not_found",
            "message": f"Không tìm thấy thiết bị có MAC {mac} trên mạng LAN.",
        }
    return {
        "status": "found",
        "message": f"Tìm thấy thiết bị tại IP: {new_ip}",
        "ip": new_ip,
    }


@app.get("/api/discover/{station_id}")
def discover_camera(station_id: int, current_user: AdminUser):
    station = database.get_station(station_id)
    if not station:
        return {"status": "error", "message": "Trạm không tồn tại"}

    mac = station.get("mac_address", "")
    if not mac or not network.validate_mac(mac):
        return {
            "status": "error",
            "message": "Trạm chưa cấu hình MAC Address. Vui lòng nhập MAC trong phần Cài đặt.",
        }

    old_ip = station["ip_camera_1"]
    new_ip = network.scan_lan_for_mac(mac)

    if not new_ip:
        return {
            "status": "not_found",
            "message": f"Không tìm thấy thiết bị có MAC {mac} trên mạng LAN.",
        }

    if new_ip == old_ip:
        return {
            "status": "same_ip",
            "message": f"Camera đang ở đúng địa chỉ {old_ip}.",
            "ip": old_ip,
        }

    database.update_station_ip(station_id, "ip_camera_1", new_ip)
    brand = station.get("camera_brand", "imou")
    code = station.get("safety_code", "")
    live_quality = database.get_setting("LIVE_VIEW_STREAM", "sub")
    url_fn = get_rtsp_url if live_quality == "main" else get_rtsp_sub_url
    new_url = url_fn(new_ip, code, channel=1, brand=brand)
    if station_id in stream_managers:
        stream_managers[station_id].update_url(new_url)

    return {
        "status": "found",
        "message": f"Đã tìm thấy camera! IP mới: {new_ip} (cũ: {old_ip})",
        "old_ip": old_ip,
        "new_ip": new_ip,
    }


@app.get("/api/reconnect-status")
def get_reconnect_status(current_user: CurrentUser, station_id: int | None = None):
    if station_id:
        return {"data": reconnect_status.get(station_id, None)}
    return {"data": reconnect_status}


# --- SESSION LOCKING API ---


@app.post("/api/sessions/acquire")
def acquire_session(station_id: int, current_user: CurrentUser):
    if current_user["role"] == "ADMIN":
        return {
            "status": "error",
            "message": "Admin không thể đóng hàng. Vui lòng dùng tài khoản Operator.",
        }

    database.expire_stale_sessions()

    existing = database.get_active_session(station_id)
    if existing:
        if existing["user_id"] != current_user["id"]:
            return {
                "status": "error",
                "message": f"Trạm đang được sử dụng bởi {existing['full_name'] or existing['username']}.",
            }
        return {
            "status": "success",
            "session_id": existing["id"],
            "message": "Session đã tồn tại.",
        }

    session_id = database.create_session(current_user["id"], station_id)
    return {"status": "success", "session_id": session_id}


@app.post("/api/sessions/heartbeat")
def heartbeat_session(session_id: int, current_user: CurrentUser):
    session = database.get_session_by_id(session_id)
    if not session or session["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not your session")
    database.update_session_heartbeat(session_id)
    return {"status": "success"}


@app.post("/api/sessions/release")
def release_session(station_id: int, current_user: CurrentUser):
    existing = database.get_active_session(station_id)
    if existing and existing["user_id"] == current_user["id"]:
        database.end_session(existing["id"])
    return {"status": "success"}


@app.get("/api/sessions/active")
def get_active_sessions_api(admin: AdminUser):
    sessions = database.get_active_sessions()
    return {"data": sessions}


@app.delete("/api/sessions/{session_id}")
def force_end_session(session_id: int, admin: AdminUser):
    session = database.get_session_by_id(session_id)
    if not session or session["status"] != "ACTIVE":
        return {
            "status": "error",
            "message": "Session không tồn tại hoặc đã kết thúc.",
        }
    database.end_session_by_id(session_id)
    database.log_audit(admin["id"], "FORCE_END_SESSION", f"Kicked session {session_id}")
    return {"status": "success"}


@app.get("/api/sessions/station-status")
def get_station_status(current_user: CurrentUser):
    database.expire_stale_sessions()
    stations = database.get_stations()
    result = []
    for st in stations:
        session = database.get_active_session(st["id"])
        result.append(
            {
                "station_id": st["id"],
                "station_name": st["name"],
                "occupied": session is not None,
                "occupied_by": session["username"] if session else None,
                "occupied_by_name": session["full_name"] if session else None,
            }
        )
    return {"data": result}


@app.get("/api/audit-logs")
def get_audit_logs_api(
    admin: AdminUser,
    user_id: int | None = None,
    action: str | None = None,
    limit: int = 200,
    offset: int = 0,
):
    logs = database.get_audit_logs(
        user_id=user_id, action=action, limit=limit, offset=offset
    )
    return {"data": logs}


# --- SCAN API ---


class ScanPayload(BaseModel):
    barcode: str = Field(..., max_length=200)
    station_id: int


@app.post("/api/scan")
def handle_scan(payload: ScanPayload, current_user: CurrentUser):
    if current_user["role"] == "ADMIN":
        return {
            "status": "error",
            "message": "Quản trị viên không thể ghi hình. Chỉ Người vận hành (OPERATOR) mới có quyền đóng hàng.",
        }

    sid = payload.station_id
    lock = _station_locks.setdefault(sid, threading.Lock())
    with lock:
        return _handle_scan_locked(payload, sid, current_user)


def _handle_scan_locked(payload, sid, current_user):
    barcode = payload.barcode.strip().upper()

    session = database.get_active_session(sid)
    if not session or session["user_id"] != current_user["id"]:
        return {
            "status": "error",
            "message": "Bạn chưa mở session cho trạm này. Vui lòng chọn trạm và bấm 'Bắt đầu'.",
        }
    database.update_session_heartbeat(session["id"])

    if not barcode:
        return {"status": "error", "message": "M\u00e3 v\u1ea1ch tr\u1ed1ng"}

    station = database.get_station(sid)
    if not station:
        return {"status": "error", "message": "Tr\u1ea1m kh\u00f4ng t\u1ed3n t\u1ea1i"}

    current_recorder = active_recorders.get(sid)
    current_waybill = active_waybills.get(sid)
    current_record_id = active_record_ids.get(sid)

    if barcode == "EXIT":
        if current_recorder:
            database.update_record_status(current_record_id, "PROCESSING")
            notify_sse(
                "video_status",
                {
                    "station_id": sid,
                    "status": "PROCESSING",
                    "record_id": current_record_id,
                },
            )
            _processing_count[sid] = _processing_count.get(sid, 0) + 1
            active_recorders.pop(sid, None)
            video_worker.submit_stop_and_save(
                current_record_id, current_recorder, current_waybill, sid, save=False
            )
            return {
                "status": "processing",
                "message": "\u0110ang h\u1ee7y ghi h\u00ecnh...",
            }
        return {"status": "idle", "message": "Tr\u1ea1m \u0111ang nh\u00e0n r\u1ed7i."}

    if barcode == "STOP":
        if current_recorder:
            database.update_record_status(current_record_id, "PROCESSING")
            notify_sse(
                "video_status",
                {
                    "station_id": sid,
                    "status": "PROCESSING",
                    "record_id": current_record_id,
                },
            )
            _processing_count[sid] = _processing_count.get(sid, 0) + 1
            active_recorders.pop(sid, None)
            database.log_audit(
                current_user["id"],
                "STOP_RECORD",
                f"waybill={current_waybill}",
                station_id=sid,
            )
            video_worker.submit_stop_and_save(
                current_record_id, current_recorder, current_waybill, sid, save=True
            )
            return {
                "status": "processing",
                "message": "\u0110ang x\u1eed l\u00fd video. Vui l\u00f2ng \u0111\u1ee3i...",
            }
        return {"status": "idle", "message": "Tr\u1ea1m \u0111ang nh\u00e0n r\u1ed7i."}

    if current_recorder:
        return {
            "status": "recording",
            "message": "\u0110ang ghi \u0111\u01a1n. Vui l\u00f2ng qu\u00e9t STOP \u0111\u1ec3 k\u1ebft th\u00fac \u0111\u01a1n h\u00e0ng hi\u1ec7n t\u1ea1i.",
        }

    ok, err_msg = _preflight_checks(sid)
    if not ok:
        return {"status": "error", "message": err_msg}

    active_waybills[sid] = barcode

    ip1 = station["ip_camera_1"]
    ip2 = station["ip_camera_2"]
    code = station["safety_code"]
    c_mode = station["camera_mode"]
    brand = station.get("camera_brand", "imou")

    if not ip1 or not code:
        return {
            "status": "error",
            "message": "Tr\u1ea1m ch\u01b0a c\u1ea5u h\u00ecnh IP Camera v\u00e0 Safety Code.",
        }

    mac = station.get("mac_address", "")
    if mac and network.validate_mac(mac):
        discovered_ip = network.scan_lan_for_mac(mac)
        if discovered_ip and discovered_ip != ip1:
            ip1 = discovered_ip
            database.update_station_ip(sid, "ip_camera_1", ip1)
            brand = station.get("camera_brand", "imou")
            code = station.get("safety_code", "")
            new_url = get_rtsp_sub_url(ip1, code, channel=1, brand=brand)

    url1 = get_rtsp_url(ip1, code, channel=1, brand=brand)
    if c_mode in ["dual_file", "pip"]:
        url2 = get_rtsp_url(ip2 if ip2 else ip1, code, channel=2, brand=brand)
    elif c_mode in ["dual_file_sim", "pip_sim"]:
        url2 = url1
    else:
        url2 = url1

    if c_mode in ["dual_file", "dual_file_sim"]:
        r_mode = "DUAL_FILE"
    elif c_mode in ["pip", "pip_sim"]:
        r_mode = "PIP"
    else:
        r_mode = "SINGLE"

    record_id = database.create_record(sid, barcode, r_mode)
    active_record_ids[sid] = record_id

    new_recorder = CameraRecorder(url1, rtsp_url_2=url2, record_mode=r_mode)
    active_recorders[sid] = new_recorder
    new_recorder.start_recording(barcode)

    database.log_audit(
        current_user["id"],
        "START_RECORD",
        f"waybill={barcode}",
        station_id=sid,
    )

    notify_sse(
        "video_status",
        {
            "station_id": sid,
            "status": "RECORDING",
            "record_id": record_id,
            "waybill": barcode,
        },
    )

    return {
        "status": "recording",
        "record_id": record_id,
        "message": f"Bắt đầu ghi hình đơn {barcode} tại Trạm {sid}...",
    }


@app.get("/api/status")
def get_status(station_id: int, current_user: CurrentUser):
    if station_id in _processing_count:
        return {"status": "processing", "waybill": active_waybills.get(station_id, "")}
    return {
        "status": "recording" if station_id in active_recorders else "idle",
        "waybill": active_waybills.get(station_id, ""),
    }


# --- RECORDS & STORAGE API ---


@app.get("/api/records")
def get_records(current_user: CurrentUser, station_id: int = None, search: str = ""):
    records = database.get_records(search, station_id)
    results = []
    for r in records:
        r_id, waybill_code, video_paths, record_mode, recorded_at, s_name, status = r
        results.append(
            {
                "id": r_id,
                "waybill_code": waybill_code,
                "video_paths": video_paths.split(","),
                "record_mode": record_mode,
                "recorded_at": recorded_at,
                "station_name": s_name,
                "status": status,
            }
        )
    return {"data": results}


@app.delete("/api/records/{record_id}")
def delete_record(record_id: int, admin: AdminUser):
    try:
        database.delete_record(record_id)
        return {"status": "success"}
    except Exception as e:
        print(f"[DB] delete record {record_id} failed: {e}")
        return {"status": "error", "message": f"Không thể xoá bản ghi: {e}"}


@app.get("/api/storage/info")
def get_storage_info(current_user: CurrentUser):
    total_size = 0
    dir_path = "recordings"
    file_count = 0
    if os.path.exists(dir_path):
        for f in os.listdir(dir_path):
            fp = os.path.join(dir_path, f)
            if os.path.isfile(fp) and f.endswith(".mp4"):
                total_size += os.path.getsize(fp)
                file_count += 1
    size_mb = total_size / (1024 * 1024)
    size_str = f"{size_mb / 1024:.2f} GB" if size_mb > 1024 else f"{size_mb:.2f} MB"
    return {
        "data": {
            "size_str": size_str,
            "size_bytes": total_size,
            "file_count": file_count,
        }
    }


# --- ANALYTICS DASHBOARD API ---


@app.get("/api/analytics/today")
def get_analytics_today(station_id: int, current_user: CurrentUser):
    with sqlite3.connect(database.DB_FILE) as conn:
        cursor = conn.cursor()

        # Đếm tổng đơn toàn hệ thống kho hôm nay (SQLite local time)
        cursor.execute(
            "SELECT COUNT(*) FROM packing_video WHERE date(recorded_at) = date('now', 'localtime')"
        )
        total_today = cursor.fetchone()[0]

        # Đếm số đơn riêng của trạm đang chọn
        cursor.execute(
            "SELECT COUNT(*) FROM packing_video WHERE date(recorded_at) = date('now', 'localtime') AND station_id = ?",
            (station_id,),
        )
        station_today = cursor.fetchone()[0]

        return {"data": {"total_today": total_today, "station_today": station_today}}


# --- ANALYTICS PRO API ---


@app.get("/api/analytics/hourly")
def get_hourly_stats_api(
    current_user: CurrentUser, date: str | None = None, station_id: int | None = None
):
    data = database.get_hourly_stats(date=date, station_id=station_id)
    return {"data": data}


@app.get("/api/analytics/trend")
def get_daily_trend_api(current_user: CurrentUser, days: int = 7):
    data = database.get_daily_trend(days=min(days, 30))
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


@app.get("/api/live")
def live_preview(station_id: int, current_user: CurrentUser):
    return {
        "status": "ok",
        "webrtc_url": f"http://localhost:8889/station_{station_id}",
    }


@app.get("/api/live-cam2")
def live_preview_cam2(station_id: int, current_user: CurrentUser):
    return {
        "status": "ok",
        "webrtc_url": f"http://localhost:8889/station_{station_id}_cam2",
        "has_cam2": station_id in stream_managers
        and stream_managers[station_id].cam2_url is not None,
    }


@app.get("/api/mtx-status")
def mtx_status(current_user: CurrentUser):
    try:
        req = urllib.request.Request(f"{MTX_API}/v3/paths/list", method="GET")
        resp = urllib.request.urlopen(req, timeout=3)
        return json.loads(resp.read())
    except Exception:
        raise HTTPException(status_code=503, detail="MediaMTX not running")


@app.get("/api/events")
async def sse_events(request: Request, stations: str = ""):
    token = request.query_params.get("token") or request.headers.get(
        "Authorization", ""
    ).replace("Bearer ", "")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        auth.decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    import queue

    q = queue.Queue()
    with _sse_lock:
        _sse_clients.append(q)

    async def event_stream():
        try:
            while True:
                try:
                    msg = q.get_nowait()
                    yield msg
                except queue.Empty:
                    await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass
        finally:
            with _sse_lock:
                try:
                    _sse_clients.remove(q)
                except ValueError:
                    pass

    return StreamingResponse(event_stream(), media_type="text/event-stream")


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

    uptime_seconds = int(time.time() - _SERVER_START_TIME)
    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_str = (
        f"{days}d {hours}h {minutes}m {seconds}s"
        if days > 0
        else f"{hours}h {minutes}m {seconds}s"
    )

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
    ffmpeg_procs = []
    for proc in psutil.process_iter(
        ["pid", "name", "cmdline", "cpu_percent", "memory_percent", "create_time"]
    ):
        try:
            name = proc.info["name"] or ""
            if "ffmpeg" in name.lower():
                cmdline = proc.info.get("cmdline") or []
                cmdline_str = " ".join(cmdline)[:120] if cmdline else ""
                import re as _re
                cmdline_str = _re.sub(r'://[^@]+@', '://***@', cmdline_str)
                ffmpeg_procs.append(
                    {
                        "pid": proc.info["pid"],
                        "name": name,
                        "cmdline_short": cmdline_str,
                        "cpu_percent": proc.info.get("cpu_percent") or 0,
                        "memory_percent": round(
                            proc.info.get("memory_percent") or 0, 1
                        ),
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
    import socket

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
                import subprocess

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


# --- AUTO-UPDATE API ---

_update_lock = threading.Lock()
_is_updating = False
_update_check_cache = {"result": None, "timestamp": 0}
_UPDATE_CHECK_TTL = 3600



def _get_git_branch():
    try:
        import subprocess as _sp
        r = _sp.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        if r.returncode == 0:
            branch = r.stdout.strip()
            if branch and branch != "HEAD":
                return branch
        r2 = _sp.run(
            ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        if r2.returncode == 0:
            return r2.stdout.strip().replace("refs/remotes/origin/", "")
    except Exception:
        pass
    return "master"


@app.get("/api/system/update-check")
def check_update(admin: AdminUser):
    now = time.time()
    if _update_check_cache["result"] and (now - _update_check_cache["timestamp"]) < _UPDATE_CHECK_TTL:
        return _update_check_cache["result"]

    import subprocess as _sp

    current = _read_version()
    mode = "dev" if os.path.exists(".git") else "production"
    latest = current
    update_available = False
    changelog = ""

    try:
        if mode == "dev":
            branch = _get_git_branch()
            _sp.run(
                ["git", "fetch", "origin", branch],
                capture_output=True, timeout=30,
            )
            r = _sp.run(
                ["git", "describe", "--tags", "--abbrev=0", f"origin/{branch}"],
                capture_output=True, text=True, timeout=10,
            )
            if r.returncode == 0 and r.stdout.strip():
                latest = r.stdout.strip()
            else:
                r2 = _sp.run(
                    ["git", "rev-parse", "--short", f"origin/{branch}"],
                    capture_output=True, text=True, timeout=10,
                )
                if r2.returncode == 0:
                    latest = r2.stdout.strip()
            r3 = _sp.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True, text=True, timeout=10,
            )
            local_head = r3.stdout.strip() if r3.returncode == 0 else ""
            r4 = _sp.run(
                ["git", "rev-parse", f"origin/{branch}"],
                capture_output=True, text=True, timeout=10,
            )
            remote_head = r4.stdout.strip() if r4.returncode == 0 else ""
            update_available = local_head != remote_head and remote_head != ""
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
            update_available = latest != current and latest != "unknown"
    except Exception as e:
        print(f"[UPDATE] check failed: {e}")

    result = {
        "current_version": current,
        "latest_version": latest,
        "update_available": update_available,
        "mode": mode,
        "changelog": changelog,
    }
    _update_check_cache["result"] = result
    _update_check_cache["timestamp"] = now
    return result


def _notify_update_progress(stage, message, progress=0):
    notify_sse("update_progress", {
        "stage": stage,
        "message": message,
        "progress": progress,
    })


def _do_graceful_restart():
    time.sleep(1.5)
    try:
        for rec in active_recorders.values():
            try:
                rec.stop_recording()
            except Exception as e:
                print(f"[RESTART] stop recorder failed: {e}")
        video_worker.shutdown()
        _notify_update_progress("restarting", "Đang khởi động lại...", 100)
        time.sleep(1.5)
        if _platform.system() == "Windows":
            bat_content = "@echo off\r\n"
            bat_content += "timeout /t 3 /nobreak >nul\r\n"
            bat_content += 'cd /d "' + os.getcwd() + '"\r\n'
            bat_content += 'call start_windows.bat\r\n'
            bat_content += 'del "%~f0"\r\n'
            bat_path = os.path.join(os.getcwd(), "_update_restart.bat")
            with open(bat_path, "w") as f:
                f.write(bat_content)
            import subprocess as _sp
            _sp.Popen(["cmd", "/c", bat_path], creationflags=0x00000008)
        else:
            sh_content = "#!/bin/bash\n"
            sh_content += "sleep 3\n"
            sh_content += 'cd "' + os.getcwd() + '"\n'
            sh_content += "bash start.sh\n"
            sh_content += 'rm -- "$0"\n'
            sh_path = os.path.join(os.getcwd(), "_update_restart.sh")
            with open(sh_path, "w") as f:
                f.write(sh_content)
            import subprocess as _sp
            _sp.run(["chmod", "+x", sh_path])
            _sp.Popen(["bash", sh_path], start_new_session=True)
    except Exception as e:
        print(f"[RESTART] CRITICAL: graceful restart failed: {e}")
    finally:
        os._exit(0)


def _update_dev():
    import subprocess as _sp

    try:
        _notify_update_progress("checking", "Đang kiểm tra bản cập nhật...", 10)
        branch = _get_git_branch()

        stash_result = _sp.run(
            ["git", "stash"], capture_output=True, text=True, timeout=30,
        )
        had_stash = "No local changes" not in (stash_result.stdout or "")

        _notify_update_progress("downloading", "Đang tải bản cập nhật (git pull)...", 30)
        r = _sp.run(
            ["git", "pull", "origin", branch],
            capture_output=True, text=True, timeout=120,
        )
        if r.returncode != 0:
            if had_stash:
                _sp.run(["git", "stash", "pop"], capture_output=True, timeout=30)
            return {
                "status": "error",
                "message": f"Git pull thất bại: {r.stderr[:200]}",
            }

        if had_stash:
            _sp.run(["git", "stash", "pop"], capture_output=True, timeout=30)

        _notify_update_progress("installing", "Đang cài đặt npm dependencies...", 50)
        if _platform.system() == "Windows":
            _sp.run(
                ["cmd", "/c", "npm", "install"],
                cwd="web-ui", capture_output=True, timeout=120,
            )
        else:
            _sp.run(
                ["npm", "install"],
                cwd="web-ui", capture_output=True, timeout=120,
            )

        _notify_update_progress("building", "Đang build frontend...", 70)
        if _platform.system() == "Windows":
            _sp.run(
                ["cmd", "/c", "npm", "run", "build"],
                cwd="web-ui", capture_output=True, timeout=120,
            )
        else:
            _sp.run(
                ["npm", "run", "build"],
                cwd="web-ui", capture_output=True, timeout=120,
            )

        _notify_update_progress("restarting", "Đang chuẩn bị khởi động lại...", 90)
        return {"status": "restarting", "message": "Cập nhật thành công. Đang khởi động lại..."}
    except Exception as e:
        return {"status": "error", "message": f"Lỗi cập nhật: {e}"}


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
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmp_dir)
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
            "recordings", "venv", "bin", "credentials.json",
            ".env", "install_log.txt", "__pycache__", ".git",
            "_update_restart.bat", "_update_restart.sh",
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
            capture_output=True, timeout=120,
        )

        _notify_update_progress("building", "Đang build frontend...", 85)
        has_npm = False
        if _platform.system() == "Windows":
            has_npm = _sp.run(
                ["cmd", "/c", "where", "npm"],
                capture_output=True, timeout=5,
            ).returncode == 0
        else:
            has_npm = shutil.which("npm") is not None
        if has_npm:
            if _platform.system() == "Windows":
                _sp.run(
                    ["cmd", "/c", "npm", "install"],
                    cwd="web-ui", capture_output=True, timeout=120,
                )
                _sp.run(
                    ["cmd", "/c", "npm", "run", "build"],
                    cwd="web-ui", capture_output=True, timeout=120,
                )
            else:
                _sp.run(
                    ["npm", "install"],
                    cwd="web-ui", capture_output=True, timeout=120,
                )
                _sp.run(
                    ["npm", "run", "build"],
                    cwd="web-ui", capture_output=True, timeout=120,
                )
        else:
            _notify_update_progress("building", "Bỏ qua npm build (không có Node.js). Dùng dist/ có sẵn.", 85)

        shutil.rmtree(tmp_dir, ignore_errors=True)
        db_bak = os.path.join("recordings", "packing_records.db.bak")
        if os.path.exists(db_bak):
            try:
                os.remove(db_bak)
            except OSError:
                pass

        _notify_update_progress("restarting", "Đang chuẩn bị khởi động lại...", 95)
        return {"status": "restarting", "message": "Cập nhật thành công. Đang khởi động lại..."}
    except Exception as e:
        db_path = os.path.join("recordings", "packing_records.db")
        if os.path.exists(db_path + ".bak"):
            shutil.copy2(db_path + ".bak", db_path)
        return {"status": "error", "message": f"Lỗi cập nhật: {e}"}


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
        return {"status": "error", "message": f"Lỗi cập nhật: {e}"}


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
