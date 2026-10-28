import uuid

import pytest

from app.cli import set_plan


@pytest.fixture
def headers(client):
    return {"X-User-Id": client.post("/v1/users").json()["id"]}


def create(client, headers, text="graph neural networks for chemistry"):
    return client.post("/v1/prompts", json={"text": text}, headers=headers)


def test_create_prompt_strips_text_and_is_pending(client, headers):
    response = create(client, headers, "  protein folding  ")

    assert response.status_code == 201
    body = response.json()
    assert body["text"] == "protein folding"
    assert body["status"] == "pending"


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
    assert set(response.json()[0]) == {"id", "text", "created_at", "status"}


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
    ("method", "path"),
    [("get", "/v1/prompts"), ("post", "/v1/prompts"), ("delete", "/v1/prompts/1")],
)
def test_prompt_routes_require_user(client, method, path):
    assert client.request(method, path, json={"text": "x"}).status_code == 401
