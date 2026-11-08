from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import aggregate_order_by
from sqlalchemy.orm import Session

from app.api.v1.papers import PAPER_COLUMNS, PaperOut
from app.api.v1.users import current_user
from app.config import BACKFILL_DAYS, MATCH_THRESHOLD
from app.db import get_session
from app.models import Paper, Prompt, Source, User

router = APIRouter()

# Same order as /v1/papers; id breaks ties so pages never overlap.
ORDER = (Paper.published_at.desc().nulls_last(), Paper.id.desc())


class FeedPaperOut(PaperOut):
    score: float  # cosine similarity with the prompt


class GlobalFeedPaperOut(FeedPaperOut):
    prompt_ids: list[int]  # prompts that keep the paper; score is the best of them


def match(prompt):
    """Score and match conditions; `prompt` is a Prompt row, or the Prompt class inside a join."""
    # Vectors are normalized, so 1 - cosine distance is the similarity.
    score = 1 - Paper.embedding.cosine_distance(prompt.embedding)
    since = prompt.created_at - timedelta(days=BACKFILL_DAYS)
    return score, (
        score >= MATCH_THRESHOLD,
        func.coalesce(Paper.published_at, Paper.fetched_at) >= since,
    )


@router.get("/prompts/{prompt_id}/feed")
def prompt_feed(
    prompt_id: int,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[Session, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[FeedPaperOut]:
    prompt = session.scalar(select(Prompt).where(Prompt.id == prompt_id, Prompt.user_id == user.id))
    if prompt is None:
        raise HTTPException(404, "prompt not found")
    if prompt.embedding is None:
        return []
    score, conditions = match(prompt)
    query = (
        select(*PAPER_COLUMNS, score.label("score"))
        .join(Source)
        .where(*conditions)
        .order_by(*ORDER)
        .limit(limit)
        .offset(offset)
    )
    return session.execute(query).mappings().all()


@router.get("/feed")
def global_feed(
    user: Annotated[User, Depends(current_user)],
    session: Annotated[Session, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[GlobalFeedPaperOut]:
    score, conditions = match(Prompt)
    query = (
        select(
            *PAPER_COLUMNS,
            func.max(score).label("score"),
            func.array_agg(aggregate_order_by(Prompt.id, Prompt.id)).label("prompt_ids"),
        )
        .join(Source)
        # Pending prompts have no embedding: their score is NULL and never matches.
        .join(Prompt, Prompt.user_id == user.id)
        .where(*conditions)
        .group_by(Paper.id, Source.id)
        .order_by(*ORDER)
        .limit(limit)
        .offset(offset)
    )
    return session.execute(query).mappings().all()
