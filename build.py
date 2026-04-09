# =============================================================================
# V-Pack Monitor - CamDongHang v1.7.0
# Copyright (c) 2024-2026 VDT - Vu Duc Thang (thangvd2)
# All rights reserved. Unauthorized copying or distribution is prohibited.
# =============================================================================

import os
import sys
import subprocess
import shutil

print("=== V-Pack Monitor Builder ===")

# 1. Ensure npm is built
print("\n[1/3] Building Web UI...")
os.chdir("web-ui")
# Dùng npm hoặc npx vite build tuỳ dự án, giả sử chuẩn dùng npm run build
subprocess.run("npm run build", shell=True, check=True)
os.chdir("..")

# 2. Check if PyInstaller is installed
print("\n[2/3] Checking PyInstaller...")
try:
    import PyInstaller
except ImportError:
    print("Installing PyInstaller...")
    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)

# 3. Build executable
print("\n[3/3] Running PyInstaller...")
separator = ";" if os.name == "nt" else ":"
command = [
    sys.executable,
    "-m",
    "PyInstaller",
    "--name",
    "V-Pack-Monitor",
    "--add-data",
    f"web-ui/dist{separator}web-ui/dist",
    "--hidden-import",
    "telebot",
    "--hidden-import",
    "uvicorn",
    "--hidden-import",
    "fastapi",
    "--hidden-import",
    "urllib3",
    "--hidden-import",
    "boto3",
    "--hidden-import",
    "google",
    "--noconsole",
    "--onefile",
    "api.py",
]

subprocess.run(command, check=True)

print("\n=== BUILD HOÀN TẤT ===")
print("File thực thi nằm trong thư mục 'dist' (V-Pack-Monitor.exe hoặc V-Pack-Monitor)")
