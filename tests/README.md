# Marketplace API Tests

Professional pytest test suite for the Marketplace API.

## Prerequisites

1. Start all services:
```bash
docker-compose up -d
```

2. Install test dependencies:
```bash
cd tests
uv pip install -r requirements.txt
```

## Running Tests

### Run all tests:
```bash
pytest
```

### Run specific test file:
```bash
pytest tests/test_products.py
```

### Run specific test:
```bash
pytest tests/test_orders.py::test_create_order
```

### Run with coverage:
```bash
pytest --cov=services --cov-report=html
```

### Run only fast tests:
```bash
pytest -m "not slow"
```

## Test Structure

- `conftest.py` - Pytest fixtures and configuration
- `test_products.py` - Product CRUD tests (19 tests)
- `test_orders.py` - Order business logic tests (15 tests)
- `test_promo_codes.py` - Promo code tests (8 tests)
- `test_rbac.py` - Role-based access control tests (9 tests)
- `test_validation.py` - Input validation tests (9 tests)
- `test_logging.py` - JSON logging tests (13 tests)

## Total Tests: 73

## Coverage

The test suite covers all 10 requirements from task.md:

1. ✅ OpenAPI Specification for Product CRUD
2. ✅ Data Schemas in OpenAPI
3. ✅ Code Generation from OpenAPI
4. ✅ PostgreSQL with Alembic migrations
5. ✅ Contract-based Error Handling
6. ✅ Contract-based Input Validation
7. ✅ Complex Order Business Logic
8. ✅ JSON Logging
9. ✅ JWT Authorization
10. ✅ Role-based Access Control (USER, SELLER, ADMIN)
