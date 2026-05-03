# V-Pack Monitor — Quality Control Framework

## Chất lượng là gì

Hệ thống này chạy ở xưởng đóng hàng, camera quay video kiểm tra chất lượng sản phẩm.
Nghĩa là:

| Dimension | Fail = | Ghi nhận khi nào |
|---|---|---|
| **Availability** | Xưởng không scan được trong giờ làm | Camera recorder down, server crash |
| **Data Integrity** | Mất video đã scan | Video file corrupt, record bị drop |
| **Security** | Camera feed lộ ra ngoài | Auth bypass, path traversal, credential leak |
| **Compatibility** | Deploy xong toàn bộ xưởng đứng | API format đổi, DB schema migrate fail |
| **Recoverability** | Down quá 15 phút | Không có backup, không có rollback |

Mọi thay đổi trong hệ thống đều phải trả lời được câu hỏi:
**"Nếu thay đổi này sai, ảnh hưởng gì và rollback thế nào?"**

---

## Decision Flow — Bắt đầu từ đây

Khi nhận yêu cầu thay đổi, follow theo thứ tự:

```
BƯỚC 1: Xác định loại thay đổi
  ├── Feature mới      → Section "Thêm tính năng mới"
  ├── Thay đổi có sẵn  → Section "Thay đổi/nâng cấp tính năng"
  ├── Loại bỏ           → Section "Loại bỏ tính năng"
  ├── Security vuln     → Section "Sửa security vulnerabilities"
  ├── Upgrade deps      → Section "Nâng cấp libs/third parties"
  └── Bug/issue khác    → Section "Sửa bugs/issues"

BƯỚC 2: Risk Assessment (quick)
  ├── Chạm DB schema / auth / scan-record flow? → P0
  ├── Đổi API format / UI flow?                 → P1
  ├── Thêm UI mới / feature phụ?                → P2
  └── Refactor / docs / config?                 → P3

BƯỚC 3: Prevention (P0/P1 bắt buộc, P2/P3 nên có)
  ├── Impact Mapping: LSP find-references → liệt kê tất cả callers
  ├── Behavioral Baseline: test cho behavior hiện tại TRƯỚC khi sửa
  └── Caller không có test = rủi ro cao → thêm test trước

BƯỚC 4: Implement theo process của loại thay đổi
  └── Follow section tương ứng ở dưới

BƯỚC 5: 5 Essential Checks
  1. Risk level đã xác định?
  2. Files bị chạm đã liệt kê?
  3. CI green?
  4. Có test mới cover thay đổi?
  5. Rollback plan? (P0/P1 phải có explicit plan)

BƯỚC 6: Merge
  ├── P0/P1 → cần review + CI pass + manual smoke test
  └── P2/P3 → CI pass là đủ
```

---

## Enforcement Layers

Document không tự enforce. 3 tầng sau đảm bảo tuân thủ **cơ học**, không phụ thuộc vào ý thức:

```
Layer 1 — Pre-commit hooks (LOCAL, block commit)
  ├── ruff lint + format → fail = không commit được
  ├── detect-secrets → block nếu thêm secret mới
  └── (sẽ thêm: pytest fast subset)
  ✅ STATUS: ĐANG CHẠY — pre-commit install, ruff.toml config

Layer 1.5 — Pre-push hook (LOCAL, block push)
  └── pytest → 326 tests, fail = không push được
  ✅ STATUS: ĐANG CHẠY — pre-push install

Layer 2 — CI Pipeline (REMOTE, block merge)
  ├── python-test  → pytest
  ├── frontend-build → npm run build
  └── python-lint  → ruff check
  ✅ STATUS: ĐANG CHẠY — mọi PR phải pass 3 jobs

Layer 3 — Branch Protection (GITHUB, block push)
  ├── master: cần PR + 1 review + CI pass + enforce admins + no force push
  └── dev: cần PR + CI pass (không cần review)
  ✅ STATUS: ĐANG CHẠY — master + dev đều protected trên GitHub
```

**Nguyên tắc**: Nếu có thể automate, KHÔNG ghi vào document.
Document chỉ chứa những gì CẦN CON NGƯỜI quyết định.

---

## Risk Classification

Mỗi thay đổi bắt đầu bằng việc xác định risk level:

| Level | Nghĩa là | Reviewer | Ví dụ |
|---|---|---|---|
| **P0** | Crash system, mất data, lộ info | Phải review kỹ | Đổi DB schema, sửa auth, upgrade core deps |
| **P1** | Phá 1 flow quan trọng | Nên review | Đổi API format, sửa scan/record flow |
| **P2** | Ảnh hưởng UI hoặc feature phụ | CI pass là đủ | Thêm chart, đổi layout |
| **P3** | Không ảnh hưởng runtime | CI pass là đủ | Refactor, docs, comment |

### Quick Risk Assessment

