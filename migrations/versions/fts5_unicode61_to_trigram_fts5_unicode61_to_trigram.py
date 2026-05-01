"""fts5_unicode61_to_trigram

Revision ID: fts5_unicode61_to_trigram
Revises: initial_schema
Create Date: 2026-05-01 23:13:32.143576

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "fts5_unicode61_to_trigram"
down_revision: str | Sequence[str] | None = "initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()

    # Check if packing_video_fts uses unicode61
    result = conn.execute(
        sa.text("SELECT sql FROM sqlite_master WHERE type='table' AND name='packing_video_fts'")
    ).fetchone()
    if result:
        fts_sql = result[0] or ""
        if "unicode61" in fts_sql:
            # Drop old table and triggers
            conn.execute(sa.text("DROP TABLE IF EXISTS packing_video_fts"))
            conn.execute(sa.text("DROP TRIGGER IF EXISTS packing_video_fts_insert"))
            conn.execute(sa.text("DROP TRIGGER IF EXISTS packing_video_fts_update"))
            conn.execute(sa.text("DROP TRIGGER IF EXISTS packing_video_fts_delete"))

            # Recreate with trigram
            conn.execute(
                sa.text("""
                CREATE VIRTUAL TABLE IF NOT EXISTS packing_video_fts USING fts5(
                    waybill_code,
                    content='packing_video',
                    content_rowid='id',
                    tokenize='trigram'
                )
            """)
            )

            # Recreate triggers
            conn.execute(
                sa.text("""
                CREATE TRIGGER IF NOT EXISTS packing_video_fts_insert AFTER INSERT ON packing_video BEGIN
                    INSERT INTO packing_video_fts(rowid, waybill_code) VALUES (new.id, new.waybill_code);
                END
            """)
            )
            conn.execute(
                sa.text("""
                CREATE TRIGGER IF NOT EXISTS packing_video_fts_update AFTER UPDATE ON packing_video BEGIN
                    INSERT INTO packing_video_fts(packing_video_fts, rowid, waybill_code)
                        VALUES ('delete', old.id, old.waybill_code);
                    INSERT INTO packing_video_fts(rowid, waybill_code) VALUES (new.id, new.waybill_code);
                END
            """)
            )
            conn.execute(
                sa.text("""
                CREATE TRIGGER IF NOT EXISTS packing_video_fts_delete AFTER DELETE ON packing_video BEGIN
                    INSERT INTO packing_video_fts(packing_video_fts, rowid, waybill_code)
                        VALUES ('delete', old.id, old.waybill_code);
                END
            """)
            )

            # Rebuild index
            conn.execute(sa.text("INSERT INTO packing_video_fts(packing_video_fts) VALUES ('rebuild')"))


def downgrade() -> None:
    pass
