from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Source(Base):
    """A feed from the fixed catalog (sources.yaml), fetched once for all users."""

    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    url: Mapped[str] = mapped_column(String(2000))
    kind: Mapped[str] = mapped_column(String(20))
    active: Mapped[bool] = mapped_column(default=True)
    # Fetch state, filled by the worker.
    etag: Mapped[str | None] = mapped_column(String(500))
    last_modified: Mapped[str | None] = mapped_column(String(100))
    next_fetch_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    consecutive_failures: Mapped[int] = mapped_column(default=0)
    last_error: Mapped[str | None]