```
Chạm vào DB schema?              → P0
Chạm vào auth/encryption?        → P0
Chạm vào scan → record → video?  → P0
Xóa/đổi tên API field?           → P0
Thêm API field mới?              → P1
Đổi UI flow?                     → P1
Thêm UI mới (không sửa cũ)?      → P2
Refactor nội bộ (không đổi API)? → P3
Docs/config?                     → P3
```

---

## Prevention: Tránh bug trước khi nó xuất hiện

Gốc vấn đề: "fix bug này → tạo bug mới ở nơi khác".

### Impact Mapping (TRƯỚC khi code)

Bước bắt buộc đối với P0/P1 changes:

```
1. Dùng LSP find-references trên function/class chuẩn bị sửa
2. Liệt kê TẤT CẢ callers
3. Đánh dấu: caller nào có test? caller nào KHÔNG có test?
4. Caller không có test = rủi ro cao → thêm test TRƯỚC khi sửa
```

### Behavioral Baseline (cho thay đổi logic)

Khi sửa logic của function/module:

```
1. Viết test cho behavior HIỆN TẠI (chưa sửa gì)
2. Verify test pass (green)
3. Sửa code
4. Nếu test cũ fail → đây là INTENDED change hay UNINTENDED side effect?
5. Nếu intended → cập nhật test + ghi rõ trong PR
6. Nếu unintended → fix code, KHÔNG xóa test
```

### Dependency Graph

```
vpack/app.py ← vpack/routes/vpack/auth.py    (auth state, login_attempts)
vpack/app.py ← vpack/routes/stations.py (stream_managers, recorders, locks)
vpack/app.py ← vpack/routes/records.py  (ALL shared state)
vpack/app.py ← vpack/routes/system.py   (update state, settings, streams)
vpack/database.py ← tất cả modules
vpack/auth.py ← vpack/routes/vpack/auth.py, vpack/routes/records.py
vpack/video_worker.py ← vpack/routes/records.py, vpack/recorder.py
```

Sửa bất kỳ ô nào → kiểm tra tất cả mũi tên đi ra từ ô đó.

---

## 5 Essential Checks (cho MỌI thay đổi)

Thay vì 16-item checklist, 5 câu hỏi thực sự cần trả lời:

```
1. RISK LEVEL: P0 / P1 / P2 / P3?
   └─ P0/P1 → cần impact mapping + behavioral baseline

2. FILES CHẠM: liệt kê tất cả files sẽ sửa
   └─ Cross-check với dependency graph ở trên

3. TEST PASS: CI green?
   └─ Automated — CI enforce, không cần tự nhớ

4. TEST MỚI: có test nào cover thay đổi này không?
   └─ P0/P1: bắt buộc. P2/P3: nên có.

5. ROLLBACK PLAN: nếu fail, revert thế nào?
   └─ P0: phải có explicit plan. P1-P3: git revert là đủ.
```

---

## Process theo loại thay đổi

### 1. Thêm tính năng mới

```
Design → Impact map → Test trước → Implement → Verify → Merge
```

**Prevention gates**:
- Impact map: module nào bị chạm?
- DB schema change → PHẢI có migration UP + DOWN script
- API format → KHÔNG xóa field cũ, thêm field mới + deprecation
- Viết acceptance test TRƯỚC khi implement (test-first cho P0/P1)

**Enforcement**:
- CI pass (automated)
- Manual smoke test trên local (P0/P1)

---

### 2. Thay đổi/nâng cấp tính năng đang có

```
Baseline test → Minimal change → Regression check → Verify callers → Merge
```

**Prevention gates**:
- Behavioral baseline: test cho behavior hiện tại TRƯỚC khi sửa
- LSP find-references: tìm TẤT CẢ callers
- Minimal change: CHỈ sửa đúng thứ cần sửa, KHÔNG refactor kèm

**Critical rule**: Nếu test cũ fail sau khi sửa → PHẢI trả lời:
intended change hay bug? Không được xóa test cũ để cho pass.

**Enforcement**:
- CI pass (automated)
- Caller audit qua LSP (manual nhưng tool hỗ trợ)

---

### 3. Loại bỏ tính năng

```
Search references → Deprecation notice → Wait 1 version → Remove → Clean up
```

**Prevention gates**:
- LSP find-references + grep: tìm TẤT CẢ references (backend + frontend)
- Dead code (0 references) → xóa trực tiếp, P3
- Active code (có references) → deprecation path bắt buộc

**Enforcement**:
- CI pass sau khi remove (automated)
- grep confirm không còn orphan references

---

### 4. Sửa security vulnerabilities

```
Triage → Workaround → Minimal fix + regression test → Deploy → Rotate creds → Post-mortem
```

**Prevention gates**:
- Root cause: TẠI SAO vuln tồn tại? Process nào bỏ sót?
- Regression test: MỌI security fix PHẢI có test mới
- Security review: fix có tạo vuln mới không?

