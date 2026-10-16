from alembic import command

from tests.conftest import alembic_config


def test_models_match_migrations(engine):
    """Fails if a model changed without a new migration (alembic revision --autogenerate)."""
    command.check(alembic_config())
