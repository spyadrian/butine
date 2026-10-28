from dataclasses import asdict
from datetime import UTC, datetime, timedelta

import httpx2
from sqlalchemy import func, literal_column, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import Paper, Source
from app.services.feeds import FeedError, PaperEntry, parse_feed

FETCH_INTERVAL = timedelta(minutes=30)
MAX_BACKOFF = timedelta(hours=24)
MAX_FAILURES = 10


def upsert_papers(session: Session, source: Source, entries: list[PaperEntry]) -> tuple[int, int]:
    """Insert new papers; overwrite an existing one only with a newer version.

    Return (new, updated) counts.
    """
    # One row per id: Postgres refuses to upsert the same row twice in one statement.
    latest = {e.external_id: e for e in sorted(entries, key=lambda e: e.version)}
    if not latest:
        return 0, 0
    stmt = insert(Paper).values([asdict(e) | {"source_id": source.id} for e in latest.values()])
    updated = ["version", "title", "authors", "abstract", "categories", "link", "published_at"]
    # Postgres leaves xmax at 0 on freshly inserted rows, so it tells inserts from updates.
    inserted = session.scalars(
        stmt.on_conflict_do_update(
            index_elements=[Paper.external_id],
            set_={col: stmt.excluded[col] for col in updated} | {"fetched_at": func.now()},
            where=Paper.version < stmt.excluded.version,
        ).returning(literal_column("xmax = 0"))
    ).all()
    new = sum(inserted)
    return new, len(inserted) - new


def fetch_source(session: Session, client: httpx2.Client, source: Source) -> tuple[int, int]:
    """Fetch one source; return (new, updated) paper counts."""
    headers = {}
    if source.etag:
        headers["If-None-Match"] = source.etag
    if source.last_modified:
        headers["If-Modified-Since"] = source.last_modified
    response = client.get(source.url, headers=headers)
    counts = 0, 0
    if response.status_code != 304:
        response.raise_for_status()
        counts = upsert_papers(session, source, parse_feed(source.kind, response.content))
        source.etag = response.headers.get("ETag")
        source.last_modified = response.headers.get("Last-Modified")
    source.consecutive_failures = 0
    source.next_fetch_at = datetime.now(UTC) + FETCH_INTERVAL
    return counts


def record_failure(source: Source, error: Exception) -> None:
    """Back off exponentially, and give up on the source after MAX_FAILURES in a row."""
    source.consecutive_failures += 1
    source.last_error = f"{type(error).__name__}: {error}"
    backoff = FETCH_INTERVAL * 2 ** (source.consecutive_failures - 1)
    source.next_fetch_at = datetime.now(UTC) + min(backoff, MAX_BACKOFF)
    if source.consecutive_failures >= MAX_FAILURES:
        source.active = False


def run_cycle(session: Session, client: httpx2.Client) -> dict[str, int]:
    """Fetch every active source that is due, committing after each one; return counts."""
    due = session.scalars(
        select(Source)
        .where(Source.active, Source.next_fetch_at <= datetime.now(UTC))
        .order_by(Source.id)
    ).all()
    stats = {"feeds_polled": len(due), "new_papers": 0, "updated_papers": 0, "errors": 0}
    for source in due:
        try:
            # Savepoint: a failure undoes only this source's partial writes.
            with session.begin_nested():
                new, updated = fetch_source(session, client, source)
            stats["new_papers"] += new
            stats["updated_papers"] += updated
        except (httpx2.HTTPError, FeedError) as error:
            record_failure(source, error)
            stats["errors"] += 1
        session.commit()
    return stats
