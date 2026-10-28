import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import User

router = APIRouter()


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    plan: str


def current_user(
    session: Annotated[Session, Depends(get_session)],
    x_user_id: Annotated[uuid.UUID | None, Header()] = None,
) -> User:
    """User routes dependency: malformed id → 422 (FastAPI), missing or unknown → 401."""
    user = x_user_id and session.get(User, x_user_id)
    if not user:
        raise HTTPException(401, "missing or unknown X-User-Id")
    return user


# No route changes the plan: without auth, anyone could make themselves paid (app.cli set-plan).
@router.post("/users", status_code=201)
def create_user(session: Annotated[Session, Depends(get_session)]) -> UserOut:
    user = User()
    session.add(user)
    session.commit()
    return user
