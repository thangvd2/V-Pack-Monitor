import logging
import sys

# Formatter chuẩn: Thời gian | Level | Module | Message
_LOG_FORMAT = "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Khởi tạo và cấu hình logger chuẩn cho toàn bộ ứng dụng.
    """
    logger = logging.getLogger(name)

    # Nếu logger đã có handler thì không thêm nữa (tránh ghi log nhiều lần)
    if logger.hasHandlers():
        return logger

    logger.setLevel(level)

    # Ghi ra stdout thay vì stderr (print mặc định là stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    formatter = logging.Formatter(fmt=_LOG_FORMAT, datefmt=_DATE_FORMAT)
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    # Ngăn log nổi bọt lên root logger nếu không cần thiết
    logger.propagate = False

    return logger
