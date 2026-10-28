import uuid
from typing import Annotated

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.api.v1.users import current_user
from app.cli import main, set_plan
from app.db import get_session
from app.main import app
from app.models import User


@pytest.fixture
def user_client(session):
    """A bare app with one route behind current_user (prompts will be the first real user)."""
    test_app = FastAPI()

    @test_app.get("/whoami")
    def whoami(user: Annotated[User, Depends(current_user)]) -> dict:
        return {"id": str(user.id), "plan": user.plan}

    test_app.dependency_overrides[get_session] = lambda: session
    return TestClient(test_app)


def test_create_user_returns_free_user(client, session):
    response = client.post("/v1/users")

    assert response.status_code == 201
    body = response.json()
    assert body["plan"] == "free"
    assert session.get(User, uuid.UUID(body["id"])).plan == "free"


def test_current_user_reads_header(client, user_client):
    user_id = client.post("/v1/users").json()["id"]

    response = user_client.get("/whoami", headers={"X-User-Id": user_id})

    assert response.json() == {"id": user_id, "plan": "free"}


@pytest.mark.parametrize(
    ("headers", "status"),
    [({}, 401), ({"X-User-Id": str(uuid.uuid4())}, 401), ({"X-User-Id": "not-a-uuid"}, 422)],
)
def test_current_user_rejects_missing_unknown_or_malformed_id(user_client, headers, status):
    assert user_client.get("/whoami", headers=headers).status_code == status


def test_no_route_changes_the_plan():
    paths = app.openapi()["paths"]
    methods = {m for p, ops in paths.items() if p.startswith("/v1/users") for m in ops}
    assert methods == {"post"}


def test_set_plan_changes_the_plan(client, session):
    user_id = uuid.UUID(client.post("/v1/users").json()["id"])

    assert set_plan(session, user_id, "paid")
    assert session.get(User, user_id).plan == "paid"


def test_set_plan_unknown_user_returns_false(session):
    assert not set_plan(session, uuid.uuid4(), "paid")


@pytest.mark.parametrize("argv", [["not-a-uuid", "paid"], [str(uuid.uuid4()), "gold"]])
def test_set_plan_cli_rejects_bad_arguments(argv, capsys):
    with pytest.raises(SystemExit) as exit_:
        main(["set-plan", *argv])
    assert exit_.value.code != 0
    assert "invalid" in capsys.readouterr().err
