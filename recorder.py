# =============================================================================
# V-Pack Monitor - CamDongHang v3.3.1
import logging

logger = logging.getLogger(__name__)

# Copyright (c) 2024-2026 VDT - Vu Duc Thang (thangvd2)
# All rights reserved. Unauthorized copying or distribution is prohibited.
# =============================================================================

import os
import platform
import subprocess
import threading
import time
from datetime import datetime

_MAX_RECORDING_SECONDS = 600


def _ffmpeg_bin(name):
    base = os.path.dirname(os.path.abspath(__file__))
    if platform.system() == "Windows":
        local = os.path.join(base, "bin", "ffmpeg", "bin", name + ".exe")
    else:
        local = os.path.join(base, "bin", "ffmpeg", "bin", name)
    if os.path.exists(local):
        return local
    if platform.system() == "Windows":
        local2 = os.path.join(base, "bin", "ffmpeg", "bin", name)
        if os.path.exists(local2):
            return local2
    return name


_hw_encoder_cache = None


def _detect_hw_encoder():
    global _hw_encoder_cache
    if _hw_encoder_cache is not None:
        return _hw_encoder_cache
    candidates = [
        ("h264_qsv", "-hwaccel qsv"),
        ("h264_nvenc", ""),
        ("h264_amf", ""),
        ("h264_videotoolbox", ""),
    ]
    for enc, extra in candidates:
        try:
            cmd = [_ffmpeg_bin("ffmpeg"), "-hide_banner", "-y"]
            if extra:
                cmd += extra.split()
            cmd += [
                "-f",
                "lavfi",
                "-i",
                "nullsrc=s=256x256:d=0.1",
                "-c:v",
                enc,
                "-f",
                "null",
                "-",
            ]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if r.returncode == 0:
                _hw_encoder_cache = (enc, extra)
                logger.info(f"GPU encoder detected: {enc}")
                return _hw_encoder_cache
        except Exception:
            pass
    _hw_encoder_cache = ("libx264", "")
    logger.info("No GPU encoder found, using libx264 ultrafast")
    return _hw_encoder_cache


def _build_transcode_cmd(input_file, output_file):
    encoder, hw_accel = _detect_hw_encoder()
    cmd = [_ffmpeg_bin("ffmpeg"), "-y"]
    if hw_accel:
        cmd += hw_accel.split()
    cmd += ["-i", input_file]
    if encoder == "libx264":
        cmd += [
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-crf",
            "23",
            "-threads",
            "0",
            "-c:a",
            "copy",
        ]
    elif encoder == "h264_videotoolbox":
        cmd += ["-c:v", encoder, "-b:v", "5M", "-c:a", "copy"]
    else:
        cmd += ["-c:v", encoder, "-c:a", "copy"]
    cmd += ["-movflags", "+faststart", output_file]
    return cmd


