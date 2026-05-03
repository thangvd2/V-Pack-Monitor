"""Tests for Plan #21 Phase 4: get_records_v2() + updated /api/records endpoint.

Covers FTS5 search, pagination, date range, status filter, sorting, and API response format.
"""

from datetime import date

import database
import pytest


def _create_test_records(station_id, count, prefix="WB"):
    """Create count READY records for testing pagination."""
    ids = []
    for i in range(count):
        rid = database.create_record(station_id, f"{prefix}{i:04d}", "SINGLE")
        database.update_record_status(rid, "READY")
        ids.append(rid)
    return ids


# ---------------------------------------------------------------------------
# Group 1: FTS5 Search
# ---------------------------------------------------------------------------
@pytest.mark.usefixtures("isolate_db")
class TestFTS5Search:
    def test_fts5_exact_match(self, sample_station_id):
        rid = database.create_record(sample_station_id, "SPXVN123456", "SINGLE")
        database.update_record_status(rid, "READY")
        result = database.get_records_v2(search="SPXVN123456")
        assert result["total"] >= 1
        codes = [r["waybill_code"] for r in result["records"]]
        assert "SPXVN123456" in codes

    def test_fts5_prefix_match(self, sample_station_id):
        rid = database.create_record(sample_station_id, "SPXVN123456", "SINGLE")
        database.update_record_status(rid, "READY")
        result = database.get_records_v2(search="SPXVN")
        assert result["total"] >= 1
        codes = [r["waybill_code"] for r in result["records"]]
        assert "SPXVN123456" in codes

    def test_fts5_no_match(self, sample_station_id):
        rid = database.create_record(sample_station_id, "SPXVN123456", "SINGLE")
        database.update_record_status(rid, "READY")
        result = database.get_records_v2(search="ZZZZZ")
        assert result["total"] == 0
        assert result["records"] == []

    def test_fts5_special_chars_escaped(self, sample_station_id):
        rid = database.create_record(sample_station_id, "SPX-VN-123", "SINGLE")
        database.update_record_status(rid, "READY")
        result = database.get_records_v2(search="SPX-VN")
        assert result["total"] >= 1
        codes = [r["waybill_code"] for r in result["records"]]
        assert "SPX-VN-123" in codes

    def test_fts5_multiple_results(self, sample_station_id):
        for code in ["SPXVN001", "SPXVN002", "SPXVN003"]:
            rid = database.create_record(sample_station_id, code, "SINGLE")
            database.update_record_status(rid, "READY")
        result = database.get_records_v2(search="SPXVN")
        assert result["total"] >= 3

    def test_fts5_search_with_station_filter(self):
        sid1 = database.add_station(
            {
                "name": "Station-A",
                "ip_camera_1": "10.0.0.10",
                "ip_camera_2": "",
                "safety_code": "SA",
                "camera_mode": "SINGLE",
                "camera_brand": "imou",
                "mac_address": "",
            }
        )
        sid2 = database.add_station(
            {
                "name": "Station-B",
                "ip_camera_1": "10.0.0.11",
                "ip_camera_2": "",
                "safety_code": "SB",
                "camera_mode": "SINGLE",
                "camera_brand": "imou",
                "mac_address": "",
            }
        )
        rid1 = database.create_record(sid1, "SPXVN-AAA", "SINGLE")
        database.update_record_status(rid1, "READY")
        rid2 = database.create_record(sid2, "SPXVN-BBB", "SINGLE")
        database.update_record_status(rid2, "READY")

        result = database.get_records_v2(search="SPXVN", station_id=sid1)
        assert result["total"] >= 1
        codes = [r["waybill_code"] for r in result["records"]]
        assert "SPXVN-AAA" in codes
        assert "SPXVN-BBB" not in codes


