# Plan 44: E2E Tests với Playwright

**Ngày**: 2026-04-24
**Mức độ**: High — 326 unit tests nhưng 0 E2E. Mỗi release manual test rất tốn thời gian
**Loại**: Testing infrastructure

---

## Problem

Hệ thống có 326 unit tests nhưng chưa có end-to-end test. Các user flow quan trọng chưa được test tự động:
- Operator: login → scan START → verify recording → scan STOP → verify video ready
- Admin: login → grid view → tab switch → click station → single view → back
- Records: filter by station → search waybill → download video → verify filename

Mỗi lần release phải manual test tất cả flow này.

---

## Scope

### Phase 1: Setup

- `npm install -D @playwright/test` (dev dependency)
- `playwright.config.ts` — base URL, timeouts, retries
- CI: add `e2e` job to `.github/workflows/ci.yml` (separate from unit tests)

### Phase 2: Core E2E Flows

| # | Flow | Pages/Actions | Priority |
|---|------|---------------|----------|
| 1 | Auth flow | Login → verify redirect → logout → verify login page | 🔴 |
| 2 | Admin grid view | Login admin → verify grid → verify tabs → click station → single view → back | 🔴 |
| 3 | Records list | Login → filter by station → search → verify results → change page | 🟡 |
| 4 | Settings modal | Login admin → open settings → change cleanup days → save → verify toast | 🟡 |
| 5 | Operator scan flow | Login operator → mock scan START → verify status → mock scan STOP → verify processing | 🔴 |

### Test data strategy:
- Seed test DB via API calls in `beforeEach`
- Use test-specific station names (prefix `e2e_`)
- Cleanup test data in `afterAll`

---

## Constraints

- Playwright chỉ thêm vào `web-ui/package.json` devDependencies
- E2E tests chạy SAU unit tests trong CI (separate job)
- E2E tests không phụ thuộc external services (MediaMTX, camera) — mock hoặc skip
- Operator scan flow cần mock barcode scanner (không có physical scanner trong CI)

---

## Verification

- [ ] `npx playwright test` pass locally
- [ ] CI e2e job pass
- [ ] 5 core flows covered
- [ ] Test data cleanup verified (no leftover in DB)