def _is_hevc(filepath):
    try:
        r = subprocess.run(
            [
                _ffmpeg_bin("ffprobe"),
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=codec_name",
                "-of",
                "csv=p=0",
                filepath,
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return "hevc" in r.stdout.strip().lower()
    except Exception:
        return False


class CameraRecorder:
    def __init__(self, rtsp_url_1, rtsp_url_2=None, output_dir="recordings", record_mode="SINGLE"):
        self.rtsp_url_1 = rtsp_url_1
        self.rtsp_url_2 = rtsp_url_2 if rtsp_url_2 else rtsp_url_1

        self.output_dir = output_dir
        self.record_mode = record_mode
        self.processes = []
        self.current_files = []
        self._stop_lock = threading.Lock()
        self._stopped = False

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def start_recording(self, waybill_code):
        # Sanitize waybill_code to prevent path traversal
        import re

        safe_code = re.sub(r"[^\w\-.]", "_", waybill_code)
        if not safe_code:
            safe_code = "unknown"
        waybill_code = safe_code

        with self._stop_lock:
            self._stopped = False  # Reset for reuse after stop

        if self.processes:
            self.stop_recording()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.processes = []
        self.current_files = []

        if self.record_mode == "SINGLE":
            filename = f"{waybill_code}_{timestamp}.mp4"
            filepath = os.path.join(self.output_dir, filename)
            tmpfile = filepath + ".tmp.ts"
            self._launch_ffmpeg(
                [
                    "ffmpeg",
                    "-y",
                    "-rtsp_transport",
                    "tcp",
                    "-i",
                    self.rtsp_url_1,
                    "-c:v",
                    "copy",
                    "-c:a",
                    "copy",
                    "-f",
                    "mpegts",
                    "-t",
                    str(_MAX_RECORDING_SECONDS),
                    tmpfile,
                ],
                final_path=filepath,
            )
            self.current_files.append(filepath)

        elif self.record_mode == "DUAL_FILE":
            file1 = os.path.join(self.output_dir, f"{waybill_code}_{timestamp}_Cam1.mp4")
            tmp1 = file1 + ".tmp.ts"
            self._launch_ffmpeg(
                [
                    "ffmpeg",
                    "-y",
                    "-rtsp_transport",
                    "tcp",
                    "-i",
                    self.rtsp_url_1,
                    "-c:v",
                    "copy",
                    "-c:a",
                    "copy",
                    "-f",
                    "mpegts",
                    "-t",
                    str(_MAX_RECORDING_SECONDS),
                    tmp1,
                ],
                final_path=file1,
            )
            self.current_files.append(file1)

            file2 = os.path.join(self.output_dir, f"{waybill_code}_{timestamp}_Cam2.mp4")
            tmp2 = file2 + ".tmp.ts"
            self._launch_ffmpeg(
                [
                    "ffmpeg",
                    "-y",
                    "-rtsp_transport",
                    "tcp",
                    "-i",
                    self.rtsp_url_2,
                    "-c:v",
                    "copy",
                    "-c:a",
                    "copy",
                    "-f",
                    "mpegts",
                    "-t",
                    str(_MAX_RECORDING_SECONDS),
                    tmp2,
                ],
                final_path=file2,
            )
            self.current_files.append(file2)

        elif self.record_mode == "PIP":
            filename = f"{waybill_code}_{timestamp}_PIP.mp4"
            filepath = os.path.join(self.output_dir, filename)
            tmpfile = filepath + ".tmp.ts"

            sys_os = platform.system()
            vcodec = "libx264"
            if sys_os == "Darwin":
                vcodec = "h264_videotoolbox"

            if self.rtsp_url_1 == self.rtsp_url_2:
                command = [
                    "ffmpeg",
                    "-y",
                    "-rtsp_transport",
                    "tcp",
                    "-i",
                    self.rtsp_url_1,
                    "-filter_complex",
                    "[0:v]split=2[main][pip_raw]; [pip_raw]scale=iw/3:-1[pip]; [main][pip]overlay=main_w-overlay_w-10:main_h-overlay_h-10",
                    "-c:v",
                    vcodec,
                    "-b:v",
                    "2000k",
                    "-pix_fmt",
                    "yuv420p",
                    "-c:a",
                    "aac",
                    "-f",
                    "mpegts",
                    "-t",
                    str(_MAX_RECORDING_SECONDS),
                    tmpfile,
                ]
            else:
                command = [
                    "ffmpeg",
                    "-y",
                    "-use_wallclock_as_timestamps",
                    "1",
                    "-rtsp_transport",
                    "tcp",
                    "-i",
                    self.rtsp_url_1,
                    "-use_wallclock_as_timestamps",
                    "1",
                    "-rtsp_transport",
                    "tcp",
                    "-i",
                    self.rtsp_url_2,
                    "-filter_complex",
                    "[1:v]scale=iw/3:-1[pip]; [0:v][pip]overlay=main_w-overlay_w-10:main_h-overlay_h-10",
                    "-c:v",
                    vcodec,
                    "-b:v",
                    "2000k",
                    "-pix_fmt",
                    "yuv420p",
                    "-c:a",
                    "aac",
                    "-f",
                    "mpegts",
                    "-t",
                    str(_MAX_RECORDING_SECONDS),
                    tmpfile,
                ]
            self._launch_ffmpeg(command, final_path=filepath)
            self.current_files.append(filepath)

        logger.info(f"Bat dau ghi hinh ({self.record_mode}) Don hang: {waybill_code}")
        for f in self.current_files:
            logger.info(f"Luu tai: {f}")

        return self.current_files

    def _launch_ffmpeg(self, cmd, final_path=None):
        ffmpeg_path = _ffmpeg_bin("ffmpeg")
        if cmd[0] == "ffmpeg":
            cmd[0] = ffmpeg_path
        p = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self.processes.append({"proc": p, "final_path": final_path})

    def stop_recording(self):
        with self._stop_lock:
            if self._stopped or not self.processes:
                self._stopped = True
                return []
            self._stopped = True

        logger.info("Dang dung ghi hinh va dong goi video...")

        for pinfo in self.processes:
            p = pinfo["proc"]
            try:
                p.stdin.write(b"q\n")
                p.stdin.flush()
            except Exception:
                pass

        for pinfo in self.processes:
            p = pinfo["proc"]
            try:
                p.wait(timeout=30)
            except subprocess.TimeoutExpired:
                try:
                    p.stdin.write(b"q\n")
                    p.stdin.flush()
                except Exception:
                    pass
                try:
                    p.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    p.terminate()
                    try:
                        p.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        p.kill()

        for pinfo in self.processes:
            final_path = pinfo["final_path"]
            if not final_path:
                continue
            ts_path = final_path + ".tmp.ts"
            if not os.path.exists(ts_path):
                continue

            is_hevc = _is_hevc(ts_path)
            transcode_ok = False
            try:
                if is_hevc:
                    cmd = _build_transcode_cmd(ts_path, final_path)
                else:
                    cmd = [
                        _ffmpeg_bin("ffmpeg"),
                        "-y",
                        "-i",
                        ts_path,
                        "-c",
                        "copy",
                        "-movflags",
                        "+faststart",
                        final_path,
                    ]
                subprocess.run(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=120,
                )
                transcode_ok = True
            except Exception as e:
                logger.error(f"[RECORDER] Transcode failed for {final_path}: {e}")
                # Fall through to rename as .FAILED.ts

            if transcode_ok:
                # 3 retries with 1s sleep is intentional for Windows file locking
                for _ in range(3):
                    try:
                        if os.path.exists(ts_path):
                            os.remove(ts_path)
                        break
                    except PermissionError:
                        time.sleep(1)
            else:
                failed_path = final_path + ".FAILED.ts"
                try:
                    if os.path.exists(ts_path) and not os.path.exists(failed_path):
                        os.rename(ts_path, failed_path)
                        logger.error(f"Transcode failed, kept raw TS: {failed_path}")
                except Exception:
                    pass

        self.processes = []

        time.sleep(0.5)

        final_files = []
        for f in self.current_files:
            if os.path.exists(f) and os.path.getsize(f) > 0:
                final_files.append(f)
            elif os.path.exists(f):
                os.remove(f)

        self.current_files = []
        return final_files
