from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Source

router = APIRouter()


class SourceOut(BaseModel):
    """Public view of a source: fetch state (etag, errors…) stays internal."""

    model_config = ConfigDict(from_attributes=True)

    slug: str
    name: str
    url: str
    kind: str


@router.get("/sources")
def list_sources(session: Annotated[Session, Depends(get_session)]) -> list[SourceOut]:
    return session.scalars(select(Source).where(Source.active).order_by(Source.name)).all()
