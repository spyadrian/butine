from collections.abc import Callable, Iterable, Sequence

import numpy as np
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models import Paper, Prompt

COMMIT_EVERY = 100  # papers; ~15 s of embedding on CPU

Embed = Callable[[list[str]], Iterable[Sequence[float]]]


def _store(session: Session, model: type[Paper | Prompt], rows, embed: Embed) -> None:
    """Embed (id, text) rows, normalized so cosine = dot product, then commit."""
    if not rows:
        return
    vectors = embed([text for _, text in rows])
    for (row_id, _), vector in zip(rows, vectors, strict=True):
        vector = np.asarray(vector, dtype=np.float32)
        # UPDATE … WHERE id: a prompt deleted meanwhile by the API is simply skipped.
        session.execute(
            update(model)
            .where(model.id == row_id)
            .values(embedding=vector / np.linalg.norm(vector))
        )
    session.commit()


def _embed_prompts(session: Session, embed: Embed) -> None:
    rows = session.execute(select(Prompt.id, Prompt.text).where(Prompt.embedding.is_(None))).all()
    _store(session, Prompt, rows, embed)


def embed_pending(session: Session, embed: Embed, batch_limit: int) -> int:
    """Embed every pending prompt, then up to batch_limit pending papers, newest first.

    Return the number of papers embedded.
    """
    _embed_prompts(session, embed)
    papers = session.execute(
        select(Paper.id, Paper.title + "\n\n" + Paper.abstract)
        .where(Paper.embedding.is_(None))
        .order_by(Paper.fetched_at.desc(), Paper.id.desc())
        .limit(batch_limit)
    ).all()
    for start in range(0, len(papers), COMMIT_EVERY):
        _store(session, Paper, papers[start : start + COMMIT_EVERY], embed)
        # A prompt created meanwhile waits for one chunk, not for the whole batch.
        _embed_prompts(session, embed)
    return len(papers)
