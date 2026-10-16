from app.models import Source


def add_source(session, slug, name, active=True):
    session.add(
        Source(
            slug=slug,
            name=name,
            url=f"https://{slug}.example/feed",
            kind="rss",
            active=active,
            etag="secret-etag",
            last_error="boom",
        )
    )
    session.flush()


def test_lists_only_active_sources_sorted_by_name(client, session):
    add_source(session, "zeta", "Zeta")
    add_source(session, "alpha", "Alpha")
    add_source(session, "gone", "Gone", active=False)

    response = client.get("/v1/sources")

    assert response.status_code == 200
    assert response.json() == [
        {"slug": "alpha", "name": "Alpha", "url": "https://alpha.example/feed", "kind": "rss"},
        {"slug": "zeta", "name": "Zeta", "url": "https://zeta.example/feed", "kind": "rss"},
    ]
