import os
import sys
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import network
import database


# ---------------------------------------------------------------------------
# validate_mac
# ---------------------------------------------------------------------------


class TestValidateMac:
    """Tests for network.validate_mac()."""

    def test_valid_colon_format(self):
        assert network.validate_mac("AA:BB:CC:DD:EE:FF") is True

    def test_valid_dash_format(self):
        assert network.validate_mac("aa-bb-cc-dd-ee-ff") is True

    def test_valid_dot_cisco_format(self):
        assert network.validate_mac("aabb.ccdd.eeff") is True

    def test_valid_no_separator(self):
        assert network.validate_mac("AABBCCDDEEFF") is True

    def test_invalid_empty(self):
        assert network.validate_mac("") is False

    def test_invalid_all_zeros(self):
        """All-zero MAC is technically valid hex but semantically useless."""
        assert network.validate_mac("00:00:00:00:00:00") is True

    def test_invalid_too_short(self):
        assert network.validate_mac("AA:BB:CC") is False

    def test_invalid_garbage(self):
        assert network.validate_mac("not-a-mac!!") is False

    def test_invalid_broadcast(self):
        """Broadcast FF:FF:FF:FF:FF:FF is valid hex (12 F's)."""
        assert network.validate_mac("FF:FF:FF:FF:FF:FF") is True


# ---------------------------------------------------------------------------
# normalize_mac
# ---------------------------------------------------------------------------


class TestNormalizeMac:
    """Tests for network.normalize_mac()."""

    def test_colon_uppercase_passthrough(self):
        assert network.normalize_mac("AA:BB:CC:DD:EE:FF") == "AA:BB:CC:DD:EE:FF"

    def test_dash_to_colon(self):
        assert network.normalize_mac("aa-bb-cc-dd-ee-ff") == "AA:BB:CC:DD:EE:FF"

    def test_dot_cisco_to_colon(self):
        assert network.normalize_mac("aabb.ccdd.eeff") == "AA:BB:CC:DD:EE:FF"

    def test_no_separator_to_colon(self):
        assert network.normalize_mac("AABBCCDDEEFF") == "AA:BB:CC:DD:EE:FF"

    def test_single_digit_octet_zero_padded(self):
        """e.g. 30:24:50:48:9:38 -> 9 becomes 09."""
        assert network.normalize_mac("30:24:50:48:9:38") == "30:24:50:48:09:38"

    def test_mixed_case_uppercased(self):
        assert network.normalize_mac("Aa:Bb:cC:dD:Ee:fF") == "AA:BB:CC:DD:EE:FF"


# ---------------------------------------------------------------------------
# get_local_subnet
# ---------------------------------------------------------------------------


class TestGetLocalSubnet:
    """Tests for network.get_local_subnet()."""

    @patch("network.socket")
    def test_returns_cidr_on_socket_success(self, mock_socket_mod):
        mock_sock = MagicMock()
        mock_sock.getsockname.return_value = ("192.168.10.55", 12345)
        mock_socket_mod.socket.return_value = mock_sock
        mock_socket_mod.AF_INET = 2
        mock_socket_mod.SOCK_DGRAM = 2
        result = network.get_local_subnet()
        assert result == "192.168.10.0/24"

    @patch("network.socket")
    def test_fallback_default_on_failure(self, mock_socket_mod):
        mock_socket_mod.socket.side_effect = Exception("no network")
        mock_socket_mod.gethostname.side_effect = Exception("no hostname")
        mock_socket_mod.gethostbyname.side_effect = Exception("no resolve")
        result = network.get_local_subnet()
        assert result == "192.168.1.0/24"

    @patch("network.socket")
    def test_fallback_hostname_when_socket_fails(self, mock_socket_mod):
        mock_socket_mod.socket.side_effect = Exception("fail")
        mock_socket_mod.gethostname.return_value = "mypc"
        mock_socket_mod.gethostbyname.return_value = "10.0.5.100"
        mock_socket_mod.AF_INET = 2
        mock_socket_mod.SOCK_DGRAM = 2
        result = network.get_local_subnet()
        assert result == "10.0.5.0/24"


# ---------------------------------------------------------------------------
# scan_lan_for_mac / scan_lan_all
# ---------------------------------------------------------------------------