**Enforcement**:
- Test bắt được vuln (automated regression)
- Post-mortem document (manual)

---

### 5. Nâng cấp libs/third parties

```
Read changelog → 1 dep at a time → Test → Commit separate → Verify
```

**Prevention gates**:
- Đọc breaking changes TRƯỚC khi upgrade
- Pin exact version: `package==X.Y.Z`, KHÔNG dùng `>=`
- 1 dependency per commit (để git bisect)

**Enforcement**:
- CI pass sau mỗi dependency upgrade (automated)
- requirements.txt pin check (pre-commit hook)

---

### 6. Sửa bugs/issues

```
Root cause analysis → Minimal fix + regression test → Verify → Merge
```

**Prevention gates**:
- Root cause: hỏi "tại sao?" cho đến khi chạm architectural issue
- Regression test: MỌI bug fix PHẢI có test mới. Không có test = chưa xong.
- Minimal fix: chỉ sửa root cause, KHÔNG refactor xung quanh

**Enforcement**:
- CI pass (automated)
- Bug fix PHẢI có test mới (review check)

---

## Incident Response

Khi có lỗi trên production:

```
DETECT → TRIAGE → FIX → VERIFY → POST-MORTEM
```

### Detect (hiện tại: user report, sẽ có: monitoring)

```
Hiện tại:
  - User gọi điện báo không scan được
  - Chủ động mở dashboard thấy lỗi

Khi có monitoring (v3.1.0):
  - Telegram alert khi: server down, disk > 90%, camera offline > 5min
  - /health endpoint cho external uptime monitor
```

### Triage

```
P0 (system down / data loss)     → Hotfix ngay, deploy trong 15 phút
P1 (1 flow broken)               → Fix trong ngày
P2 (UI issue)                    → Normal flow, next release
```

### Post-mortem (P0/P1 bắt buộc)

Ghi vào `docs/incidents/YYYY-MM-DD-title.md`:
- Timeline: xảy ra khi nào → phát hiện khi nào → fix khi nào
- Root cause: không phải "typo ở line X" mà là "tại sao typo không bị bắt?"
- Action item: process/tool nào cần thêm để không lặp lại

---

## Tooling Status & Roadmap

### Hiện có (v3.5.0)

| Tool | Enforce cái gì | Layer |
|---|---|---|
| ruff (CI) | Lint check | CI |
| pytest (CI) | Test pass | CI |
| vite build (CI) | Frontend build | CI |
| Branch protection | PR + review cho master | GitHub |
| AGENTS.md | AI session rules | Auto-load |
| Pre-commit hooks | Lint + test trước khi commit | Local |
| E2E tests | Frontend flow verification | CI |

### Thiếu — theo thứ tự ưu tiên

| # | Tool | Enforce cái gì | Giải quyết vấn đề |
|---|---|---|---|
| 2 | **Structured logging** | Thay print() → logging module | Debug được khi có incident |
| 3 | **pip-audit / npm audit** | Scan dependency vulnerabilities | P0 security issues |
| 4 | **DB backup cron** | Daily backup recordings DB | Data loss prevention |
| 5 | **Health endpoint + Telegram alert** | Server/camera/disk monitoring | Detect issues trong < 5 phút |
| 6 | **pytest-cov** | Test coverage report | Biết module nào thiếu test |
| 7 | **Integration tests** | End-to-end scan→record→video flow | Catch cross-module bugs |
| 8 | **Process manager** | Auto-restart khi crash | Availability |
| 10 | **Rollback mechanism** | 1-click revert | Recoverability |

### Metrics — chỉ đo những gì có tooling

| Metric | Đo bằng | Mục tiêu |
|---|---|---|
| CI pass rate | GitHub Actions | 100% (tất cả PR phải green) |
| Test count | pytest output | Không giảm sau mỗi release |
| Lint error count | ruff output | 0 trên CI |
| Build duration | GitHub Actions | < 5 phút total |

Khi có tooling thêm (v3.1+):

| Metric | Đo bằng | Mục tiêu |
|---|---|---|
| Test coverage | pytest-cov | > 80% core modules |
| Vulnerability count | pip-audit | 0 critical/high |
| Uptime | monitoring | > 99.5% trong giờ làm việc |
| Backup success | cron log | 100% daily |

---

## Document Maintenance

Document này sẽ outdated nếu không review. Nguyên tắc:

- **Review mỗi lần bump minor version** (v3.1.0, v3.2.0, ...)
- **Update status markers** (⚠️ CHƯA SETUP → ✅ ĐANG CHẠY) khi implement tooling
- **Xóa rules không còn áp dụng** — document chết khi chứa rules ai cũng ignore
- **Giảm không tăng** — thêm rule mới thì tìm rule cũ có thể gộp/xóa
