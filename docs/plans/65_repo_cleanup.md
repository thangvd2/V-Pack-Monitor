# Plan 65: Repo Cleanup — Tinh Gọn Repository

> **Status:** READY
> **Priority:** MEDIUM — Hygiene
> **Scope:** 10+ files removed, 3 files fixed, 22 branches deleted
> **Estimated Effort:** 30 min

---

## Background

Sau audit toàn diện, phát hiện nhiều files thừa, gitignore thiếu, stale branches, và config Docker sai. Plan này gom quick wins thành 1 PR.

---

## Phase 1: Remove Stale Files

### A. Machine-specific scripts (không liên quan V-Pack Monitor)
- `scripts/fix_crashdump.ps1` — Windows crash dump config, hardcode `E:\pagefile.sys`
- `scripts/remove_amd_radeon.ps1` — AMD Radeon cleanup, hardcode `C:\Users\Admin\`

### B. Binary PDFs (markdown source đã có, PDF bloat git history 1.3MB)
- `docs/USER_GUIDE_ADMIN.pdf` (778KB)
- `docs/USER_GUIDE_OPERATOR.pdf` (537KB)

### C. Default Vite template files (không dùng, không có giá trị)
- `web-ui/README.md` — Default Vite boilerplate
- `web-ui/src/assets/react.svg` — Default React logo
- `web-ui/src/assets/vite.svg` — Default Vite logo

### D. Outdated archived docs (đã đánh dấu OUTDATED, tất cả đã fix)
- `docs/archive/windows_fixes_needed.md` — "All issues fixed in v2.2.2 and v3.0.0"
- `docs/archive/brainstorm_roadmap.md` — "Most items implemented in v2.2-v3.5"

---

## Phase 2: Fix .gitignore Gaps

Thêm vào root `.gitignore`:
```gitignore
# Python tool caches
.ruff_cache/
.mypy_cache/

# Logs (root level)
*.log

# OS files
Thumbs.db
```

---

## Phase 3: Fix Minor Issues

### README.md typo
- Line 24: `"đangoccupied"` → `"đang occupied"`

### docs/plans/62 unchecked checkbox
- Line 351: `- [ ] grep -r "v2.1.0"` → `- [x] grep -r "v2.1.0"`

---

## Phase 4: Delete Stale Branches (NO PR needed — direct operation)

### 7 stale local branches:
```
docs/62-production-readiness
docs/hardware-req-link
docs/hardware-specs
docs/plan-status-update
feature/49-alembic-migration
feature/add-implementation-workflow-rules
feature/add-plan-file-rules
```

### 15 stale remote branches:
```
docs/48-websocket-plan-update
docs/design-patterns-audit
docs/fix-plans-51-56
docs/hardware-req-link
docs/hardware-specs
docs/plan-status-update
docs/roadmap-plans
feature/47-sse-auto-reconnect
feature/53-cloud-sync-scheduler
feature/57-bundle-optimization
feature/add-plan-file-rules
fix/51-pyinstaller-hidden-imports
fix/52-backend-input-validation
fix/58-mtx-orphaned-paths
refactor/46-api-response-models
```

---

## NOT in this plan (separate plans needed)

| Issue | Plan |
|-------|------|
| Docker config bugs (DB path, ports, Python version) | Plan 66 |
| `SystemHealth.tsx` unused `currentUser` prop | Code smell, low priority |
| Duplicate `_MAX_RECORDING_SECONDS` constant | Code smell, low priority |

---

## Verification

1. `ruff check .` passes
2. `npm run build && npm run lint` passes
3. `pytest tests/ -q` passes
4. `git ls-files | grep -E '(fix_crashdump|remove_amd|USER_GUIDE.*pdf|react.svg|vite.svg|web-ui/README)'` returns empty
5. All 22 stale branches deleted
