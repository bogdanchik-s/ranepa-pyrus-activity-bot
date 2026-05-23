FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

ENV UV_NO_DEV=1
ENV UV_LINK_MODE=copy
ENV UV_COMPILE_BYTECODE=1
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project
    
COPY . .

RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked

# prod
FROM python:3.12-slim-bookworm

RUN groupadd --system --gid 999 appgroup && useradd --system --gid 999 --uid 999 --create-home appuser

COPY --from=builder --chown=appuser:appgroup /app /app

ENV PATH="/app/.venv/bin:$PATH"

USER appuser

WORKDIR /app

CMD ["python", "app.py"]
