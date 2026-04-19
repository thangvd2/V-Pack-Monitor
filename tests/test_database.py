import os
import sqlite3

from database import (
    _ENCRYPT_PREFIX,
    _SENSITIVE_KEYS,
    _decrypt_value,
    _encrypt_value,
    add_station,
    cleanup_audit_log,
    cleanup_old_records,
    clear_must_change_password,
    create_record,
    create_session,
    create_user,
    delete_record,
    delete_station,
    delete_user,
    end_session,
    end_session_by_id,
    expire_stale_sessions,
    get_active_session,
    get_all_settings,
    get_all_users,
    get_audit_logs,
    get_daily_trend,
    get_hourly_stats,
    get_pending_records,
    get_record_by_id,
    get_records_v2,
    get_session_by_id,
    get_setting,
    get_station,
    get_stations,
    get_stations_comparison,
    get_user_by_id,
    get_user_by_username,
    init_db,
    is_jti_revoked,
    log_audit,
    revoke_jti,
    set_setting,
    set_settings,
    update_record_status,
    update_session_heartbeat,
    update_station,
    update_station_ip,
    update_user,
    update_user_password,
)


class TestEncryption:
    def test_encrypt_decrypt_roundtrip(self):
        original = "my_secret_password"
        encrypted = _encrypt_value(original)
        assert encrypted.startswith(_ENCRYPT_PREFIX)
        assert encrypted != original
        decrypted = _decrypt_value(encrypted)
        assert decrypted == original

    def test_decrypt_non_encrypted_passthrough(self):
        plain = "just_a_string"
        assert _decrypt_value(plain) == plain

    def test_decrypt_corrupted_data_returns_ciphertext(self):
        import base64

        bad = _ENCRYPT_PREFIX + base64.b64encode(b"\xff\xfe\xfd\xfc\xfb").decode()
        result = _decrypt_value(bad)
        assert result == bad

    def test_encrypt_empty_string(self):
        encrypted = _encrypt_value("")
        assert _decrypt_value(encrypted) == ""

    def test_encrypt_unicode(self):
        original = "Mật_khẩu_đặc_biệt!@#$%"
        encrypted = _encrypt_value(original)
        assert _decrypt_value(encrypted) == original


class TestInitDb:
    def test_creates_tables(self, tmp_path, monkeypatch):
        db_path = str(tmp_path / "test.db")
        monkeypatch.setattr("database.DB_FILE", db_path)
        monkeypatch.setattr("database._DB_DIR", str(tmp_path / "recordings"))
        init_db()
        with sqlite3.connect(db_path) as conn:
            tables = [
                r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
            ]
        for expected in [
            "packing_video",
            "system_settings",
            "stations",
            "users",
            "sessions",
            "audit_log",
            "revoked_tokens",
        ]:
            assert expected in tables

    def test_default_admin_created(self):
        admin = get_user_by_username("admin")
        assert admin is not None
        assert admin["role"] == "ADMIN"
        assert admin["must_change_password"] == 1

    def test_default_admin_password_is_08012011(self):
        admin = get_user_by_username("admin")
        import bcrypt

        assert bcrypt.checkpw(b"08012011", admin["password_hash"].encode())

    def test_idempotent(self):
        init_db()
        init_db()
        admin = get_user_by_username("admin")
        assert admin is not None
        users = get_all_users()
        assert len(users) == 1


class TestSettings:
    def test_set_get_roundtrip(self):
        set_setting("TEST_KEY", "hello")
        assert get_setting("TEST_KEY") == "hello"

    def test_get_nonexistent_returns_default(self):
        assert get_setting("NOPE") is None
        assert get_setting("NOPE", "fallback") == "fallback"

    def test_sensitive_keys_encrypted(self):
        for key in _SENSITIVE_KEYS:
            set_setting(key, "secret_value_123")
            raw = get_setting(key)
            assert raw == "secret_value_123"

    def test_overwrite_setting(self):
        set_setting("TEST_KEY", "v1")
        set_setting("TEST_KEY", "v2")
        assert get_setting("TEST_KEY") == "v2"

    def test_get_all_settings(self):
        set_setting("KEY_A", "val_a")
        set_setting("KEY_B", "val_b")
        all_settings = get_all_settings()
        assert all_settings["KEY_A"] == "val_a"
        assert all_settings["KEY_B"] == "val_b"

    def test_set_settings_batch(self):
        set_settings({"K1": "v1", "K2": "v2", "K3": "v3"})
        assert get_setting("K1") == "v1"
        assert get_setting("K2") == "v2"
        assert get_setting("K3") == "v3"


