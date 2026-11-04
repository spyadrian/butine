FROM python:3.14-slim
COPY --from=ghcr.io/astral-sh/uv:0.13.1 /uv /usr/local/bin/uv

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PATH="/app/.venv/bin:$PATH"

# Dependencies first so code changes don't invalidate this layer.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Bake the embedding model into the image: the worker starts without downloading it.
ENV FASTEMBED_CACHE_PATH=/opt/fastembed
# Only config.py, so a code change does not download the model again.
COPY app/__init__.py app/config.py app/
RUN python -c "from fastembed import TextEmbedding; from app.config import EMBEDDING_MODEL; \
    TextEmbedding(EMBEDDING_MODEL)"

COPY . .
# Apply pending migrations, then start the API.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]
