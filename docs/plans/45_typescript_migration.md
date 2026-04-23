# Plan 45: TypeScript Migration (Frontend)

**Ngày**: 2026-04-24
**Mức độ**: Medium — Type safety cho props, API responses, state
**Loại**: Refactor (no behavior change, gradual migration)

---

## Problem

Frontend viết bằng JSX (JavaScript). Không có type safety cho:
- Component props (10 components × ~20 props = 200+ untyped values)
- API response shapes (backend trả dict, frontend guess fields)
- State types (60 useState, mỗi cái có type ẩn)
- Event handlers (SSE data shape unknown)

Khi backend thêm/xóa field → frontend crash silent hoặc hiển thị undefined.

---

## Scope

### Phase 1: Setup (1 giờ)
- `npm install -D typescript` — NOTE: `@types/react` và `@types/react-dom` đã có trong devDependencies
- `tsconfig.json` — `allowJs: true` (gradual migration)
- `vite.config.ts` — TypeScript support
- Rename `vite.config.js` → `vite.config.ts`

### Phase 2: Shared Types (1 giờ)
- `web-ui/src/types/api.ts` — API response interfaces
  ```typescript
  interface Station { id: number; name: string; ip: string; brand: string; camera_mode: string; ... }
  interface Record { id: number; waybill_code: string; status: 'READY' | 'RECORDING' | 'PROCESSING' | 'FAILED'; ... }
  interface User { id: number; username: string; role: 'ADMIN' | 'OPERATOR'; ... }
  ```
- `web-ui/src/types/props.ts` — Component props interfaces

### Phase 3: Migrate file-by-file (2-3 giờ)
Order by dependency (leaf first):
1. `config.js` → `config.ts`
2. `utils/notificationSounds.js` → `notificationSounds.ts`
3. `MtxFallback.jsx` → `MtxFallback.tsx`
4. `AdminDashboard.jsx` → `AdminDashboard.tsx`
5. `SystemHealth.jsx` → `SystemHealth.tsx`
6. `Dashboard.jsx` → `Dashboard.tsx`
7. `VideoPlayerModal.jsx` → `VideoPlayerModal.tsx`
8. `SetupModal.jsx` → `SetupModal.tsx`
9. `UserManagementModal.jsx` → `UserManagementModal.tsx`
10. `App.jsx` → `App.tsx` (last, largest)

---

## Constraints

- **Gradual migration** — `allowJs: true` cho phép .js và .ts共存
- **NO behavior change** — chỉ thêm types, không sửa logic
- Mỗi file migrate xong phải pass lint + build
- Không dùng `any` — dùng `unknown` + type guard
- Props interfaces phải match actual prop usage (không invent types)

---

## Verification

- [ ] `npm run build` pass sau mỗi file migration
- [ ] `npm run lint` pass
- [ ] No `any` types in production code
- [ ] All component props typed
- [ ] API response interfaces match backend actual responses
