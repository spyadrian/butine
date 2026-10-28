import html
import re
from dataclasses import dataclass
from datetime import UTC, datetime

import feedparser


class FeedError(Exception):
    pass


@dataclass(frozen=True)
class PaperEntry:
    external_id: str  # "arxiv:2410.12345" / "doi:10.1101/…", without the version
    version: int
    title: str
    authors: list[str]
    abstract: str
    categories: list[str]
    link: str
    published_at: datetime | None


ARXIV_ID = re.compile(r"^oai:arXiv\.org:(.+)v(\d+)$")
ARXIV_PREAMBLE = re.compile(r"^arXiv:\S+ Announce Type: \S+ Abstract: ")
BIORXIV_VERSION = re.compile(r"v(\d+)$")
BIORXIV_PREAMBLE = re.compile(r"^Abstract ")
BIORXIV_AUTHOR_SEP = re.compile(r"(?<=\.),\s*")  # "Mangan, M., Millward, B." → per author


def clean(text: str) -> str:
    """Strip HTML tags and entities, collapse whitespace."""
    # shortcut: paragraph breaks are lost, keep them if the UI needs them.
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", text)).split())


def published_at(entry) -> datetime | None:
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    return datetime(*parsed[:6], tzinfo=UTC) if parsed else None


def parse_arxiv(entry, feed) -> PaperEntry | None:
    match = ARXIV_ID.match(entry.get("id", ""))
    if not match:
        return None
    return PaperEntry(
        external_id=f"arxiv:{match[1]}",
        version=int(match[2]),
        title=clean(entry.get("title", "")),
        authors=[a.strip() for a in entry.get("author", "").split(",") if a.strip()],
        abstract=ARXIV_PREAMBLE.sub("", clean(entry.get("summary", ""))),
        categories=[t.term for t in entry.get("tags", [])],
        link=entry.get("link", ""),
        published_at=published_at(entry),
    )


def parse_biorxiv(entry, feed) -> PaperEntry | None:
    doi = entry.get("dc_identifier", "")
    if not doi.startswith("doi:"):
        return None
    link = entry.get("link", "").removesuffix("?rss=1")
    version = BIORXIV_VERSION.search(link)
    # Feeds are per subject: "bioRxiv Subject Collection: Neuroscience".
    subject = feed.get("title", "").rpartition(": ")[2]
    return PaperEntry(
        external_id=doi,
        version=int(version[1]) if version else 1,
        title=clean(entry.get("title", "")),
        authors=[a for a in BIORXIV_AUTHOR_SEP.split(clean(entry.get("author", ""))) if a],
        abstract=BIORXIV_PREAMBLE.sub("", clean(entry.get("summary", ""))),
        categories=[subject] if subject else [],
        link=link,
        published_at=published_at(entry),
    )


PARSERS = {"arxiv": parse_arxiv, "biorxiv": parse_biorxiv}


def parse_feed(kind: str, content: bytes) -> list[PaperEntry]:
    """Parse a feed into paper entries. Entries without an identifier are skipped."""
    if kind not in PARSERS:
        raise FeedError(f"unknown kind '{kind}'")
    parsed = feedparser.parse(content)
    if parsed.bozo and not parsed.entries:
        raise FeedError(f"unreadable feed: {parsed.get('bozo_exception')}")
    entries = (PARSERS[kind](entry, parsed.feed) for entry in parsed.entries)
    return [e for e in entries if e is not None]
