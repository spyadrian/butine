from datetime import UTC, datetime, timedelta

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models import FetchCycle, Paper


def purge_papers(session: Session, retention_days: int) -> int:
    """Delete papers fetched more than retention_days ago; return how many."""
    cutoff = datetime.now(UTC) - timedelta(days=retention_days)
    return session.execute(delete(Paper).where(Paper.fetched_at < cutoff)).rowcount


def purge_fetch_cycles(session: Session, retention_days: int) -> None:
    """Delete cycle logs older than retention_days (one row per minute otherwise piles up)."""
    cutoff = datetime.now(UTC) - timedelta(days=retention_days)
    session.execute(delete(FetchCycle).where(FetchCycle.started_at < cutoff))
