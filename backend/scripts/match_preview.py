"""Preview prompt ↔ paper matching to choose the embedding model and threshold.

Usage: uv run python scripts/match_preview.py prompts.txt [--model granite-s] [--top 10]
    [--batch-size 2] [--until YYYY-MM-DD]
prompts.txt holds one English prompt per line. Run once per model: RAM is per process.
Long-context models (granite-s, nomic, gemma, arctic-l2, qwen3) need small batches;
512-token ones (bge, e5, arctic-s) run faster with --batch-size 16.
"""

import argparse
import resource
import sys
import time
from datetime import date
from pathlib import Path

import numpy as np
from fastembed import TextEmbedding
from fastembed.common.model_description import ModelSource, PoolingType
from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.db import SessionLocal  # noqa: E402
from app.models import Paper  # noqa: E402

# name -> (fastembed model, query prefix, passage prefix)
MODELS = {
    "bge": (
        "BAAI/bge-small-en-v1.5",
        "Represent this sentence for searching relevant passages: ",
        "",
    ),
    "e5": ("intfloat/e5-small-v2", "query: ", "passage: "),
    "arctic-s": (
        "snowflake/snowflake-arctic-embed-s",
        "Represent this sentence for searching relevant passages: ",
        "",
    ),
    "granite-s": ("ibm-granite/granite-embedding-small-english-r2", "", ""),
    "bge-base": (
        "BAAI/bge-base-en-v1.5",
        "Represent this sentence for searching relevant passages: ",
        "",
    ),
    "nomic": ("nomic-ai/nomic-embed-text-v1.5", "search_query: ", "search_document: "),
    "qwen3": (
        "Qwen/Qwen3-Embedding-0.6B-Q",
        "Instruct: Given a research interest, retrieve relevant paper abstracts\nQuery: ",
        "",
    ),
    "bge-large": (
        "BAAI/bge-large-en-v1.5",
        "Represent this sentence for searching relevant passages: ",
        "",
    ),
    "arctic-l2": ("Snowflake/snowflake-arctic-embed-l-v2.0", "query: ", ""),
    "gemma": (
        "google/embeddinggemma-300m",
        "task: search result | query: ",
        "title: none | text: ",
    ),
}

TextEmbedding.add_custom_model(
    model="intfloat/e5-small-v2",
    pooling=PoolingType.MEAN,
    normalization=True,
    sources=ModelSource(hf="Xenova/e5-small-v2"),
    dim=384,
    model_file="onnx/model.onnx",
)
TextEmbedding.add_custom_model(
    model="Snowflake/snowflake-arctic-embed-l-v2.0",
    pooling=PoolingType.CLS,
    normalization=True,
    sources=ModelSource(hf="Snowflake/snowflake-arctic-embed-l-v2.0"),
    dim=1024,
    model_file="onnx/model.onnx",
    additional_files=["onnx/model.onnx_data"],
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("prompts", type=Path)
    parser.add_argument("--model", choices=MODELS, default="granite-s")
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=2)
    # the worker keeps adding papers: a fixed cutoff gives every model the same corpus
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

    name, query_prefix, passage_prefix = MODELS[args.model]
    model = TextEmbedding(name)

    start = time.perf_counter()
    texts = [f"{passage_prefix}{p.title}\n\n{p.abstract}" for p in papers]
    # fastembed's default batch of 256 long abstracts needs >12 GB of RAM
    paper_vecs = np.array(list(model.embed(texts, batch_size=args.batch_size)))
    elapsed = time.perf_counter() - start
    prompt_vecs = np.array(list(model.embed([query_prefix + p for p in prompts])))

    # fastembed does not normalize every model (granite, nomic): normalize so dot = cosine
    paper_vecs /= np.linalg.norm(paper_vecs, axis=1, keepdims=True)
    prompt_vecs /= np.linalg.norm(prompt_vecs, axis=1, keepdims=True)
    scores = prompt_vecs @ paper_vecs.T
    for prompt, row in zip(prompts, scores, strict=True):
        print(f"\n=== {prompt}")
        for i in np.argsort(row)[::-1][: args.top]:
            print(f"  {row[i]:.3f}  {papers[i].title[:100]}  {papers[i].link}")

    rss_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024  # kB on Linux
    print(
        f"\nmodel={name} papers={len(papers)} embed_time={elapsed:.1f}s "
        f"per_3000={elapsed * 3000 / len(papers):.1f}s peak_rss={rss_mb:.0f}MB"
    )


if __name__ == "__main__":
    main()
