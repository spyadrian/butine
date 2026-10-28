from pathlib import Path

import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Source

CATALOG_PATH = Path(__file__).parent.parent.parent / "sources.yaml"
KINDS = {"arxiv", "biorxiv"}
FIELDS = ("slug", "name", "url", "kind")


class CatalogError(Exception):
    pass


def load_catalog(path: Path) -> list[dict]:
    """Read and validate sources.yaml. Raises CatalogError before anything touches the DB."""
    try:
        data = yaml.safe_load(path.read_text())
    except (OSError, yaml.YAMLError) as e:
        raise CatalogError(f"cannot read {path}: {e}") from e
    if not isinstance(data, dict) or not isinstance(data.get("sources"), list):
        raise CatalogError("expected a top-level 'sources:' list")

    entries, seen = [], set()
    for i, raw in enumerate(data["sources"], start=1):
        where = f"source #{i}"
        if not isinstance(raw, dict):
            raise CatalogError(f"{where}: expected a mapping")
        for field in FIELDS:
            if not isinstance(raw.get(field), str) or not raw[field].strip():
                raise CatalogError(f"{where}: missing or empty '{field}'")
        if raw["kind"] not in KINDS:
            raise CatalogError(f"{where}: kind must be one of {sorted(KINDS)}")
        if not raw["url"].startswith(("http://", "https://")):
            raise CatalogError(f"{where}: url must start with http:// or https://")
        if raw["slug"] in seen:
            raise CatalogError(f"{where}: duplicate slug '{raw['slug']}'")
        seen.add(raw["slug"])
        entries.append({field: raw[field].strip() for field in FIELDS})
    return entries


def sync_sources(session: Session, entries: list[dict]) -> dict[str, int]:
    """Make the sources table match the catalog. Removed sources are deactivated, never deleted."""
    counts = {"added": 0, "updated": 0, "deactivated": 0, "reactivated": 0}
    existing = {s.slug: s for s in session.scalars(select(Source))}

    for entry in entries:
        source = existing.pop(entry["slug"], None)
        if source is None:
            session.add(Source(**entry))
            counts["added"] += 1
            continue
        if (source.name, source.url, source.kind) != (entry["name"], entry["url"], entry["kind"]):
            source.name, source.url, source.kind = entry["name"], entry["url"], entry["kind"]
            counts["updated"] += 1
        if not source.active:
            # Back in the catalog, or re-listed after too many failures: retry from scratch.
            source.active = True
            source.consecutive_failures = 0
            counts["reactivated"] += 1

    for source in existing.values():
        if source.active:
            source.active = False
            counts["deactivated"] += 1

    session.flush()
    return counts
