# =============================================================================
# V-Pack Monitor - CamDongHang v2.1.0
# Copyright (c) 2024-2026 VDT - Vu Duc Thang (thangvd2)
# All rights reserved. Unauthorized copying or distribution is prohibited.
# =============================================================================

import sqlite3
import os
import time as _time
import hashlib
import base64
from datetime import datetime, timezone

_ENCRYPT_PREFIX = "enc:v1:"


_DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recordings")
os.makedirs(_DB_DIR, exist_ok=True)


def _get_enc_key():
    try:
        from auth import SECRET_KEY
        if SECRET_KEY:
            return hashlib.sha256(SECRET_KEY.encode()).digest()
    except (ImportError, AttributeError):
        pass
    fallback = os.environ.get("VPACK_SECRET", "vpack-default-encryption-key")
    return hashlib.sha256(fallback.encode()).digest()


def _encrypt_value(plaintext: str) -> str:
    key = _get_enc_key()
    raw = plaintext.encode("utf-8")
    encrypted = bytes(a ^ b for a, b in zip(raw, (key * (len(raw) // len(key) + 1))[:len(raw)]))
    return _ENCRYPT_PREFIX + base64.b64encode(encrypted).decode()


def _decrypt_value(ciphertext: str) -> str:
    if not ciphertext.startswith(_ENCRYPT_PREFIX):
        return ciphertext
    key = _get_enc_key()
    encrypted = base64.b64decode(ciphertext[len(_ENCRYPT_PREFIX):])
    decrypted = bytes(a ^ b for a, b in zip(encrypted, (key * (len(encrypted) // len(key) + 1))[:len(encrypted)]))
    try:
        return decrypted.decode("utf-8")
    except UnicodeDecodeError:
        return ciphertext


_SENSITIVE_KEYS = {"S3_SECRET_KEY", "S3_ACCESS_KEY", "TELEGRAM_BOT_TOKEN"}

DB_FILE = "recordings/packing_records.db"


def init_db():
    if not os.path.exists("recordings"):
        os.makedirs("recordings")

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS packing_video (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                station_id INTEGER DEFAULT 1,
                waybill_code TEXT NOT NULL,
                video_paths TEXT NOT NULL,
                record_mode TEXT NOT NULL,
                recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Check and add columns if not exists (for migration)
        cursor.execute("PRAGMA table_info(packing_video);")
        columns = [col[1] for col in cursor.fetchall()]
        if "station_id" not in columns:
            cursor.execute(
                "ALTER TABLE packing_video ADD COLUMN station_id INTEGER DEFAULT 1;"
            )
        if "is_synced" not in columns:
            cursor.execute(
                "ALTER TABLE packing_video ADD COLUMN is_synced INTEGER DEFAULT 0;"
            )
        if "status" not in columns:
            cursor.execute(
                "ALTER TABLE packing_video ADD COLUMN status TEXT DEFAULT 'READY';"
            )

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_settings (
                config_key TEXT PRIMARY KEY,
                config_value TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                ip_camera_1 TEXT,
                ip_camera_2 TEXT,
                safety_code TEXT,
                camera_mode TEXT DEFAULT 'SINGLE',
                camera_brand TEXT DEFAULT 'imou'
            )
        """)

        cursor.execute("PRAGMA table_info(stations);")
        st_cols = [col[1] for col in cursor.fetchall()]
        if "camera_brand" not in st_cols:
            cursor.execute(
                "ALTER TABLE stations ADD COLUMN camera_brand TEXT DEFAULT 'imou';"
            )
        if "mac_address" not in st_cols:
            cursor.execute(
                "ALTER TABLE stations ADD COLUMN mac_address TEXT DEFAULT '';"
            )

        # Migrate old settings to station 1 if stations table is empty
        cursor.execute("SELECT COUNT(*) FROM stations")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "SELECT config_value FROM system_settings WHERE config_key = 'IP_CAMERA'"
            )
            ip_row = cursor.fetchone()
            ip1 = ip_row[0] if ip_row else ""

            cursor.execute(
                "SELECT config_value FROM system_settings WHERE config_key = 'SAFETY_CODE'"
            )
            code_row = cursor.fetchone()
            code = code_row[0] if code_row else ""

            cursor.execute(
                "SELECT config_value FROM system_settings WHERE config_key = 'RECORD_MODE'"
            )
            mode_row = cursor.fetchone()
            mode = mode_row[0] if mode_row else "SINGLE"

            cursor.execute(
                """
                INSERT INTO stations (name, ip_camera_1, ip_camera_2, safety_code, camera_mode, camera_brand)
                VALUES ('Bàn Chốt Đơn 1', ?, '', ?, ?, 'imou')
            """,
                (ip1, code, mode),
            )

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'OPERATOR',
                full_name TEXT NOT NULL DEFAULT '',
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                must_change_password INTEGER DEFAULT 0
            )
        """)
        cursor.execute("PRAGMA table_info(users);")
        user_cols = [col[1] for col in cursor.fetchall()]
        if "must_change_password" not in user_cols:
            cursor.execute(
                "ALTER TABLE users ADD COLUMN must_change_password INTEGER DEFAULT 0;"
            )

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                station_id INTEGER NOT NULL,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'ACTIVE',
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (station_id) REFERENCES stations(id)
            )
        """)

        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            import bcrypt as _bcrypt

            hashed = _bcrypt.hashpw(
                "08012011".encode("utf-8"), _bcrypt.gensalt()
            ).decode("utf-8")
            cursor.execute(
                "INSERT INTO users (username, password_hash, role, full_name, must_change_password) VALUES (?, ?, 'ADMIN', 'Administrator', 1)",
                ("admin", hashed),
            )
            print("Default admin created. Please login and change password.")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                details TEXT,
                station_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Clean up audit logs older than 90 days
        cursor.execute(
            "DELETE FROM audit_log WHERE created_at < datetime('now', '-90 days')"
        )

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS revoked_tokens (
                jti TEXT PRIMARY KEY,
                expires_at REAL NOT NULL
            )
        """)
        cursor.execute("DELETE FROM revoked_tokens WHERE expires_at < ?", (_time.time(),))

        # Expire all stale sessions on startup
        cursor.execute("UPDATE sessions SET status = 'EXPIRED' WHERE status = 'ACTIVE'")

        conn.commit()

        # --- Indexes for packing_video ---
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pv_recorded_at ON packing_video(recorded_at DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pv_station_id ON packing_video(station_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pv_status ON packing_video(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pv_station_date ON packing_video(station_id, recorded_at DESC)")

        # --- FTS5 virtual table (external content, trigram for substring search) ---
        # Migration: drop old unicode61 FTS5 table if it exists (tokenizer cannot be altered)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='packing_video_fts'")
        if cursor.fetchone():
            # Check if it's the old unicode61 version — if so, drop and recreate
            try:
                cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='packing_video_fts'")
                fts_sql = cursor.fetchone()[0] or ""
                if "unicode61" in fts_sql:
                    cursor.execute("DROP TABLE IF EXISTS packing_video_fts")
                    # Drop triggers too — they'll be recreated below
                    cursor.execute("DROP TRIGGER IF EXISTS packing_video_fts_insert")
                    cursor.execute("DROP TRIGGER IF EXISTS packing_video_fts_update")
                    cursor.execute("DROP TRIGGER IF EXISTS packing_video_fts_delete")
            except Exception:
                pass

        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS packing_video_fts USING fts5(
                waybill_code,
                content='packing_video',
                content_rowid='id',
                tokenize='trigram'
            )
        """)

        # --- Triggers for auto-sync FTS5 ---
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS packing_video_fts_insert AFTER INSERT ON packing_video BEGIN
                INSERT INTO packing_video_fts(rowid, waybill_code) VALUES (new.id, new.waybill_code);
            END
        """)
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS packing_video_fts_update AFTER UPDATE ON packing_video BEGIN
                INSERT INTO packing_video_fts(packing_video_fts, rowid, waybill_code)
                    VALUES ('delete', old.id, old.waybill_code);
                INSERT INTO packing_video_fts(rowid, waybill_code) VALUES (new.id, new.waybill_code);
            END
        """)
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS packing_video_fts_delete AFTER DELETE ON packing_video BEGIN
                INSERT INTO packing_video_fts(packing_video_fts, rowid, waybill_code)
                    VALUES ('delete', old.id, old.waybill_code);
            END
        """)

        # Rebuild FTS5 index from existing data (safe to call multiple times)
        try:
            _rebuild_fts_index()
        except Exception:
            pass  # FTS5 may not be available on all SQLite builds

        conn.commit()


def _rebuild_fts_index():
    """Populate FTS5 index from existing packing_video records. Safe to call multiple times."""
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("INSERT INTO packing_video_fts(packing_video_fts) VALUES ('rebuild')")
        conn.commit()


def get_setting(key, default=None):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT config_value FROM system_settings WHERE config_key = ?", (key,)
        )
        row = cursor.fetchone()
        if row:
            return _decrypt_value(row[0])
        return default


def set_setting(key, value):
    str_val = str(value)
    if key in _SENSITIVE_KEYS and str_val:
        str_val = _encrypt_value(str_val)
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO system_settings (config_key, config_value)
            VALUES (?, ?)
            ON CONFLICT(config_key) DO UPDATE SET config_value=excluded.config_value
        """,
            (key, str_val),
        )
        conn.commit()


def get_all_settings():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT config_key, config_value FROM system_settings")
        rows = cursor.fetchall()
        return {k: _decrypt_value(v) for k, v in rows}


def set_settings(settings_dict):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        for k, v in settings_dict.items():
            str_val = str(v)
            if k in _SENSITIVE_KEYS and str_val:
                str_val = _encrypt_value(str_val)
            cursor.execute(
                """
                INSERT INTO system_settings (config_key, config_value)
                VALUES (?, ?)
                ON CONFLICT(config_key) DO UPDATE SET config_value=excluded.config_value
            """,
                (k, str_val),
            )
        conn.commit()


def save_record(station_id, waybill_code, video_paths, record_mode):
    paths_str = ",".join(video_paths)
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO packing_video (station_id, waybill_code, video_paths, record_mode, recorded_at)
            VALUES (?, ?, ?, ?, ?)
        """,
            (station_id, waybill_code, paths_str, record_mode, datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")),
        )
        conn.commit()


def create_record(station_id, waybill_code, record_mode, video_paths=""):
    paths_str = ",".join(video_paths) if isinstance(video_paths, list) else video_paths
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO packing_video (station_id, waybill_code, video_paths, record_mode, recorded_at, status)
            VALUES (?, ?, ?, ?, ?, 'RECORDING')""",
            (station_id, waybill_code, paths_str, record_mode, datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")),
        )
        conn.commit()
        return cursor.lastrowid


def update_record_status(record_id, status, video_paths=None):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        if video_paths is not None:
            paths_str = (
                ",".join(video_paths) if isinstance(video_paths, list) else video_paths
            )
            cursor.execute(
                "UPDATE packing_video SET status = ?, video_paths = ? WHERE id = ?",
                (status, paths_str, record_id),
            )
        else:
            cursor.execute(
                "UPDATE packing_video SET status = ? WHERE id = ?",
                (status, record_id),
            )
        conn.commit()


def get_pending_records():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, station_id, waybill_code, video_paths, record_mode, status FROM packing_video WHERE status IN ('RECORDING', 'PROCESSING')"
        )
        rows = cursor.fetchall()
        return [
            {
                "id": r[0],
                "station_id": r[1],
                "waybill_code": r[2],
                "video_paths": r[3],
                "record_mode": r[4],
                "status": r[5],
            }
            for r in rows
        ]


def get_records(search="", station_id=None):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        query = "SELECT p.id, p.waybill_code, p.video_paths, p.record_mode, p.recorded_at, s.name, p.status FROM packing_video p LEFT JOIN stations s ON p.station_id = s.id WHERE 1=1"
        params = []

        if search:
            query += " AND p.waybill_code LIKE ?"
            params.append(f"%{search}%")
            # Nếu có nhập tên mã (Global Search) thì bỏ qua filter Trạm
        else:
            if station_id:
                query += " AND p.station_id = ?"
                params.append(station_id)

        query += " ORDER BY p.id DESC LIMIT 100"
        cursor.execute(query, params)
        records = cursor.fetchall()
    return records


_SORT_COLUMNS = {
    "recorded_at": "p.recorded_at",
    "waybill_code": "p.waybill_code",
    "station_name": "s.name",
    "status": "p.status",
}


def get_records_v2(
    search: str = "",
    station_id: int | None = None,
    status: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    page: int = 1,
    limit: int = 20,
    sort_by: str = "recorded_at",
    sort_order: str = "desc",
) -> dict:
    """Paginated record search with FTS5, date range, status filter."""
    limit = min(max(limit, 1), 100)  # Clamp 1-100
    page = max(page, 1)
    offset = (page - 1) * limit

    # Validate sort
    sort_col = _SORT_COLUMNS.get(sort_by, "p.recorded_at")
    sort_dir = "DESC" if sort_order.lower() == "desc" else "ASC"

    base_select = "p.id, p.waybill_code, p.video_paths, p.record_mode, p.recorded_at, s.name, p.status"

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        params = []
        where_clauses = []

        if search:
            # Check if FTS5 table exists (graceful degradation)
            try:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='packing_video_fts'")
                has_fts = cursor.fetchone() is not None
            except Exception:
                has_fts = False

            # Trigram tokenizer requires >= 3 chars for indexed match.
            # For short queries, fall back to LIKE (which works fine for small result sets).
            use_fts = has_fts and len(search) >= 3

            if use_fts:
                # FTS5 trigram: substring match (no prefix * needed)
                from_clause = "packing_video p JOIN packing_video_fts fts ON fts.rowid = p.id LEFT JOIN stations s ON p.station_id = s.id"
                safe_search = search.replace('"', '""')
                where_clauses.append("fts.waybill_code MATCH ?")
                params.append(f'"{safe_search}"')
            else:
                # Fallback to LIKE for short queries or if FTS5 not available
                from_clause = "packing_video p LEFT JOIN stations s ON p.station_id = s.id"
                where_clauses.append("p.waybill_code LIKE ?")
                params.append(f"%{search}%")
        else:
            from_clause = "packing_video p LEFT JOIN stations s ON p.station_id = s.id"

        if station_id is not None:
            where_clauses.append("p.station_id = ?")
            params.append(station_id)

        if status is not None:
            where_clauses.append("p.status = ?")
            params.append(status)

        if date_from is not None:
            where_clauses.append("date(p.recorded_at, 'localtime') >= ?")
            params.append(date_from)

        if date_to is not None:
            where_clauses.append("date(p.recorded_at, 'localtime') <= ?")
            params.append(date_to)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        # Count query
        count_query = f"SELECT COUNT(*) FROM {from_clause} WHERE {where_sql}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]

        # Data query
        data_query = f"SELECT {base_select} FROM {from_clause} WHERE {where_sql} ORDER BY {sort_col} {sort_dir} LIMIT ? OFFSET ?"
        cursor.execute(data_query, params + [limit, offset])
        rows = cursor.fetchall()

    records = []
    for r in rows:
        records.append({
            "id": r[0],
            "waybill_code": r[1],
            "video_paths": [p for p in r[2].split(",") if p] if r[2] else [],
            "record_mode": r[3],
            "recorded_at": r[4],
            "station_name": r[5],
            "status": r[6],
        })

    total_pages = (total + limit - 1) // limit if limit > 0 else 0

    return {
        "records": records,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "has_more": page < total_pages,
    }


def get_record_by_id(record_id):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, waybill_code, video_paths, record_mode, recorded_at, station_id, status FROM packing_video WHERE id = ?",
            (record_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "waybill_code": row[1],
            "video_paths": row[2],
            "record_mode": row[3],
            "recorded_at": row[4],
            "station_id": row[5],
            "status": row[6],
        }


def cleanup_old_records(days=7):
    """Xóa các video và bản ghi cũ hơn X ngày để giải phóng dung lượng ổ cứng."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, video_paths FROM packing_video WHERE recorded_at <= datetime('now', '-' || ? || ' days')",
            (days,)
        )
        old_records = cursor.fetchall()

        for r_id, video_paths in old_records:
            for path in video_paths.split(","):
                if os.path.exists(path):
                    try:
                        os.remove(path)
                        print(f"🗑️ Đã dọn dẹp file cũ: {path}")
                    except Exception as e:
                        print(f"Error removing {path}: {e}")
            cursor.execute("DELETE FROM packing_video WHERE id = ?", (r_id,))
        conn.commit()


def delete_record(record_id):
    """Xoá một bản ghi cụ thể và file cứng đi kèm"""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT video_paths FROM packing_video WHERE id = ?", (record_id,)
        )
        row = cursor.fetchone()
        if row:
            for path in row[0].split(","):
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except Exception as e:
                        print(f"Error removing {path}: {e}")
            cursor.execute("DELETE FROM packing_video WHERE id = ?", (record_id,))
        conn.commit()


# --- Quản lý Danh sách Trạm ---


def get_stations():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, ip_camera_1, ip_camera_2, safety_code, camera_mode, camera_brand, mac_address FROM stations ORDER BY id ASC"
        )
        rows = cursor.fetchall()
        return [
            {
                "id": r[0],
                "name": r[1],
                "ip_camera_1": r[2],
                "ip_camera_2": r[3],
                "safety_code": r[4],
                "camera_mode": r[5],
                "camera_brand": r[6],
                "mac_address": r[7] if len(r) > 7 else "",
            }
            for r in rows
        ]


def get_station(station_id):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, ip_camera_1, ip_camera_2, safety_code, camera_mode, camera_brand, mac_address FROM stations WHERE id = ?",
            (station_id,),
        )
        row = cursor.fetchone()
        if row:
            return {
                "id": row[0],
                "name": row[1],
                "ip_camera_1": row[2],
                "ip_camera_2": row[3],
                "safety_code": row[4],
                "camera_mode": row[5],
                "camera_brand": row[6],
                "mac_address": row[7] if len(row) > 7 else "",
            }
        return None


def update_station(station_id, data):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE stations
            SET name=?, ip_camera_1=?, ip_camera_2=?, safety_code=?, camera_mode=?, camera_brand=?, mac_address=?
            WHERE id=?
        """,
            (
                data["name"],
                data["ip_camera_1"],
                data.get("ip_camera_2", ""),
                data["safety_code"],
                data["camera_mode"],
                data.get("camera_brand", "imou"),
                data.get("mac_address", ""),
                station_id,
            ),
        )
        conn.commit()


def update_station_ip(station_id, field, new_ip):
    allowed_fields = {"ip_camera_1", "ip_camera_2"}
    if field not in allowed_fields:
        return
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE stations SET {field} = ? WHERE id = ?",
            (new_ip, station_id),
        )
        conn.commit()


def add_station(data):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO stations (name, ip_camera_1, ip_camera_2, safety_code, camera_mode, camera_brand, mac_address)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                data["name"],
                data["ip_camera_1"],
                data.get("ip_camera_2", ""),
                data["safety_code"],
                data["camera_mode"],
                data.get("camera_brand", "imou"),
                data.get("mac_address", ""),
            ),
        )
        conn.commit()
        return cursor.lastrowid


def delete_station(station_id):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM stations WHERE id = ?", (station_id,))
        conn.commit()


def get_user_by_username(username):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, password_hash, role, full_name, is_active, must_change_password FROM users WHERE username = ?",
            (username,),
        )
        row = cursor.fetchone()
        if row:
            return {
                "id": row[0],
                "username": row[1],
                "password_hash": row[2],
                "role": row[3],
                "full_name": row[4],
                "is_active": row[5],
                "must_change_password": row[6] if len(row) > 6 else 0,
            }
        return None


def clear_must_change_password(user_id):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET must_change_password = 0 WHERE id = ?",
            (user_id,),
        )
        conn.commit()


def get_user_by_id(user_id):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, role, full_name, is_active FROM users WHERE id = ?",
            (user_id,),
        )
        row = cursor.fetchone()
        if row:
            return {
                "id": row[0],
                "username": row[1],
                "role": row[2],
                "full_name": row[3],
                "is_active": row[4],
            }
        return None


def get_all_users():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, role, full_name, is_active, created_at FROM users ORDER BY id ASC"
        )
        rows = cursor.fetchall()
        return [
            {
                "id": r[0],
                "username": r[1],
                "role": r[2],
                "full_name": r[3],
                "is_active": r[4],
                "created_at": r[5],
            }
            for r in rows
        ]


def create_user(username, password, role="OPERATOR", full_name=""):
    import bcrypt as _bcrypt

    hashed = _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, password_hash, role, full_name) VALUES (?, ?, ?, ?)",
                (username, hashed, role, full_name),
            )
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None


def update_user(user_id, **kwargs):
    allowed = {"role", "full_name", "is_active"}
    sets = []
    vals = []
    for k, v in kwargs.items():
        if k in allowed:
            sets.append(f"{k} = ?")
            vals.append(v)
    if not sets:
        return
    vals.append(user_id)
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE users SET {', '.join(sets)} WHERE id = ?", vals)
        conn.commit()


def update_user_password(user_id, new_password):
    import bcrypt as _bcrypt

    hashed = _bcrypt.hashpw(new_password.encode("utf-8"), _bcrypt.gensalt()).decode(
        "utf-8"
    )
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (hashed, user_id),
        )
        conn.commit()


def delete_user(user_id):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()


def create_session(user_id, station_id):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sessions (user_id, station_id, status) VALUES (?, ?, 'ACTIVE')",
            (user_id, station_id),
        )
        conn.commit()
        return cursor.lastrowid


def get_active_session(station_id):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT s.id, s.user_id, s.station_id, s.last_heartbeat, u.username, u.full_name FROM sessions s JOIN users u ON s.user_id = u.id WHERE s.station_id = ? AND s.status = 'ACTIVE'",
            (station_id,),
        )
        row = cursor.fetchone()
        if row:
            return {
                "id": row[0],
                "user_id": row[1],
                "station_id": row[2],
                "last_heartbeat": row[3],
                "username": row[4],
                "full_name": row[5],
            }
        return None


def update_session_heartbeat(session_id):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE sessions SET last_heartbeat = CURRENT_TIMESTAMP WHERE id = ?",
            (session_id,),
        )
        conn.commit()


def end_session(session_id):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE sessions SET status = 'EXPIRED' WHERE id = ?", (session_id,)
        )
        conn.commit()


def expire_stale_sessions(timeout_seconds=90):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE sessions SET status = 'EXPIRED' WHERE status = 'ACTIVE' AND strftime('%s', 'now') - strftime('%s', last_heartbeat) > ?",
            (timeout_seconds,),
        )
        conn.commit()
        return cursor.rowcount


def log_audit(
    user_id: int, action: str, details: str | None = None, station_id: int | None = None
):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO audit_log (user_id, action, details, station_id) VALUES (?, ?, ?, ?)",
            (user_id, action, details, station_id),
        )
        conn.commit()


def cleanup_audit_log(days: int = 90):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM audit_log WHERE created_at < datetime('now', ?)",
            (f"-{days} days",),
        )
        conn.commit()


def get_audit_logs(
    user_id: int | None = None,
    action: str | None = None,
    limit: int = 200,
    offset: int = 0,
) -> list[dict]:
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        query = (
            "SELECT audit_log.id, audit_log.user_id, audit_log.action, "
            "audit_log.details, audit_log.station_id, audit_log.created_at, "
            "users.username FROM audit_log LEFT JOIN users "
            "ON audit_log.user_id = users.id WHERE 1=1"
        )
        params = []
        if user_id is not None:
            query += " AND audit_log.user_id = ?"
            params.append(user_id)
        if action:
            query += " AND audit_log.action = ?"
            params.append(action)
        query += " ORDER BY audit_log.id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [
            {
                "id": r[0],
                "user_id": r[1],
                "action": r[2],
                "details": r[3],
                "station_id": r[4],
                "created_at": r[5],
                "username": r[6],
            }
            for r in rows
        ]


def get_active_sessions() -> list[dict]:
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT s.id, s.user_id, s.station_id, s.started_at, s.last_heartbeat, "
            "s.status, u.username, u.full_name, st.name AS station_name "
            "FROM sessions s JOIN users u ON s.user_id = u.id "
            "JOIN stations st ON s.station_id = st.id "
            "WHERE s.status = 'ACTIVE' ORDER BY s.started_at DESC"
        )
        rows = cursor.fetchall()
        return [
            {
                "id": r[0],
                "user_id": r[1],
                "station_id": r[2],
                "started_at": r[3],
                "last_heartbeat": r[4],
                "status": r[5],
                "username": r[6],
                "full_name": r[7],
                "station_name": r[8],
            }
            for r in rows
        ]


def get_session_by_id(session_id: int):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, user_id, station_id, status FROM sessions WHERE id = ?",
            (session_id,),
        )
        row = cursor.fetchone()
        if row:
            return {
                "id": row[0],
                "user_id": row[1],
                "station_id": row[2],
                "status": row[3],
            }
        return None


def end_session_by_id(session_id: int):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE sessions SET status = 'EXPIRED' WHERE id = ?", (session_id,)
        )
        conn.commit()


# --- ANALYTICS FUNCTIONS ---


def get_hourly_stats(
    date: str | None = None, station_id: int | None = None
) -> list[dict]:
    """Get record counts grouped by hour for a given date.
    Returns list of {hour, count} for hours 0-23.
    date format: YYYY-MM-DD, defaults to today."""
    target_date = date or datetime.now().strftime("%Y-%m-%d")
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        query = (
            "SELECT CAST(strftime('%H', recorded_at, 'localtime') AS INTEGER) as hour, COUNT(*) as count "
            "FROM packing_video WHERE status = 'READY' AND date(recorded_at, 'localtime') = ?"
        )
        params: list[str | int] = [target_date]
        if station_id is not None:
            query += " AND station_id = ?"
            params.append(station_id)
        query += " GROUP BY hour ORDER BY hour"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        hour_map = {r[0]: r[1] for r in rows}
    result = []
    for h in range(24):
        result.append({"hour": h, "count": hour_map.get(h, 0)})
    return result


def get_daily_trend(days: int = 7) -> list[dict]:
    """Get daily record counts for last N days.
    Returns list of {date, count}."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT date(recorded_at, 'localtime') as d, COUNT(*) as count "
            "FROM packing_video WHERE status = 'READY' "
            "AND date(recorded_at, 'localtime') >= date('now', 'localtime', '-' || ? || ' days') "
            "GROUP BY d ORDER BY d",
            (days,)
        )
        rows = cursor.fetchall()
        date_map = {r[0]: r[1] for r in rows}
    result = []
    from datetime import timedelta

    for i in range(days):
        d = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        result.append({"date": d, "count": date_map.get(d, 0)})
    result.reverse()
    return result


def get_stations_comparison() -> list[dict]:
    """Get today's record count per station.
    Returns list of {station_id, station_name, count}."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT s.id, s.name, COUNT(p.id) as count "
            "FROM stations s LEFT JOIN packing_video p "
            "ON s.id = p.station_id AND date(p.recorded_at, 'localtime') = date('now', 'localtime') AND p.status = 'READY' "
            "GROUP BY s.id ORDER BY count DESC"
        )
        rows = cursor.fetchall()
        return [{"station_id": r[0], "station_name": r[1], "count": r[2]} for r in rows]


def get_records_for_export(
    date: str | None = None, station_id: int | None = None
) -> list[dict]:
    """Get records for CSV export.
    Returns list of {waybill_code, station_name, recorded_at, status, video_paths}."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        query = (
            "SELECT p.waybill_code, s.name, p.recorded_at, p.status, p.video_paths "
            "FROM packing_video p JOIN stations s ON p.station_id = s.id WHERE 1=1"
        )
        params = []
        if date is not None:
            query += " AND date(p.recorded_at, 'localtime') = ?"
            params.append(date)
        if station_id is not None:
            query += " AND p.station_id = ?"
            params.append(station_id)
        query += " ORDER BY p.recorded_at DESC"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [
            {
                "waybill_code": r[0],
                "station_name": r[1],
                "recorded_at": r[2],
                "status": r[3],
                "video_paths": r[4],
            }
            for r in rows
        ]


def revoke_jti(jti: str, expires_at: float):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO revoked_tokens (jti, expires_at) VALUES (?, ?)",
            (jti, expires_at),
        )
        conn.commit()


def is_jti_revoked(jti: str) -> bool:
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM revoked_tokens WHERE jti = ?", (jti,)
        )
        return cursor.fetchone() is not None
