from fastapi import FastAPI

from app.api.v1 import health, papers, prompts, sources, stats, users

app = FastAPI(title="Butine")
app.include_router(health.router, prefix="/v1")
app.include_router(sources.router, prefix="/v1")
app.include_router(papers.router, prefix="/v1")
app.include_router(stats.router, prefix="/v1")
app.include_router(users.router, prefix="/v1")
app.include_router(prompts.router, prefix="/v1")
