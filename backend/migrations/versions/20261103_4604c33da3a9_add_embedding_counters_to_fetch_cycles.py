"""add embedding counters to fetch cycles

Revision ID: 4604c33da3a9
Revises: ac78fbd3db33
Create Date: 2026-11-03 11:47:28.743256

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4604c33da3a9"
down_revision: str | Sequence[str] | None = "ac78fbd3db33"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Existing cycles get 0, then the default goes so the worker must always set them.
    for column in ("embedded_papers", "pending_embeddings"):
        op.add_column(
            "fetch_cycles", sa.Column(column, sa.Integer(), nullable=False, server_default="0")
        )
        op.alter_column("fetch_cycles", column, server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("fetch_cycles", "pending_embeddings")
    op.drop_column("fetch_cycles", "embedded_papers")
