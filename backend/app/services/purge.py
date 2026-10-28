from datetime import UTC, datetime, timedelta

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models import Paper


def purge_papers(session: Session, retention_days: int) -> int:
    """Delete papers fetched more than retention_days ago; return how many."""
    cutoff = datetime.now(UTC) - timedelta(days=retention_days)
    return session.execute(delete(Paper).where(Paper.fetched_at < cutoff)).rowcount
