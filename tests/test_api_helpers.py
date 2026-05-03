import pytest
from api import get_rtsp_sub_url, get_rtsp_url


class TestGetRtspUrl:
    @pytest.mark.parametrize(
        "brand, channel, ip, code, expected",
        [
            (
                "imou",
                1,
                "192.168.1.10",
                "CODE123",
                "rtsp://admin:CODE123@192.168.1.10:554/cam/realmonitor?channel=1&subtype=0",
            ),
            (
                "imou",
                2,
                "192.168.1.10",
                "CODE123",
                "rtsp://admin:CODE123@192.168.1.10:554/cam/realmonitor?channel=2&subtype=0",
            ),
            ("dahua", 1, "10.0.0.1", "SECRET", "rtsp://admin:SECRET@10.0.0.1:554/cam/realmonitor?channel=1&subtype=0"),
            ("tenda", 1, "10.0.0.2", "CODE", "rtsp://admin:CODE@10.0.0.2:554/ch=1&subtype=0"),
            ("tenda", 2, "10.0.0.2", "CODE", "rtsp://admin:CODE@10.0.0.2:554/ch=2&subtype=0"),
            ("ezviz", 1, "10.0.0.3", "CODE", "rtsp://admin:CODE@10.0.0.3:554/ch1/main"),
            ("ezviz", 2, "10.0.0.3", "CODE", "rtsp://admin:CODE@10.0.0.3:554/ch2/main"),
            ("tapo", 1, "10.0.0.4", "CODE", "rtsp://admin:CODE@10.0.0.4:554/stream1"),
            ("tapo", 2, "10.0.0.4", "CODE", "rtsp://admin:CODE@10.0.0.4:554/stream2"),
        ],
        ids=[
            "imou_ch1",
            "imou_ch2",
            "dahua_ch1",
            "tenda_ch1",
            "tenda_ch2",
            "ezviz_ch1",
            "ezviz_ch2",
            "tapo_ch1",
            "tapo_ch2",
        ],
    )
    def test_get_rtsp_url_brands(self, brand, channel, ip, code, expected):
        url = get_rtsp_url(ip, code, channel=channel, brand=brand)
        assert url == expected

    @pytest.mark.parametrize(
        "ip, code",
        [
            ("", "CODE"),
            ("1.1.1.1", ""),
            (None, "CODE"),
            ("1.1.1.1", None),
        ],
        ids=["empty_ip", "empty_code", "none_ip", "none_code"],
    )
    def test_get_rtsp_url_edge_cases(self, ip, code):
        assert get_rtsp_url(ip, code) == ""


class TestGetRtspSubUrl:
    @pytest.mark.parametrize(
        "brand, channel, ip, code, expected",
        [
            (
                "imou",
                1,
                "192.168.1.10",
                "CODE123",
                "rtsp://admin:CODE123@192.168.1.10:554/cam/realmonitor?channel=1&subtype=1",
            ),
            (
                "imou",
                2,
                "192.168.1.10",
                "CODE123",
                "rtsp://admin:CODE123@192.168.1.10:554/cam/realmonitor?channel=2&subtype=1",
            ),
            ("tenda", 1, "10.0.0.2", "CODE", "rtsp://admin:CODE@10.0.0.2:554/ch=1&subtype=1"),
            ("ezviz", 1, "10.0.0.3", "CODE", "rtsp://admin:CODE@10.0.0.3:554/ch1/sub"),
            ("ezviz", 2, "10.0.0.3", "CODE", "rtsp://admin:CODE@10.0.0.3:554/ch2/sub"),
            ("tapo", 1, "10.0.0.4", "CODE", "rtsp://admin:CODE@10.0.0.4:554/stream2"),
        ],
        ids=[
            "imou_sub_ch1",
            "imou_sub_ch2",
            "tenda_sub_ch1",
            "ezviz_sub_ch1",
            "ezviz_sub_ch2",
            "tapo_sub_ch1",
        ],
    )
    def test_get_rtsp_sub_url_brands(self, brand, channel, ip, code, expected):
        url = get_rtsp_sub_url(ip, code, channel=channel, brand=brand)
        assert url == expected

    @pytest.mark.parametrize(
        "ip, code",
        [
            ("", "CODE"),
            ("1.1.1.1", ""),
        ],
        ids=["empty_ip", "empty_code"],
    )
    def test_get_rtsp_sub_url_edge_cases(self, ip, code):
        assert get_rtsp_sub_url(ip, code) == ""

    def test_main_and_sub_different(self):
        main = get_rtsp_url("1.1.1.1", "CODE", brand="imou")
        sub = get_rtsp_sub_url("1.1.1.1", "CODE", brand="imou")
        assert main != sub
        assert "subtype=0" in main
        assert "subtype=1" in sub