# ---------------------------------------------------------------------------
# Group 1b: Trigram Substring Search (the key improvement over unicode61)
# ---------------------------------------------------------------------------
@pytest.mark.usefixtures("isolate_db")
class TestTrigramSubstringSearch:
    """Verify that trigram tokenizer supports substring search, not just prefix."""

    def test_substring_middle(self, sample_station_id):
        """Search '123456' in 'SPXVN123456789' — middle substring."""
        rid = database.create_record(sample_station_id, "SPXVN123456789", "SINGLE")
        database.update_record_status(rid, "READY")
        result = database.get_records_v2(search="123456")
        assert result["total"] >= 1
        codes = [r["waybill_code"] for r in result["records"]]
        assert "SPXVN123456789" in codes

    def test_substring_trailing(self, sample_station_id):
        """Search '789' in 'SPXVN123456789' — trailing substring."""
        rid = database.create_record(sample_station_id, "SPXVN123456789", "SINGLE")
        database.update_record_status(rid, "READY")
        result = database.get_records_v2(search="789")
        assert result["total"] >= 1
        codes = [r["waybill_code"] for r in result["records"]]
        assert "SPXVN123456789" in codes

    def test_substring_cross_segment(self, sample_station_id):
        """Search 'VN123' in 'SPXVN123456789' — cross letter-digit boundary."""
        rid = database.create_record(sample_station_id, "SPXVN123456789", "SINGLE")
        database.update_record_status(rid, "READY")
        result = database.get_records_v2(search="VN123")
        assert result["total"] >= 1
        codes = [r["waybill_code"] for r in result["records"]]
        assert "SPXVN123456789" in codes

    def test_substring_multiple_records(self, sample_station_id):
        """Substring search finds all matching records."""
        for code in ["SPXVN123456789", "SPXVN987654321", "GHN111222333"]:
            rid = database.create_record(sample_station_id, code, "SINGLE")
            database.update_record_status(rid, "READY")
        result = database.get_records_v2(search="SPXVN")
        assert result["total"] >= 2
        codes = [r["waybill_code"] for r in result["records"]]
        assert "SPXVN123456789" in codes
        assert "SPXVN987654321" in codes

    def test_short_query_falls_back_to_like(self, sample_station_id):
        """Queries < 3 chars fall back to LIKE (trigram can't index these)."""
        rid = database.create_record(sample_station_id, "SPXVN123", "SINGLE")
        database.update_record_status(rid, "READY")
        # 2-char search should still work via LIKE fallback
        result = database.get_records_v2(search="VN")
        assert result["total"] >= 1
        codes = [r["waybill_code"] for r in result["records"]]
        assert "SPXVN123" in codes

    def test_short_query_single_char(self, sample_station_id):
        """Single char search still works via LIKE fallback."""
        rid = database.create_record(sample_station_id, "SPXVN123", "SINGLE")
        database.update_record_status(rid, "READY")
        result = database.get_records_v2(search="X")
        assert result["total"] >= 1


# ---------------------------------------------------------------------------
# Group 2: Pagination
# ---------------------------------------------------------------------------
@pytest.mark.usefixtures("isolate_db")
class TestPagination:
    def test_pagination_default(self, sample_station_id):
        _create_test_records(sample_station_id, 25)
        result = database.get_records_v2()
        assert len(result["records"]) == 20
        assert result["has_more"] is True
        assert result["page"] == 1
        assert result["total"] == 25

    def test_pagination_page_2(self, sample_station_id):
        _create_test_records(sample_station_id, 25)
        result = database.get_records_v2(page=2)
        assert len(result["records"]) == 5
        assert result["has_more"] is False
        assert result["page"] == 2

    def test_pagination_custom_limit(self, sample_station_id):
        _create_test_records(sample_station_id, 25)
        result = database.get_records_v2(limit=5)
        assert len(result["records"]) == 5
        assert result["total_pages"] == 5
        assert result["limit"] == 5

    def test_pagination_beyond_total(self, sample_station_id):
        _create_test_records(sample_station_id, 5)
        result = database.get_records_v2(page=100)
        assert result["records"] == []
        assert result["has_more"] is False
        assert result["total"] == 5

    def test_pagination_limit_clamped_max(self, sample_station_id):
        _create_test_records(sample_station_id, 150)
        result = database.get_records_v2(limit=999)
        assert result["limit"] == 100
        assert len(result["records"]) == 100

    def test_pagination_limit_clamped_min(self, sample_station_id):
        _create_test_records(sample_station_id, 5)
        result = database.get_records_v2(limit=-1)
        assert result["limit"] == 1
        assert len(result["records"]) == 1


# ---------------------------------------------------------------------------
# Group 3: Date Range Filter
# ---------------------------------------------------------------------------
@pytest.mark.usefixtures("isolate_db")
class TestDateRange:
    def test_date_from_filter(self, sample_station_id):
        rid = database.create_record(sample_station_id, "DATE-001", "SINGLE")
        database.update_record_status(rid, "READY")
        today = date.today().isoformat()
        result = database.get_records_v2(date_from=today)
        assert result["total"] >= 1
        codes = [r["waybill_code"] for r in result["records"]]
        assert "DATE-001" in codes

    def test_date_to_filter(self, sample_station_id):
        rid = database.create_record(sample_station_id, "DATE-002", "SINGLE")
        database.update_record_status(rid, "READY")
        yesterday = date.fromordinal(date.today().toordinal() - 1).isoformat()
        result = database.get_records_v2(date_to=yesterday)
        # All records are from today, so date_to=yesterday should return 0
        assert result["total"] == 0

    def test_date_range_both(self, sample_station_id):
        rid = database.create_record(sample_station_id, "DATE-003", "SINGLE")
        database.update_record_status(rid, "READY")
        today = date.today().isoformat()
        result = database.get_records_v2(date_from=today, date_to=today)
        assert result["total"] >= 1
        codes = [r["waybill_code"] for r in result["records"]]
        assert "DATE-003" in codes

    def test_date_from_invalid_format(self, sample_station_id):
        rid = database.create_record(sample_station_id, "DATE-004", "SINGLE")
        database.update_record_status(rid, "READY")
        result = database.get_records_v2(date_from="not-a-date")
        # Invalid date string won't match any SQLite date comparison
        assert result["total"] == 0

    def test_date_range_empty_results(self, sample_station_id):
        rid = database.create_record(sample_station_id, "DATE-005", "SINGLE")
        database.update_record_status(rid, "READY")
        result = database.get_records_v2(date_from="2099-01-01")
        assert result["total"] == 0
        assert result["records"] == []


