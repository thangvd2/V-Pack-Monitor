# =============================================================================
# V-Pack Monitor - CamDongHang
# Copyright (c) 2024-2026 VDT - Vu Duc Thang (thangvd2)
# All rights reserved. Unauthorized copying or distribution is prohibited.
# =============================================================================


import re

from fastapi import HTTPException
from pydantic import BaseModel, Field, field_validator

from vpack import database, network, state
from vpack.auth import AdminUser, CurrentUser

IP_PATTERN = re.compile(r"^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$")


class StationPayload(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    ip_camera_1: str = Field(..., min_length=7, max_length=45)
    ip_camera_2: str = ""
    safety_code: str = Field(..., min_length=1, max_length=50)
    camera_mode: str = Field(default="single")
    camera_brand: str = "imou"
    mac_address: str = ""

    @field_validator("ip_camera_1", "ip_camera_2")
    @classmethod
    def validate_ip(cls, v):
        if not v:
            return v
        if not IP_PATTERN.match(v):
            raise ValueError(f"Invalid IP address format: {v}")
        return v


def _resolve_cam2_url(payload, url_fn):
    """Generate cam2_url. If ip_camera_2 is provided, use it.
    If empty but camera_mode is dual/pip, use ip_camera_1 (same device, channel 2)."""
    if payload.ip_camera_2:
        return url_fn(payload.ip_camera_2, payload.safety_code, channel=2, brand=payload.camera_brand)
    if payload.camera_mode.lower() in ("pip", "dual_file"):
        return url_fn(payload.ip_camera_1, payload.safety_code, channel=2, brand=payload.camera_brand)
    return None


class StationModel(BaseModel):
    id: int
    name: str
    ip_camera_1: str
    ip_camera_2: str
    safety_code: str | None = None
    camera_mode: str
    camera_brand: str
    mac_address: str
    processing_count: int | None = None
    camera_health: dict | None = None


class StationsResponse(BaseModel):
    data: list[StationModel]


def register_routes(app):
    # --- STATIONS CRUD API ---

    @app.get("/api/stations", response_model=StationsResponse, response_model_exclude_none=True)
    def get_stations_api(current_user: CurrentUser):
        stations = database.get_stations()

        with state._processing_lock:
            for s in stations:
                s["processing_count"] = state._processing_count.get(s["id"], 0)

        with state._camera_health_lock:
            for s in stations:
                sid = str(s["id"])
                if sid in state._camera_health:
                    s["camera_health"] = state._camera_health[sid]

        if current_user.get("role") != "ADMIN":
            for s in stations:
                s.pop("safety_code", None)
        return {"data": stations}

    @app.get("/api/stations/check-conflict")
    def check_station_conflict(
        admin: AdminUser,
        ip: str = "",
        ip2: str = "",
        mac: str = "",
        name: str = "",
        exclude_id: int = 0,
    ):
        stations = database.get_stations()
        warnings = []
        mac_clean = mac.replace(":", "").replace("-", "").replace(".", "").upper() if mac else ""
        for s in stations:
            if s["id"] == exclude_id:
                continue
            if ip and (s.get("ip_camera_1") == ip or s.get("ip_camera_2") == ip):
                warnings.append(f'IP {ip} đã được dùng ở trạm "{s["name"]}"')
            if ip2 and (s.get("ip_camera_1") == ip2 or s.get("ip_camera_2") == ip2):
                warnings.append(f'IP {ip2} đã được dùng ở trạm "{s["name"]}"')
            if mac_clean:
                s_mac = s.get("mac_address", "").replace(":", "").replace("-", "").replace(".", "").upper()
                if s_mac and s_mac == mac_clean:
                    warnings.append(f'MAC {mac} đã được gán cho trạm "{s["name"]}"')
            if name and s.get("name", "").lower() == name.lower():
                warnings.append(f'Tên "{name}" đã tồn tại ở trạm khác')
        return {"warnings": warnings}

    @app.post("/api/stations")
    def create_station(payload: StationPayload, admin: AdminUser):
        new_id = database.add_station(payload.model_dump())
        database.log_audit(admin["id"], "STATION_CREATE", f"station_id={new_id}")
        live_quality = database.get_setting("LIVE_VIEW_STREAM", "sub")
        url_fn = state.get_rtsp_url if live_quality == "main" else state.get_rtsp_sub_url
        url = url_fn(
            payload.ip_camera_1,
            payload.safety_code,
            channel=1,
            brand=payload.camera_brand,
        )
        cam2_url = _resolve_cam2_url(payload, url_fn)
        sm = state.CameraStreamManager(url, station_id=new_id, cam2_url=cam2_url, station_name=payload.name)
        with state._streams_lock:
            state.stream_managers[new_id] = sm
        sm.start()
        return {"status": "success", "id": new_id}

    @app.put("/api/stations/{station_id}")
    def update_station(station_id: int, payload: StationPayload, admin: AdminUser):
        database.update_station(station_id, payload.model_dump())
        database.log_audit(admin["id"], "STATION_UPDATE", f"station_id={station_id}")
        with state._streams_lock:
            sm = state.stream_managers.get(station_id)
        if sm:
            live_quality = database.get_setting("LIVE_VIEW_STREAM", "sub")
            url_fn = state.get_rtsp_url if live_quality == "main" else state.get_rtsp_sub_url
            url = url_fn(
                payload.ip_camera_1,
                payload.safety_code,
                channel=1,
                brand=payload.camera_brand,
            )
            sm.update_url(url)
            cam2_url = _resolve_cam2_url(payload, url_fn)
            sm.station_name = payload.name
            sm.update_cam2_url(cam2_url)
        return {"status": "success"}

    @app.delete("/api/stations/{station_id}")
    def delete_station(station_id: int, admin: AdminUser):
        database.delete_station(station_id)
        database.log_audit(admin["id"], "STATION_DELETE", f"station_id={station_id}")
        with state._streams_lock:
            sm = state.stream_managers.pop(station_id, None)
            state.reconnect_status.pop(station_id, None)
        if sm:
            sm.stop()

        # Safety net — always cleanup MediaMTX path even if sm is missing
        state._mtx_remove_path(station_id)
        state._mtx_remove_path(station_id, suffix="_cam2")

        with state._recorders_lock:
            rec = state.active_recorders.pop(station_id, None)
            state.active_waybills.pop(station_id, None)
            state.active_record_ids.pop(station_id, None)
        if rec:
            rec.stop_recording()
        with state._processing_lock:
            state._processing_count.pop(station_id, None)
        with state._station_locks_lock:
            state._station_locks.pop(station_id, None)
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
        url_fn = state.get_rtsp_url if live_quality == "main" else state.get_rtsp_sub_url
        new_url = url_fn(new_ip, code, channel=1, brand=brand)
        with state._streams_lock:
            sm = state.stream_managers.get(station_id)
        if sm:
            sm.update_url(new_url)

        return {
            "status": "found",
            "message": f"Đã tìm thấy camera! IP mới: {new_ip} (cũ: {old_ip})",
            "old_ip": old_ip,
            "new_ip": new_ip,
        }

    @app.get("/api/reconnect-status")
    def get_reconnect_status(current_user: CurrentUser, station_id: int | None = None):
        with state._streams_lock:
            if station_id:
                return {"data": state.reconnect_status.get(station_id, None)}
            return {"data": dict(state.reconnect_status)}

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
        limit = min(max(limit, 1), 500)
        offset = max(offset, 0)
        logs = database.get_audit_logs(user_id=user_id, action=action, limit=limit, offset=offset)
        return {"data": logs}
