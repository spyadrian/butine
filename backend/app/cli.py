import argparse
import sys
from pathlib import Path

from app.db import SessionLocal
from app.services.catalog import CATALOG_PATH, CatalogError, load_catalog, sync_sources


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    commands = parser.add_subparsers(dest="command", required=True)
    sync = commands.add_parser("sync-sources", help="sync sources.yaml into the database")
    sync.add_argument("--file", type=Path, default=CATALOG_PATH)
    args = parser.parse_args(argv)

    try:
        entries = load_catalog(args.file)
    except CatalogError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    with SessionLocal.begin() as session:
        counts = sync_sources(session, entries)
    print(", ".join(f"{name}: {n}" for name, n in counts.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