class TestRecords:
    def test_create_record_recording_status(self, sample_station_id):
        rid = create_record(sample_station_id, "WB001", "SINGLE")
        rec = get_record_by_id(rid)
        assert rec is not None
        assert rec["status"] == "RECORDING"
        assert rec["waybill_code"] == "WB001"

    def test_update_record_status_lifecycle(self, sample_station_id):
        rid = create_record(sample_station_id, "WB002", "SINGLE")
        update_record_status(rid, "PROCESSING")
        assert get_record_by_id(rid)["status"] == "PROCESSING"
        update_record_status(rid, "READY")
        assert get_record_by_id(rid)["status"] == "READY"

    def test_update_record_with_video_paths(self, sample_station_id):
        rid = create_record(sample_station_id, "WB003", "SINGLE")
        update_record_status(rid, "READY", video_paths="/path/a.mp4,/path/b.mp4")
        rec = get_record_by_id(rid)
        assert rec["video_paths"] == "/path/a.mp4,/path/b.mp4"

    def test_get_records_search(self, sample_station_id):
        create_record(sample_station_id, "ALPHA-001", "SINGLE")
        create_record(sample_station_id, "BETA-002", "SINGLE")
        results = get_records_v2(search="ALPHA")["records"]
        assert len(results) == 1
        assert results[0]["waybill_code"] == "ALPHA-001"

    def test_get_records_by_station(self):
        sid1 = add_station(
            {
                "name": "S1",
                "ip_camera_1": "10.0.0.1",
                "ip_camera_2": "",
                "safety_code": "X",
                "camera_mode": "SINGLE",
                "camera_brand": "imou",
                "mac_address": "",
            }
        )
        sid2 = add_station(
            {
                "name": "S2",
                "ip_camera_1": "10.0.0.2",
                "ip_camera_2": "",
                "safety_code": "Y",
                "camera_mode": "SINGLE",
                "camera_brand": "imou",
                "mac_address": "",
            }
        )
        create_record(sid1, "WB-S1", "SINGLE")
        create_record(sid2, "WB-S2", "SINGLE")
        results = get_records_v2(station_id=sid1)
        assert all(r["station_name"] == "S1" for r in results["records"])

    def test_get_record_by_id_not_found(self):
        assert get_record_by_id(99999) is None

    def test_get_pending_records(self, sample_station_id):
        rid1 = create_record(sample_station_id, "P001", "SINGLE")
        rid2 = create_record(sample_station_id, "P002", "SINGLE")
        update_record_status(rid2, "READY")
        pending = get_pending_records()
        pending_ids = [r["id"] for r in pending]
        assert rid1 in pending_ids
        assert rid2 not in pending_ids

    def test_cleanup_old_records(self, sample_station_id, tmp_path):
        fake_video = str(tmp_path / "old_video.mp4")
        with open(fake_video, "w") as f:
            f.write("fake")
        rid = create_record(sample_station_id, "OLD-WB", "SINGLE")
        update_record_status(rid, "READY", video_paths=fake_video)
        with sqlite3.connect(database.DB_FILE) as conn:
            conn.execute(
                "UPDATE packing_video SET recorded_at = datetime('now', '-10 days') WHERE id = ?",
                (rid,),
            )
            conn.commit()
        assert os.path.exists(fake_video)
        cleanup_old_records(days=7)
        assert not os.path.exists(fake_video)
        assert get_record_by_id(rid) is None

    def test_delete_record(self, sample_station_id, tmp_path):
        fake_video = str(tmp_path / "del_video.mp4")
        with open(fake_video, "w") as f:
            f.write("fake")
        rid = create_record(sample_station_id, "DEL-WB", "SINGLE")
        update_record_status(rid, "READY", video_paths=fake_video)
        assert os.path.exists(fake_video)
        delete_record(rid)
        assert not os.path.exists(fake_video)
        assert get_record_by_id(rid) is None


