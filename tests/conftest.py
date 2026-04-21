import os
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bcrypt

import auth
import database


@pytest.fixture(autouse=True, scope="session")
def patch_bcrypt_for_tests():
    """Make bcrypt extremely fast during tests to avoid 200s+ test suites on Windows."""
    original_gensalt = bcrypt.gensalt

    def fast_gensalt(rounds=12, prefix=b"2b"):
        return original_gensalt(rounds=4, prefix=prefix)

    bcrypt.gensalt = fast_gensalt
    yield
    bcrypt.gensalt = original_gensalt


@pytest.fixture(autouse=True)
def isolate_db(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr(database, "DB_FILE", db_path)
    monkeypatch.setattr(database, "_DB_DIR", str(tmp_path / "recordings"))
    database.init_db()
    yield


@pytest.fixture
def admin_user_id():
    user = database.get_user_by_username("admin")
    assert user is not None, "Default admin should exist after init_db"
    return user["id"]


@pytest.fixture
def admin_token(admin_user_id):
    return auth.create_access_token({"sub": str(admin_user_id), "role": "ADMIN"})


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def operator_user_id():
    uid = database.create_user("operator1", "TestPass123!", "OPERATOR", "Test Op")
    assert uid is not None
    return uid


@pytest.fixture
def operator_token(operator_user_id):
    return auth.create_access_token({"sub": str(operator_user_id), "role": "OPERATOR"})


@pytest.fixture
def operator_headers(operator_token):
    return {"Authorization": f"Bearer {operator_token}"}


@pytest.fixture
def sample_station_id():
    return database.add_station(
        {
            "name": "Test Station",
            "ip_camera_1": "192.168.5.18",
            "ip_camera_2": "",
            "safety_code": "TESTCODE",
            "camera_mode": "SINGLE",
            "camera_brand": "imou",
            "mac_address": "AA:BB:CC:DD:EE:FF",
        }
    )


@pytest.fixture
def client(isolate_db, monkeypatch):
    import api
    import routes_auth

    monkeypatch.setattr(api, "stream_managers", {})
    monkeypatch.setattr(api, "active_recorders", {})
    monkeypatch.setattr(api, "active_waybills", {})
    monkeypatch.setattr(api, "active_record_ids", {})
    monkeypatch.setattr(api, "_processing_count", {})
    monkeypatch.setattr(api, "_station_locks", {})
    monkeypatch.setattr(api, "reconnect_status", {})
    monkeypatch.setattr(api, "_recording_timers", {})
    monkeypatch.setattr(api, "_recording_start_times", {})
    monkeypatch.setattr(api, "_recording_warning_timers", {})
    monkeypatch.setattr(routes_auth, "_login_attempts", {})
    with (
        patch.object(api.CameraStreamManager, "start"),
        patch.object(api.CameraStreamManager, "stop"),
        patch.object(api.CameraStreamManager, "update_url"),
        patch.object(api.CameraStreamManager, "update_cam2_url"),
    ):
        from starlette.testclient import TestClient

        with TestClient(api.app) as c:
            yield c
