# syntax=docker/dockerfile:1

FROM ghcr.io/astral-sh/uv:0.13 AS uv

# Build stage: resolve the locked runtime dependencies into a virtualenv.
FROM python:3.14-slim AS builder
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project

# Runtime stage: only the virtualenv and the source code, run as an unprivileged user.
FROM python:3.14-slim
LABEL org.opencontainers.image.title="pulso-api" \
      org.opencontainers.image.description="Standalone REST API over YouTube Music with an audio streaming proxy" \
      org.opencontainers.image.source="https://github.com/adrogodev/pulso-api"
RUN useradd --create-home --uid 10001 app
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY app ./app
COPY core ./core
COPY ioc ./ioc
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/', timeout=4)"]
# One worker: the memory cache and rate limiter live in the process (use Redis before adding workers).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--loop", "uvloop", "--http", "httptools", \
     "--proxy-headers", "--forwarded-allow-ips", "*", "--no-access-log", \
     "--no-server-header", "--header", "Server:pulso-api"]
