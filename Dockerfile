FROM --platform=amd64 python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency manifests first for layer caching
COPY pyproject.toml ./

# Install dependencies into the system Python (no virtualenv needed in Docker)
RUN uv pip install --system --no-cache -e .

# Copy application source
COPY app/ ./app/

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]