class TestStations:
    def test_add_get_station(self):
        sid = add_station(
            {
                "name": "Station A",
                "ip_camera_1": "192.168.1.1",
                "ip_camera_2": "",
                "safety_code": "ABC",
                "camera_mode": "SINGLE",
                "camera_brand": "imou",
                "mac_address": "",
            }
        )
        s = get_station(sid)
        assert s is not None
        assert s["name"] == "Station A"
        assert s["ip_camera_1"] == "192.168.1.1"

    def test_get_stations_list(self):
        add_station(
            {
                "name": "S1",
                "ip_camera_1": "10.0.0.1",
                "ip_camera_2": "",
                "safety_code": "X",
                "camera_mode": "SINGLE",
                "camera_brand": "imou",
                "mac_address": "",
            }
        )
        add_station(
            {
                "name": "S2",
                "ip_camera_1": "10.0.0.2",
                "ip_camera_2": "",
                "safety_code": "Y",
                "camera_mode": "SINGLE",
                "camera_brand": "imou",
                "mac_address": "",
            }
        )
        stations = get_stations()
        assert len(stations) >= 2

    def test_update_station(self):
        sid = add_station(
            {
                "name": "Old",
                "ip_camera_1": "1.1.1.1",
                "ip_camera_2": "",
                "safety_code": "X",
                "camera_mode": "SINGLE",
                "camera_brand": "imou",
                "mac_address": "",
            }
        )
        update_station(
            sid,
            {
                "name": "New",
                "ip_camera_1": "2.2.2.2",
                "ip_camera_2": "3.3.3.3",
                "safety_code": "Y",
                "camera_mode": "DUAL_FILE",
                "camera_brand": "dahua",
                "mac_address": "11:22:33:44:55:66",
            },
        )
        s = get_station(sid)
        assert s["name"] == "New"
        assert s["ip_camera_1"] == "2.2.2.2"
        assert s["camera_brand"] == "dahua"

    def test_update_station_ip_allowed_fields(self):
        sid = add_station(
            {
                "name": "IP Test",
                "ip_camera_1": "1.1.1.1",
                "ip_camera_2": "",
                "safety_code": "X",
                "camera_mode": "SINGLE",
                "camera_brand": "imou",
                "mac_address": "",
            }
        )
        update_station_ip(sid, "ip_camera_1", "10.0.0.100")
        assert get_station(sid)["ip_camera_1"] == "10.0.0.100"
        update_station_ip(sid, "ip_camera_2", "10.0.0.200")
        assert get_station(sid)["ip_camera_2"] == "10.0.0.200"

    def test_update_station_ip_rejects_invalid_field(self):
        sid = add_station(
            {
                "name": "IP Test 2",
                "ip_camera_1": "1.1.1.1",
                "ip_camera_2": "",
                "safety_code": "X",
                "camera_mode": "SINGLE",
                "camera_brand": "imou",
                "mac_address": "",
            }
        )
        with sqlite3.connect(database.DB_FILE) as conn:
            before = conn.execute("SELECT ip_camera_1 FROM stations WHERE id=?", (sid,)).fetchone()[0]
        update_station_ip(sid, "malicious_field", "evil")
        with sqlite3.connect(database.DB_FILE) as conn:
            after = conn.execute("SELECT ip_camera_1 FROM stations WHERE id=?", (sid,)).fetchone()[0]
        assert before == after

    def test_delete_station(self):
        sid = add_station(
            {
                "name": "To Delete",
                "ip_camera_1": "1.1.1.1",
                "ip_camera_2": "",
                "safety_code": "X",
                "camera_mode": "SINGLE",
                "camera_brand": "imou",
                "mac_address": "",
            }
        )
        delete_station(sid)
        assert get_station(sid) is None

    def test_get_station_not_found(self):
        assert get_station(99999) is None


