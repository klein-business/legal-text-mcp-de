FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.10.12 /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --no-group prepare-data --no-install-project --compile-bytecode

COPY mcp/ ./mcp/

ENV DATASET_PATH=/data/legal-texts
ENV STRICT_STARTUP=true
ENV PYTHONPATH=/app/mcp
ENV HOST=0.0.0.0
ENV PORT=8001

CMD ["uv", "run", "--frozen", "--no-sync", "python", "mcp/server.py"]
