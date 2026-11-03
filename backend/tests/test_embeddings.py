import uuid

import numpy as np
from sqlalchemy import select

from app.models import Paper, Prompt, Source, User
from app.services import embeddings
from app.services.embeddings import embed_pending


class FakeEmbedder:
    """Return [3, 4, 0, …] for every text and remember each call's texts."""

    def __init__(self):
        self.calls: list[list[str]] = []

    def __call__(self, texts: list[str]):
        self.calls.append(list(texts))
        return [[3.0, 4.0] + [0.0] * 382 for _ in texts]


def add_paper(session, n: int, source: Source) -> Paper:
    paper = Paper(
        external_id=f"arxiv:2410.{n}",
        source_id=source.id,
        version=1,
        title=f"Title {n}",
        authors=[],
        abstract=f"Abstract {n}",
        categories=[],
        link=f"https://arxiv.org/abs/2410.{n}",
    )
    session.add(paper)
    return paper


def setup(session, papers: int) -> Prompt:
    source = Source(slug="cs", name="cs", url="https://feeds.example/cs", kind="arxiv")
    user = User(id=uuid.uuid4())
    session.add_all([source, user])
    session.flush()
    for n in range(papers):
        add_paper(session, n, source)
    prompt = Prompt(user_id=user.id, text="protein folding")
    session.add(prompt)
    session.flush()
    return prompt


def test_fills_prompts_then_papers_with_normalized_vectors(session):
    prompt = setup(session, papers=2)
    embed = FakeEmbedder()

    embedded = embed_pending(session, embed, batch_limit=10)

    assert embedded == 2
    assert embed.calls[0] == ["protein folding"]
    assert sorted(embed.calls[1]) == ["Title 0\n\nAbstract 0", "Title 1\n\nAbstract 1"]
    session.expire_all()
    for row in [prompt, *session.scalars(select(Paper))]:
        assert np.allclose(row.embedding[:2], [0.6, 0.8])


def test_respects_batch_limit_and_skips_embedded_rows(session):
    setup(session, papers=5)
    embed = FakeEmbedder()

    assert embed_pending(session, embed, batch_limit=3) == 3
    assert embed_pending(session, embed, batch_limit=3) == 2
    assert embed_pending(session, embed, batch_limit=3) == 0

    assert [len(texts) for texts in embed.calls] == [1, 3, 2]  # the prompt only once


def test_prompt_created_mid_batch_waits_one_chunk(session, monkeypatch):
    monkeypatch.setattr(embeddings, "COMMIT_EVERY", 1)
    prompt = setup(session, papers=3)
    fake = FakeEmbedder()

    def embed(texts):
        if len(fake.calls) == 1:  # while the first paper is being embedded
            session.add(Prompt(user_id=prompt.user_id, text="new prompt"))
        return fake(texts)

    embed_pending(session, embed, batch_limit=10)

    assert fake.calls[2] == ["new prompt"]
    assert len(fake.calls) == 5
