# Plan 49: Database Migration System (Alembic)

**Ngày**: 2026-04-24
**Mức độ**: Low — Schema hiện ổn định, migration viết tay đang work
**Loại**: Infrastructure improvement

---

## Problem

Database schema migration hiện viết tay trong `database.py`:
- `init_db()` kiểm tra `PRAGMA table_info` rồi `ALTER TABLE ADD COLUMN`
- Crypto migration `_migrate_v1_to_v2()` chạy on startup
- Không có rollback capability
- Không track migration history

Khi schema phức tạp hơn (nhiều table, FK changes, data transforms), viết tay dễ bug.

---

## Scope

### Files to add:
- `alembic.ini` — Alembic configuration
- `migrations/` — Migration directory
- `migrations/env.py` — Alembic environment (connect to SQLite)
- `migrations/versions/` — Individual migration files

### Migration steps:
1. Install: `pip install alembic` → add to requirements.txt
2. Init: `alembic init migrations`
3. Generate initial migration from current schema
4. Replace hand-written migrations in `init_db()` with `alembic upgrade head`
5. Keep `_migrate_v1_to_v2()` as data migration within Alembic

### Integration with app startup:
```python
# api.py lifespan
from alembic.config import Config
from alembic import command
alembic_cfg = Config("alembic.ini")
command.upgrade(alembic_cfg, "head")
```

---

## Constraints

- Alembic chỉ thêm vào requirements.txt (prod dependency)
- Initial migration phải capture full current schema
- Crypto migration giữ nguyên logic, chỉ wrap trong Alembic migration
- `init_db()` vẫn handle initial table creation (fallback nếu Alembic chưa run)
- Phải test với existing production DB (không break data)

---

## Decision

**Khuyến nghị: KHÔNG LÀM NGAY.** Schema ổn định (không thêm table mới gần đây). Chỉ implement khi:
- Thêm table/relationship mới
- Cần rollback capability
- Schema changes trở nên frequent

Giữ plan này trong backlog.

---

## Verification

- [ ] `alembic upgrade head` idempotent trên DB mới
- [ ] `alembic upgrade head` trên production DB (không break)
- [ ] `pytest tests/ -q` pass
- [ ] Existing data preserved after migration
