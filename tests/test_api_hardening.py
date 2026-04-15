import os
import sys
import pytest
import time
import threading
import json
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database
import auth


# ---------------------------------------------------------------------------
# Plan #19 – Station input validation (backend hardening)
# Plan #18 – Auto-update concurrent protection
# Plan #16 – Settings validation
# RBAC edge cases
# ---------------------------------------------------------------------------


class TestStationValidation:
    """Station CRUD input validation tests (Plan #19).

    Backend ``StationPayload`` (api.py line 832) currently has *no*
    server-side constraints on name length, IP format, safety_code length,
    or MAC format.  These tests document the current behaviour and act as
    regression guards so that when validation is added the test suite will
    flag the change for review.
    """

    def test_create_station_empty_name(self, client, admin_headers):
        """Empty name is currently accepted — needs backend validation."""
        # Empty name now rejected with 422 (Pydantic min_length=1)
        r = client.post(
            "/api/stations",
            headers=admin_headers,
            json={
                "name": "",
                "ip_camera_1": "10.0.0.1",
                "safety_code": "ABCD",
                "camera_mode": "SINGLE",
            },
        )
        assert r.status_code == 422

    def test_create_station_very_long_name(self, client, admin_headers):
        """Names exceeding 50 characters are currently accepted."""
        # TODO(Plan #19): Backend should reject name > 50 characters
        r = client.post(
            "/api/stations",
            headers=admin_headers,
            json={
                "name": "X" * 100,
                "ip_camera_1": "10.0.0.1",
                "safety_code": "ABCD",
                "camera_mode": "SINGLE",
            },
        )
        assert r.status_code == 200
        assert r.json()["status"] == "success"

    def test_create_station_empty_ip_camera(self, client, admin_headers):
        """Empty ip_camera_1 is currently accepted."""
        # Empty ip_camera_1 now rejected with 422 (Pydantic min_length=7)
        r = client.post(
            "/api/stations",
            headers=admin_headers,
            json={
                "name": "NoIP Station",
                "ip_camera_1": "",
                "safety_code": "ABCD",
                "camera_mode": "SINGLE",
            },
        )
        assert r.status_code == 422

    def test_create_station_empty_safety_code(self, client, admin_headers):
        """Empty safety_code is currently accepted."""
        # Empty safety_code now rejected with 422 (Pydantic min_length=1)
        r = client.post(
            "/api/stations",
            headers=admin_headers,
            json={
                "name": "NoCode Station",
                "ip_camera_1": "10.0.0.1",
                "safety_code": "",
                "camera_mode": "SINGLE",
            },
        )
        assert r.status_code == 422

    def test_create_station_invalid_ip_format(self, client, admin_headers):
        """Invalid IP format is currently accepted — no server-side regex check."""
        # TODO(Plan #19): Backend should validate IP address format
        r = client.post(
            "/api/stations",
            headers=admin_headers,
            json={
                "name": "BadIP Station",
                "ip_camera_1": "not-an-ip-address",
                "safety_code": "ABCD",
                "camera_mode": "SINGLE",
            },
        )
        assert r.status_code == 200
        assert r.json()["status"] == "success"


