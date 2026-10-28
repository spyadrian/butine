from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, StringConstraints
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.api.v1.users import current_user
from app.db import get_session
from app.models import Prompt, User

router = APIRouter()

PROMPT_LIMITS = {"free": 1, "paid": 10}


class PromptIn(BaseModel):
    text: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]


class PromptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    created_at: datetime
    status: str = "pending"  # shortcut: always pending, derive it from the embedding once it exists


@router.post("/prompts", status_code=201)
def create_prompt(
    body: PromptIn,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> PromptOut:
    # Row lock: two concurrent requests must not both pass the limit check.
    session.execute(select(User).where(User.id == user.id).with_for_update())
    count = session.scalar(select(func.count()).where(Prompt.user_id == user.id))
    if count >= PROMPT_LIMITS[user.plan]:
        raise HTTPException(403, f"{user.plan} plan allows {PROMPT_LIMITS[user.plan]} prompts")
    prompt = Prompt(user_id=user.id, text=body.text)
    session.add(prompt)
    session.commit()
    return prompt


@router.get("/prompts")
def list_prompts(
    user: Annotated[User, Depends(current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> list[PromptOut]:
    return session.scalars(
        select(Prompt).where(Prompt.user_id == user.id).order_by(Prompt.created_at, Prompt.id)
    ).all()


@router.delete("/prompts/{prompt_id}", status_code=204)
def delete_prompt(
    prompt_id: int,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> None:
    deleted = session.execute(
        delete(Prompt).where(Prompt.id == prompt_id, Prompt.user_id == user.id)
    ).rowcount
    if not deleted:
        raise HTTPException(404, "prompt not found")
    session.commit()
