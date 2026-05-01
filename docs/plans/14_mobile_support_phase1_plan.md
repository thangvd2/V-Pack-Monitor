# Plan 14: Mobile Support — Phase 1 (Responsive Quick Wins)

> **Version:** v2.2.0 → v2.3.0
> **Date:** 2026-04-11
> **Author:** VDT
> **Status:** DONE — Implemented in v3.x series. All responsive CSS (min-h-[44px], sm:/md:/lg: breakpoints, mobile-friendly touch targets) applied across all components.

## Mục tiêu

Hỗ trợ operator sử dụng tablet/phone để đóng hàng từ xa. Phase 1 chỉ sửa responsive CSS — **không thay đổi cấu trúc component, không ảnh hưởng PC/laptop layout**.

## Context

- Server (Windows/macOS) đặt xa khu đóng hàng
- Operator dùng tablet/phone → mở browser → quét mã vạch (Bluetooth scanner hoặc gõ tay)
- Desktop layout phải giữ nguyên 100%

## Thiết kế hiện tại

```
Desktop (≥1024px):
┌────────────────────────────────────────────────────────┐
│ Header: [Logo] [Station▼] [⊞] [📊] [🔍] [User ▼]     │
├──────────────────────────┬─────────────────────────────┤
│ Live View (2/3 width)    │ Lịch sử ghi hình (1/3)      │
│ ┌──────────────────────┐ │ ┌─────────────────────────┐ │
│ │ MediaMTX iframe      │ │ │ Record 1 (READY)        │ │
│ │ + status overlays    │ │ │ Record 2 (PROCESSING)   │ │
│ └──────────────────────┘ │ │ Record 3 (RECORDING)    │ │
│ [Barcode Simulator]      │ │ ...                     │ │
│                          │ └─────────────────────────┘ │
└──────────────────────────┴─────────────────────────────┘
```

```
Mobile hiện tại (<768px) — VẤN ĐỀ:
┌──────────────────────────┐
│ Header overflow, khó đọc │  ← Station + buttons tràn
├──────────────────────────┤
│ Live View (full width    │  ← NHỎ vì aspect-ratio bị compress
│ nhưng aspect ratio cố    │
│ định → height thấp)      │
├──────────────────────────┤
│ Barcode Simulator        │  ← Ẩn trên mobile (operator cần nó!)
├──────────────────────────┤
│ Lịch sử (full width)     │  ← PHẢI SCROLL XUỐNG RẤT XA
│ Record 1                 │
│ Record 2                 │
│ Record 3                 │
│ ...                      │
└──────────────────────────┘
```

## Thay đổi Phase 1

### 1. Header — Mobile Compact

**File:** `web-ui/src/App.jsx` (header area ~dòng 860-1060)

**Desktop:** Giữ nguyên — không thay đổi class nào có prefix `lg:` hoặc `md:`

**Mobile (<768px):**
- Header xếp 2 hàng: Hàng 1: Logo + Station + User. Hàng 2: Search (full width)
- Dashboard/Grid toggle icons ẩn (operator mobile không cần)
- Touch-friendly: buttons min 44px (Apple HIG)

```diff
- <div className="mt-6 md:mt-0 flex items-center gap-3 w-full md:w-auto">
+ <div className="mt-4 md:mt-6 flex items-center gap-2 md:gap-3 w-full md:w-auto flex-wrap">
```

### 2. Main Layout — Mobile Single Column, Live View Ưu Tiên

**File:** `web-ui/src/App.jsx` (main content ~dòng 1035-1430)

**Desktop:** Giữ nguyên `lg:grid-cols-3`

**Mobile (<768px):**
- 1 column, live view **full width** + aspect-ratio 16:9 (không bị compress)
- Lịch sử ghi hình **giới hạn 3 records gần nhất** + nút "Xem tất cả"
- Barcode simulator **luôn hiện** trên mobile (hiện tại đang hiện cho OPERATOR)
- Barcode simulator rename "Công Cụ Quét Mã Vạch" thay vì "DEV MODE"

### 3. Barcode Input — Mobile-First

**File:** `web-ui/src/App.jsx` (barcode simulator ~dòng 1268-1320)

**Desktop:** Giữ nguyên — không thay đổi

**Mobile (<768px):**
- Bỏ label "DEV MODE" + "Công Cụ Giả Lập Máy Quét (Manual Simulator)"
- Thay bằng: "Quét Mã Vạch" (compact header)
- Input field **lớn hơn**: `py-3.5 text-base` (iOS không zoom trên input < 16px)
- Buttons **lớn hơn**: `py-3.5 min-h-[44px]`
- Layout: Input full width, 2 buttons ngang (Bắt Đầu Ghi | STOP)
- Auto-focus input trên mobile (tap anywhere = focus input)

### 4. History Records — Mobile Compact

**File:** `web-ui/src/App.jsx` (records list ~dòng 1330-1425)

**Desktop:** Giữ nguyên

**Mobile (<768px):**
- Giới hạn **3 records gần nhất** + nút "Xem thêm" (expand to full list)
- Mỗi record card compact hơn: bỏ thumbnail, chỉ hiện waybill + status + time
- Status badge nhỏ hơn

### 5. Login Page — Mobile Responsive

**File:** `web-ui/src/App.jsx` (login ~dòng 68-87)

**Desktop:** Giữ nguyên

**Mobile:**
- Form full width, padding giảm
- Input fields `text-base` (tránh iOS zoom)

### 6. Touch Target Compliance

**Toàn bộ app:**
- Tất cả interactive elements ≥ 44×44px (Apple HIG / Material Design)
- Không thay đổi desktop — chỉ thêm `min-h-[44px] min-w-[44px]` cho mobile-specific elements
- Spacing giữa buttons ≥ 8px

## Files Thay Đổi

| File | Thay đổi | Desktop Impact |
|------|----------|---------------|
| `web-ui/src/App.jsx` | Responsive classes, mobile barcode UI, compact records | ❌ None |
| `web-ui/src/Dashboard.jsx` | Touch-friendly stat cards, responsive grid | ❌ None |

## Không Thay Đổi

- ❌ Backend (api.py, video_worker.py, etc.)
- ❌ Desktop layout (tất cả `lg:` và `md:` classes giữ nguyên)
- ❌ SSE logic, scan logic, auth logic
- ❌ SystemHealth, VideoPlayerModal, SetupModal, UserManagementModal

## Testing Plan

| Device | Test |
|--------|------|
| iPhone SE (375px) | Login → Station → Scan → Live view → History |
| iPad (768px) | Tất cả flows, cả portrait + landscape |
| Android phone (360px) | Tất cả flows |
| Desktop (1440px) | **Verify KHÔNG có thay đổi** so với hiện tại |

## Risks

| Risk | Mitigation |
|------|-----------|
| CSS thay đổi ảnh hưởng desktop | Chỉ thêm mobile-first classes (`sm:`, `md:` prefix) — không sửa `lg:` classes |
| Barcode input focus trên iOS | Dùng `inputmode="text"` + `enterkeyhint="send"` |
| MediaMTX iframe không responsive | Đã có `w-full h-full` — chỉ cần container aspect-ratio đúng |

## Implementation Steps

1. Thêm mobile breakpoint classes cho header
2. Main layout: mobile single-column + live view aspect-ratio
3. Barcode simulator: mobile-first UI (luôn hiện, input lớn, buttons lớn)
4. History records: mobile compact (3 records + "Xem thêm")
5. Login page: mobile responsive
6. Touch target audit
7. Build + test trên mobile browsers
8. Desktop regression test

## Estimate: ~2-3 hours
