from pathlib import Path

import pytest
from sqlalchemy import select

from app.models import Source
from app.services.catalog import CATALOG_PATH, CatalogError, load_catalog, sync_sources


def write_catalog(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "sources.yaml"
    path.write_text(content)
    return path


def entry(slug: str, **overrides) -> dict:
    return {
        "slug": slug,
        "name": slug.title(),
        "url": f"https://{slug}.example/feed",
        "kind": "rss",
    } | overrides


def sources_by_slug(session) -> dict[str, Source]:
    return {s.slug: s for s in session.scalars(select(Source))}


def test_shipped_catalog_is_valid():
    assert len(load_catalog(CATALOG_PATH)) > 0


def test_load_rejects_missing_field(tmp_path):
    path = write_catalog(tmp_path, "sources:\n  - slug: a\n    name: A\n    kind: rss\n")
    with pytest.raises(CatalogError, match="url"):
        load_catalog(path)


def test_load_rejects_duplicate_slugs(tmp_path):
    path = write_catalog(
        tmp_path,
        """
sources:
  - {slug: a, name: A, url: "https://a.example/feed", kind: rss}
  - {slug: a, name: B, url: "https://b.example/feed", kind: rss}
""",
    )
    with pytest.raises(CatalogError, match="duplicate"):
        load_catalog(path)


def test_load_rejects_unknown_kind(tmp_path):
    path = write_catalog(
        tmp_path,
        """
sources:
  - {slug: a, name: A, url: "https://a.example/feed", kind: instagram}
""",
    )
    with pytest.raises(CatalogError, match="kind"):
        load_catalog(path)


def test_load_rejects_non_http_url(tmp_path):
    path = write_catalog(
        tmp_path,
        """
sources:
  - {slug: a, name: A, url: "file:///etc/passwd", kind: rss}
""",
    )
    with pytest.raises(CatalogError, match="url"):
        load_catalog(path)


def test_sync_adds_new_sources(session):
    sync_sources(session, [entry("a"), entry("b", kind="youtube")])

    sources = sources_by_slug(session)
    assert set(sources) == {"a", "b"}
    assert sources["b"].kind == "youtube"
    assert sources["a"].active


def test_sync_updates_name_and_url(session):
    sync_sources(session, [entry("a")])
    sync_sources(session, [entry("a", name="New name", url="https://new.example/feed")])

    source = sources_by_slug(session)["a"]
    assert source.name == "New name"
    assert source.url == "https://new.example/feed"


def test_sync_deactivates_sources_removed_from_catalog(session):
    sync_sources(session, [entry("a"), entry("b")])
    sync_sources(session, [entry("a")])

    sources = sources_by_slug(session)
    assert sources["a"].active
    assert not sources["b"].active


def test_sync_reactivates_returning_source_and_resets_failures(session):
    sync_sources(session, [entry("a")])
    source = sources_by_slug(session)["a"]
    source.active = False
    source.consecutive_failures = 10

    sync_sources(session, [entry("a")])

    assert source.active
    assert source.consecutive_failures == 0


def test_sync_reports_counts(session):
    sync_sources(session, [entry("a"), entry("b")])
    result = sync_sources(session, [entry("a", name="Renamed"), entry("c")])

    assert result == {"added": 1, "updated": 1, "deactivated": 1, "reactivated": 0}
