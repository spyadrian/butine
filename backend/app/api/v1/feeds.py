from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.v1.papers import PaperOut
from app.api.v1.users import current_user
from app.config import BACKFILL_DAYS, MATCH_THRESHOLD
from app.db import get_session
from app.models import Paper, Prompt, Source, User

router = APIRouter()


class FeedPaperOut(PaperOut):
    score: float  # cosine similarity with the prompt


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
    # Vectors are normalized, so 1 - cosine distance is the similarity.
    score = 1 - Paper.embedding.cosine_distance(prompt.embedding)
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
            score.label("score"),
        )
        .join(Source)
        .where(
            score >= MATCH_THRESHOLD,
            func.coalesce(Paper.published_at, Paper.fetched_at)
            >= prompt.created_at - timedelta(days=BACKFILL_DAYS),
        )
        # Same order as /v1/papers; id breaks ties so pages never overlap.
        .order_by(Paper.published_at.desc().nulls_last(), Paper.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return session.execute(query).mappings().all()
