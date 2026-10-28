from datetime import UTC, datetime

from app.models import Paper, Source


def add_source(session, slug):
    source = Source(slug=slug, name=slug.upper(), url=f"https://{slug}.example/feed", kind="arxiv")
    session.add(source)
    session.flush()
    return source


def add_paper(session, source, number, day):
    session.add(
        Paper(
            external_id=f"arxiv:2410.{number:05d}",
            source_id=source.id,
            version=1,
            title=f"Paper {number}",
            authors=["Ada Lovelace"],
            abstract="Abstract.",
            categories=["cs.AI"],
            link=f"https://arxiv.org/abs/2410.{number:05d}",
            published_at=datetime(2026, 10, day, tzinfo=UTC),
        )
    )
    session.flush()


def titles(response):
    return [paper["title"] for paper in response.json()]


def test_lists_papers_newest_first_with_source_name(client, session):
    cs = add_source(session, "cs")
    add_paper(session, cs, 1, day=1)
    add_paper(session, cs, 2, day=3)
    add_paper(session, cs, 3, day=2)

    response = client.get("/v1/papers")

    assert response.status_code == 200
    assert titles(response) == ["Paper 2", "Paper 3", "Paper 1"]
    assert response.json()[0] == {
        "external_id": "arxiv:2410.00002",
        "version": 1,
        "title": "Paper 2",
        "authors": ["Ada Lovelace"],
        "abstract": "Abstract.",
        "categories": ["cs.AI"],
        "link": "https://arxiv.org/abs/2410.00002",
        "published_at": "2026-10-03T00:00:00Z",
        "source": "CS",
    }


def test_paginates_with_limit_and_offset(client, session):
    cs = add_source(session, "cs")
    for day in range(1, 6):
        add_paper(session, cs, day, day=day)

    response = client.get("/v1/papers", params={"limit": 2, "offset": 1})

    assert titles(response) == ["Paper 4", "Paper 3"]


def test_rejects_limit_above_200(client):
    assert client.get("/v1/papers", params={"limit": 201}).status_code == 422


def test_filters_by_source_slug(client, session):
    add_paper(session, add_source(session, "cs"), 1, day=1)
    add_paper(session, add_source(session, "math"), 2, day=2)

    assert titles(client.get("/v1/papers", params={"source": "cs"})) == ["Paper 1"]
    assert client.get("/v1/papers", params={"source": "unknown"}).json() == []
