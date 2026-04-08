# Sử dụng Python 3.14
FROM python:3.14-slim

LABEL maintainer="VDT - Vu Duc Thang <thangvd2>"
LABEL org.opencontainers.image.title="V-Pack Monitor"
LABEL org.opencontainers.image.authors="VDT - Vu Duc Thang"
LABEL org.opencontainers.image.source="https://github.com/thangvd2/V-Pack-Monitor"

# Thiết lập thư mục làm việc
WORKDIR /app

# Cài đặt FFmpeg và các thư viện hỗ trợ OpenCV
RUN apt-get update && apt-get install -y ffmpeg libsm6 libxext6 libgl1 && rm -rf /var/lib/apt/lists/*

# Copy thư mục cài đặt requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ mã nguồn V-Pack Monitor (Cả Backend và Frontend Build)
COPY . .

# Tạo thư mục recordings nếu chưa có
RUN mkdir -p recordings

# Expose port chia sẻ mạng LAN
EXPOSE 8001

# Lệnh khởi động
CMD ["python", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8001"]
