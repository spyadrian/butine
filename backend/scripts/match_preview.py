"""Preview prompt ↔ paper matching, to tune MATCH_THRESHOLD.

Usage: uv run python scripts/match_preview.py prompts.txt [--top 10] [--batch-size 2]
    [--until YYYY-MM-DD]
prompts.txt holds one English prompt per line.
"""

import argparse
import resource
import sys
import time
from datetime import date
from pathlib import Path

import numpy as np
from fastembed import TextEmbedding
from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import EMBEDDING_MODEL  # noqa: E402
from app.db import SessionLocal  # noqa: E402
from app.models import Paper  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("prompts", type=Path)
    parser.add_argument("--top", type=int, default=10)
    # 8k-token context: big batches of long abstracts blow up the RAM
    parser.add_argument("--batch-size", type=int, default=2)
    # the worker keeps adding papers: a fixed cutoff keeps the corpus the same between runs
    parser.add_argument(
        "--until", type=date.fromisoformat, help="only papers fetched before this date (YYYY-MM-DD)"
    )
    args = parser.parse_args()

    prompts = [p.strip() for p in args.prompts.read_text().splitlines() if p.strip()]
    with SessionLocal() as session:
        query = select(Paper.title, Paper.abstract, Paper.link)
        if args.until:
            query = query.where(Paper.fetched_at < args.until)
        papers = session.execute(query).all()

    model = TextEmbedding(EMBEDDING_MODEL)
    start = time.perf_counter()
    texts = [f"{p.title}\n\n{p.abstract}" for p in papers]
    paper_vecs = np.array(list(model.embed(texts, batch_size=args.batch_size)))
    elapsed = time.perf_counter() - start
    prompt_vecs = np.array(list(model.embed(prompts)))

    # fastembed does not normalize this model: normalize so dot = cosine
    paper_vecs /= np.linalg.norm(paper_vecs, axis=1, keepdims=True)
    prompt_vecs /= np.linalg.norm(prompt_vecs, axis=1, keepdims=True)
    scores = prompt_vecs @ paper_vecs.T
    for prompt, row in zip(prompts, scores, strict=True):
        print(f"\n=== {prompt}")
        for i in np.argsort(row)[::-1][: args.top]:
            print(f"  {row[i]:.3f}  {papers[i].title[:100]}  {papers[i].link}")

    rss_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024  # kB on Linux
    print(
        f"\npapers={len(papers)} embed_time={elapsed:.1f}s "
        f"per_3000={elapsed * 3000 / len(papers):.1f}s peak_rss={rss_mb:.0f}MB"
    )


if __name__ == "__main__":
    main()
