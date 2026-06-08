FROM python:3.11-slim

ARG POETRY_VERSION=1.7.1

ENV POETRY_HOME="/opt/poetry" \
   PATH="$POETRY_HOME/bin:$PATH" \
   PIP_DISABLE_PIP_VERSION_CHECK=1 \
   PIP_NO_CACHE_DIR=1

RUN apt-get update \
   && apt-get install -y --no-install-recommends \
      ca-certificates \
      libmagic1 \
   && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --upgrade pip setuptools wheel \
   && pip install "poetry==${POETRY_VERSION}"

RUN useradd --create-home --shell /bin/bash app \
   && mkdir -p /app \
   && chown -R app:app /app

USER app
WORKDIR /app