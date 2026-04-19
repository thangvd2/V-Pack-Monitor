import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import auth
import database


class TestLogin:
    def test_login_success(self, client):
        database.update_user_password(database.get_user_by_username("admin")["id"], "AdminPass1!")
        r = client.post("/api/auth/login", json={"username": "admin", "password": "AdminPass1!"})
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "success"
        assert "access_token" in data
        assert data["user"]["role"] == "ADMIN"

    def test_login_wrong_password(self, client):
        r = client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
        assert r.status_code == 401
        assert r.json()["status"] == "error"

    def test_login_nonexistent_user(self, client):
        r = client.post("/api/auth/login", json={"username": "ghost", "password": "x"})
        assert r.json()["status"] == "error"

    def test_login_inactive_user(self, client, admin_user_id):
        database.update_user(admin_user_id, is_active=0)
        r = client.post("/api/auth/login", json={"username": "admin", "password": "08012011"})
        assert r.json()["status"] == "error"
        assert "khóa" in r.json()["message"].lower() or "locked" in r.json()["message"].lower()

    def test_login_rate_limiting(self, client):
        for i in range(5):
            client.post("/api/auth/login", json={"username": "admin", "password": f"wrong{i}"})
        r = client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
        assert "nhiều" in r.json()["message"].lower() or "thử lại" in r.json()["message"].lower()


