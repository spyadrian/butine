"""add name and icon to prompts

Revision ID: 64d18eb3aee3
Revises: c42a7cc923d3
Create Date: 2026-11-08 17:08:23.744714

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "64d18eb3aee3"
down_revision: str | Sequence[str] | None = "c42a7cc923d3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def first_words(text: str, limit: int = 24) -> str:
    """Whole leading words of `text` within `limit` chars; cuts a longer first word."""
    if len(text) <= limit:
        return text
    return text[: limit + 1].rsplit(" ", 1)[0][:limit].rstrip()


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("prompts", sa.Column("name", sa.String(length=24), nullable=True))
    op.add_column("prompts", sa.Column("icon", sa.String(length=40), nullable=True))
    conn = op.get_bind()
    for prompt_id, text in conn.execute(sa.text("SELECT id, text FROM prompts")).all():
        conn.execute(
            sa.text("UPDATE prompts SET name = :name, icon = 'label' WHERE id = :id"),
            {"name": first_words(text), "id": prompt_id},
        )
    op.alter_column("prompts", "name", nullable=False)
    op.alter_column("prompts", "icon", nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("prompts", "icon")
    op.drop_column("prompts", "name")


assert first_words("graph neural networks for chemistry") == "graph neural networks"
assert first_words("protein folding") == "protein folding"
assert first_words("x" * 30) == "x" * 24
