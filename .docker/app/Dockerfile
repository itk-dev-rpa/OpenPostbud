# pull pyhton
FROM python:3.11-bookworm

# Update PIP
RUN apt update && \
    pip install --no-cache-dir --upgrade pip

WORKDIR /app

COPY pyproject.toml /app/pyproject.toml
COPY src /app/src

# Install dependencies
RUN pip install --no-cache-dir build \
  && pip install -e .

# Add deploy use to match server.
RUN addgroup --gid 1042 deploy \
    && useradd --gid 1042 --uid 1042 --home-dir /home/deploy --create-home --shell /bin/bash deploy

# Ensure app is owned by deploy
RUN chown deploy:deploy /app

USER deploy

# Make port 8000 available to the world outside this container
EXPOSE 8000
