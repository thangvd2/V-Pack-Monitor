# Project Context

> **This file is the SINGLE SOURCE OF TRUTH for project context.**
> Both OpenCode (AGENTS.md) and Antigravity (.agents/rules/project-rules.md) are AUTO-GENERATED from this file.
> **DO NOT edit generated files directly.** Edit .ai-sync/ files, then run `python .ai-sync/sync.py`.

---

## Project: V-Pack Monitor (CamDongHang)

Hệ thống giám sát đóng hàng và lưu trữ tự động tối ưu hóa cho nền tảng thương mại điện tử (Shopee, TikTok, Lazada). Quản lý Camera trạm đóng gói, ghi hình chính xác theo kiện hàng, cung cấp bằng chứng xử lý khiếu nại.

## Tech Stack

- **Backend**: Python 3.10+, FastAPI, SQLite, FFmpeg, JWT
- **Frontend**: React, WebRTC, Vite
- **Infrastructure**: MediaMTX (RTSP→WebRTC), Docker, GitHub Actions CI

## Project Structure

```
├── api.py                  # FastAPI app, shared state, lifespan (DO NOT add routes here)
├── routes_auth.py          # Auth + User management routes
├── routes_stations.py      # Station CRUD + sessions + discovery
├── routes_records.py       # Scan, records, download, SSE, live
├── routes_system.py        # Settings, analytics, health, update
├── database.py             # DB layer, Fernet encryption, FTS5 search
├── auth.py                 # JWT, password hashing, token revocation
├── video_worker.py         # Video processing queue (bounded, max 10 pending)
├── recorder.py             # FFmpeg recording
├── cloud_sync.py           # Google Drive / S3 backup
├── telegram_bot.py         # Telegram notifications
├── network.py              # LAN scanner
├── tests/                  # Pytest suite with tmp_path isolation
├── web-ui/                 # React frontend
├── requirements.txt        # Python dependencies (production)
├── requirements-dev.txt    # Python dependencies (development only)
```

## Versioning

- **PATCH** (x.x.Z): bugfix only
- **MINOR** (x.Y.0): new feature, backward-compatible
- **MAJOR** (X.0.0): breaking change (API format, DB schema, response structure)
- Update `VERSION` file + `api.py` header + `RELEASE_NOTES.md` on release

## Language

- User communicates in Vietnamese
- Code, comments, commit messages in English
- Respond in Vietnamese unless user uses English

## Key Constraints

- Single developer (sole GitHub account)
- Branch and release rules: see RULES.md
