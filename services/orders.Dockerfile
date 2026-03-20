FROM python:3.11-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY orders/pyproject.toml ./

# Install dependencies
RUN uv sync

# Copy OpenAPI spec and generate code
COPY shared/openapi/orders.yaml ./openapi.yaml
RUN mkdir -p src/api/generated && uv run datamodel-codegen --input openapi.yaml --output src/api/generated/models.py --input-file-type openapi

# Copy application code
COPY orders/src/ ./src/
COPY shared/src/ ./shared/src/
COPY orders/alembic.ini ./
COPY orders/alembic/ ./alembic/

# Expose port
EXPOSE 8003

# Run migrations and start server
CMD ["sh", "-c", "uv run alembic upgrade head && uv run uvicorn src.main:app --host 0.0.0.0 --port 8003"]
