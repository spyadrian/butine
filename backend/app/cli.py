import argparse
import sys
import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import User
from app.services.catalog import CATALOG_PATH, CatalogError, load_catalog, sync_sources


def set_plan(session: Session, user_id: uuid.UUID, plan: str) -> bool:
    """Set a user's plan; False when the user does not exist."""
    user = session.get(User, user_id)
    if user:
        user.plan = plan
    return user is not None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    commands = parser.add_subparsers(dest="command", required=True)
    sync = commands.add_parser("sync-sources", help="sync sources.yaml into the database")
    sync.add_argument("--file", type=Path, default=CATALOG_PATH)
    plan = commands.add_parser("set-plan", help="change a user's plan")
    plan.add_argument("user_id", type=uuid.UUID)
    plan.add_argument("plan", choices=["free", "paid"])
    args = parser.parse_args(argv)

    if args.command == "set-plan":
        with SessionLocal.begin() as session:
            if not set_plan(session, args.user_id, args.plan):
                print(f"error: no user {args.user_id}", file=sys.stderr)
                return 1
        print(f"{args.user_id}: {args.plan}")
        return 0

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
