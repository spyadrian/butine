import os

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+psycopg://butine:butine@localhost:5432/butine"
)
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://butine:butine@localhost:5432/butine_test"
)
PAPER_RETENTION_DAYS = int(os.environ.get("PAPER_RETENTION_DAYS", "30"))
EMBED_BATCH_LIMIT = int(os.environ.get("EMBED_BATCH_LIMIT", "2000"))  # papers per cycle
