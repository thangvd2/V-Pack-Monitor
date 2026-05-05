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

## Versioning

- **PATCH** (x.x.Z): bugfix only
- **MINOR** (x.Y.0): new feature, backward-compatible
- **MAJOR** (X.0.0): breaking change (API format, DB schema, response structure)
- **ALWAYS use `python scripts/bump_version.py X.Y.Z`** to bump — it syncs all 5 files (`VERSION`, `vpack/app.py`, `README.md`, `web-ui/package.json`, `web-ui/package-lock.json`). Edit `RELEASE_NOTES.md` manually.

## Language

- User communicates in Vietnamese
- Code, comments, commit messages in English
- Respond in Vietnamese unless user uses English

## Key Constraints

- Single developer (sole GitHub account)
- Branch and release rules: see RULES.md
