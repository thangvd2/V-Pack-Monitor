# =============================================================================
# V-Pack Monitor - CamDongHang v2.1.0
# Copyright (c) 2024-2026 VDT - Vu Duc Thang (thangvd2)
# All rights reserved. Unauthorized copying or distribution is prohibited.
# =============================================================================

import threading
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
import database
import recorder
import telegram_bot


_executor = None
_lock = threading.Lock()


def _verify_video(filepath):
    if not filepath or not os.path.exists(filepath):
        return False
    if os.path.getsize(filepath) == 0:
        return False
    try:
        cmd = [
            recorder._ffmpeg_bin("ffprobe"),
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "csv=p=0",
            filepath,
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        duration_str = r.stdout.strip()
        if duration_str and float(duration_str) > 0:
            return True
    except Exception:
        pass
    return False


def _decrement_processing(station_id):
    try:
        import api

        count = api._processing_count.get(station_id, 0)
        if count <= 1:
            api._processing_count.pop(station_id, None)
        else:
            api._processing_count[station_id] = count - 1
    except Exception:
        pass


def _notify_sse_safe(station_id, status, record_id):
    try:
        import api

        api.notify_sse(
            "video_status",
            {
                "station_id": station_id,
                "status": status,
                "record_id": record_id,
            },
        )
    except Exception:
        pass


def _process_stop_and_save(record_id, rec, waybill, station_id, save=True):
    try:
        saved_files = rec.stop_recording()

        if not save or not saved_files:
            if not save:
                database.delete_record(record_id)
                _decrement_processing(station_id)
                _notify_sse_safe(station_id, "DELETED", record_id)
                return
            database.update_record_status(record_id, "FAILED")
            _send_failed_alert(
                record_id,
                waybill,
                "FFmpeg không tạo được file video.",
            )
            _decrement_processing(station_id)
            _notify_sse_safe(station_id, "FAILED", record_id)
            return

        all_valid = True
        for f in saved_files:
            if not _verify_video(f):
                all_valid = False
                break

        if all_valid:
            database.update_record_status(record_id, "READY", video_paths=saved_files)
            _decrement_processing(station_id)
            _notify_sse_safe(station_id, "READY", record_id)
        else:
            database.update_record_status(record_id, "FAILED", video_paths=saved_files)
            _send_failed_alert(
                record_id,
                waybill,
                "Video không hợp lệ (ffprobe verify thất bại).",
            )
            _decrement_processing(station_id)
            _notify_sse_safe(station_id, "FAILED", record_id)
    except Exception as e:
        print(f"VideoWorker error for record {record_id}: {e}")
        try:
            database.update_record_status(record_id, "FAILED")
            _send_failed_alert(record_id, waybill, f"Lỗi xử lý video: {e}")
            _decrement_processing(station_id)
            _notify_sse_safe(station_id, "FAILED", record_id)
        except Exception:
            pass


def _send_failed_alert(record_id, waybill, reason):
    try:
        msg = (
            f"\u26a0\ufe0f <b>VIDEO L\u1ed6I</b>\n\n"
            f"\U0001f4e6 M\u00e3 v\u1eadn \u0111\u01a1n: <b>{waybill}</b>\n"
            f"\u274c L\u00fd do: {reason}\n"
            f"\U0001f194 Record ID: {record_id}\n\n"
            f"Vui l\u00f2ng ki\u1ec3m tra h\u1ec7 th\u1ed1ng."
        )
        telegram_bot.send_telegram_message(msg)
    except Exception:
        pass


def submit_stop_and_save(record_id, rec, waybill, station_id, save=True):
    global _executor
    with _lock:
        if _executor is None:
            _executor = ThreadPoolExecutor(max_workers=1)
    _executor.submit(_process_stop_and_save, record_id, rec, waybill, station_id, save)


def shutdown():
    global _executor
    with _lock:
        if _executor:
            _executor.shutdown(wait=True)
            _executor = None
