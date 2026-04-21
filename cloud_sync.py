# =============================================================================
# V-Pack Monitor - CamDongHang v3.3.1
import logging

logger = logging.getLogger(__name__)

# Copyright (c) 2024-2026 VDT - Vu Duc Thang (thangvd2)
# All rights reserved. Unauthorized copying or distribution is prohibited.
# =============================================================================

import datetime
import os
import threading
import zipfile

# AWS / S3 API
import boto3
from botocore.exceptions import NoCredentialsError

# Google API
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

import database
import telegram_bot
from database import get_setting

# Scope cho Google Drive
SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def _safe_video_path(path, recordings_dir=None):
    """Validate video path is within recordings directory."""
    if not recordings_dir:
        recordings_dir = os.path.abspath("recordings")
    path_abs = os.path.abspath(path)
    return path_abs.startswith(recordings_dir + os.sep) or path_abs == recordings_dir


_gdrive_creds = None
_gdrive_creds_mtime = 0


def _get_gdrive_creds():
    """Cache and reuse GDrive service account credentials."""
    global _gdrive_creds, _gdrive_creds_mtime
    creds_path = "credentials.json"
    try:
        mtime = os.path.getmtime(creds_path)
        if _gdrive_creds and mtime == _gdrive_creds_mtime:
            return _gdrive_creds
        from google.oauth2 import service_account

        _gdrive_creds = service_account.Credentials.from_service_account_file(creds_path, scopes=SCOPES)
        _gdrive_creds_mtime = mtime
        return _gdrive_creds
    except Exception:
        return None


_sync_lock = threading.Lock()


def get_unsynced_records():
    with database.get_connection() as conn:
        cursor = conn.cursor()
        # Lấy file chua sync từ ngày hqua trở về trước (tuỳ ý, hoặc lấy hết).
        # Tạm thời lấy hết.
        cursor.execute("SELECT id, video_paths FROM packing_video WHERE is_synced = 0")
        return cursor.fetchall()


def mark_as_synced(record_ids):
    if not record_ids:
        return
    with database.get_connection() as conn:
        cursor = conn.cursor()
        placeholders = ",".join("?" for _ in record_ids)
        cursor.execute(
            f"UPDATE packing_video SET is_synced = 1 WHERE id IN ({placeholders})",
            record_ids,
        )
        conn.commit()


def create_backup_zip():
    records = get_unsynced_records()
    if not records:
        return None, []

    date_str = datetime.datetime.now().strftime("%Y_%m_%d_%H%M%S")
    zip_filename = f"V-Pack_Backup_{date_str}.zip"
    zip_filepath = os.path.join("recordings", zip_filename)

    synced_ids = []

    # Compress
    with zipfile.ZipFile(zip_filepath, "w", zipfile.ZIP_DEFLATED) as zipf:
        for r_id, video_paths in records:
            added_any = False
            for path in video_paths.split(","):
                path = path.strip()
                if not path or not os.path.exists(path):
                    continue
                if not _safe_video_path(path):
                    logger.warning(f"[CLOUD] Skipping unsafe path: {path}")
                    continue
                zipf.write(path, arcname=os.path.basename(path))
                added_any = True
            if added_any:
                synced_ids.append(r_id)

    if not synced_ids:
        if os.path.exists(zip_filepath):
            os.remove(zip_filepath)
        return None, []

    return zip_filepath, synced_ids


def upload_to_gdrive(file_path, folder_id=None):
    creds_path = "credentials.json"
    if not os.path.exists(creds_path):
        raise FileNotFoundError("Chưa cấu hình File credentials.json cho Google Drive!")

    creds = _get_gdrive_creds()
    if not creds:
        raise Exception("Không thể tải Google Drive credentials.")
    service = build("drive", "v3", credentials=creds)

    file_metadata = {"name": os.path.basename(file_path)}
    if folder_id:
        file_metadata["parents"] = [folder_id]

    media = MediaFileUpload(file_path, mimetype="application/zip", resumable=True)
    request = service.files().create(body=file_metadata, media_body=media, fields="id")

    response = None
    while response is None:
        status, response = request.next_chunk()
        # Có thể in ra % progress nếu muốn console
        if status:
            logger.info(f"Uploading... {int(status.progress() * 100)}%")

    logger.info(f"Upload Google Drive Hoàn Tất: File ID {response.get('id')}")
    return True


def upload_to_s3(file_path, endpoint, access_key, secret_key, bucket_name):
    s3_client = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )
    file_name = os.path.basename(file_path)
    try:
        s3_client.upload_file(file_path, bucket_name, file_name)
        logger.info(f"Upload S3 Hoàn Tất: {file_name}")
        return True
    except NoCredentialsError:
        raise Exception("Sai thông tin S3 Credentials")
    except Exception as e:
        raise Exception(f"Lỗi S3: {str(e)}")


def process_cloud_sync():
    """Được gọi thông qua API Thủ công"""
    if not _sync_lock.acquire(blocking=False):
        return {"status": "error", "message": "Cloud sync already in progress."}
    try:
        return _process_cloud_sync_inner()
    finally:
        _sync_lock.release()


def _process_cloud_sync_inner():
    provider = get_setting("CLOUD_PROVIDER", "NONE")

    if provider == "NONE":
        raise Exception("Bạn chưa cấu hình Lát Cắt Đám Mây (Google Drive / S3) trong mục Cài Đặt!")

    zip_path, synced_ids = create_backup_zip()

    if not zip_path:
        return "Không có video mới nào cần Đồng Bộ!"

    try:
        if provider == "GDRIVE":
            folder_id = get_setting("GDRIVE_FOLDER_ID")
            upload_to_gdrive(zip_path, folder_id)
        elif provider == "S3":
            endpoint = get_setting("S3_ENDPOINT")
            access = get_setting("S3_ACCESS_KEY")
            secret = get_setting("S3_SECRET_KEY")
            bucket = get_setting("S3_BUCKET_NAME")
            if not all([endpoint, access, secret, bucket]):
                raise Exception("Thiếu thông tin S3!")
            upload_to_s3(zip_path, endpoint, access, secret, bucket)

        # Thành công: Cập nhật CSDL
        mark_as_synced(synced_ids)

        # Dọn file Zip để tránh làm tràn ổ cứng
        # Note: Only the backup zip is deleted. Original video files remain on disk.
        if os.path.exists(zip_path):
            os.remove(zip_path)

        success_msg = f"Đã sao lưu {len(synced_ids)} video đơn hàng lên {provider} thành công!"
        telegram_bot.send_telegram_message(f"✅ <b>Cloud Sync Hoàn Tất</b>\n{success_msg}")
        return success_msg
    except Exception as e:
        # Nếu thất bại, xóa zip và văng lỗi ra UI
        if os.path.exists(zip_path):
            os.remove(zip_path)
        err_msg = str(e)
        telegram_bot.send_telegram_message(f"❌ <b>Cloud Sync Thất Bại</b>\nLỗi: {err_msg}")
        raise e
