FROM python:3.13-slim

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .
RUN uv sync --frozen --no-dev

RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

# Render (and most PaaS targets) inject a dynamic $PORT; the ${PORT:-8000}
# fallback keeps `docker run -p 8000:8000` working unchanged locally.
# Migrations are NOT run here — Render's Pre-Deploy Command (see render.yaml
# at the repo root) runs `alembic upgrade head` once per deploy in a fresh
# instance of this same image, before traffic is cut over. Chaining it into
# CMD instead would re-run it on every container restart, not just deploys.
# --no-sync: the venv is already built (line 11) — without this, `uv run`
# re-resolves against pyproject.toml's default group set (including dev
# deps like mypy/ruff) and re-syncs over the network on every boot.
CMD ["sh", "-c", "uv run --no-sync uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
