import uuid

import pytest

from app.cli import set_plan
from app.models import Prompt


@pytest.fixture
def headers(client):
    return {"X-User-Id": client.post("/v1/users").json()["id"]}


def create(client, headers, text="graph neural networks for chemistry", **fields):
    body = {"name": "Chemistry", "icon": "science", "text": text} | fields
    return client.post("/v1/prompts", json=body, headers=headers)


def test_create_prompt_strips_text_and_name_and_is_pending(client, headers):
    response = create(client, headers, "  protein folding  ", name="  Proteins  ")

    assert response.status_code == 201
    body = response.json()
    assert body["text"] == "protein folding"
    assert body["name"] == "Proteins"
    assert body["icon"] == "science"
    assert body["status"] == "pending"


def test_prompt_is_ready_once_embedded(client, session, headers):
    prompt_id = create(client, headers).json()["id"]
    session.get(Prompt, prompt_id).embedding = [1.0] * 384

    (prompt,) = client.get("/v1/prompts", headers=headers).json()

    assert prompt["status"] == "ready"


def test_free_plan_allows_one_prompt(client, headers):
    assert create(client, headers).status_code == 201

    response = create(client, headers)

    assert response.status_code == 403
    assert "1" in response.json()["detail"]


def test_paid_plan_allows_ten_prompts_and_free_keeps_them(client, session, headers):
    user_id = headers["X-User-Id"]
    set_plan(session, uuid.UUID(user_id), "paid")
    for _ in range(10):
        assert create(client, headers).status_code == 201
    assert create(client, headers).status_code == 403

    set_plan(session, uuid.UUID(user_id), "free")

    assert len(client.get("/v1/prompts", headers=headers).json()) == 10
    assert create(client, headers).status_code == 403


def test_list_prompts_oldest_first_and_only_own(client, session, headers):
    set_plan(session, uuid.UUID(headers["X-User-Id"]), "paid")
    first = create(client, headers, "first").json()
    second = create(client, headers, "second").json()
    other = {"X-User-Id": client.post("/v1/users").json()["id"]}
    create(client, other, "someone else")

    response = client.get("/v1/prompts", headers=headers)

    assert [p["id"] for p in response.json()] == [first["id"], second["id"]]
    assert set(response.json()[0]) == {"id", "name", "icon", "text", "created_at", "status"}


def test_delete_prompt(client, headers):
    prompt_id = create(client, headers).json()["id"]

    assert client.delete(f"/v1/prompts/{prompt_id}", headers=headers).status_code == 204
    assert client.get("/v1/prompts", headers=headers).json() == []


def test_delete_other_users_or_missing_prompt_is_404(client, headers):
    prompt_id = create(client, headers).json()["id"]
    other = {"X-User-Id": client.post("/v1/users").json()["id"]}

    assert client.delete(f"/v1/prompts/{prompt_id}", headers=other).status_code == 404
    assert client.delete(f"/v1/prompts/{prompt_id + 1}", headers=headers).status_code == 404


@pytest.mark.parametrize("text", ["", "   ", "x" * 501])
def test_create_prompt_rejects_empty_or_too_long_text(client, headers, text):
    assert create(client, headers, text).status_code == 422


def test_create_prompt_accepts_500_chars(client, headers):
    assert create(client, headers, "x" * 500).status_code == 201


@pytest.mark.parametrize(
    "fields",
    [
        {"name": None},
        {"icon": None},
        {"name": ""},
        {"name": "   "},
        {"name": "x" * 25},
        {"icon": "Bad-Icon"},
        {"icon": ""},
        {"icon": "x" * 41},
    ],
)
def test_create_prompt_rejects_missing_or_invalid_name_and_icon(client, headers, fields):
    body = {"name": "Chemistry", "icon": "science", "text": "chemistry"} | fields
    body = {k: v for k, v in body.items() if v is not None}

    assert client.post("/v1/prompts", json=body, headers=headers).status_code == 422


def test_create_prompt_accepts_24_char_name_and_40_char_icon(client, headers):
    assert create(client, headers, name="x" * 24, icon="a_1" + "x" * 37).status_code == 201


@pytest.mark.parametrize(
    ("method", "path"),
    [("get", "/v1/prompts"), ("post", "/v1/prompts"), ("delete", "/v1/prompts/1")],
)
def test_prompt_routes_require_user(client, method, path):
    assert client.request(method, path, json={"text": "x"}).status_code == 401
