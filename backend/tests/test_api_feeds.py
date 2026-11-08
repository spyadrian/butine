import math
from datetime import UTC, datetime

import pytest

from app.models import Paper, Prompt, Source

CREATED = datetime(2026, 10, 20, tzinfo=UTC)


@pytest.fixture
def headers(client):
    return {"X-User-Id": client.post("/v1/users").json()["id"]}


@pytest.fixture
def source(session):
    source = Source(slug="cs", name="CS", url="https://cs.example/feed", kind="arxiv")
    session.add(source)
    session.flush()
    return source


def vector(similarity):
    """Unit vector whose cosine similarity with the prompt vector [1, 0, …] is `similarity`."""
    return [similarity, math.sqrt(1 - similarity**2)] + [0.0] * 382


PROMPT_VECTOR = [1.0] + [0.0] * 383


def add_prompt(session, headers, embedding=PROMPT_VECTOR):
    prompt = Prompt(
        user_id=headers["X-User-Id"],
        name="p",
        icon="label",
        text="p",
        created_at=CREATED,
        embedding=embedding,
    )
    session.add(prompt)
    session.flush()
    return prompt


def add_paper(session, source, number, similarity=0.9, day=25, published=True):
    date = datetime(2026, 10, day, tzinfo=UTC)
    session.add(
        Paper(
            external_id=f"arxiv:2410.{number:05d}",
            source_id=source.id,
            version=1,
            title=f"Paper {number}",
            authors=["Ada Lovelace"],
            abstract="Abstract.",
            categories=["cs.AI"],
            link=f"https://arxiv.org/abs/2410.{number:05d}",
            published_at=date if published else None,
            fetched_at=date,
            embedding=vector(similarity),
        )
    )
    session.flush()


def feed(client, headers, prompt, **params):
    return client.get(f"/v1/prompts/{prompt.id}/feed", params=params, headers=headers)


def titles(response):
    return [paper["title"] for paper in response.json()]


def test_threshold_keeps_papers_just_above(client, session, headers, source):
    prompt = add_prompt(session, headers)
    add_paper(session, source, 1, similarity=0.85)
    add_paper(session, source, 2, similarity=0.83)

    response = feed(client, headers, prompt)

    assert response.status_code == 200
    (paper,) = response.json()
    assert paper["title"] == "Paper 1"
    assert paper["source"] == "CS"
    assert paper["fetched_at"] == "2026-10-25T00:00:00Z"
    assert paper["score"] == pytest.approx(0.85, abs=1e-4)


def test_backfill_keeps_papers_of_the_last_seven_days(client, session, headers, source):
    prompt = add_prompt(session, headers)
    add_paper(session, source, 1, day=14)  # 6 days before the prompt
    add_paper(session, source, 2, day=12)  # 8 days before
    add_paper(session, source, 3, day=14, published=False)  # falls back on fetched_at

    assert titles(feed(client, headers, prompt)) == ["Paper 1", "Paper 3"]


def test_sorted_and_paginated_like_papers(client, session, headers, source):
    prompt = add_prompt(session, headers)
    add_paper(session, source, 1, day=21)
    add_paper(session, source, 2, day=23)
    add_paper(session, source, 3, day=22)
    add_paper(session, source, 4, published=False)

    assert titles(feed(client, headers, prompt)) == ["Paper 2", "Paper 3", "Paper 1", "Paper 4"]
    assert titles(feed(client, headers, prompt, limit=2, offset=1)) == ["Paper 3", "Paper 1"]
    assert feed(client, headers, prompt, limit=201).status_code == 422


def test_pending_prompt_has_empty_feed(client, session, headers, source):
    prompt = add_prompt(session, headers, embedding=None)
    add_paper(session, source, 1)

    assert feed(client, headers, prompt).json() == []


def test_other_users_or_unknown_prompt_is_404(client, session, headers, source):
    prompt = add_prompt(session, headers)
    other = {"X-User-Id": client.post("/v1/users").json()["id"]}

    assert feed(client, other, prompt).status_code == 404
    assert client.get("/v1/prompts/999999/feed", headers=headers).status_code == 404


def test_feed_requires_user(client, session, headers):
    prompt = add_prompt(session, headers)

    assert client.get(f"/v1/prompts/{prompt.id}/feed").status_code == 401


def global_feed(client, headers, **params):
    return client.get("/v1/feed", params=params, headers=headers)


def at(degrees):
    """Unit vector at `degrees` from the prompt vector [1, 0, …], on the first two axes."""
    return [math.cos(math.radians(degrees)), math.sin(math.radians(degrees))] + [0.0] * 382


def test_global_feed_merges_prompts_with_best_score(client, session, headers, source):
    first = add_prompt(session, headers)
    second = add_prompt(session, headers, embedding=at(40))
    add_paper(session, source, 1, day=25)
    add_paper(session, source, 2, day=26)
    papers = session.query(Paper).order_by(Paper.external_id).all()
    papers[0].embedding = at(-10)  # first: cos 10° ≈ 0.98, second: cos 50° ≈ 0.64 (dropped)
    papers[1].embedding = at(15)  # first: cos 15° ≈ 0.97, second: cos 25° ≈ 0.91
    session.flush()

    response = global_feed(client, headers)

    assert response.status_code == 200
    both, only_first = response.json()
    assert both["title"] == "Paper 2"
    assert both["fetched_at"] == "2026-10-26T00:00:00Z"
    assert both["prompt_ids"] == [first.id, second.id]
    assert both["score"] == pytest.approx(math.cos(math.radians(15)), abs=1e-4)
    assert only_first["prompt_ids"] == [first.id]
    assert only_first["score"] == pytest.approx(math.cos(math.radians(10)), abs=1e-4)


def test_global_feed_ignores_other_users_prompts(client, session, headers, source):
    other = {"X-User-Id": client.post("/v1/users").json()["id"]}
    add_prompt(session, other)
    add_paper(session, source, 1)

    assert global_feed(client, headers).json() == []


def test_global_feed_empty_without_ready_prompt(client, session, headers, source):
    add_prompt(session, headers, embedding=None)
    add_paper(session, source, 1)

    assert global_feed(client, headers).json() == []


def test_global_feed_applies_backfill_sort_and_pagination(client, session, headers, source):
    add_prompt(session, headers)
    add_paper(session, source, 1, day=21)
    add_paper(session, source, 2, day=23)
    add_paper(session, source, 3, day=12)  # 8 days before the prompt
    add_paper(session, source, 4, published=False)

    assert titles(global_feed(client, headers)) == ["Paper 2", "Paper 1", "Paper 4"]
    assert titles(global_feed(client, headers, limit=1, offset=1)) == ["Paper 1"]
    assert global_feed(client, headers, limit=201).status_code == 422
    assert client.get("/v1/feed").status_code == 401


def test_global_feed_backfill_follows_each_prompt_date(client, session, headers, source):
    old = add_prompt(session, headers)  # created on the 20th: keeps papers from the 13th
    recent = add_prompt(session, headers, embedding=at(20))  # similarity cos 20° ≈ 0.94
    recent.created_at = datetime(2026, 10, 25, tzinfo=UTC)  # keeps papers from the 18th
    add_paper(session, source, 1, day=15)
    session.flush()

    (paper,) = global_feed(client, headers).json()
    assert paper["prompt_ids"] == [old.id]
