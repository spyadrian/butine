from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.services.feeds import FeedError, parse_feed

FIXTURES = Path(__file__).parent / "fixtures"


def fixture(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def test_arxiv_entries():
    first, replaced = parse_feed("arxiv", fixture("arxiv.xml"))

    assert first.external_id == "arxiv:2610.35890"
    assert first.version == 1
    assert first.title.startswith("scPyviewer: a Python-native interactive viewer")
    assert first.authors == ["Hao Xuan", "Yu Huang", "Jiang Bian", "Xiangtao Liu"]
    assert first.categories == ["q-bio.GN", "cs.AI"]
    assert first.link == "https://arxiv.org/abs/2610.35890"
    assert first.published_at == datetime(2026, 10, 28, 4, 0, tzinfo=UTC)
    # Full abstract, without the "arXiv:… Announce Type: new Abstract:" preamble.
    assert first.abstract.startswith("Motivation: Interactive web tools")
    assert first.abstract.endswith("https://github.com/xuan13hao/scPyviewer.git")

    assert replaced.external_id == "arxiv:2310.03186"
    assert replaced.version == 4


def test_biorxiv_entries():
    first, second = parse_feed("biorxiv", fixture("biorxiv.xml"))

    assert first.external_id == "doi:10.64898/2026.10.22.760929"
    assert first.version == 1
    assert first.title == (
        "What do navigating animals see? Reconstructing the visual histories of desert ants"
    )
    assert first.authors == ["Mangan, M.", "Millward, B.", "James, S.", "Baird, E."]
    assert first.categories == ["Animal Behavior And Cognition"]
    assert first.link == "https://www.biorxiv.org/content/10.64898/2026.10.22.760929v1"
    assert first.published_at == datetime(2026, 10, 27, tzinfo=UTC)
    assert first.abstract.startswith("To understand how brains translate")
    assert first.abstract.endswith("ecologically relevant scenarios.")

    assert second.authors[0] == "Whishaw, I. Q."
    assert second.abstract.startswith("Catarrhine primates")


def test_abstract_html_is_stripped():
    xml = b"""<rss version="2.0"><channel><item>
      <title>T</title><link>https://arxiv.org/abs/2410.12345</link>
      <guid>oai:arXiv.org:2410.12345v2</guid>
      <description>arXiv:2410.12345v2 Announce Type: replace
Abstract: We study &lt;i&gt;x&lt;/i&gt; &amp;amp; y.</description>
    </item></channel></rss>"""
    (entry,) = parse_feed("arxiv", xml)
    assert entry.abstract == "We study x & y."
    assert (entry.external_id, entry.version) == ("arxiv:2410.12345", 2)


def test_entry_without_identifier_is_skipped():
    xml = b"""<rss version="2.0"><channel>
      <item><title>No id</title><link>https://example.org/x</link></item>
    </channel></rss>"""
    assert parse_feed("arxiv", xml) == []
    assert parse_feed("biorxiv", xml) == []


def test_malformed_feed_raises():
    with pytest.raises(FeedError):
        parse_feed("arxiv", b"<html><body>Service unavailable")


def test_unknown_kind_raises():
    with pytest.raises(FeedError, match="kind"):
        parse_feed("rss", fixture("arxiv.xml"))
