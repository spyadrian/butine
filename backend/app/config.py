import os

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+psycopg://butine:butine@localhost:5432/butine"
)
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://butine:butine@localhost:5432/butine_test"
)