# ---------------------------------------------------------------------------
# Group 4: Status Filter
# ---------------------------------------------------------------------------
@pytest.mark.usefixtures("isolate_db")
class TestStatusFilter:
    def test_status_filter_ready(self, sample_station_id):
        rid = database.create_record(sample_station_id, "STATUS-001", "SINGLE")
        database.update_record_status(rid, "READY")
        result = database.get_records_v2(status="READY")
        assert result["total"] >= 1
        for rec in result["records"]:
            assert rec["status"] == "READY"

    def test_status_filter_recording(self, sample_station_id):
        rid = database.create_record(sample_station_id, "STATUS-002", "SINGLE")
        # Don't update — stays RECORDING
        assert database.get_record_by_id(rid)["status"] == "RECORDING"
        result = database.get_records_v2(status="RECORDING")
        assert result["total"] >= 1
        for rec in result["records"]:
            assert rec["status"] == "RECORDING"

    def test_status_filter_no_match(self, sample_station_id):
        rid = database.create_record(sample_station_id, "STATUS-003", "SINGLE")
        database.update_record_status(rid, "READY")
        result = database.get_records_v2(status="FAILED")
        assert result["total"] == 0
        assert result["records"] == []


# ---------------------------------------------------------------------------
# Group 5: Sorting
# ---------------------------------------------------------------------------
@pytest.mark.usefixtures("isolate_db")
class TestSorting:
    def test_sort_by_recorded_at_desc(self, sample_station_id):
        _create_test_records(sample_station_id, 5, prefix="SORT")
        result = database.get_records_v2(sort_by="recorded_at", sort_order="desc")
        records = result["records"]
        for i in range(len(records) - 1):
            assert records[i]["recorded_at"] >= records[i + 1]["recorded_at"]

    def test_sort_by_waybill_code_asc(self, sample_station_id):
        for code in ["ZZZ", "AAA", "MMM"]:
            rid = database.create_record(sample_station_id, code, "SINGLE")
            database.update_record_status(rid, "READY")
        result = database.get_records_v2(sort_by="waybill_code", sort_order="asc")
        codes = [r["waybill_code"] for r in result["records"]]
        # Filter to just our test codes
        test_codes = [c for c in codes if c in ("AAA", "MMM", "ZZZ")]
        assert test_codes == sorted(test_codes)

    def test_sort_invalid_column_defaults(self, sample_station_id):
        _create_test_records(sample_station_id, 3, prefix="SORTINV")
        # Should not crash, defaults to recorded_at
        result = database.get_records_v2(sort_by="invalid_column")
        assert result["total"] >= 3
        assert len(result["records"]) >= 3


# ---------------------------------------------------------------------------
# Group 6: API Endpoint
# ---------------------------------------------------------------------------
@pytest.mark.usefixtures("isolate_db")
class TestAPIRecordsEndpoint:
    def test_api_records_new_format(self, client, admin_headers, sample_station_id):
        rid = database.create_record(sample_station_id, "API-001", "SINGLE")
        database.update_record_status(rid, "READY")
        r = client.get("/api/records", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert "records" in data
        assert "total" in data
        assert "page" in data
        assert "limit" in data
        assert "total_pages" in data
        assert "has_more" in data
        assert data["total"] >= 1
        assert data["page"] == 1

    def test_api_records_pagination_params(self, client, admin_headers, sample_station_id):
        _create_test_records(sample_station_id, 15, prefix="APIPG")
        r = client.get("/api/records?page=2&limit=5", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert len(data["records"]) == 5
        assert data["page"] == 2
        assert data["limit"] == 5
        assert data["total"] == 15

    def test_api_records_date_params(self, client, admin_headers, sample_station_id):
        rid = database.create_record(sample_station_id, "APIDATE-001", "SINGLE")
        database.update_record_status(rid, "READY")
        today = date.today().isoformat()
        r = client.get(
            f"/api/records?date_from={today}&date_to={today}",
            headers=admin_headers,
        )
        assert r.status_code == 200
        data = r.json()
        assert data["total"] >= 1
        codes = [rec["waybill_code"] for rec in data["records"]]
        assert "APIDATE-001" in codes

    def test_api_records_status_param(self, client, admin_headers, sample_station_id):
        rid = database.create_record(sample_station_id, "APISTATUS-001", "SINGLE")
        database.update_record_status(rid, "READY")
        r = client.get("/api/records?status=READY", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        for rec in data["records"]:
            assert rec["status"] == "READY"

    def test_api_records_search_with_pagination(self, client, admin_headers, sample_station_id):
        for code in ["SPXSEARCH01", "SPXSEARCH02", "SPXSEARCH03"]:
            rid = database.create_record(sample_station_id, code, "SINGLE")
            database.update_record_status(rid, "READY")
        r = client.get("/api/records?search=SPXSEARCH&limit=2&page=1", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert len(data["records"]) == 2
        assert data["total"] >= 3
        assert data["has_more"] is True