class TestAuthEndpoints:
    def test_get_me(self, client, admin_headers, admin_user_id):
        r = client.get("/api/auth/me", headers=admin_headers)
        assert r.status_code == 200
        assert r.json()["user"]["id"] == admin_user_id

    def test_get_me_unauthorized(self, client):
        r = client.get("/api/auth/me")
        assert r.status_code == 401

    def test_logout(self, client, admin_headers):
        r = client.post("/api/auth/logout", headers=admin_headers)
        assert r.status_code == 200
        assert r.json()["status"] == "success"

    def test_logout_revokes_token(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        client.post("/api/auth/logout", headers=headers)
        r = client.get("/api/auth/me", headers=headers)
        assert r.status_code == 401

    def test_change_password(self, client, admin_headers, admin_user_id):
        database.update_user_password(admin_user_id, "OldPass1!")
        r = client.put(
            "/api/auth/change-password",
            headers=admin_headers,
            json={"old_password": "OldPass1!", "new_password": "NewPass1!"},
        )
        assert r.status_code == 200
        assert r.json()["status"] == "success"
        user = database.get_user_by_username("admin")
        assert auth.verify_password("NewPass1!", user["password_hash"])

    def test_change_password_wrong_old(self, client, admin_headers, admin_user_id):
        database.update_user_password(admin_user_id, "RealPass1!")
        r = client.put(
            "/api/auth/change-password",
            headers=admin_headers,
            json={"old_password": "WrongOld!", "new_password": "NewPass1!"},
        )
        assert r.json()["status"] == "error"

    def test_change_password_too_short(self, client, admin_headers):
        r = client.put(
            "/api/auth/change-password",
            headers=admin_headers,
            json={"old_password": "whatever", "new_password": "short"},
        )
        assert r.status_code == 422


class TestStationCRUD:
    def test_create_station(self, client, admin_headers):
        r = client.post(
            "/api/stations",
            headers=admin_headers,
            json={
                "name": "New Station",
                "ip_camera_1": "10.0.0.1",
                "ip_camera_2": "",
                "safety_code": "ABC123",
                "camera_mode": "SINGLE",
            },
        )
        assert r.status_code == 200
        assert r.json()["status"] == "success"
        assert "id" in r.json()

    def test_get_stations_admin_sees_safety_code(self, client, admin_headers, sample_station_id):
        r = client.get("/api/stations", headers=admin_headers)
        stations = r.json()["data"]
        assert any(s.get("safety_code") for s in stations)

    def test_get_stations_operator_no_safety_code(self, client, operator_headers, sample_station_id):
        r = client.get("/api/stations", headers=operator_headers)
        stations = r.json()["data"]
        assert all("safety_code" not in s for s in stations)

    def test_update_station(self, client, admin_headers, sample_station_id):
        r = client.put(
            f"/api/stations/{sample_station_id}",
            headers=admin_headers,
            json={
                "name": "Updated",
                "ip_camera_1": "10.0.0.99",
                "ip_camera_2": "",
                "safety_code": "NEWCODE",
                "camera_mode": "DUAL_FILE",
                "camera_brand": "dahua",
            },
        )
        assert r.json()["status"] == "success"
        s = database.get_station(sample_station_id)
        assert s["name"] == "Updated"
        assert s["camera_brand"] == "dahua"

    def test_delete_station(self, client, admin_headers, sample_station_id):
        r = client.delete(f"/api/stations/{sample_station_id}", headers=admin_headers)
        assert r.json()["status"] == "success"
        assert database.get_station(sample_station_id) is None

    def test_check_conflict_ip(self, client, admin_headers, sample_station_id):
        r = client.get(
            "/api/stations/check-conflict",
            headers=admin_headers,
            params={"ip": "192.168.5.18"},
        )
        assert len(r.json()["warnings"]) > 0

    def test_check_conflict_mac(self, client, admin_headers, sample_station_id):
        r = client.get(
            "/api/stations/check-conflict",
            headers=admin_headers,
            params={"mac": "AA:BB:CC:DD:EE:FF"},
        )
        assert len(r.json()["warnings"]) > 0

    def test_check_conflict_name(self, client, admin_headers, sample_station_id):
        r = client.get(
            "/api/stations/check-conflict",
            headers=admin_headers,
            params={"name": "Test Station"},
        )
        assert len(r.json()["warnings"]) > 0

    def test_check_conflict_exclude_self(self, client, admin_headers, sample_station_id):
        r = client.get(
            "/api/stations/check-conflict",
            headers=admin_headers,
            params={"ip": "192.168.5.18", "exclude_id": sample_station_id},
        )
        assert len(r.json()["warnings"]) == 0

    def test_check_conflict_no_conflict(self, client, admin_headers):
        r = client.get(
            "/api/stations/check-conflict",
            headers=admin_headers,
            params={"ip": "99.99.99.99", "mac": "00:00:00:00:00:00", "name": "Unique"},
        )
        assert len(r.json()["warnings"]) == 0


class TestRecords:
    def test_get_records_empty(self, client, admin_headers):
        r = client.get("/api/records", headers=admin_headers)
        assert r.status_code == 200
        assert r.json()["records"] == []

    def test_get_records_with_data(self, client, admin_headers, sample_station_id):
        rid = database.create_record(sample_station_id, "WB001", "SINGLE")
        database.update_record_status(rid, "READY", video_paths="/a.mp4,/b.mp4")
        r = client.get("/api/records", headers=admin_headers)
        data = r.json()["records"]
        assert len(data) >= 1
        rec = data[0]
        assert rec["video_paths"] == ["/a.mp4", "/b.mp4"]

    def test_get_records_empty_video_paths(self, client, admin_headers, sample_station_id):
        rid = database.create_record(sample_station_id, "WB-EMPTY", "SINGLE")
        database.update_record_status(rid, "RECORDING")
        r = client.get("/api/records", headers=admin_headers)
        rec = [d for d in r.json()["records"] if d["waybill_code"] == "WB-EMPTY"][0]
        assert rec["video_paths"] == []

    def test_get_records_search(self, client, admin_headers, sample_station_id):
        database.create_record(sample_station_id, "FINDME-001", "SINGLE")
        r = client.get("/api/records", headers=admin_headers, params={"search": "FINDME"})
        assert len(r.json()["records"]) >= 1

    def test_delete_record(self, client, admin_headers, sample_station_id):
        rid = database.create_record(sample_station_id, "DEL-WB", "SINGLE")
        r = client.delete(f"/api/records/{rid}", headers=admin_headers)
        assert r.json()["status"] == "success"

    def test_get_status_idle(self, client, admin_headers, sample_station_id):
        r = client.get(
            "/api/status",
            headers=admin_headers,
            params={"station_id": sample_station_id},
        )
        assert r.json()["status"] == "idle"

    def test_get_status_unauthorized(self, client, sample_station_id):
        r = client.get("/api/status", params={"station_id": sample_station_id})
        assert r.status_code == 401


class TestSettings:
    def test_get_settings_masks_sensitive(self, client, admin_headers):
        database.set_setting("S3_SECRET_KEY", "super_secret")
        r = client.get("/api/settings", headers=admin_headers)
        settings = r.json()["data"]
        assert settings["S3_SECRET_KEY"] == "****"

    def test_update_settings(self, client, admin_headers):
        r = client.post(
            "/api/settings",
            headers=admin_headers,
            json={"RECORD_KEEP_DAYS": 30, "CLOUD_PROVIDER": "NONE"},
        )
        assert r.json()["status"] == "success"
        assert database.get_setting("RECORD_KEEP_DAYS") == "30"

    def test_update_settings_preserve_masked(self, client, admin_headers):
        database.set_setting("S3_SECRET_KEY", "original_secret")
        client.post(
            "/api/settings",
            headers=admin_headers,
            json={"RECORD_KEEP_DAYS": 7, "S3_SECRET_KEY": "****"},
        )
        assert database.get_setting("S3_SECRET_KEY") == "original_secret"

    def test_get_live_stream_quality_default(self, client, admin_headers):
        r = client.get("/api/live-stream-quality", headers=admin_headers)
        assert r.json()["quality"] == "sub"

    def test_set_live_stream_quality(self, client, admin_headers):
        r = client.post("/api/live-stream-quality", headers=admin_headers, json={"quality": "main"})
        assert r.json()["status"] == "success"
        assert database.get_setting("LIVE_VIEW_STREAM") == "main"

    def test_settings_require_admin(self, client, operator_headers):
        r = client.get("/api/settings", headers=operator_headers)
        assert r.status_code == 403


class TestSessions:
    def test_acquire_session(self, client, operator_headers, sample_station_id):
        r = client.post(
            "/api/sessions/acquire",
            headers=operator_headers,
            params={"station_id": sample_station_id},
        )
        assert r.json()["status"] == "success"
        assert "session_id" in r.json()

    def test_acquire_session_admin_rejected(self, client, admin_headers, sample_station_id):
        r = client.post(
            "/api/sessions/acquire",
            headers=admin_headers,
            params={"station_id": sample_station_id},
        )
        assert r.json()["status"] == "error"

    def test_acquire_session_conflict(self, client, operator_headers, operator_user_id, sample_station_id):
        client.post(
            "/api/sessions/acquire",
            headers=operator_headers,
            params={"station_id": sample_station_id},
        )
        uid2 = database.create_user("op2", "Pass123!", "OPERATOR")
        tok2 = auth.create_access_token({"sub": str(uid2), "role": "OPERATOR"})
        h2 = {"Authorization": f"Bearer {tok2}"}
        r = client.post(
            "/api/sessions/acquire",
            headers=h2,
            params={"station_id": sample_station_id},
        )
        assert r.json()["status"] == "error"
        assert "sử dụng" in r.json()["message"].lower()

    def test_heartbeat_session(self, client, operator_headers, sample_station_id):
        r = client.post(
            "/api/sessions/acquire",
            headers=operator_headers,
            params={"station_id": sample_station_id},
        )
        sid = r.json()["session_id"]
        r = client.post(
            "/api/sessions/heartbeat",
            headers=operator_headers,
            params={"session_id": sid},
        )
        assert r.json()["status"] == "success"

    def test_heartbeat_wrong_user(self, client, operator_headers, sample_station_id):
        r = client.post(
            "/api/sessions/acquire",
            headers=operator_headers,
            params={"station_id": sample_station_id},
        )
        sid = r.json()["session_id"]
        uid2 = database.create_user("op3", "Pass123!", "OPERATOR")
        tok2 = auth.create_access_token({"sub": str(uid2), "role": "OPERATOR"})
        h2 = {"Authorization": f"Bearer {tok2}"}
        r = client.post("/api/sessions/heartbeat", headers=h2, params={"session_id": sid})
        assert r.status_code == 403

    def test_release_session(self, client, operator_headers, sample_station_id):
        r = client.post(
            "/api/sessions/acquire",
            headers=operator_headers,
            params={"station_id": sample_station_id},
        )
        r = client.post(
            "/api/sessions/release",
            headers=operator_headers,
            params={"station_id": sample_station_id},
        )
        assert r.json()["status"] == "success"
        assert database.get_active_session(sample_station_id) is None


class TestUserCRUD:
    def test_list_users(self, client, admin_headers):
        r = client.get("/api/users", headers=admin_headers)
        assert r.status_code == 200
        assert len(r.json()["data"]) >= 1

    def test_create_user(self, client, admin_headers):
        r = client.post(
            "/api/users",
            headers=admin_headers,
            json={"username": "newuser", "password": "Pass123!", "role": "OPERATOR"},
        )
        assert r.json()["status"] == "success"

    def test_create_user_duplicate(self, client, admin_headers):
        client.post(
            "/api/users",
            headers=admin_headers,
            json={"username": "dupuser", "password": "Pass123!"},
        )
        r = client.post(
            "/api/users",
            headers=admin_headers,
            json={"username": "dupuser", "password": "Pass456!"},
        )
        assert r.json()["status"] == "error"

    def test_create_user_invalid_role(self, client, admin_headers):
        r = client.post(
            "/api/users",
            headers=admin_headers,
            json={"username": "badrole", "password": "Pass123!", "role": "SUPERUSER"},
        )
        assert r.json()["status"] == "error"

    def test_update_user(self, client, admin_headers, operator_user_id):
        r = client.put(
            f"/api/users/{operator_user_id}",
            headers=admin_headers,
            json={"full_name": "Updated Name"},
        )
        assert r.json()["status"] == "success"

    def test_delete_user(self, client, admin_headers, operator_user_id):
        r = client.delete(f"/api/users/{operator_user_id}", headers=admin_headers)
        assert r.json()["status"] == "success"
        assert database.get_user_by_id(operator_user_id) is None

    def test_delete_self_prevented(self, client, admin_headers, admin_user_id):
        r = client.delete(f"/api/users/{admin_user_id}", headers=admin_headers)
        assert r.json()["status"] == "error"

    def test_reset_password(self, client, admin_headers, operator_user_id):
        r = client.put(
            f"/api/users/{operator_user_id}/password",
            headers=admin_headers,
            json={"password": "NewPass123!"},
        )
        assert r.json()["status"] == "success"
        user = database.get_user_by_username("operator1")
        assert auth.verify_password("NewPass123!", user["password_hash"])

    def test_reset_password_too_short(self, client, admin_headers, operator_user_id):
        r = client.put(
            f"/api/users/{operator_user_id}/password",
            headers=admin_headers,
            json={"password": "short"},
        )
        assert r.status_code == 422


class TestAnalytics:
    def test_analytics_today_empty(self, client, admin_headers, sample_station_id):
        r = client.get(
            "/api/analytics/today",
            headers=admin_headers,
            params={"station_id": sample_station_id},
        )
        assert r.status_code == 200
        assert r.json()["data"]["total_today"] == 0

    def test_analytics_today_with_data(self, client, admin_headers, sample_station_id):
        rid = database.create_record(sample_station_id, "TODAY-WB", "SINGLE")
        database.update_record_status(rid, "READY")
        r = client.get(
            "/api/analytics/today",
            headers=admin_headers,
            params={"station_id": sample_station_id},
        )
        assert r.json()["data"]["total_today"] >= 1


class TestLivePreview:
    def test_live_preview(self, client, admin_headers, sample_station_id):
        r = client.get("/api/live", headers=admin_headers, params={"station_id": sample_station_id})
        assert r.status_code == 200
        assert "webrtc_url" in r.json()


class TestExportCSV:
    def test_export_csv(self, client, admin_headers, sample_station_id):
        rid = database.create_record(sample_station_id, "CSV-WB", "SINGLE")
        database.update_record_status(rid, "READY")
        r = client.get("/api/export/csv", headers=admin_headers)
        assert r.status_code == 200
        assert "text/csv" in r.headers.get("content-type", "")
        assert "CSV-WB" in r.text

    def test_export_csv_has_bom(self, client, admin_headers):
        r = client.get("/api/export/csv", headers=admin_headers)
        raw = r.content
        assert raw[:3] == b"\xef\xbb\xbf"


class TestDownloadAuthorization:
    def test_download_operator_own_station_allowed(self, client, operator_headers, operator_user_id, sample_station_id):
        client.post(
            "/api/sessions/acquire",
            headers=operator_headers,
            params={"station_id": sample_station_id},
        )
        rid = database.create_record(sample_station_id, "DL-OWN", "SINGLE")
        database.update_record_status(rid, "READY", video_paths="recordings/dl_own.mp4")
        token = operator_headers["Authorization"].replace("Bearer ", "")
        r = client.get(f"/api/records/{rid}/download/0", params={"token": token})
        assert r.status_code != 403

    def test_download_operator_other_station_forbidden(
        self, client, operator_headers, operator_user_id, sample_station_id
    ):
        station_b = database.add_station(
            {
                "name": "Station B",
                "ip_camera_1": "10.0.0.2",
                "ip_camera_2": "",
                "safety_code": "CODEB",
                "camera_mode": "SINGLE",
            }
        )
        rid = database.create_record(station_b, "DL-OTHER", "SINGLE")
        database.update_record_status(rid, "READY", video_paths="recordings/dl_other.mp4")
        token = operator_headers["Authorization"].replace("Bearer ", "")
        r = client.get(f"/api/records/{rid}/download/0", params={"token": token})
        assert r.status_code == 403

    def test_download_admin_any_station(self, client, admin_headers, sample_station_id):
        rid = database.create_record(sample_station_id, "DL-ADMIN", "SINGLE")
        database.update_record_status(rid, "READY", video_paths="recordings/dl_admin.mp4")
        token = admin_headers["Authorization"].replace("Bearer ", "")
        r = client.get(f"/api/records/{rid}/download/0", params={"token": token})
        assert r.status_code != 403

    def test_download_operator_no_session_forbidden(self, client, operator_headers, sample_station_id):
        rid = database.create_record(sample_station_id, "DL-NOSESSION", "SINGLE")
        database.update_record_status(rid, "READY", video_paths="recordings/dl_nosession.mp4")
        token = operator_headers["Authorization"].replace("Bearer ", "")
        r = client.get(f"/api/records/{rid}/download/0", params={"token": token})
        assert r.status_code == 403
