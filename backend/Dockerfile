# =============================================================================
# Stage: base
# Common setup shared by all environments (dev and prod).
# =============================================================================
FROM python:3.11-slim AS base

ARG POETRY_VERSION=1.8.5

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VERSION=${POETRY_VERSION} \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

ENV PATH="$POETRY_HOME/bin:$PATH"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        build-essential \
        libpq-dev \
        libmagic1 \
    && curl -sSL https://install.python-poetry.org | python - \
    && poetry config virtualenvs.create false \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash app \
    && mkdir -p /app \
    && chown -R app:app /app

WORKDIR /app

# =============================================================================
# Stage: dev
# Installs all dependencies including dev group (pytest, mypy, etc.).
# Hot-reload is enabled via volume mount in docker-compose.dev.yml.
# =============================================================================
FROM base AS dev

COPY --chown=app:app backend/pyproject.toml backend/poetry.lock ./

RUN poetry install --no-interaction --no-ansi

USER app

# =============================================================================
# Stage: prod
# Installs only main (runtime) dependencies. No source volume mount.
# Source code is copied into the image at build time.
# =============================================================================
FROM base AS prod

COPY --chown=app:app backend/pyproject.toml backend/poetry.lock ./

RUN poetry install --only main --no-interaction --no-ansi

COPY --chown=app:app backend/ .

USER app

EXPOSE 8000