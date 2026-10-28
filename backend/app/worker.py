import json
import logging
import time
from datetime import UTC, datetime

import httpx2
from sqlalchemy.orm import Session

from app.config import PAPER_RETENTION_DAYS
from app.db import SessionLocal
from app.models import FetchCycle
from app.services.fetcher import run_cycle
from app.services.purge import purge_fetch_cycles, purge_papers

CYCLE_PAUSE_SECONDS = 60


def run_once(session: Session, client: httpx2.Client) -> None:
    """Fetch, purge, then record the cycle in the database and as one JSON line on stdout."""
    started_at = datetime.now(UTC)
    start = time.monotonic()
    stats = run_cycle(session, client)
    stats["purged"] = purge_papers(session, PAPER_RETENTION_DAYS)
    purge_fetch_cycles(session, PAPER_RETENTION_DAYS)
    duration_ms = round((time.monotonic() - start) * 1000)
    session.add(FetchCycle(started_at=started_at, duration_ms=duration_ms, **stats))
    session.commit()
    print(
        json.dumps({"started_at": started_at.isoformat(), "duration_ms": duration_ms, **stats}),
        flush=True,
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    with httpx2.Client(
        timeout=30, follow_redirects=True, headers={"User-Agent": "butine/0.1"}
    ) as client:
        while True:
            try:
                with SessionLocal() as session:
                    run_once(session, client)
            except Exception:
                # Keep the worker alive (e.g. tables not migrated yet, a feed down).
                logging.exception("fetch cycle failed")
            time.sleep(CYCLE_PAUSE_SECONDS)


if __name__ == "__main__":
    main()
