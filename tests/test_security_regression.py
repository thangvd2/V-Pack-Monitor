import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database
import auth


class TestSecurityRegression:
    """18 security regression tests guarding against 26 vulnerabilities (Plan #17)
    and 9 bugs (Plan #15)."""

    # --- Test 1: Unauthenticated station access (VULN-02) ---
    def test_get_stations_without_token_returns_401(self, client):
        r = client.get("/api/stations")
        assert r.status_code == 401

    # --- Test 2: Operator cannot see safety_code (VULN-04) ---
    def test_operator_stations_no_safety_code(self, client, operator_headers, sample_station_id):
        r = client.get("/api/stations", headers=operator_headers)
        assert r.status_code == 200
        stations = r.json()["data"]
        assert all("safety_code" not in s for s in stations)

    # --- Test 3: Admin can see safety_code (VULN-04) ---
    def test_admin_stations_has_safety_code(self, client, admin_headers, sample_station_id):
        r = client.get("/api/stations", headers=admin_headers)
        assert r.status_code == 200
        stations = r.json()["data"]
        assert any(s.get("safety_code") for s in stations)

    # --- Test 4: Download endpoint requires authentication (VULN-01) ---
    def test_download_without_token_returns_401(self, client, sample_station_id):
        record_id = database.create_record(sample_station_id, "DL-SEC-001", "SINGLE")
        database.update_record_status(record_id, "READY", video_paths="/fake/path.mp4")
        r = client.get(f"/api/records/{record_id}/download/0")
        assert r.status_code == 401

    # --- Test 5: CORS does not use wildcard origin (VULN-02) ---
    def test_cors_no_wildcard_origin(self, client):
        r = client.options(
            "/api/stations",
            headers={
                "Origin": "http://evil.example.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        acao = r.headers.get("access-control-allow-origin", "")
        assert acao != "*", f"CORS allows wildcard origin: {acao}"

    # --- Test 6: Default admin has must_change_password=1 (VULN-03) ---
    def test_default_admin_must_change_password(self, client):
        user = database.get_user_by_username("admin")
        assert user is not None
        assert user["must_change_password"] == 1

    # --- Test 7: Login returns must_change_password flag (VULN-03) ---
    def test_login_returns_must_change_password_flag(self, client):
        r = client.post("/api/auth/login", json={"username": "admin", "password": "08012011"})
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "success"
        assert "must_change_password" in data["user"]
        assert data["user"]["must_change_password"] == 1

    # --- Test 8: Password shorter than 6 chars rejected (VULN-13) ---
    def test_password_change_too_short_rejected(self, client, admin_headers, admin_user_id):
        database.update_user_password(admin_user_id, "OldPass1!")
        r = client.put(
            "/api/auth/change-password",
            headers=admin_headers,
            json={
                "old_password": "OldPass1!",
                "new_password": "abc",
            },
        )
        assert r.status_code == 422

    # --- Test 9: Session heartbeat by different user returns 403 (VULN-14) ---
    def test_heartbeat_wrong_user_returns_403(self, client, operator_headers, sample_station_id):
        r = client.post(
            "/api/sessions/acquire",
            headers=operator_headers,
            params={"station_id": sample_station_id},
        )
        assert r.json()["status"] == "success"
        session_id = r.json()["session_id"]

        uid2 = database.create_user("hb_intruder", "Pass123!", "OPERATOR")
        tok2 = auth.create_access_token({"sub": str(uid2), "role": "OPERATOR"})
        h2 = {"Authorization": f"Bearer {tok2}"}

        r2 = client.post(
            "/api/sessions/heartbeat",
            headers=h2,
            params={"session_id": session_id},
        )
        assert r2.status_code == 403

    # --- Test 10: Sensitive settings are masked on GET (VULN-10) ---
    def test_settings_sensitive_keys_masked(self, client, admin_headers):
        database.set_setting("S3_SECRET_KEY", "my-s3-secret-key")
        database.set_setting("S3_ACCESS_KEY", "AKIA-ACCESS-KEY")
        database.set_setting("TELEGRAM_BOT_TOKEN", "123456:ABC-telegram-token")
        r = client.get("/api/settings", headers=admin_headers)
        settings = r.json()["data"]
        assert settings.get("S3_SECRET_KEY") == "****"
        assert settings.get("S3_ACCESS_KEY") == "****"
        assert settings.get("TELEGRAM_BOT_TOKEN") == "****"

    # --- Test 11: Sending masked value "****" does not overwrite (VULN-10) ---
    def test_settings_masked_value_preserves_original(self, client, admin_headers):
        database.set_setting("TELEGRAM_BOT_TOKEN", "original-bot-token-value")
        r = client.post(
            "/api/settings",
            headers=admin_headers,
            json={
                "RECORD_KEEP_DAYS": 7,
                "TELEGRAM_BOT_TOKEN": "****",
            },
        )
        assert r.json()["status"] == "success"
        actual = database.get_setting("TELEGRAM_BOT_TOKEN")
        assert actual == "original-bot-token-value"

    # --- Test 12: SQL injection in station name is prevented ---
    def test_sql_injection_station_name_parameterized(self, client, admin_headers):
        injection_name = "Station'; DROP TABLE stations; --"
        r = client.post(
            "/api/stations",
            headers=admin_headers,
            json={
                "name": injection_name,
                "ip_camera_1": "10.0.0.1",
                "ip_camera_2": "",
                "safety_code": "SAFE123",
                "camera_mode": "SINGLE",
            },
        )
        assert r.status_code == 200
        stations = database.get_stations()
        assert any(s["name"] == injection_name for s in stations), "SQL injection may have altered query behavior"
        # Verify stations table still exists and is queryable
        assert len(stations) >= 1

    # --- Test 13: update_station_ip only allows whitelisted fields ---
    def test_update_station_ip_whitelisted_fields_only(self, client, sample_station_id):
        station_before = database.get_station(sample_station_id)
        original_name = station_before["name"]
        database.update_station_ip(sample_station_id, "name", "Hacked Name")
        station_after = database.get_station(sample_station_id)
        assert station_after["name"] == original_name, "update_station_ip accepted a non-whitelisted field"

    # --- Test 14: API error responses do not leak stack traces ---
    def test_error_response_no_stack_trace_leak(self, client, admin_headers):
        r = client.get("/api/records/999999", headers=admin_headers)
        body = r.text.lower()
        assert "traceback" not in body
        assert "exception" not in body or r.status_code == 200

    # --- Test 15: Malformed IP in ping endpoint returns reachable=False ---
    def test_ping_malformed_ip_returns_false(self, client, admin_headers):
        r = client.get("/api/ping", headers=admin_headers, params={"ip": "999.999.999.999"})
        assert r.status_code == 400
        assert r.json()["status"] == "error"

    # --- Test 16: Oversized barcode handled gracefully (max_length=200) ---
    def test_scan_oversized_barcode_rejected(self, client, operator_headers, sample_station_id):
        client.post(
            "/api/sessions/acquire",
            headers=operator_headers,
            params={"station_id": sample_station_id},
        )
        long_barcode = "A" * 250
        r = client.post(
            "/api/scan",
            headers=operator_headers,
            json={
                "barcode": long_barcode,
                "station_id": sample_station_id,
            },
        )
        assert r.status_code == 422

    # --- Test 17: JWT token with wrong secret fails to decode (Bug #1) ---
    def test_jwt_wrong_secret_decode_fails(self, client):
        import jwt as _jwt

        fake_payload = {
            "sub": "1",
            "role": "ADMIN",
            "jti": "fake123",
            "exp": time.time() + 3600,
        }
        fake_token = _jwt.encode(fake_payload, "wrong-secret-key-12345", algorithm="HS256")
        headers = {"Authorization": f"Bearer {fake_token}"}
        r = client.get("/api/auth/me", headers=headers)
        assert r.status_code == 401

    # --- Test 18: Record timestamps stored as UTC-aware datetime ---
    def test_record_timestamp_stored_correctly(self, client, admin_headers, sample_station_id):
        before = time.time()
        record_id = database.create_record(sample_station_id, "TS-CHECK-001", "SINGLE")
        after = time.time()
        record = database.get_record_by_id(record_id)
        assert record is not None
        recorded_at = record["recorded_at"]
        assert recorded_at is not None
        # Verify the timestamp is a non-empty string representing a valid datetime
        assert len(recorded_at) > 0
        # Parse the timestamp as UTC (matching storage format) and verify it falls within the time window
        from datetime import datetime, timezone

        ts = datetime.fromisoformat(recorded_at).replace(tzinfo=timezone.utc)
        ts_epoch = ts.timestamp()
        assert before - 1 <= ts_epoch <= after + 1, f"Timestamp {recorded_at} outside expected window"