class TestScanLan:
    """Tests for network.scan_lan_for_mac() and scan_lan_all()."""

    def test_invalid_mac_returns_none(self):
        assert network.scan_lan_for_mac("garbage") is None

    @patch("network._parse_arp_table")
    def test_found_in_arp_immediately(self, mock_arp):
        mock_arp.return_value = [
            {"ip": "192.168.1.42", "mac": "AA:BB:CC:DD:EE:FF"},
        ]
        result = network.scan_lan_for_mac("AA:BB:CC:DD:EE:FF")
        assert result == "192.168.1.42"

    @patch("network._ping_host")
    @patch("network._parse_arp_table")
    def test_found_after_sweep(self, mock_arp, mock_ping):
        # First call: not found; second call: found
        mock_arp.side_effect = [
            [],
            [{"ip": "192.168.1.99", "mac": "AA:BB:CC:DD:EE:FF"}],
        ]
        result = network.scan_lan_for_mac("aa-bb-cc-dd-ee-ff", subnet="192.168.1.0/24")
        assert result == "192.168.1.99"

    @patch("network._ping_host")
    @patch("network._parse_arp_table")
    def test_not_found_returns_none(self, mock_arp, mock_ping):
        mock_arp.return_value = []
        result = network.scan_lan_for_mac("AA:BB:CC:DD:EE:FF", subnet="192.168.1.0/24")
        assert result is None

    @patch("network._parse_arp_table")
    def test_case_insensitive_match(self, mock_arp):
        mock_arp.return_value = [
            {"ip": "192.168.1.10", "mac": "AA:BB:CC:DD:EE:FF"},
        ]
        result = network.scan_lan_for_mac("aa:bb:cc:dd:ee:ff")
        assert result == "192.168.1.10"

    @patch("network._parse_arp_table")
    def test_scan_lan_all_returns_entries(self, mock_arp):
        mock_arp.return_value = [
            {"ip": "192.168.1.1", "mac": "00:11:22:33:44:55"},
            {"ip": "192.168.1.2", "mac": "66:77:88:99:AA:BB"},
        ]
        result = network.scan_lan_all()
        assert len(result) == 2
        assert result[0]["ip"] == "192.168.1.1"


# ---------------------------------------------------------------------------
# API endpoints for camera discovery
# ---------------------------------------------------------------------------


class TestDiscoverAPI:
    """Tests for /api/discover-mac and /api/discover/{station_id}."""

    def test_discover_mac_invalid(self, client, admin_headers):
        r = client.get("/api/discover-mac", headers=admin_headers, params={"mac": "bad"})
        assert r.status_code == 200
        assert r.json()["status"] == "error"

    @patch("network.scan_lan_for_mac", return_value="192.168.1.77")
    def test_discover_mac_found(self, mock_scan, client, admin_headers):
        r = client.get(
            "/api/discover-mac",
            headers=admin_headers,
            params={"mac": "AA:BB:CC:DD:EE:FF"},
        )
        assert r.json()["status"] == "found"
        assert r.json()["ip"] == "192.168.1.77"

    @patch("network.scan_lan_for_mac", return_value=None)
    def test_discover_mac_not_found(self, mock_scan, client, admin_headers):
        r = client.get(
            "/api/discover-mac",
            headers=admin_headers,
            params={"mac": "AA:BB:CC:DD:EE:FF"},
        )
        assert r.json()["status"] == "not_found"

    def test_discover_station_not_exist(self, client, admin_headers):
        r = client.get("/api/discover/9999", headers=admin_headers)
        assert r.json()["status"] == "error"

    @patch("network.scan_lan_for_mac", return_value=None)
    def test_discover_station_not_found(self, mock_scan, client, admin_headers, sample_station_id):
        r = client.get(f"/api/discover/{sample_station_id}", headers=admin_headers)
        assert r.json()["status"] == "not_found"

    @patch("network.scan_lan_for_mac", return_value="192.168.1.18")
    def test_discover_station_same_ip(self, mock_scan, client, admin_headers, sample_station_id):
        # Station was created with ip_camera_1="192.168.5.18", mock returns different
        # so let's update station IP to match what mock returns
        database.update_station_ip(sample_station_id, "ip_camera_1", "192.168.1.18")
        r = client.get(f"/api/discover/{sample_station_id}", headers=admin_headers)
        assert r.json()["status"] == "same_ip"

    @patch("network.scan_lan_for_mac", return_value="192.168.1.200")
    def test_discover_station_new_ip(self, mock_scan, client, admin_headers, sample_station_id):
        r = client.get(f"/api/discover/{sample_station_id}", headers=admin_headers)
        assert r.json()["status"] == "found"
        assert r.json()["new_ip"] == "192.168.1.200"
        assert r.json()["old_ip"] == "192.168.5.18"

    def test_discover_station_no_mac(self, client, admin_headers):
        sid = database.add_station(
            {
                "name": "No MAC",
                "ip_camera_1": "10.0.0.1",
                "ip_camera_2": "",
                "safety_code": "",
                "camera_mode": "SINGLE",
                "mac_address": "",
            }
        )
        r = client.get(f"/api/discover/{sid}", headers=admin_headers)
        assert r.json()["status"] == "error"
        assert "MAC" in r.json()["message"]

    def test_discover_mac_requires_auth(self, client):
        r = client.get("/api/discover-mac", params={"mac": "AA:BB:CC:DD:EE:FF"})
        assert r.status_code == 401

    def test_discover_station_requires_auth(self, client, sample_station_id):
        r = client.get(f"/api/discover/{sample_station_id}")
        assert r.status_code == 401
