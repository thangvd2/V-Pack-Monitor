# =============================================================================
# V-Pack Monitor - CamDongHang v1.3.0
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
import urllib.request
import urllib.error
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import database
from recorder import CameraRecorder
import cloud_sync
import network

# --- Quản lý Trạng thái Ghi hình Đa Trạm ---
active_recorders = {}
active_waybills = {}
stream_managers = {}

reconnect_status = {}

MTX_API = "http://127.0.0.1:9997"


def _mtx_add_path(station_id, rtsp_url):
    name = f"station_{station_id}"
    conf = {
        "name": name,
        "source": rtsp_url,
        "rtspTransport": "tcp",
    }
    try:
        req = urllib.request.Request(
            f"{MTX_API}/v3/config/paths/remove/{name}",
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
    except Exception:
        pass


def _mtx_remove_path(station_id):
    name = f"station_{station_id}"
    try:
        req = urllib.request.Request(
            f"{MTX_API}/v3/config/paths/remove/{name}",
            method="POST",
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass


class CameraStreamManager:
    def __init__(self, url, station_id=None):
        self.url = url
        self.station_id = station_id
        self.is_running = False
        self.thread = None
        self._fail_count = 0
        self._lock = threading.Lock()

    def start(self):
        if not self.is_running and self.url:
            self.is_running = True
            self._fail_count = 0
            self._mtx_register()
            self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.thread.start()

    def stop(self):
        self.is_running = False
        if self.station_id:
            _mtx_remove_path(self.station_id)
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
            new_url = get_rtsp_sub_url(new_ip, code, channel=1, brand=brand)
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
            except Exception:
                pass

    def update_url(self, new_url):
        with self._lock:
            self.url = new_url
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
    stations = database.get_stations()
    for st in stations:
        sub_url = get_rtsp_sub_url(
            st["ip_camera_1"],
            st["safety_code"],
            channel=1,
            brand=st.get("camera_brand", "imou"),
        )
        manager = CameraStreamManager(sub_url, station_id=st["id"])
        stream_managers[st["id"]] = manager
        manager.start()

    # Kích hoạt Telegram Bot 2 chiều (Lắng nghe)
    telegram_bot.start_polling()

    yield
    for manager in stream_managers.values():
        manager.stop()
    for recorder in active_recorders.values():
        recorder.stop_recording()
    telegram_bot.stop_polling()


app = FastAPI(title="CamDongHang API Multi-Station", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if not os.path.exists("recordings"):
    os.makedirs("recordings")
app.mount("/recordings", StaticFiles(directory="recordings"), name="recordings")

# Tự động dọn dẹp các video cũ
try:
    keep_days = int(database.get_setting("RECORD_KEEP_DAYS", 7))
    database.cleanup_old_records(keep_days)
except BaseException:
    pass


# --- SYSTEM HEALTH API ---
@app.get("/api/system/disk")
def get_disk_health():
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
    CLOUD_PROVIDER: str = "NONE"
    GDRIVE_FOLDER_ID: str = ""
    S3_ENDPOINT: str = ""
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_BUCKET_NAME: str = ""
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""


@app.get("/api/settings")
def get_settings():
    return {"data": database.get_all_settings()}


@app.post("/api/settings")
def update_settings(payload: SettingsUpdate):
    database.set_settings(payload.dict())

    # Restart Telegram Bot polling if tokens change
    if payload.TELEGRAM_BOT_TOKEN and payload.TELEGRAM_CHAT_ID:
        # Import dynamic if not already
        import telegram_bot

        telegram_bot.start_polling()

    return {"status": "success", "message": "Đã lưu cài đặt hệ thống."}


# --- CLOUD BACKUP API ---


@app.post("/api/credentials")
async def upload_credentials(file: UploadFile = File(...)):
    contents = await file.read()
    with open("credentials.json", "wb") as f:
        f.write(contents)
    return {"status": "success", "message": "Đã cập nhật credentials.json"}


@app.post("/api/cloud-sync")
def trigger_cloud_sync():
    try:
        msg = cloud_sync.process_cloud_sync()
        return {"status": "success", "message": msg}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# --- SECURITY PIN API ---


class PinPayload(BaseModel):
    pin: str


@app.post("/api/verify-pin")
def verify_pin(payload: PinPayload):
    # Lấy PIN từ database, nếu không có lấy mặc định 08012011
    correct_pin = database.get_setting("ADMIN_PIN", "08012011")
    if payload.pin == correct_pin:
        return {"status": "success"}
    return {"status": "error", "message": "Sai mã PIN quản trị viên."}


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
def get_stations_api():
    return {"data": database.get_stations()}


@app.post("/api/stations")
def create_station(payload: StationPayload):
    new_id = database.add_station(payload.dict())
    url = get_rtsp_sub_url(
        payload.ip_camera_1, payload.safety_code, channel=1, brand=payload.camera_brand
    )
    sm = CameraStreamManager(url, station_id=new_id)
    stream_managers[new_id] = sm
    sm.start()
    return {"status": "success", "id": new_id}


@app.put("/api/stations/{station_id}")
def update_station(station_id: int, payload: StationPayload):
    database.update_station(station_id, payload.dict())
    if station_id in stream_managers:
        url = get_rtsp_sub_url(
            payload.ip_camera_1,
            payload.safety_code,
            channel=1,
            brand=payload.camera_brand,
        )
        stream_managers[station_id].update_url(url)
    return {"status": "success"}


@app.delete("/api/stations/{station_id}")
def delete_station(station_id: int):
    database.delete_station(station_id)
    if station_id in stream_managers:
        stream_managers[station_id].stop()
        del stream_managers[station_id]
    if station_id in active_recorders:
        active_recorders[station_id].stop_recording()
        del active_recorders[station_id]
        del active_waybills[station_id]
    if station_id in reconnect_status:
        del reconnect_status[station_id]
    return {"status": "success"}


# --- CAMERA DISCOVERY API ---


@app.get("/api/discover-mac")
def discover_camera_by_mac(mac: str):
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
def discover_camera(station_id: int):
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
    new_url = get_rtsp_sub_url(new_ip, code, channel=1, brand=brand)
    if station_id in stream_managers:
        stream_managers[station_id].update_url(new_url)

    return {
        "status": "found",
        "message": f"Đã tìm thấy camera! IP mới: {new_ip} (cũ: {old_ip})",
        "old_ip": old_ip,
        "new_ip": new_ip,
    }


@app.get("/api/reconnect-status")
def get_reconnect_status(station_id: int | None = None):
    if station_id:
        return {"data": reconnect_status.get(station_id, None)}
    return {"data": reconnect_status}


# --- SCAN API ---


class ScanPayload(BaseModel):
    barcode: str
    station_id: int


_stopping_recorders = {}
_stopping_lock = threading.Lock()


def _async_stop_and_save(sid, recorder, waybill, save=True):
    with _stopping_lock:
        if sid in _stopping_recorders:
            return
        _stopping_recorders[sid] = waybill
        active_recorders.pop(sid, None)

    try:
        saved_files = recorder.stop_recording()
        if save and saved_files:
            database.save_record(sid, waybill, saved_files, recorder.record_mode)
    except Exception as e:
        print(f"Loi khi luu video station {sid}: {e}")
    finally:
        active_waybills.pop(sid, None)
        _stopping_recorders.pop(sid, None)


@app.post("/api/scan")
def handle_scan(payload: ScanPayload):
    sid = payload.station_id
    barcode = payload.barcode.strip().upper()

    if not barcode:
        return {"status": "error", "message": "Mã vạch trống"}

    if sid in _stopping_recorders:
        return {"status": "busy", "message": "Đang lưu video đơn hàng trước. Vui lòng quét lại sau vài giây."}

    station = database.get_station(sid)
    if not station:
        return {"status": "error", "message": "Trạm không tồn tại"}

    current_recorder = active_recorders.get(sid)
    current_waybill = active_waybills.get(sid)

    if barcode == "EXIT":
        if current_recorder:
            t = threading.Thread(
                target=_async_stop_and_save,
                args=(sid, current_recorder, current_waybill, False),
                daemon=True,
            )
            t.start()
            return {"status": "busy", "message": "Đang hủy ghi hình..."}
        return {"status": "idle", "message": "Trạm đang nhàn rỗi."}

    if barcode == "STOP":
        if current_recorder:
            t = threading.Thread(
                target=_async_stop_and_save,
                args=(sid, current_recorder, current_waybill, True),
                daemon=True,
            )
            t.start()
            return {"status": "busy", "message": "Đang đóng gói và lưu video. Vui lòng đợi..."}
        return {"status": "idle", "message": "Trạm đang nhàn rỗi."}

    if current_recorder:
        return {"status": "recording", "message": "Đang ghi đơn. Vui lòng quét STOP để kết thúc đơn hàng hiện tại."}

    active_waybills[sid] = barcode

    station = database.get_station(sid)
    if not station:
        return {"status": "error", "message": "Trạm không tồn tại"}
    ip1 = station["ip_camera_1"]
    ip2 = station["ip_camera_2"]
    code = station["safety_code"]
    c_mode = station["camera_mode"]
    brand = station.get("camera_brand", "imou")

    if not ip1 or not code:
        return {
            "status": "error",
            "message": "Trạm chưa cấu hình IP Camera và Safety Code.",
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
            if sid in stream_managers:
                stream_managers[sid].update_url(new_url)

    url1 = get_rtsp_url(ip1, code, channel=1, brand=brand)
    if c_mode in ["dual_file", "pip"]:
        url2 = get_rtsp_url(ip2 if ip2 else ip1, code, channel=2, brand=brand)
    elif c_mode in ["dual_file_sim", "pip_sim"]:
        url2 = get_rtsp_url(ip1, code, channel=1, brand=brand)
    else:
        url2 = url1

    if c_mode in ["dual_file", "dual_file_sim"]:
        r_mode = "DUAL_FILE"
    elif c_mode in ["pip", "pip_sim"]:
        r_mode = "PIP"
    else:
        r_mode = "SINGLE"

    new_recorder = CameraRecorder(url1, rtsp_url_2=url2, record_mode=r_mode)
    active_recorders[sid] = new_recorder
    new_recorder.start_recording(barcode)

    return {
        "status": "recording",
        "message": f"Bắt đầu ghi hình đơn {barcode} tại Trạm {sid}...",
    }


@app.get("/api/status")
def get_status(station_id: int):
    if station_id in _stopping_recorders:
        return {
            "status": "saving",
            "waybill": _stopping_recorders.get(station_id, ""),
        }
    return {
        "status": "recording" if station_id in active_recorders else "idle",
        "waybill": active_waybills.get(station_id, ""),
    }


# --- RECORDS & STORAGE API ---


@app.get("/api/records")
def get_records(station_id: int = None, search: str = ""):
    records = database.get_records(search, station_id)
    results = []
    for r in records:
        r_id, waybill_code, video_paths, record_mode, recorded_at, s_name = r
        results.append(
            {
                "id": r_id,
                "waybill_code": waybill_code,
                "video_paths": video_paths.split(","),
                "record_mode": record_mode,
                "recorded_at": recorded_at,
                "station_name": s_name,
            }
        )
    return {"data": results}


@app.delete("/api/records/{record_id}")
def delete_record(record_id: int):
    try:
        database.delete_record(record_id)
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/api/storage/info")
def get_storage_info():
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
def get_analytics_today(station_id: int):
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


@app.get("/api/live")
def live_preview(station_id: int):
    return {
        "status": "ok",
        "webrtc_url": f"http://localhost:8889/station_{station_id}",
    }


@app.get("/api/mtx-status")
def mtx_status():
    try:
        req = urllib.request.Request(f"{MTX_API}/v3/paths/list", method="GET")
        resp = urllib.request.urlopen(req, timeout=3)
        return json.loads(resp.read())
    except Exception:
        return {"status": "error", "message": "MediaMTX not running"}


# --- SERVE FRONTEND (PRODUCTION BUILD) ---
dist_dir = os.path.join(os.getcwd(), "web-ui", "dist")
if getattr(sys, "frozen", False):
    dist_dir = os.path.join(sys._MEIPASS, "web-ui", "dist")

if os.path.exists(dist_dir):
    app.mount("/", StaticFiles(directory=dist_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
