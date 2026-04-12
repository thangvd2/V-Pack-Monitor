# =============================================================================
# V-Pack Monitor - CamDongHang v2.1.0
# Copyright (c) 2024-2026 VDT - Vu Duc Thang (thangvd2)
# All rights reserved. Unauthorized copying or distribution is prohibited.
# =============================================================================

import telebot
import database
import threading
import time
import shutil
import sqlite3

_bot = None
_bot_thread = None
_stop_event = threading.Event()


def _run_bot(bot_token, authorized_chat_id):
    global _bot
    try:
        _bot = telebot.TeleBot(bot_token)

        @_bot.message_handler(commands=["baocao"])
        def handle_baocao(message):
            if str(message.chat.id) != authorized_chat_id:
                return

            try:
                # 1. Đếm số đơn hôm nay
                with sqlite3.connect(database.DB_FILE) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT COUNT(*) FROM packing_video WHERE date(recorded_at) = date('now', 'localtime')"
                    )
                    total_today = cursor.fetchone()[0]

                # 2. Check dung lượng ổ cứng
                total, used, free = shutil.disk_usage("recordings")
                percentage = round((used / total) * 100, 1)
                free_gb = round(free / (1024**3), 1)

                msg = (
                    f"📊 <b>BÁO CÁO HỆ THỐNG V-PACK</b>\n\n"
                    f"📦 Đơn đã đóng hôm nay: <b>{total_today} đơn</b>\n"
                    f"💾 Ổ cứng trống: <b>{free_gb} GB</b>\n"
                )
                if percentage > 90:
                    msg += f"⚠️ BÁO ĐỘNG: Ổ cứng đã dùng {percentage}%. Vui lòng dọn dẹp hoặc kích hoạt Cloud Sync ngay!"
                else:
                    msg += f"✅ Tình trạng bộ nhớ: An toàn ({percentage}% đã dùng)"

                _bot.reply_to(message, msg, parse_mode="HTML")
            except Exception as e:
                _bot.reply_to(message, f"Lỗi truy xuất: {str(e)}")

        @_bot.message_handler(commands=["kiemtra"])
        def handle_kiemtra(message):
            if str(message.chat.id) != authorized_chat_id:
                return

            stations = database.get_stations()
            msg = f"🔍 <b>KIỂM TRA HỆ THỐNG</b>\nSố trạm cài đặt: {len(stations)}\n\n"
            for st in stations:
                msg += f"🔹 Trạm {st['id']}: {st['name']} ({st.get('ip_camera_1', 'Chưa cấu hình IP')})\n"

            _bot.reply_to(message, msg, parse_mode="HTML")

        # Vòng lặp lắng nghe thông minh giúp dừng bot an toàn khi stop_event được gọi
        while not _stop_event.is_set():
            try:
                _bot.polling(non_stop=True, interval=1, timeout=10)
            except Exception as e:
                time.sleep(3)
    except Exception as e:
        print(f"Lỗi khởi chạy Telegram Bot: {e}")


def start_polling():
    global _bot_thread, _stop_event
    stop_polling()  # Xoá bot hiện tại nếu có

    bot_token = database.get_setting("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = database.get_setting("TELEGRAM_CHAT_ID", "").strip()

    if not bot_token or not chat_id:
        return False, "Chưa đủ cấu hình Telegram"

    _stop_event.clear()
    _bot_thread = threading.Thread(
        target=_run_bot, args=(bot_token, chat_id), daemon=True
    )
    _bot_thread.start()
    return True, "Đã khởi động Bot"


def stop_polling():
    global _bot, _bot_thread, _stop_event
    _stop_event.set()
    if _bot:
        _bot.stop_polling()
    if _bot_thread:
        _bot_thread.join(timeout=2)
    _bot = None


def send_telegram_message(message: str):
    """
    Gửi tin nhắn 1 chiều (Dùng cho Cảnh báo lỗi, Alert Cloud Sync)
    """
    bot_token = database.get_setting("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = database.get_setting("TELEGRAM_CHAT_ID", "").strip()

    if not bot_token or not chat_id:
        return False, "Chưa cấu hình Telegram Bot Token hoặc Chat ID."

    # Ưu tiên tái sử dụng _bot nếu đang chạy ngầm
    if _bot:
        try:
            _bot.send_message(chat_id, message, parse_mode="HTML")
            return True, "Đã gửi qua session hiện tại."
        except Exception as e:
            return False, f"Lỗi gửi tin qua bot: {e}"

    # Fallback xuống Raw API nếu bot chưa start_polling
    try:
        import requests

        url = "https://api.telegram.org/bot{}/sendMessage".format(bot_token)
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return True, "Đã gửi."
    except Exception as e:
        return False, f"Lỗi gửi Telegram: {str(e)}"
