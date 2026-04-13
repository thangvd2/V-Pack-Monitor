import os
import sys
import pytest
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database
import auth


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
def operator_user_id():
    uid = database.create_user("operator1", "TestPass123!", "OPERATOR", "Test Op")
    assert uid is not None
    return uid


@pytest.fixture
def operator_token(operator_user_id):
    return auth.create_access_token({"sub": str(operator_user_id), "role": "OPERATOR"})


@pytest.fixture
def sample_station_id():
    return database.add_station({
        "name": "Test Station",
        "ip_camera_1": "192.168.5.18",
        "ip_camera_2": "",
        "safety_code": "TESTCODE",
        "camera_mode": "SINGLE",
        "camera_brand": "imou",
        "mac_address": "AA:BB:CC:DD:EE:FF",
    })
