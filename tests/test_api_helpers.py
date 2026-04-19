import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api import get_rtsp_sub_url, get_rtsp_url


class TestGetRtspUrl:
    def test_imou_default(self):
        url = get_rtsp_url("192.168.1.10", "CODE123", channel=1, brand="imou")
        assert url == "rtsp://admin:CODE123@192.168.1.10:554/cam/realmonitor?channel=1&subtype=0"

    def test_imou_channel_2(self):
        url = get_rtsp_url("192.168.1.10", "CODE123", channel=2, brand="imou")
        assert "channel=2" in url
        assert "subtype=0" in url

    def test_dahua_same_as_imou(self):
        url = get_rtsp_url("10.0.0.1", "SECRET", channel=1, brand="dahua")
        assert url == "rtsp://admin:SECRET@10.0.0.1:554/cam/realmonitor?channel=1&subtype=0"

    def test_tenda(self):
        url = get_rtsp_url("10.0.0.2", "CODE", channel=1, brand="tenda")
        assert url == "rtsp://admin:CODE@10.0.0.2:554/ch=1&subtype=0"

    def test_tenda_channel_2(self):
        url = get_rtsp_url("10.0.0.2", "CODE", channel=2, brand="tenda")
        assert "ch=2" in url

    def test_ezviz(self):
        url = get_rtsp_url("10.0.0.3", "CODE", channel=1, brand="ezviz")
        assert url == "rtsp://admin:CODE@10.0.0.3:554/ch1/main"

    def test_ezviz_channel_2(self):
        url = get_rtsp_url("10.0.0.3", "CODE", channel=2, brand="ezviz")
        assert url == "rtsp://admin:CODE@10.0.0.3:554/ch2/main"

    def test_tapo_channel_1(self):
        url = get_rtsp_url("10.0.0.4", "CODE", channel=1, brand="tapo")
        assert url == "rtsp://admin:CODE@10.0.0.4:554/stream1"

    def test_tapo_channel_2(self):
        url = get_rtsp_url("10.0.0.4", "CODE", channel=2, brand="tapo")
        assert url == "rtsp://admin:CODE@10.0.0.4:554/stream2"

    def test_empty_ip(self):
        assert get_rtsp_url("", "CODE") == ""

    def test_empty_safety_code(self):
        assert get_rtsp_url("1.1.1.1", "") == ""

    def test_none_ip(self):
        assert get_rtsp_url(None, "CODE") == ""

    def test_none_code(self):
        assert get_rtsp_url("1.1.1.1", None) == ""


class TestGetRtspSubUrl:
    def test_imou_sub(self):
        url = get_rtsp_sub_url("192.168.1.10", "CODE123", channel=1, brand="imou")
        assert "subtype=1" in url

    def test_imou_sub_channel_2(self):
        url = get_rtsp_sub_url("192.168.1.10", "CODE123", channel=2, brand="imou")
        assert "channel=2" in url
        assert "subtype=1" in url

    def test_tenda_sub(self):
        url = get_rtsp_sub_url("10.0.0.2", "CODE", channel=1, brand="tenda")
        assert "subtype=1" in url

    def test_ezviz_sub(self):
        url = get_rtsp_sub_url("10.0.0.3", "CODE", channel=1, brand="ezviz")
        assert url == "rtsp://admin:CODE@10.0.0.3:554/ch1/sub"

    def test_ezviz_sub_ch2(self):
        url = get_rtsp_sub_url("10.0.0.3", "CODE", channel=2, brand="ezviz")
        assert url == "rtsp://admin:CODE@10.0.0.3:554/ch2/sub"

    def test_tapo_sub(self):
        url = get_rtsp_sub_url("10.0.0.4", "CODE", channel=1, brand="tapo")
        assert url == "rtsp://admin:CODE@10.0.0.4:554/stream2"

    def test_empty_ip(self):
        assert get_rtsp_sub_url("", "CODE") == ""

    def test_empty_code(self):
        assert get_rtsp_sub_url("1.1.1.1", "") == ""

    def test_main_and_sub_different(self):
        main = get_rtsp_url("1.1.1.1", "CODE", brand="imou")
        sub = get_rtsp_sub_url("1.1.1.1", "CODE", brand="imou")
        assert main != sub
        assert "subtype=0" in main
        assert "subtype=1" in sub