class TestStationConflict:
    """Conflict-detection edge cases for /api/stations/check-conflict.

    The endpoint (api.py line 851) normalises MAC addresses, compares names
    case-insensitively, and checks both ip_camera_1 and ip_camera_2 fields.
    """

    def test_conflict_ip2_parameter(self, client, admin_headers, sample_station_id):
        """The ``ip2`` query param should detect conflicts with existing IPs."""
        r = client.get(
            "/api/stations/check-conflict",
            headers=admin_headers,
            params={"ip2": "192.168.5.18"},
        )
        warnings = r.json()["warnings"]
        assert len(warnings) > 0
        assert "192.168.5.18" in warnings[0]

    def test_conflict_ip_matches_camera_2(self, client, admin_headers):
        """Queried IP should match a station's ip_camera_2 field."""
        database.add_station(
            {
                "name": "Dual Station",
                "ip_camera_1": "10.0.0.1",
                "ip_camera_2": "10.0.0.2",
                "safety_code": "CODE1",
                "camera_mode": "DUAL",
                "camera_brand": "imou",
                "mac_address": "",
            }
        )
        r = client.get(
            "/api/stations/check-conflict",
            headers=admin_headers,
            params={"ip": "10.0.0.2"},
        )
        warnings = r.json()["warnings"]
        assert len(warnings) > 0
        assert "10.0.0.2" in warnings[0]

    def test_conflict_mac_normalization(self, client, admin_headers, sample_station_id):
        """MAC comparison normalises separators (dashes → stripped)."""
        r = client.get(
            "/api/stations/check-conflict",
            headers=admin_headers,
            params={"mac": "AA-BB-CC-DD-EE-FF"},
        )
        warnings = r.json()["warnings"]
        assert len(warnings) > 0

    def test_conflict_name_case_insensitive(
        self, client, admin_headers, sample_station_id
    ):
        """Name conflict detection is case-insensitive."""
        r = client.get(
            "/api/stations/check-conflict",
            headers=admin_headers,
            params={"name": "test station"},
        )
        warnings = r.json()["warnings"]
        assert len(warnings) > 0

    def test_conflict_multiple_warnings_combined(
        self, client, admin_headers, sample_station_id
    ):
        """Requesting IP + MAC + name together yields >= 3 warnings."""
        r = client.get(
            "/api/stations/check-conflict",
            headers=admin_headers,
            params={
                "ip": "192.168.5.18",
                "mac": "AA:BB:CC:DD:EE:FF",
                "name": "Test Station",
            },
        )
        warnings = r.json()["warnings"]
        assert len(warnings) >= 3


class TestSettingsValidation:
    """Settings input validation tests (Plan #16).

    ``SettingsUpdate`` Pydantic model (api.py line 553) defines
    ``RECORD_STREAM_TYPE: str = "main"`` with no enum constraint.
    """

    def test_settings_stream_type_main(self, client, admin_headers):
        r = client.post(
            "/api/settings",
            headers=admin_headers,
            json={
                "RECORD_KEEP_DAYS": 7,
                "RECORD_STREAM_TYPE": "main",
                "CLOUD_PROVIDER": "NONE",
            },
        )
        assert r.json()["status"] == "success"
        assert database.get_setting("RECORD_STREAM_TYPE") == "main"

    def test_settings_stream_type_sub(self, client, admin_headers):
        database.set_setting("RECORD_STREAM_TYPE", "main")
        r = client.post(
            "/api/settings",
            headers=admin_headers,
            json={
                "RECORD_KEEP_DAYS": 7,
                "RECORD_STREAM_TYPE": "sub",
                "CLOUD_PROVIDER": "NONE",
            },
        )
        assert r.json()["status"] == "success"
        assert database.get_setting("RECORD_STREAM_TYPE") == "sub"

    def test_settings_invalid_stream_type_accepted(self, client, admin_headers):
        """Invalid stream type is persisted without validation."""
        # TODO(Plan #16): Backend should validate RECORD_STREAM_TYPE ∈ {main, sub}
        r = client.post(
            "/api/settings",
            headers=admin_headers,
            json={
                "RECORD_KEEP_DAYS": 7,
                "RECORD_STREAM_TYPE": "INVALID_TYPE",
                "CLOUD_PROVIDER": "NONE",
            },
        )
        assert r.json()["status"] == "success"
        assert database.get_setting("RECORD_STREAM_TYPE") == "INVALID_TYPE"


