from dataclasses import asdict
from datetime import UTC, datetime, timedelta

import httpx2
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import Paper, Source
from app.services.feeds import PaperEntry, parse_feed

FETCH_INTERVAL = timedelta(minutes=30)


def upsert_papers(session: Session, source: Source, entries: list[PaperEntry]) -> None:
    """Insert new papers; overwrite an existing one only with a newer version."""
    # One row per id: Postgres refuses to upsert the same row twice in one statement.
    latest = {e.external_id: e for e in sorted(entries, key=lambda e: e.version)}
    if not latest:
        return
    stmt = insert(Paper).values([asdict(e) | {"source_id": source.id} for e in latest.values()])
    updated = ["version", "title", "authors", "abstract", "categories", "link", "published_at"]
    session.execute(
        stmt.on_conflict_do_update(
            index_elements=[Paper.external_id],
            set_={col: stmt.excluded[col] for col in updated} | {"fetched_at": func.now()},
            where=Paper.version < stmt.excluded.version,
        )
    )


def fetch_source(session: Session, client: httpx2.Client, source: Source) -> None:
    headers = {}
    if source.etag:
        headers["If-None-Match"] = source.etag
    if source.last_modified:
        headers["If-Modified-Since"] = source.last_modified
    response = client.get(source.url, headers=headers)
    if response.status_code != 304:
        response.raise_for_status()
        upsert_papers(session, source, parse_feed(source.kind, response.content))
        source.etag = response.headers.get("ETag")
        source.last_modified = response.headers.get("Last-Modified")
    source.next_fetch_at = datetime.now(UTC) + FETCH_INTERVAL


def run_cycle(session: Session, client: httpx2.Client) -> None:
    """Fetch every active source that is due, committing after each one."""
    due = session.scalars(
        select(Source)
        .where(Source.active, Source.next_fetch_at <= datetime.now(UTC))
        .order_by(Source.id)
    ).all()
    for source in due:
        # shortcut: an error stops the cycle (earlier sources stay committed), backoff comes next.
        fetch_source(session, client, source)
        session.commit()
