# Sử dụng Python 3.10 mỏng nhẹ
FROM python:3.10-slim

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
