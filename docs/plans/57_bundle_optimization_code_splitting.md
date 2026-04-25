# Plan 57: Bundle Optimization — Code Splitting & Dependency Audit

**Ngày**: 2026-04-25
**Mức độ**: Low — Build warning, không ảnh hưởng chức năng. Performance optimization
**Loại**: Performance improvement (frontend)

---

**Status**: Plan created, not yet implemented

## Problem

### 1. Chunk size warning
```
dist/assets/index-jJJKwHEB.js   757.79 kB │ gzip: 219.87 kB
(!) Some chunks are larger than 500 kB after minification.
```

Toàn bộ app bundle thành 1 file JS duy nhất ~758 KB (gzip ~220 KB). Lần đầu load phải download toàn bộ, kể cả các component user chưa truy cập (Dashboard charts, SystemHealth, VideoPlayerModal, SetupModal, UserManagementModal).

### 2. NPM moderate vulnerability
```
postcss < 8.5.10 — XSS via Unescaped </style> in CSS Stringify Output
```
Dev dependency, không ảnh hưởng production runtime. Fix bằng `npm audit fix`.

---

## Scope

### Part 1: Code Splitting với React.lazy()

Thay static imports bằng dynamic imports cho các component "nặng" hoặc ít dùng:

| Component | Lý do lazy-load | Estimated saving |
|-----------|----------------|-----------------|
| `Dashboard` | Recharts (~150KB), chỉ load khi user vào tab Dashboard | ~150KB |
| `SystemHealth` | Polling + complex UI, chỉ load khi tab Health | ~20KB |
| `VideoPlayerModal` | Chỉ load khi click play video | ~30KB |
| `SetupModal` | Chỉ load khi admin mở settings (~845 dòng) | ~25KB |
| `UserManagementModal` | Chỉ load khi admin quản lý users | ~15KB |

**Implementation pattern:**
```jsx
// Thay: import Dashboard from './Dashboard';
// Bằng:
const Dashboard = React.lazy(() => import('./Dashboard'));

// Wrap với Suspense:
<Suspense fallback={<div className="p-4 text-slate-400 animate-pulse">Đang tải...</div>}>
  <Dashboard ... />
</Suspense>
```

### Part 2: NPM audit fix
```bash
cd web-ui && npm audit fix
```

### Part 3: Build config tuning (optional)
Nếu sau code splitting vẫn > 500KB, thêm vào `vite.config.js`:
```js
build: {
  rollupOptions: {
    output: {
      manualChunks: {
        vendor: ['react', 'react-dom'],
        charts: ['recharts'],
      }
    }
  }
}
```

---

## Constraints

- Không thay đổi behavior — lazy-load transparent to user (chỉ thêm loading spinner/fallback)
- ErrorBoundary đã wrap từng section (Plan 43), nên lazy-load failure được handle tự động
- `npm audit fix` chỉ fix dev dependencies — không breaking change
- Giữ `Suspense` fallback consistent với existing UI style (slate-400, animate-pulse)

---

## Verification

- [ ] `npm run build` pass, no chunk size warning (hoặc significantly reduced)
- [ ] `npm audit` clean (0 vulnerabilities)
- [ ] `npm run lint` pass
- [ ] Mỗi lazy-loaded component hiển thị fallback đúng khi load
- [ ] Total bundle size giảm đáng kể (target: main chunk < 500KB)
- [ ] Không regression — tất cả UI flows vẫn hoạt động
