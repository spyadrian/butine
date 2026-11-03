"""add embeddings

Revision ID: ac78fbd3db33
Revises: fdaa4c6fd49c
Create Date: 2026-11-03 10:30:19.551063

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "ac78fbd3db33"
down_revision: str | Sequence[str] | None = "fdaa4c6fd49c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.add_column("papers", sa.Column("embedding", Vector(dim=384), nullable=True))
    op.add_column("prompts", sa.Column("embedding", Vector(dim=384), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("prompts", "embedding")
    op.drop_column("papers", "embedding")
    op.execute("DROP EXTENSION vector")
