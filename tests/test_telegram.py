import os
import sys
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import telegram_bot


class TestSendMessage:
    """Tests for send_telegram_message function."""

    @patch("telegram_bot._bot", None)
    @patch("requests.post")
    @patch("database.get_setting")
    def test_send_message_success(self, mock_get_setting, mock_post):
        """Successful raw API call returns (True, ...) with correct URL and payload."""
        mock_get_setting.side_effect = lambda key, default="": {
            "TELEGRAM_BOT_TOKEN": "123456:ABC-DEF",
            "TELEGRAM_CHAT_ID": "987654321",
        }.get(key, default)

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Ensure _bot is None so raw API path is taken
        telegram_bot._bot = None

        success, msg = telegram_bot.send_telegram_message("Test alert message")

        assert success is True
        mock_post.assert_called_once()
        call_args = mock_post.call_args

        expected_url = "https://api.telegram.org/bot123456:ABC-DEF/sendMessage"
        assert call_args[0][0] == expected_url

        payload = call_args[1]["json"]
        assert payload["chat_id"] == "987654321"
        assert payload["text"] == "Test alert message"
        assert payload["parse_mode"] == "HTML"

    @patch("database.get_setting")
    def test_send_message_missing_token(self, mock_get_setting):
        """Missing bot token should return (False, ...) without crashing."""
        # Reset cached token so _get_bot_token() re-reads from DB
        telegram_bot._cached_token = None
        telegram_bot._cached_token_time = 0

        mock_get_setting.side_effect = lambda key, default="": {
            "TELEGRAM_BOT_TOKEN": "",
            "TELEGRAM_CHAT_ID": "987654321",
        }.get(key, default)

        success, msg = telegram_bot.send_telegram_message("Test message")

        assert success is False
        assert "Chưa cấu hình" in msg

    @patch("requests.post")
    @patch("database.get_setting")
    def test_send_message_formatting(self, mock_get_setting, mock_post):
        """Verify HTML-formatted message content is passed through correctly."""
        mock_get_setting.side_effect = lambda key, default="": {
            "TELEGRAM_BOT_TOKEN": "TOKEN123",
            "TELEGRAM_CHAT_ID": "CHAT456",
        }.get(key, default)

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        telegram_bot._bot = None

        formatted_msg = "✅ <b>Cloud Sync Hoàn Tất</b>\nĐã sao lưu 5 video đơn hàng lên S3 thành công!"

        success, _ = telegram_bot.send_telegram_message(formatted_msg)

        assert success is True
        payload = mock_post.call_args[1]["json"]
        assert "<b>Cloud Sync Hoàn Tất</b>" in payload["text"]
        assert "5 video" in payload["text"]
        assert "S3 thành công" in payload["text"]

    @patch("requests.post")
    @patch("database.get_setting")
    def test_send_message_api_error(self, mock_get_setting, mock_post):
        """Telegram API error should return (False, ...) without crashing."""
        mock_get_setting.side_effect = lambda key, default="": {
            "TELEGRAM_BOT_TOKEN": "BAD_TOKEN",
            "TELEGRAM_CHAT_ID": "123",
        }.get(key, default)

        mock_post.side_effect = ConnectionError("Network unreachable")

        telegram_bot._bot = None

        success, msg = telegram_bot.send_telegram_message("Test")

        assert success is False
        assert "Lỗi" in msg
