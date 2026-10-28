import logging
import time

import httpx2

from app.db import SessionLocal
from app.services.fetcher import run_cycle

CYCLE_PAUSE_SECONDS = 60


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    with httpx2.Client(
        timeout=30, follow_redirects=True, headers={"User-Agent": "butine/0.1"}
    ) as client:
        while True:
            try:
                with SessionLocal() as session:
                    run_cycle(session, client)
            except Exception:
                # Keep the worker alive (e.g. tables not migrated yet, a feed down).
                logging.exception("fetch cycle failed")
            time.sleep(CYCLE_PAUSE_SECONDS)


if __name__ == "__main__":
    main()
