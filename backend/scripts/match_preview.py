"""Preview prompt ↔ paper matching, to tune MATCH_THRESHOLD.

Usage: uv run python scripts/match_preview.py prompts.txt [--top 10]
prompts.txt holds one English prompt per line.
"""

import argparse
import resource
import sys
import time
from pathlib import Path

import numpy as np
from fastembed import TextEmbedding
from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.db import SessionLocal  # noqa: E402
from app.models import Paper  # noqa: E402

MODEL = "ibm-granite/granite-embedding-small-english-r2"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("prompts", type=Path)
    parser.add_argument("--top", type=int, default=10)
    args = parser.parse_args()

    prompts = [p.strip() for p in args.prompts.read_text().splitlines() if p.strip()]
    with SessionLocal() as session:
        papers = session.execute(select(Paper.title, Paper.abstract, Paper.link)).all()

    model = TextEmbedding(MODEL)
    start = time.perf_counter()
    texts = [f"{p.title}\n\n{p.abstract}" for p in papers]
    # 8k-token context: big batches of long abstracts blow up the RAM
    paper_vecs = np.array(list(model.embed(texts, batch_size=2)))
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
