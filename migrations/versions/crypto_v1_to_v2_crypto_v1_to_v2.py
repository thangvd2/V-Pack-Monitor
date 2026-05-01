"""crypto_v1_to_v2

Revision ID: crypto_v1_to_v2
Revises: fts5_unicode61_to_trigram
Create Date: 2026-05-01 23:13:58.359037

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "crypto_v1_to_v2"
down_revision: str | Sequence[str] | None = "fts5_unicode61_to_trigram"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


import os
import sys

# Add project root to sys.path to import database module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import database


def upgrade() -> None:
    # Run the existing crypto migration logic
    database._migrate_v1_to_v2()


def downgrade() -> None:
    pass
