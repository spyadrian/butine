"""drop affiliations from arxiv authors

Revision ID: 2343117945c5
Revises: 64d18eb3aee3
Create Date: 2026-11-08 17:22:35.497663

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.services.feeds import split_arxiv_authors

# revision identifiers, used by Alembic.
revision: str = "2343117945c5"
down_revision: str | Sequence[str] | None = "64d18eb3aee3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Data only: the old parser split "A (Dept, Univ)" at every comma; rejoin then split again.
    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            "SELECT id, authors FROM papers"
            " WHERE external_id LIKE 'arxiv:%' AND array_to_string(authors, ' ') ~ '[()]'"
        )
    ).all()
    for paper_id, authors in rows:
        conn.execute(
            sa.text("UPDATE papers SET authors = :authors WHERE id = :id"),
            {"authors": split_arxiv_authors(", ".join(authors)), "id": paper_id},
        )


def downgrade() -> None:
    """Downgrade schema."""
    # The affiliations are not kept; the cleanup cannot be undone.
