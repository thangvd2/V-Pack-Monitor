"""Initial schema

Revision ID: initial_schema
Revises:
Create Date: 2026-05-01 23:12:49.019696

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "initial_schema"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. packing_video
    op.execute("""
        CREATE TABLE IF NOT EXISTS packing_video (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            station_id INTEGER DEFAULT 1,
            waybill_code TEXT NOT NULL,
            video_paths TEXT NOT NULL,
            record_mode TEXT NOT NULL,
            recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'READY' CHECK(status IN ('READY', 'RECORDING', 'PROCESSING', 'FAILED', 'SYNCED')),
            is_synced INTEGER DEFAULT 0,
            duration REAL DEFAULT 0
        )
    """)

    # 2. system_settings
    op.execute("""
        CREATE TABLE IF NOT EXISTS system_settings (
            config_key TEXT PRIMARY KEY,
            config_value TEXT
        )
    """)

    # 3. stations
    op.execute("""
        CREATE TABLE IF NOT EXISTS stations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            ip_camera_1 TEXT,
            ip_camera_2 TEXT,
            safety_code TEXT,
            camera_mode TEXT DEFAULT 'SINGLE',
            camera_brand TEXT DEFAULT 'imou',
            mac_address TEXT DEFAULT ''
        )
    """)

    # 4. users
    op.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'OPERATOR' CHECK(role IN ('ADMIN', 'OPERATOR')),
            full_name TEXT NOT NULL DEFAULT '',
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            must_change_password INTEGER DEFAULT 0
        )
    """)

    # 5. sessions
    op.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            station_id INTEGER NOT NULL,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'ACTIVE' CHECK(status IN ('ACTIVE', 'EXPIRED')),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (station_id) REFERENCES stations(id) ON DELETE CASCADE
        )
    """)

    # 6. audit_log
    op.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            details TEXT,
            station_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        )
    """)

    # 7. revoked_tokens
    op.execute("""
        CREATE TABLE IF NOT EXISTS revoked_tokens (
            jti TEXT PRIMARY KEY,
            expires_at REAL NOT NULL
        )
    """)

    # 8. Indexes
    op.execute("CREATE INDEX IF NOT EXISTS idx_pv_recorded_at ON packing_video(recorded_at DESC)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_pv_station_id ON packing_video(station_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_pv_status ON packing_video(status)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_pv_station_date ON packing_video(station_id, recorded_at DESC)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_sessions_station_status ON sessions(station_id, status)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_packing_video_waybill_code ON packing_video(waybill_code)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status)")

    # 9. FTS5 Virtual Table
    op.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS packing_video_fts USING fts5(
            waybill_code,
            content='packing_video',
            content_rowid='id',
            tokenize='trigram'
        )
    """)

    # 10. Triggers for FTS5
    op.execute("""
        CREATE TRIGGER IF NOT EXISTS packing_video_fts_insert AFTER INSERT ON packing_video BEGIN
            INSERT INTO packing_video_fts(rowid, waybill_code) VALUES (new.id, new.waybill_code);
        END
    """)
    op.execute("""
        CREATE TRIGGER IF NOT EXISTS packing_video_fts_update AFTER UPDATE ON packing_video BEGIN
            INSERT INTO packing_video_fts(packing_video_fts, rowid, waybill_code)
                VALUES ('delete', old.id, old.waybill_code);
            INSERT INTO packing_video_fts(rowid, waybill_code) VALUES (new.id, new.waybill_code);
        END
    """)
    op.execute("""
        CREATE TRIGGER IF NOT EXISTS packing_video_fts_delete AFTER DELETE ON packing_video BEGIN
            INSERT INTO packing_video_fts(packing_video_fts, rowid, waybill_code)
                VALUES ('delete', old.id, old.waybill_code);
        END
    """)


def downgrade() -> None:
    # Reverse of upgrade
    op.execute("DROP TRIGGER IF EXISTS packing_video_fts_delete")
    op.execute("DROP TRIGGER IF EXISTS packing_video_fts_update")
    op.execute("DROP TRIGGER IF EXISTS packing_video_fts_insert")
    op.execute("DROP TABLE IF EXISTS packing_video_fts")

    op.execute("DROP INDEX IF EXISTS idx_sessions_status")
    op.execute("DROP INDEX IF EXISTS idx_packing_video_waybill_code")
    op.execute("DROP INDEX IF EXISTS idx_audit_log_created_at")
    op.execute("DROP INDEX IF EXISTS idx_audit_log_user_id")
    op.execute("DROP INDEX IF EXISTS idx_sessions_user_id")
    op.execute("DROP INDEX IF EXISTS idx_sessions_station_status")
    op.execute("DROP INDEX IF EXISTS idx_pv_station_date")
    op.execute("DROP INDEX IF EXISTS idx_pv_status")
    op.execute("DROP INDEX IF EXISTS idx_pv_station_id")
    op.execute("DROP INDEX IF EXISTS idx_pv_recorded_at")

    op.execute("DROP TABLE IF EXISTS revoked_tokens")
    op.execute("DROP TABLE IF EXISTS audit_log")
    op.execute("DROP TABLE IF EXISTS sessions")
    op.execute("DROP TABLE IF EXISTS users")
    op.execute("DROP TABLE IF EXISTS stations")
    op.execute("DROP TABLE IF EXISTS system_settings")
    op.execute("DROP TABLE IF EXISTS packing_video")