class TestUsers:
    def test_create_user(self):
        uid = create_user("testuser", "Password123!", "OPERATOR", "Test User")
        assert uid is not None
        user = get_user_by_id(uid)
        assert user["username"] == "testuser"
        assert user["role"] == "OPERATOR"

    def test_create_duplicate_user_returns_none(self):
        create_user("dup_user", "Pass1!", "OPERATOR")
        result = create_user("dup_user", "Pass2!", "OPERATOR")
        assert result is None

    def test_get_user_by_username(self):
        create_user("findme", "Pass123!", "OPERATOR")
        user = get_user_by_username("findme")
        assert user is not None
        assert user["username"] == "findme"

    def test_get_user_by_id_no_password_hash(self):
        uid = create_user("nopwhash", "Pass123!", "OPERATOR")
        user = get_user_by_id(uid)
        assert "password_hash" not in user

    def test_update_user_allowed_fields(self):
        uid = create_user("updateme", "Pass123!", "OPERATOR", "Old Name")
        update_user(uid, role="ADMIN", full_name="New Name", is_active=0)
        user = get_user_by_id(uid)
        assert user["role"] == "ADMIN"
        assert user["full_name"] == "New Name"
        assert user["is_active"] == 0

    def test_update_user_ignores_disallowed_fields(self):
        uid = create_user("ignorefields", "Pass123!", "OPERATOR")
        update_user(uid, role="ADMIN", malicious="hacked")
        user = get_user_by_id(uid)
        assert user["role"] == "ADMIN"

    def test_update_user_password(self):
        uid = create_user("pwchange", "OldPassword!", "OPERATOR")
        update_user_password(uid, "NewPassword!")
        import bcrypt

        user = get_user_by_username("pwchange")
        assert bcrypt.checkpw(b"NewPassword!", user["password_hash"].encode())
        assert not bcrypt.checkpw(b"OldPassword!", user["password_hash"].encode())

    def test_delete_user(self):
        uid = create_user("deleteme", "Pass123!", "OPERATOR")
        delete_user(uid)
        assert get_user_by_id(uid) is None

    def test_clear_must_change_password(self):
        uid = create_user("mcpuser", "Pass123!", "OPERATOR")
        update_user(uid, is_active=1)
        user = get_user_by_username("mcpuser")
        import sqlite3

        with sqlite3.connect(database.DB_FILE) as conn:
            conn.execute("UPDATE users SET must_change_password = 1 WHERE id = ?", (uid,))
            conn.commit()
        clear_must_change_password(uid)
        user = get_user_by_username("mcpuser")
        assert user["must_change_password"] == 0

    def test_get_all_users(self):
        create_user("user1", "Pass1!", "OPERATOR")
        create_user("user2", "Pass2!", "OPERATOR")
        users = get_all_users()
        usernames = [u["username"] for u in users]
        assert "user1" in usernames
        assert "user2" in usernames


class TestSessions:
    def test_create_get_active_session(self, admin_user_id, sample_station_id):
        create_session(admin_user_id, sample_station_id)
        session = get_active_session(sample_station_id)
        assert session is not None
        assert session["user_id"] == admin_user_id
        assert session["station_id"] == sample_station_id

    def test_end_session(self, admin_user_id, sample_station_id):
        sid = create_session(admin_user_id, sample_station_id)
        end_session(sid)
        assert get_active_session(sample_station_id) is None

    def test_expire_stale_sessions(self, admin_user_id, sample_station_id):
        sid = create_session(admin_user_id, sample_station_id)
        import sqlite3

        with sqlite3.connect(database.DB_FILE) as conn:
            conn.execute(
                "UPDATE sessions SET last_heartbeat = datetime('now', '-2 minutes') WHERE id = ?",
                (sid,),
            )
            conn.commit()
        count = expire_stale_sessions(timeout_seconds=60)
        assert count >= 1
        assert get_active_session(sample_station_id) is None

    def test_expire_does_not_affect_recent_sessions(self, admin_user_id, sample_station_id):
        create_session(admin_user_id, sample_station_id)
        count = expire_stale_sessions(timeout_seconds=600)
        assert count == 0
        assert get_active_session(sample_station_id) is not None

    def test_update_session_heartbeat(self, admin_user_id, sample_station_id):
        sid = create_session(admin_user_id, sample_station_id)
        import sqlite3

        with sqlite3.connect(database.DB_FILE) as conn:
            old_hb = conn.execute("SELECT last_heartbeat FROM sessions WHERE id=?", (sid,)).fetchone()[0]
        update_session_heartbeat(sid)
        import sqlite3

        with sqlite3.connect(database.DB_FILE) as conn:
            new_hb = conn.execute("SELECT last_heartbeat FROM sessions WHERE id=?", (sid,)).fetchone()[0]
        assert new_hb >= old_hb

    def test_session_by_id(self, admin_user_id, sample_station_id):
        sid = create_session(admin_user_id, sample_station_id)
        session = get_session_by_id(sid)
        assert session is not None
        assert session["id"] == sid

    def test_end_session_by_id(self, admin_user_id, sample_station_id):
        sid = create_session(admin_user_id, sample_station_id)
        end_session_by_id(sid)
        session = get_session_by_id(sid)
        assert session["status"] == "EXPIRED"


