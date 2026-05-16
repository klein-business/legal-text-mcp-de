FROM python:3.12-slim@sha256:401f6e1a67dad31a1bd78e9ad22d0ee0a3b52154e6bd30e90be696bb6a3d7461

COPY --from=ghcr.io/astral-sh/uv:0.10.12 /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY src/legal_text_mcp_de ./src/legal_text_mcp_de

RUN uv sync --frozen --no-dev --no-group prepare-data --no-group docs --no-install-project --compile-bytecode

# Non-root user
RUN groupadd --system --gid 10001 app && \
    useradd --system --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app && \
    chown -R 10001:10001 /app
USER 10001:10001

ENV DATASET_PATH=/data/legal-texts
ENV STRICT_STARTUP=true
ENV HOST=0.0.0.0
ENV PORT=8001

# Healthcheck against /health
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health', timeout=2)" || exit 1

CMD ["uv", "run", "--frozen", "--no-sync", "legal-text-mcp-de"]
