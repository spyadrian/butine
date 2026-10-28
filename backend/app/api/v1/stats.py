from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import FetchCycle, Paper, Source

router = APIRouter()


class CycleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    started_at: datetime
    duration_ms: int
    feeds_polled: int
    new_papers: int
    updated_papers: int
    errors: int
    purged: int


class StatsOut(BaseModel):
    last_cycle: CycleOut | None
    active_sources: int
    inactive_sources: int
    papers: int


@router.get("/stats")
def get_stats(session: Annotated[Session, Depends(get_session)]) -> StatsOut:
    sources = dict(
        session.execute(select(Source.active, func.count()).group_by(Source.active)).all()
    )
    return StatsOut(
        last_cycle=session.scalar(select(FetchCycle).order_by(FetchCycle.id.desc()).limit(1)),
        active_sources=sources.get(True, 0),
        inactive_sources=sources.get(False, 0),
        papers=session.scalar(select(func.count()).select_from(Paper)),
    )
