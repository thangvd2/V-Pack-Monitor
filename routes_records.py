# =============================================================================
# V-Pack Monitor - CamDongHang v3.2.0
import logging

logger = logging.getLogger(__name__)

# Copyright (c) 2024-2026 VDT - Vu Duc Thang (thangvd2)
# All rights reserved. Unauthorized copying or distribution is prohibited.
# =============================================================================

import asyncio
import json
import os
import queue
import threading
import time
import urllib.request

import jwt as _jwt
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

import api
import auth
import database
import network
import video_worker
from auth import AdminUser, CurrentUser
from recorder import CameraRecorder


class ScanPayload(BaseModel):
    barcode: str = Field(..., max_length=200)
    station_id: int


def _handle_scan_exit(sid, current_recorder, current_waybill, current_record_id):
    if current_recorder:
        api._cancel_recording_timer(sid)
        with api._recording_timers_lock:
            api._recording_start_times.pop(sid, None)
        database.update_record_status(current_record_id, "PROCESSING")
        api.notify_sse(
            "video_status",
            {
                "station_id": sid,
                "status": "PROCESSING",
                "record_id": current_record_id,
            },
        )
        with api._processing_lock:
            api._processing_count[sid] = api._processing_count.get(sid, 0) + 1
        with api._recorders_lock:
            api.active_recorders.pop(sid, None)
            api.active_waybills.pop(sid, None)
            api.active_record_ids.pop(sid, None)
        video_worker.submit_stop_and_save(
            current_record_id,
            current_recorder,
            current_waybill,
            sid,
            save=False,
        )
        return {
            "status": "processing",
            "message": "Đang hủy ghi hình...",
        }
    return {"status": "idle", "message": "Trạm đang nhàn rỗi."}


def _handle_scan_stop(sid, current_recorder, current_waybill, current_record_id, current_user):
    if current_recorder:
        api._cancel_recording_timer(sid)
        with api._recording_timers_lock:
            api._recording_start_times.pop(sid, None)
        database.update_record_status(current_record_id, "PROCESSING")
        api.notify_sse(
            "video_status",
            {
                "station_id": sid,
                "status": "PROCESSING",
                "record_id": current_record_id,
            },
        )
        with api._processing_lock:
            api._processing_count[sid] = api._processing_count.get(sid, 0) + 1
        with api._recorders_lock:
            api.active_recorders.pop(sid, None)
            api.active_waybills.pop(sid, None)
            api.active_record_ids.pop(sid, None)
        database.log_audit(
            current_user["id"],
            "STOP_RECORD",
            f"waybill={current_waybill}",
            station_id=sid,
        )
        submitted = video_worker.submit_stop_and_save(
            current_record_id, current_recorder, current_waybill, sid, save=True
        )
        if not submitted:
            database.update_record_status(current_record_id, "FAILED")
            with api._processing_lock:
                api._processing_count.pop(sid, None)
            api.notify_sse(
                "video_status",
                {
                    "station_id": sid,
                    "status": "FAILED",
                    "record_id": current_record_id,
                },
            )
            return {
                "status": "error",
                "message": "Hệ thống đang quá tải xử lý video. Vui lòng thử lại.",
            }
        return {
            "status": "processing",
            "message": "Đang xử lý video. Vui lòng đợi...",
        }
    return {"status": "idle", "message": "Trạm đang nhàn rỗi."}


