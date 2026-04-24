import os
import sqlite3

import pytest

import database
from database import (
    add_station,
    cleanup_old_records,
    create_record,
    create_user,
    get_hourly_stats,
    get_record_by_id,
    get_records_v2,
    get_setting,
    get_station,
    get_user_by_username,
    set_settings,
    update_record_status,
    update_station_ip,
)


class TestSQLInjectionGuards:
    """Tests verifying SQL injection prevention mechanisms."""

    def test_get_records_sql_injection_search(self, sample_station_id):
        """Parameterized query treats injection string as literal text — no table dropped."""
        create_record(sample_station_id, "NORMAL-WB-001", "SINGLE")

        injection = "'; DROP TABLE packing_video; --"
        results = get_records_v2(search=injection)["records"]

        # Injection string is literal — no waybill matches it
        assert results == []

        # Table still exists and original data is intact
        all_results = get_records_v2(search="NORMAL")["records"]
        assert len(all_results) == 1
        assert all_results[0]["waybill_code"] == "NORMAL-WB-001"

    def test_update_station_ip_rejects_disallowed_field(self):
        """Allow-list filtering prevents column injection — rejected fields ignored,
        valid fields still update correctly."""
        sid = add_station(
            {
                "name": "Original Name",
                "ip_camera_1": "192.168.1.1",
                "ip_camera_2": "",
                "safety_code": "ABC",
                "camera_mode": "SINGLE",
                "camera_brand": "imou",
                "mac_address": "",
            }
        )

        # Try to inject via a real column name not in allow-list {"ip_camera_1", "ip_camera_2"}
        update_station_ip(sid, "name", "Hacked Name")
        assert get_station(sid)["name"] == "Original Name"

        # Try a fabricated column name
        update_station_ip(sid, "malicious_column", "evil_value")
        assert get_station(sid)["ip_camera_1"] == "192.168.1.1"

        # Valid field still works after rejected attempts
        update_station_ip(sid, "ip_camera_1", "10.0.0.99")
        assert get_station(sid)["ip_camera_1"] == "10.0.0.99"