class TestAudit:
    def test_log_and_get_audit(self, admin_user_id):
        log_audit(admin_user_id, "LOGIN", "test details")
        logs = get_audit_logs()
        assert len(logs) >= 1
        assert logs[0]["action"] == "LOGIN"

    def test_get_audit_logs_filter_by_user(self, admin_user_id, operator_user_id):
        log_audit(admin_user_id, "ACTION_A")
        log_audit(operator_user_id, "ACTION_B")
        logs = get_audit_logs(user_id=admin_user_id)
        assert all(l["user_id"] == admin_user_id for l in logs)

    def test_get_audit_logs_filter_by_action(self, admin_user_id):
        log_audit(admin_user_id, "SPECIAL_ACTION")
        logs = get_audit_logs(action="SPECIAL_ACTION")
        assert all(l["action"] == "SPECIAL_ACTION" for l in logs)

    def test_cleanup_audit_log(self, admin_user_id):
        log_audit(admin_user_id, "OLD_ACTION")
        import sqlite3

        with sqlite3.connect(database.DB_FILE) as conn:
            conn.execute("UPDATE audit_log SET created_at = datetime('now', '-100 days') WHERE action = 'OLD_ACTION'")
            conn.commit()
        cleanup_audit_log(days=90)
        logs = get_audit_logs(action="OLD_ACTION")
        assert len(logs) == 0


class TestAnalytics:
    def test_hourly_stats_zero_fill(self, sample_station_id):
        stats = get_hourly_stats()
        assert len(stats) == 24
        assert all(s["hour"] == i for i, s in enumerate(stats))
        assert all(s["count"] == 0 for s in stats)

    def test_hourly_stats_with_data(self, sample_station_id):
        rid = create_record(sample_station_id, "HWB001", "SINGLE")
        update_record_status(rid, "READY")
        stats = get_hourly_stats()
        total = sum(s["count"] for s in stats)
        assert total >= 1

    def test_daily_trend_zero_fill(self):
        trend = get_daily_trend(days=7)
        assert len(trend) == 7
        assert all("date" in d and "count" in d for d in trend)

    def test_daily_trend_custom_days(self):
        trend = get_daily_trend(days=14)
        assert len(trend) == 14

    def test_stations_comparison(self, sample_station_id):
        sid1 = add_station(
            {
                "name": "Comp1",
                "ip_camera_1": "10.0.0.1",
                "ip_camera_2": "",
                "safety_code": "X",
                "camera_mode": "SINGLE",
                "camera_brand": "imou",
                "mac_address": "",
            }
        )
        rid = create_record(sid1, "COMP-WB", "SINGLE")
        update_record_status(rid, "READY")
        comparison = get_stations_comparison()
        assert len(comparison) >= 1
        assert any(c["station_name"] == "Comp1" for c in comparison)


class TestTokenRevocation:
    def test_revoke_check_jti(self):
        revoke_jti("test_jti_123", 9999999999.0)
        assert is_jti_revoked("test_jti_123") is True

    def test_non_revoked_jti(self):
        assert is_jti_revoked("never_revoked_jti") is False

    def test_duplicate_revoke_no_error(self):
        revoke_jti("dup_jti", 9999999999.0)
        revoke_jti("dup_jti", 9999999999.0)
        assert is_jti_revoked("dup_jti") is True


import database