class TestAutoUpdate:
    """Auto-update concurrent protection tests (Plan #18).

    The update mechanism uses ``_update_lock`` (threading.Lock) and an
    ``_is_updating`` flag (api.py lines 1684-1685) to prevent concurrent
    updates.
    """

    def test_update_check_returns_structure(self, client, admin_headers, monkeypatch):
        """Pre-populated cache is returned with the expected keys."""
        import routes_system

        cached = {
            "current_version": "2.0.0",
            "latest_version": "2.1.0",
            "update_available": True,
            "mode": "production",
            "changelog": "Bug fixes",
        }
        monkeypatch.setattr(
            routes_system,
            "_update_check_cache",
            {
                "result": cached,
                "timestamp": time.time(),
            },
        )

        r = client.get("/api/system/update-check", headers=admin_headers)
        data = r.json()
        assert data["current_version"] == "2.0.0"
        assert data["latest_version"] == "2.1.0"
        assert data["update_available"] is True
        assert data["mode"] == "production"

    def test_update_check_caches_result(self, client, admin_headers, monkeypatch):
        """Two consecutive calls return the identical cached payload."""
        import routes_system

        cached = {
            "current_version": "1.0.0",
            "latest_version": "1.0.0",
            "update_available": False,
            "mode": "dev",
            "changelog": "",
        }
        monkeypatch.setattr(
            routes_system,
            "_update_check_cache",
            {
                "result": cached,
                "timestamp": time.time(),
            },
        )

        r1 = client.get("/api/system/update-check", headers=admin_headers)
        r2 = client.get("/api/system/update-check", headers=admin_headers)
        assert r1.json() == r2.json()
        assert r2.json()["current_version"] == "1.0.0"

    def test_update_concurrent_rejected_by_lock(
        self, client, admin_headers, monkeypatch
    ):
        """Second update attempt is rejected when ``_update_lock`` is held."""
        import routes_system

        new_lock = threading.Lock()
        monkeypatch.setattr(routes_system, "_update_lock", new_lock)
        monkeypatch.setattr(routes_system, "_is_updating", False)

        # Simulate an ongoing update by pre-acquiring the lock
        new_lock.acquire()
        try:
            r = client.post("/api/system/update", headers=admin_headers)
            data = r.json()
            assert data["status"] == "error"
        finally:
            new_lock.release()

    def test_update_rejected_when_flag_set(self, client, admin_headers, monkeypatch):
        """``_is_updating`` flag blocks even when lock is free."""
        import routes_system

        monkeypatch.setattr(routes_system, "_update_lock", threading.Lock())
        monkeypatch.setattr(routes_system, "_is_updating", True)

        r = client.post("/api/system/update", headers=admin_headers)
        data = r.json()
        assert data["status"] == "error"


class TestRBACEdgeCases:
    """Role-based access control edge cases."""

    def test_delete_self_account_rejected(self, client, admin_headers, admin_user_id):
        """Admin cannot delete their own account."""
        r = client.delete(f"/api/users/{admin_user_id}", headers=admin_headers)
        assert r.json()["status"] == "error"
        # Confirm the admin still exists
        assert database.get_user_by_id(admin_user_id) is not None

    def test_release_session_other_user_noop(
        self, client, operator_headers, sample_station_id
    ):
        """Releasing another operator's session silently succeeds without
        actually ending the session (api.py line 1060-1065)."""
        # Operator 1 acquires the station
        r1 = client.post(
            "/api/sessions/acquire",
            headers=operator_headers,
            params={"station_id": sample_station_id},
        )
        session_id = r1.json()["session_id"]

        # Create a second operator
        uid2 = database.create_user("op_other", "Pass123!", "OPERATOR")
        tok2 = auth.create_access_token({"sub": str(uid2), "role": "OPERATOR"})
        h2 = {"Authorization": f"Bearer {tok2}"}

        # Operator 2 tries to release Operator 1's session
        r2 = client.post(
            "/api/sessions/release",
            headers=h2,
            params={"station_id": sample_station_id},
        )
        # API returns success but does NOT actually end the session
        assert r2.json()["status"] == "success"

        # The session should still be active and owned by Operator 1
        session = database.get_active_session(sample_station_id)
        assert session is not None
        assert session["id"] == session_id

    def test_audit_logs_operator_forbidden(self, client, operator_headers):
        """Operators cannot access audit logs (AdminUser dependency)."""
        r = client.get("/api/audit-logs", headers=operator_headers)
        assert r.status_code == 403

    def test_check_conflict_operator_forbidden(self, client, operator_headers):
        """Operators cannot check station conflicts (AdminUser dependency)."""
        r = client.get("/api/stations/check-conflict", headers=operator_headers)
        assert r.status_code == 403

    def test_operator_cannot_create_station(self, client, operator_headers):
        """Station creation requires ADMIN role."""
        r = client.post(
            "/api/stations",
            headers=operator_headers,
            json={
                "name": "Op Station",
                "ip_camera_1": "10.0.0.1",
                "safety_code": "CODE1",
                "camera_mode": "SINGLE",
            },
        )
        assert r.status_code == 403