def _handle_scan_start(sid, barcode, station, current_user):
    ok, err_msg = api._preflight_checks(sid)
    if not ok:
        return {"status": "error", "message": err_msg}

    with api._recorders_lock:
        api.active_waybills[sid] = barcode

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
            with api._streams_lock:
                sm = api.stream_managers.get(sid)
            if sm:
                live_quality = database.get_setting("LIVE_VIEW_STREAM") or "sub"
                url_fn = api.get_rtsp_url if live_quality == "main" else api.get_rtsp_sub_url
                live_url = url_fn(ip1, code, channel=1, brand=brand)
                sm.update_url(live_url)

    url1 = api.get_rtsp_url(ip1, code, channel=1, brand=brand)
    if c_mode in ["dual_file", "pip"]:
        url2 = api.get_rtsp_url(ip2 if ip2 else ip1, code, channel=2, brand=brand)
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

    new_recorder = CameraRecorder(url1, rtsp_url_2=url2, record_mode=r_mode)
    with api._recorders_lock:
        api.active_record_ids[sid] = record_id
        api.active_recorders[sid] = new_recorder
    new_recorder.start_recording(barcode)

    api._cancel_recording_timer(sid)
    with api._recording_timers_lock:
        api._recording_start_times[sid] = time.time()
        warning_timer = threading.Timer(
            api._RECORDING_WARNING_SECONDS,
            api._emit_recording_warning,
            args=[sid],
        )
        warning_timer.daemon = True
        warning_timer.start()
        api._recording_warning_timers[sid] = warning_timer
        stop_timer = threading.Timer(
            api._MAX_RECORDING_SECONDS,
            api._auto_stop_recording,
            args=[sid, record_id],
        )
        stop_timer.daemon = True
        stop_timer.start()
        api._recording_timers[sid] = stop_timer

    database.log_audit(
        current_user["id"],
        "START_RECORD",
        f"waybill={barcode}",
        station_id=sid,
    )

    api.notify_sse(
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


def register_routes(app):
    # --- VIDEO DOWNLOAD API ---

    @app.get("/api/records/{record_id}/download/{file_index}")
    def download_record_file(request: Request, record_id: int, file_index: int):
        token = request.query_params.get("token") or request.headers.get("Authorization", "").replace("Bearer ", "")
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
        # Station access authorization: OPERATOR must have active session on record's station
        if user["role"] != "ADMIN":
            session = database.get_active_session(record["station_id"])
            if not session or session["user_id"] != user["id"]:
                raise HTTPException(status_code=403, detail="No access to this station's records")
        paths_str = record.get("video_paths") or ""
        paths = [p.strip() for p in paths_str.split(",") if p.strip()]
        if file_index < 0 or file_index >= len(paths):
            raise HTTPException(status_code=404, detail="File not found")
        filepath = paths[file_index]
        # Prevent path traversal — only serve files from recordings directory
        filepath_abs = os.path.abspath(filepath)
        recordings_dir = os.path.abspath("recordings")
        if not filepath_abs.startswith(recordings_dir + os.sep) and filepath_abs != recordings_dir:
            raise HTTPException(status_code=403, detail="Access denied")
        if not os.path.exists(filepath_abs):
            raise HTTPException(status_code=404, detail="File deleted")
        return _FR(
            filepath_abs,
            media_type="video/mp4",
            filename=os.path.basename(filepath_abs),
        )

    # --- SCAN API ---

    @app.post("/api/scan")
    def handle_scan(payload: ScanPayload, current_user: CurrentUser):
        if current_user["role"] == "ADMIN":
            return {
                "status": "error",
                "message": "Quản trị viên không thể ghi hình. Chỉ Người vận hành (OPERATOR) mới có quyền đóng hàng.",
            }

        sid = payload.station_id
        with api._station_locks_lock:
            lock = api._station_locks.setdefault(sid, threading.Lock())
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
            return {"status": "error", "message": "Mã vạch trống"}

        station = database.get_station(sid)
        if not station:
            return {"status": "error", "message": "Trạm không tồn tại"}

        with api._recorders_lock:
            current_recorder = api.active_recorders.get(sid)
            current_waybill = api.active_waybills.get(sid)
            current_record_id = api.active_record_ids.get(sid)

        if barcode == "EXIT":
            return _handle_scan_exit(sid, current_recorder, current_waybill, current_record_id)

        if barcode == "STOP":
            return _handle_scan_stop(sid, current_recorder, current_waybill, current_record_id, current_user)

        if current_recorder:
            return {
                "status": "recording",
                "message": "Đang ghi đơn. Vui lòng quét STOP để kết thúc đơn hàng hiện tại.",
            }

        return _handle_scan_start(sid, barcode, station, current_user)

    @app.get("/api/status")
    def get_status(station_id: int, current_user: CurrentUser):
        with api._processing_lock:
            if station_id in api._processing_count:
                with api._recorders_lock:
                    waybill = api.active_waybills.get(station_id, "")
                return {"status": "processing", "waybill": waybill}
        with api._recorders_lock:
            is_recording = station_id in api.active_recorders
            waybill = api.active_waybills.get(station_id, "")
        return {
            "status": "recording" if is_recording else "idle",
            "waybill": waybill,
        }

    # --- RECORDS & STORAGE API ---

    @app.get("/api/records")
    def get_records(
        current_user: CurrentUser,
        station_id: int = None,
        search: str = "",
        status: str = None,
        date_from: str = None,
        date_to: str = None,
        page: int = 1,
        limit: int = 20,
        sort_by: str = "recorded_at",
        sort_order: str = "desc",
    ):
        result = database.get_records_v2(
            search=search,
            station_id=station_id,
            status=status,
            date_from=date_from,
            date_to=date_to,
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        return result

    @app.delete("/api/records/{record_id}")
    def delete_record(record_id: int, admin: AdminUser):
        try:
            database.delete_record(record_id)
            return {"status": "success"}
        except Exception as e:
            logger.error(f"[DB] delete record {record_id} failed: {e}")
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": "Không thể xoá bản ghi."},
            )

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

    @app.get("/api/live")
    def live_preview(station_id: int, current_user: CurrentUser):
        mtx_host = os.environ.get("MTX_HOST", "127.0.0.1")
        return {
            "status": "ok",
            "webrtc_url": f"http://{mtx_host}:8889/station_{station_id}",
        }

    @app.get("/api/live-cam2")
    def live_preview_cam2(station_id: int, current_user: CurrentUser):
        mtx_host = os.environ.get("MTX_HOST", "127.0.0.1")
        with api._streams_lock:
            has_cam2 = station_id in api.stream_managers and api.stream_managers[station_id].cam2_url is not None
        return {
            "status": "ok",
            "webrtc_url": f"http://{mtx_host}:8889/station_{station_id}_cam2",
            "has_cam2": has_cam2,
        }

    @app.get("/api/mtx-status")
    def mtx_status(current_user: CurrentUser):
        try:
            req = urllib.request.Request(f"{api.MTX_API}/v3/paths/list", method="GET")
            resp = urllib.request.urlopen(req, timeout=3)
            return json.loads(resp.read())
        except Exception:
            raise HTTPException(status_code=503, detail="MediaMTX not running")

    @app.get("/api/events")
    async def sse_events(request: Request, stations: str = ""):
        token = request.query_params.get("token") or request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")
        try:
            payload = auth.decode_token(token)
            jti = payload.get("jti")
            if jti and auth.is_token_revoked(jti):
                raise HTTPException(status_code=401, detail="Token revoked")
            user = database.get_user_by_id(int(payload.get("sub", 0)))
            if not user or not user.get("is_active"):
                raise HTTPException(status_code=401, detail="User inactive")
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid token")

        q = queue.Queue(maxsize=100)
        with api._sse_lock:
            if len(api._sse_clients) >= api.MAX_SSE_CLIENTS:
                raise HTTPException(status_code=503, detail="Too many SSE connections")
            api._sse_clients.append(q)

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
                with api._sse_lock:
                    try:
                        api._sse_clients.remove(q)
                    except ValueError:
                        pass

        return StreamingResponse(event_stream(), media_type="text/event-stream")
