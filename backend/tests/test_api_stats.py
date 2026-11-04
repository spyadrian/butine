import json
from datetime import datetime, timedelta

import app.worker
from app.worker import run_once
from tests.test_embeddings import FakeEmbedder
from tests.test_fetcher import add_source, arxiv_feed, serve
from tests.test_purge import add_paper


def test_stats_without_any_cycle(client):
    assert client.get("/v1/stats").json() == {
        "last_cycle": None,
        "active_sources": 0,
        "inactive_sources": 0,
        "papers": 0,
    }


def test_stats_match_last_cycle_log(client, session, capsys):
    add_source(session, "cs")
    add_source(session, "off", active=False)
    add_paper(session, "old", timedelta(days=31))  # its source "src-old" answers 304

    feed = arxiv_feed(("2410.1", 1, "A"), ("2410.2", 1, "B"))
    run_once(session, serve({"cs": feed, "src-old": b""}), FakeEmbedder())

    log = json.loads(capsys.readouterr().out)
    stats = client.get("/v1/stats").json()
    cycle = stats["last_cycle"]
    # Same instant, but Pydantic writes "Z" where isoformat() writes "+00:00".
    assert datetime.fromisoformat(cycle.pop("started_at")) == datetime.fromisoformat(
        log.pop("started_at")
    )
    assert cycle == log
    assert (log["feeds_polled"], log["new_papers"], log["errors"], log["purged"]) == (2, 2, 0, 1)
    assert (log["embedded_papers"], log["pending_embeddings"]) == (2, 0)
    assert {"duration_ms", "updated_papers"} <= log.keys()
    assert (stats["active_sources"], stats["inactive_sources"], stats["papers"]) == (2, 1, 2)


def test_pending_embeddings_counts_papers_over_the_batch_limit(
    client, session, capsys, monkeypatch
):
    monkeypatch.setattr(app.worker, "EMBED_BATCH_LIMIT", 2)
    add_source(session, "cs")
    feed = arxiv_feed(("2410.1", 1, "A"), ("2410.2", 1, "B"), ("2410.3", 1, "C"))
    run_once(session, serve({"cs": feed}), FakeEmbedder())

    log = json.loads(capsys.readouterr().out)
    cycle = client.get("/v1/stats").json()["last_cycle"]
    assert (log["embedded_papers"], log["pending_embeddings"]) == (2, 1)
    assert (cycle["embedded_papers"], cycle["pending_embeddings"]) == (2, 1)


def test_embedding_failure_still_records_the_cycle(client, session, capsys):
    def broken(texts):
        raise RuntimeError("model crashed")

    add_source(session, "cs")
    run_once(session, serve({"cs": arxiv_feed(("2410.1", 1, "A"))}), broken)

    log = json.loads(capsys.readouterr().out.splitlines()[-1])
    assert (log["new_papers"], log["errors"], log["embedded_papers"]) == (1, 1, 0)
    assert log["pending_embeddings"] == 1
    assert client.get("/v1/stats").json()["last_cycle"]["errors"] == 1
