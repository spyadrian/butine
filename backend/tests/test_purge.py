from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.models import FetchCycle, Paper
from app.services.purge import purge_fetch_cycles, purge_papers
from tests.test_fetcher import add_source


def add_paper(session, external_id: str, age: timedelta) -> None:
    source = add_source(session, f"src-{external_id}")
    session.add(
        Paper(
            external_id=external_id,
            source_id=source.id,
            version=1,
            title="T",
            authors=[],
            abstract="A",
            categories=[],
            link="https://example.org",
            fetched_at=datetime.now(UTC) - age,
        )
    )
    session.flush()


def test_purge_deletes_only_papers_older_than_retention(session):
    add_paper(session, "old", timedelta(days=31))
    add_paper(session, "recent", timedelta(days=29))

    assert purge_papers(session, retention_days=30) == 1
    assert session.scalars(select(Paper.external_id)).all() == ["recent"]


def add_cycle(session, age: timedelta) -> None:
    stats = dict.fromkeys(["feeds_polled", "new_papers", "updated_papers", "errors", "purged"], 0)
    session.add(FetchCycle(started_at=datetime.now(UTC) - age, duration_ms=0, **stats))
    session.flush()


def test_purge_deletes_only_cycles_older_than_retention(session):
    add_cycle(session, timedelta(days=31))
    add_cycle(session, timedelta(days=29))

    purge_fetch_cycles(session, retention_days=30)

    (cycle,) = session.scalars(select(FetchCycle))
    assert cycle.started_at > datetime.now(UTC) - timedelta(days=30)
