from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Paper, Source

router = APIRouter()


class PaperOut(BaseModel):
    external_id: str
    version: int
    title: str
    authors: list[str]
    abstract: str
    categories: list[str]
    link: str
    published_at: datetime | None
    source: str


@router.get("/papers")
def list_papers(
    session: Annotated[Session, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    source: str | None = None,
) -> list[PaperOut]:
    query = (
        select(
            Paper.external_id,
            Paper.version,
            Paper.title,
            Paper.authors,
            Paper.abstract,
            Paper.categories,
            Paper.link,
            Paper.published_at,
            Source.name.label("source"),
        )
        .join(Source)
        # id breaks ties so pages never overlap or skip papers.
        .order_by(Paper.published_at.desc().nulls_last(), Paper.id.desc())
        .limit(limit)
        .offset(offset)
    )
    if source is not None:
        # shortcut: matches only the first source that listed the paper, add a
        # paper_sources link table if cross-listed papers must show in every archive.
        query = query.where(Source.slug == source)
    return session.execute(query).mappings().all()
