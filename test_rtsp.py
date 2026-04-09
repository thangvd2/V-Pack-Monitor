#!/usr/bin/env python3
# =============================================================================
# V-Pack Monitor - CamDongHang v1.6.0
# Copyright (c) 2024-2026 VDT - Vu Duc Thang (thangvd2)
# All rights reserved. Unauthorized copying or distribution is prohibited.
# =============================================================================

"""
Cong cu kiem tra ket noi RTSP Camera.
Cach dung: python test_rtsp.py <IP> <SAFETY_CODE> [BRAND]

Vi du:
  python test_rtsp.py 192.168.1.10 L238AA52
  python test_rtsp.py 192.168.1.10 L238AA52 dahua
  python test_rtsp.py 192.168.1.10 L238AA52 tenda
  python test_rtsp.py 192.168.1.10 L238AA52 ezviz
  python test_rtsp.py 192.168.1.10 L238AA52 tapo
"""

import os
import sys
import time
import socket

os.environ["OPENCV_LOG_LEVEL"] = "ERROR"
import cv2


BRANDS = ["imou", "dahua", "tenda", "ezviz", "tapo"]


def generate_rtsp_urls(ip, code):
    return {
        "Imou/Dahua (ch1)": f"rtsp://admin:{code}@{ip}:554/cam/realmonitor?channel=1&subtype=0",
        "Imou/Dahua (ch2)": f"rtsp://admin:{code}@{ip}:554/cam/realmonitor?channel=2&subtype=0",
        "Tenda (ch1)": f"rtsp://admin:{code}@{ip}:554/ch=1&subtype=0",
        "Tenda (ch2)": f"rtsp://admin:{code}@{ip}:554/ch=2&subtype=0",
        "EZVIZ (ch1)": f"rtsp://admin:{code}@{ip}:554/ch1/main",
        "EZVIZ (ch2)": f"rtsp://admin:{code}@{ip}:554/ch2/main",
        "Tapo (stream1)": f"rtsp://admin:{code}@{ip}:554/stream1",
        "Tapo (stream2)": f"rtsp://admin:{code}@{ip}:554/stream2",
    }


def check_tcp(ip, port=554, timeout=3):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((ip, port))
        s.close()
        return True
    except Exception:
        return False


def test_rtsp(url, timeout=10):
    cap = cv2.VideoCapture(url)
    cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, timeout * 1000)
    cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, timeout * 1000)
    success, frame = cap.read()
    cap.release()
    if success and frame is not None:
        h, w = frame.shape[:2]
        return True, f"{w}x{h}"
    return False, ""


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    ip = sys.argv[1]
    code = sys.argv[2]
    brand_filter = sys.argv[3].lower() if len(sys.argv) > 3 else None

    if brand_filter and brand_filter not in BRANDS:
        print(f"Brand khong ho tro: {brand_filter}")
        print(f"Cac brand ho tro: {', '.join(BRANDS)}")
        sys.exit(1)

    print(f"{'=' * 50}")
    print(f" RTSP Camera Connection Tester")
    print(f"{'=' * 50}")
    print(f"IP: {ip}")
    print(f"Safety Code: {code}")
    if brand_filter:
        print(f"Brand filter: {brand_filter}")
    print()

    print(f"[1/2] Kiem tra TCP port 554...")
    if check_tcp(ip, 554):
        print(f"      Port 554 MO - Thiet bi phan hoi")
    else:
        print(f"      Port 554 DONG - Khong the ket noi!")
        print(f"      Kiem tra lai IP va dam bao camera dang bat.")
        sys.exit(1)

    print()
    print(f"[2/2] Thu ket noi RTSP...")
    print()

    urls = generate_rtsp_urls(ip, code)

    for label, url in urls.items():
        if brand_filter:
            brand_name = label.split(" ")[0].lower()
            if brand_filter not in brand_name and not (
                brand_filter == "dahua" and "imou" in brand_name
            ):
                continue

        print(f"  Thu: {label}")
        print(f"  URL: {url}")
        ok, info = test_rtsp(url)
        if ok:
            print(f"  => THANH CONG! ({info})")
        else:
            print(f"  => That bai")
        print()

    print(f"{'=' * 50}")
    print(" Hoan tat.")


if __name__ == "__main__":
    main()
