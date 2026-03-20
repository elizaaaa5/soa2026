# Catalog Service

Service for managing products in the marketplace.

## Features

- CRUD operations for products
- Soft delete (status = ARCHIVED)
- Pagination and filtering
- Seller-based product management
- PostgreSQL database with Alembic migrations

## Tech Stack

- FastAPI
- PostgreSQL
- SQLAlchemy (async)
- Alembic
- Pydantic v2

## Project Structure

```
catalog/
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── products.py      # Product endpoints
│   │   └── schemas.py       # Pydantic models
│   ├── db/
│   │   ├── __init__.py
│   │   ├── models.py        # SQLAlchemy models
│   │   └── session.py       # Database session
│   ├── services/
│   │   ├── __init__.py
│   │   └── product_service.py  # Business logic
│   ├── config.py            # Settings
│   └── main.py              # FastAPI app
├── alembic/
│   ├── versions/
│   │   └── 001_initial.py   # Initial migration
│   └── env.py
├── alembic.ini
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

## Setup

### Local Development

1. Install dependencies:
```bash
uv sync
```

2. Start PostgreSQL:
```bash
docker-compose up -d catalog-db
```

3. Run migrations:
```bash
uv run alembic upgrade head
```

4. Run the service:
```bash
uv run uvicorn src.main:app --reload
```

### Docker

1. Build and run all services:
```bash
docker-compose up -d
```

2. Run migrations:
```bash
docker-compose exec catalog-service uv run alembic upgrade head
```

## API Endpoints

### Products

- `POST /products` - Create a new product
- `GET /products` - List products with pagination and filtering
- `GET /products/{id}` - Get product by ID
- `PUT /products/{id}` - Update product
- `DELETE /products/{id}` - Soft delete product (set status to ARCHIVED)

### Query Parameters

- `page` - Page number (default: 0)
- `size` - Page size (default: 20, max: 100)
- `status` - Filter by status (ACTIVE, INACTIVE, ARCHIVED)
- `category` - Filter by category

## Product Model

Fields:
- `id` - UUID
- `name` - String (1-255 chars)
- `description` - String (optional, max 4000 chars)
- `price` - Decimal (> 0)
- `stock` - Integer (>= 0)
- `category` - String (1-100 chars)
- `status` - Enum (ACTIVE, INACTIVE, ARCHIVED)
- `seller_id` - UUID
- `created_at` - DateTime
- `updated_at` - DateTime

## Validation Rules

- `price` must be greater than 0
- `stock` must be >= 0
- `name` must be between 1 and 255 characters
- `category` must be between 1 and 100 characters

## Database

- PostgreSQL 16
- Index on `status` field for filtering performance
- Soft delete via status field

## Health Check

`GET /health` - Returns service health status

## OpenAPI Documentation

Access the interactive API documentation at:
- Swagger UI: http://localhost:8002/docs
- ReDoc: http://localhost:8002/redoc
