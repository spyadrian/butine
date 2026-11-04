import os

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+psycopg://butine:butine@localhost:5432/butine"
)
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://butine:butine@localhost:5432/butine_test"
)
PAPER_RETENTION_DAYS = int(os.environ.get("PAPER_RETENTION_DAYS", "30"))
EMBED_BATCH_LIMIT = int(os.environ.get("EMBED_BATCH_LIMIT", "2000"))  # papers per cycle
MATCH_THRESHOLD = float(os.environ.get("MATCH_THRESHOLD", "0.84"))  # see docs/DECISIONS.md
# Changing it means re-embedding everything and a new EMBEDDING_DIM, see docs/DECISIONS.md.
EMBEDDING_MODEL = "ibm-granite/granite-embedding-small-english-r2"
BACKFILL_DAYS = int(os.environ.get("BACKFILL_DAYS", "7"))  # a new prompt also gets recent papers
