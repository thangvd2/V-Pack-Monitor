# Sử dụng Python 3.13
FROM python:3.13-slim

LABEL maintainer="VDT - Vu Duc Thang <thangvd2>"
LABEL org.opencontainers.image.title="V-Pack Monitor"
LABEL org.opencontainers.image.authors="VDT - Vu Duc Thang"
LABEL org.opencontainers.image.source="https://github.com/thangvd2/V-Pack-Monitor"

ARG MTX_VERSION=1.17.1

WORKDIR /app

RUN apt-get update && apt-get install -y ffmpeg curl tar && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p bin/mediamtx && \
    ARCH=$(uname -m) && \
    if [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then MTX_ARCH="linux_arm64"; \
    elif [ "$ARCH" = "x86_64" ]; then MTX_ARCH="linux_amd64"; \
    else MTX_ARCH="linux_amd64"; fi && \
    curl -L "https://github.com/bluenviron/mediamtx/releases/download/v${MTX_VERSION}/mediamtx_v${MTX_VERSION}_${MTX_ARCH}.tar.gz" \
    | tar xz -C bin/mediamtx mediamtx mediamtx.yml LICENSE && \
    chmod +x bin/mediamtx/mediamtx

COPY . .

RUN mkdir -p recordings

EXPOSE 8001 8889 9997

CMD ["sh", "-c", "bin/mediamtx/mediamtx bin/mediamtx/mediamtx.yml & python -m uvicorn vpack.app:app --host 0.0.0.0 --port 8001"]
