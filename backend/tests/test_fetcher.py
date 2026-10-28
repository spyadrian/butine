from datetime import UTC, datetime, timedelta

import httpx2
from sqlalchemy import select

from app.models import Paper, Source
from app.services.fetcher import run_cycle


def arxiv_feed(*papers: tuple[str, int, str]) -> bytes:
    """Minimal arXiv RSS with (id, version, title) items."""
    items = "".join(
        f"<item><title>{title}</title><link>https://arxiv.org/abs/{id_}</link>"
        f"<guid>oai:arXiv.org:{id_}v{version}</guid><description>Abstract.</description></item>"
        for id_, version, title in papers
    )
    return f'<rss version="2.0"><channel>{items}</channel></rss>'.encode()


def add_source(session, slug: str, **fields) -> Source:
    source = Source(
        slug=slug, name=slug, url=f"https://feeds.example/{slug}", kind="arxiv", **fields
    )
    session.add(source)
    session.flush()
    return source


def make_due(session) -> None:
    for source in session.scalars(select(Source)):
        source.next_fetch_at = datetime.now(UTC) - timedelta(seconds=1)


def serve(feeds: dict[str, bytes], requests: list | None = None) -> httpx2.Client:
    """Client answering each source URL with its feed (or 304 when given b"")."""

    def handler(request: httpx2.Request) -> httpx2.Response:
        if requests is not None:
            requests.append(request)
        body = feeds[request.url.path.rsplit("/", 1)[1]]
        if not body:
            return httpx2.Response(304)
        return httpx2.Response(200, content=body, headers={"ETag": '"e1"'})

    return httpx2.Client(transport=httpx2.MockTransport(handler))


def papers(session) -> list[Paper]:
    return list(session.scalars(select(Paper).order_by(Paper.external_id)))


def test_two_cycles_do_not_duplicate(session):
    add_source(session, "cs")
    client = serve({"cs": arxiv_feed(("2410.1", 1, "A"), ("2410.2", 1, "B"))})

    run_cycle(session, client)
    make_due(session)
    run_cycle(session, client)

    assert [p.external_id for p in papers(session)] == ["arxiv:2410.1", "arxiv:2410.2"]


def test_paper_in_two_archives_is_stored_once(session):
    cs = add_source(session, "cs")
    add_source(session, "math")
    feed = arxiv_feed(("2410.1", 1, "A"))

    run_cycle(session, serve({"cs": feed, "math": feed}))

    (paper,) = papers(session)
    assert paper.source_id == cs.id


def test_newer_version_updates_and_older_does_not(session):
    add_source(session, "cs")

    run_cycle(session, serve({"cs": arxiv_feed(("2410.1", 1, "Old title"))}))
    make_due(session)
    run_cycle(session, serve({"cs": arxiv_feed(("2410.1", 2, "New title"))}))
    make_due(session)
    run_cycle(session, serve({"cs": arxiv_feed(("2410.1", 1, "Old title"))}))

    (paper,) = papers(session)
    assert (paper.version, paper.title) == (2, "New title")


def test_conditional_headers_and_not_modified(session):
    source = add_source(session, "cs", etag='"e0"', last_modified="Mon, 26 Oct 2026 00:00:00 GMT")
    requests = []

    run_cycle(session, serve({"cs": b""}, requests))

    (request,) = requests
    assert request.headers["If-None-Match"] == '"e0"'
    assert request.headers["If-Modified-Since"] == "Mon, 26 Oct 2026 00:00:00 GMT"
    assert papers(session) == []
    assert source.next_fetch_at > datetime.now(UTC) + timedelta(minutes=29)


def test_etag_is_stored(session):
    source = add_source(session, "cs")
    run_cycle(session, serve({"cs": arxiv_feed()}))
    assert source.etag == '"e1"'


def test_source_not_due_is_not_fetched(session):
    add_source(session, "cs", next_fetch_at=datetime.now(UTC) + timedelta(minutes=5))
    add_source(session, "off", active=False)
    requests = []

    run_cycle(session, serve({}, requests))

    assert requests == []


def failing(status: int = 500) -> httpx2.Client:
    return httpx2.Client(transport=httpx2.MockTransport(lambda request: httpx2.Response(status)))


def test_backoff_grows_and_is_capped(session):
    source = add_source(session, "cs")
    delays = []
    for _ in range(8):
        make_due(session)
        start = datetime.now(UTC)
        run_cycle(session, failing())
        delays.append(round((source.next_fetch_at - start) / timedelta(minutes=1)))

    assert delays == [30, 60, 120, 240, 480, 960, 1440, 1440]
    assert source.consecutive_failures == 8
    assert "500" in source.last_error


def test_tenth_failure_deactivates_source(session):
    source = add_source(session, "cs", consecutive_failures=9)
    run_cycle(session, serve({"cs": b"not a feed"}))
    assert (source.active, source.consecutive_failures) == (False, 10)
    assert "unreadable feed" in source.last_error


def test_success_resets_failures(session):
    source = add_source(session, "cs", consecutive_failures=3)
    run_cycle(session, serve({"cs": arxiv_feed()}))
    assert source.consecutive_failures == 0


def test_failing_source_does_not_stop_others(session):
    broken = add_source(session, "broken")
    add_source(session, "cs")

    def handler(request: httpx2.Request) -> httpx2.Response:
        if request.url.path.endswith("broken"):
            raise httpx2.ConnectError("down", request=request)
        return httpx2.Response(200, content=arxiv_feed(("2410.1", 1, "A")))

    run_cycle(session, httpx2.Client(transport=httpx2.MockTransport(handler)))

    assert broken.consecutive_failures == 1
    assert [p.external_id for p in papers(session)] == ["arxiv:2410.1"]


def test_cycle_counts_new_updated_and_errors(session):
    add_source(session, "cs")
    add_source(session, "broken")
    first = run_cycle(session, serve({"cs": arxiv_feed(("2410.1", 1, "A")), "broken": b"bad"}))
    make_due(session)

    second = run_cycle(
        session,
        serve({"cs": arxiv_feed(("2410.1", 2, "A"), ("2410.2", 1, "B")), "broken": b""}),
    )

    assert first == {"feeds_polled": 2, "new_papers": 1, "updated_papers": 0, "errors": 1}
    assert second == {"feeds_polled": 2, "new_papers": 1, "updated_papers": 1, "errors": 0}
