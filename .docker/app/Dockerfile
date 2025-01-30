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

# Make port 8000 available to the world outside this container
EXPOSE 8000
