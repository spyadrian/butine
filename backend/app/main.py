from fastapi import FastAPI

from app.api.v1 import health, sources

app = FastAPI(title="Butine")
app.include_router(health.router, prefix="/v1")
app.include_router(sources.router, prefix="/v1")
