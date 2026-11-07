"""convert latex in author names

Revision ID: c42a7cc923d3
Revises: 4604c33da3a9
Create Date: 2026-11-07 20:16:14.277126

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.services.latex import latex_to_unicode

# revision identifiers, used by Alembic.
revision: str = "c42a7cc923d3"
down_revision: str | Sequence[str] | None = "4604c33da3a9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Data only: authors imported before the parser converted LaTeX accents.
    conn = op.get_bind()
    rows = conn.execute(
        sa.text(r"SELECT id, authors FROM papers WHERE array_to_string(authors, ' ') ~ '[\\{}]'")
    ).all()
    for paper_id, authors in rows:
        conn.execute(
            sa.text("UPDATE papers SET authors = :authors WHERE id = :id"),
            {"authors": [latex_to_unicode(a) for a in authors], "id": paper_id},
        )


def downgrade() -> None:
    """Downgrade schema."""
    # The LaTeX originals are not kept; the conversion cannot be undone.
