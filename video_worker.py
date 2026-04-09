# =============================================================================
# V-Pack Monitor - CamDongHang v1.5.0
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


def _process_stop_and_save(record_id, rec, waybill, station_id, save=True):
    try:
        database.update_record_status(record_id, "PROCESSING")
        try:
            import api

            api.notify_sse(
                "video_status",
                {
                    "station_id": station_id,
                    "status": "PROCESSING",
                    "record_id": record_id,
                },
            )
        except Exception:
            pass

        saved_files = rec.stop_recording()

        if not save or not saved_files:
            if not save:
                database.delete_record(record_id)
                try:
                    import api

                    api._processing_stations.discard(station_id)
                    api.active_waybills.pop(station_id, None)
                    api.active_record_ids.pop(station_id, None)
                    api.notify_sse(
                        "video_status",
                        {
                            "station_id": station_id,
                            "status": "DELETED",
                            "record_id": record_id,
                        },
                    )
                except Exception:
                    pass
                return
            database.update_record_status(record_id, "FAILED")
            _send_failed_alert(
                record_id,
                waybill,
                "FFmpeg kh\u00f4ng t\u1ea1o \u0111\u01b0\u1ee3c file video.",
            )
            try:
                import api

                api._processing_stations.discard(station_id)
                api.active_waybills.pop(station_id, None)
                api.active_record_ids.pop(station_id, None)
                api.notify_sse(
                    "video_status",
                    {
                        "station_id": station_id,
                        "status": "FAILED",
                        "record_id": record_id,
                    },
                )
            except Exception:
                pass
            return

        all_valid = True
        for f in saved_files:
            if not _verify_video(f):
                all_valid = False
                break

        if all_valid:
            database.update_record_status(record_id, "READY", video_paths=saved_files)
            try:
                import api

                api._processing_stations.discard(station_id)
                api.active_waybills.pop(station_id, None)
                api.active_record_ids.pop(station_id, None)
                api.notify_sse(
                    "video_status",
                    {
                        "station_id": station_id,
                        "status": "READY",
                        "record_id": record_id,
                    },
                )
            except Exception:
                pass
        else:
            database.update_record_status(record_id, "FAILED", video_paths=saved_files)
            _send_failed_alert(
                record_id,
                waybill,
                "Video kh\u00f4ng h\u1ee3p l\u1ec7 (ffprobe verify th\u1ea5t b\u1ea1i).",
            )
            try:
                import api

                api._processing_stations.discard(station_id)
                api.active_waybills.pop(station_id, None)
                api.active_record_ids.pop(station_id, None)
                api.notify_sse(
                    "video_status",
                    {
                        "station_id": station_id,
                        "status": "FAILED",
                        "record_id": record_id,
                    },
                )
            except Exception:
                pass
    except Exception as e:
        print(f"VideoWorker error for record {record_id}: {e}")
        try:
            database.update_record_status(record_id, "FAILED")
            _send_failed_alert(
                record_id, waybill, f"L\u1ed7i x\u1eed l\u00fd video: {e}"
            )
            try:
                import api

                api._processing_stations.discard(station_id)
                api.active_waybills.pop(station_id, None)
                api.active_record_ids.pop(station_id, None)
                api.notify_sse(
                    "video_status",
                    {
                        "station_id": station_id,
                        "status": "FAILED",
                        "record_id": record_id,
                    },
                )
            except Exception:
                pass
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
            _executor.shutdown(wait=False)
            _executor = None