class TestBoundaryConditions:
    """Tests for boundary and off-by-one conditions."""

    def test_get_records_search_respects_station_filter(self):
        """When search is provided, station_id filter is still applied."""
        sid_a = add_station(
            {
                "name": "Station A",
                "ip_camera_1": "10.0.0.1",
                "ip_camera_2": "",
                "safety_code": "X",
                "camera_mode": "SINGLE",
                "camera_brand": "imou",
                "mac_address": "",
            }
        )
        sid_b = add_station(
            {
                "name": "Station B",
                "ip_camera_1": "10.0.0.2",
                "ip_camera_2": "",
                "safety_code": "Y",
                "camera_mode": "SINGLE",
                "camera_brand": "imou",
                "mac_address": "",
            }
        )

        create_record(sid_a, "COMMON-ALPHA", "SINGLE")
        create_record(sid_b, "COMMON-BETA", "SINGLE")
        create_record(sid_a, "UNIQUE-GAMMA", "SINGLE")

        # search="COMMON" with station_id=sid_a — station_id IS respected
        results = get_records_v2(search="COMMON", station_id=sid_a)["records"]
        waybills = [r["waybill_code"] for r in results]

        assert "COMMON-ALPHA" in waybills  # from station A
        assert "COMMON-BETA" not in waybills  # from station B — station filter is respected

    def test_cleanup_exactly_N_days_old_deleted(self, sample_station_id, tmp_path):
        """Record exactly at the N-day boundary IS deleted (<= comparison)."""
        fake_video = str(tmp_path / "boundary_exact.mp4")
        with open(fake_video, "w") as f:
            f.write("boundary-test")

        rid = create_record(sample_station_id, "BOUNDARY-EXACT", "SINGLE")
        update_record_status(rid, "READY", video_paths=fake_video)

        # Set recorded_at to exactly 7 days ago (UTC, matching storage format)
        with sqlite3.connect(database.DB_FILE) as conn:
            conn.execute(
                "UPDATE packing_video SET recorded_at = datetime('now', '-7 days') WHERE id = ?",
                (rid,),
            )
            conn.commit()

        assert os.path.exists(fake_video)
        cleanup_old_records(days=7)
        assert not os.path.exists(fake_video)
        assert get_record_by_id(rid) is None

    def test_cleanup_less_than_N_days_old_kept(self, sample_station_id):
        """Record at N-1 days should NOT be deleted — off-by-one guard."""
        rid = create_record(sample_station_id, "BOUNDARY-SAFE", "SINGLE")
        update_record_status(rid, "READY")

        # Set recorded_at to 6 days ago (UTC, matching storage format)
        with sqlite3.connect(database.DB_FILE) as conn:
            conn.execute(
                "UPDATE packing_video SET recorded_at = datetime('now', '-6 days') WHERE id = ?",
                (rid,),
            )
            conn.commit()

        cleanup_old_records(days=7)
        assert get_record_by_id(rid) is not None

    def test_cleanup_missing_video_files_graceful(self, sample_station_id):
        """cleanup_old_records should not crash when video files don't exist on disk."""
        nonexistent_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "_nonexistent_",
            "fake_video_xyz.mp4",
        )
        rid = create_record(sample_station_id, "MISSING-FILE-WB", "SINGLE")
        update_record_status(rid, "READY", video_paths=nonexistent_path)

        with sqlite3.connect(database.DB_FILE) as conn:
            conn.execute(
                "UPDATE packing_video SET recorded_at = datetime('now', '-10 days') WHERE id = ?",
                (rid,),
            )
            conn.commit()

        # Must not raise despite missing file
        cleanup_old_records(days=7)
        assert get_record_by_id(rid) is None

    def test_get_hourly_stats_no_records_all_zeros(self):
        """With no records today, all 24 hours should have count 0."""
        stats = get_hourly_stats()
        assert len(stats) == 24
        assert [s["hour"] for s in stats] == list(range(24))
        assert all(s["count"] == 0 for s in stats)


class TestInputLimits:
    """Tests for handling extreme and edge-case inputs."""

    @pytest.mark.parametrize(
        "name, label",
        [
            ("user'; DROP TABLE users; --", "sql injection"),
            ("user with spaces", "spaces"),
            ("Người_dùng", "unicode"),
        ],
        ids=["sql_injection", "spaces", "unicode"],
    )
    def test_create_user_special_characters(self, name, label):
        """Usernames with SQL metacharacters, spaces, and unicode are stored literally
        via parameterized queries — no injection possible."""
        uid = create_user(name, "Password123!", "OPERATOR")
        assert uid is not None, f"Failed to create user ({label}): {name!r}"
        user = get_user_by_username(name)
        assert user is not None, f"Failed to retrieve user ({label}): {name!r}"
        assert user["username"] == name

    def test_create_user_very_long_username_rejected(self):
        """A 300-character username should be rejected by the 50-char limit."""
        long_name = "A" * 300
        with pytest.raises(ValueError, match="Username too long"):
            create_user(long_name, "Password123!", "OPERATOR")

    def test_create_user_at_max_length(self):
        """A 50-character username (max allowed) should be stored successfully."""
        max_name = "A" * 50
        uid = create_user(max_name, "Password123!", "OPERATOR")
        assert uid is not None
        user = get_user_by_username(max_name)
        assert user is not None
        assert len(user["username"]) == 50

    def test_set_settings_large_value(self):
        """A 10KB string value should roundtrip through set_settings / get_setting."""
        large_value = "X" * 10240
        set_settings({"test_large_key": large_value})
        retrieved = get_setting("test_large_key")
        assert retrieved == large_value
        assert len(retrieved) == 10240
