import os
import sys
import pytest
from unittest.mock import patch, MagicMock, call

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cloud_sync
import database


class TestS3Upload:
    """Tests for upload_to_s3 function."""

    @patch("cloud_sync.boto3.client")
    def test_s3_upload_success(self, mock_boto_client):
        """Verify S3 upload_file called with correct parameters on success."""
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3

        result = cloud_sync.upload_to_s3(
            file_path="/recordings/backup.zip",
            endpoint="https://s3.example.com",
            access_key="AKIA_TEST",
            secret_key="SECRET_TEST",
            bucket_name="vpack-backup",
        )

        assert result is True
        mock_boto_client.assert_called_once_with(
            "s3",
            endpoint_url="https://s3.example.com",
            aws_access_key_id="AKIA_TEST",
            aws_secret_access_key="SECRET_TEST",
        )
        mock_s3.upload_file.assert_called_once_with(
            "/recordings/backup.zip", "vpack-backup", "backup.zip"
        )

    @patch("cloud_sync.boto3.client")
    def test_s3_upload_invalid_credentials(self, mock_boto_client):
        """NoCredentialsError should be caught and re-raised as generic Exception."""
        from botocore.exceptions import NoCredentialsError

        mock_s3 = MagicMock()
        mock_s3.upload_file.side_effect = NoCredentialsError()
        mock_boto_client.return_value = mock_s3

        with pytest.raises(Exception, match="Sai thông tin S3 Credentials"):
            cloud_sync.upload_to_s3(
                file_path="/recordings/backup.zip",
                endpoint="https://s3.example.com",
                access_key="BAD_KEY",
                secret_key="BAD_SECRET",
                bucket_name="vpack-backup",
            )

    @patch("cloud_sync.boto3.client")
    def test_s3_upload_generic_exception(self, mock_boto_client):
        """Other S3 errors should be caught and re-raised with descriptive message."""
        mock_s3 = MagicMock()
        mock_s3.upload_file.side_effect = ConnectionError("Network unreachable")
        mock_boto_client.return_value = mock_s3

        with pytest.raises(Exception, match="Lỗi S3"):
            cloud_sync.upload_to_s3(
                file_path="/recordings/backup.zip",
                endpoint="https://s3.example.com",
                access_key="KEY",
                secret_key="SECRET",
                bucket_name="vpack-backup",
            )


class TestGDriveUpload:
    """Tests for upload_to_gdrive function."""

    @patch("cloud_sync.MediaFileUpload")
    @patch("cloud_sync.build")
    @patch("cloud_sync._get_gdrive_creds")
    @patch("os.path.exists", return_value=True)
    def test_gdrive_upload_success(self, mock_exists, mock_get_creds, mock_build, mock_media):
        """Verify Google Drive upload creates file with correct metadata."""
        mock_creds = MagicMock()
        mock_get_creds.return_value = mock_creds

        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_request = MagicMock()
        mock_request.next_chunk.return_value = (None, {"id": "gdrive_file_123"})
        mock_service.files().create.return_value = mock_request

        mock_media_instance = MagicMock()
        mock_media.return_value = mock_media_instance

        result = cloud_sync.upload_to_gdrive(
            "/recordings/backup.zip", folder_id="folder_xyz"
        )

        assert result is True
        mock_get_creds.assert_called_once()

    @patch("os.path.exists", return_value=False)
    def test_gdrive_upload_missing_credentials(self, mock_exists):
        """Missing credentials.json should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="credentials.json"):
            cloud_sync.upload_to_gdrive("/recordings/backup.zip")


class TestProcessCloudSync:
    """Tests for process_cloud_sync orchestration function."""

    @patch("cloud_sync.telegram_bot.send_telegram_message")
    @patch("cloud_sync.get_setting")
    def test_provider_none_raises_exception(self, mock_get_setting, mock_tg):
        """When CLOUD_PROVIDER is NONE, process_cloud_sync should raise exception."""
        mock_get_setting.return_value = "NONE"

        with pytest.raises(Exception, match="chưa cấu hình"):
            cloud_sync.process_cloud_sync()

        mock_tg.assert_not_called()

    @patch("cloud_sync.telegram_bot.send_telegram_message")
    @patch("cloud_sync.upload_to_s3")
    @patch("cloud_sync.create_backup_zip")
    @patch("cloud_sync.get_setting")
    def test_s3_sync_success_path(self, mock_get_setting, mock_create_zip, mock_upload_s3, mock_tg):
        """Full S3 sync flow: create zip, upload, mark synced, notify telegram."""
        mock_get_setting.side_effect = lambda key, default=None: {
            "CLOUD_PROVIDER": "S3",
            "S3_ENDPOINT": "https://s3.example.com",
            "S3_ACCESS_KEY": "AK_TEST",
            "S3_SECRET_KEY": "SK_TEST",
            "S3_BUCKET_NAME": "bucket1",
        }.get(key, default)

        tmp_path = os.path.join(os.path.dirname(__file__), "test_backup.zip")
        mock_create_zip.return_value = (tmp_path, [1, 2])

        with patch("os.path.exists", return_value=False):
            cloud_sync.process_cloud_sync()

        mock_upload_s3.assert_called_once_with(
            tmp_path, "https://s3.example.com", "AK_TEST", "SK_TEST", "bucket1"
        )
        mock_tg.assert_called_once()
        tg_msg = mock_tg.call_args[0][0]
        assert "Cloud Sync Hoàn Tất" in tg_msg
        assert "2 video" in tg_msg

    @patch("cloud_sync.telegram_bot.send_telegram_message")
    @patch("cloud_sync.create_backup_zip")
    @patch("cloud_sync.get_setting")
    def test_sync_no_new_videos(self, mock_get_setting, mock_create_zip, mock_tg):
        """When no unsynced videos exist, return early with info message."""
        mock_get_setting.return_value = "S3"
        mock_create_zip.return_value = (None, [])

        result = cloud_sync.process_cloud_sync()

        assert "Không có video" in result
        mock_tg.assert_not_called()
