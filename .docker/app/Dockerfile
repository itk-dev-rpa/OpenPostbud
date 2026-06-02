# syntax=docker/dockerfile:1.7

FROM python:3.12-slim-bookworm

# Pull the uv binary from the official image (pin to a release for reproducibility).
COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /usr/local/bin/

# Place the project venv outside /app so the docker-compose bind-mount of ./:/app
# does not shadow it at runtime.
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Install dependencies first (without the project) for better layer caching.
COPY pyproject.toml uv.lock /app/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Copy the project source and install the project itself.
COPY src /app/src
COPY README.md /app/README.md
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

COPY .env /app/.env

# Add deploy user to match server.
RUN addgroup --gid 1042 deploy \
    && useradd --gid 1042 --uid 1042 --home-dir /home/deploy --create-home --shell /bin/bash deploy \
    && chown -R deploy:deploy /app /opt/venv

USER deploy

# Make port 8000 available to the world outside this container
EXPOSE 8000
