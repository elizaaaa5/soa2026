# API Gateway Service

Единая точка входа для всех сервисов SOA 2026.

## Возможности

- **Проксирование запросов** к микросервисам
- **JWT валидация** для защищенных endpoints
- **JSON логирование** всех запросов
- **Request ID** для трассировки запросов

## Структура

```
gateway/
├── src/
│   ├── main.py              # FastAPI приложение
│   ├── config.py            # Конфигурация
│   ├── middleware/          # Middleware
│   │   ├── request_id.py    # Генерация X-Request-ID
│   │   ├── logging.py       # JSON логирование
│   │   └── auth.py          # JWT валидация
│   └── proxy/               # Проксирование
│       └── router.py        # Логика проксирования
├── pyproject.toml           # Зависимости
├── Dockerfile               # Docker образ
├── docker-compose.yml       # Docker Compose конфигурация
└── README.md                # Документация
```

## Routing

| Path Prefix | Service | Port |
|-------------|---------|------|
| `/auth/*` | users-service | 8001 |
| `/users/*` | users-service | 8001 |
| `/products/*` | catalog-service | 8002 |
| `/orders/*` | orders-service | 8003 |
| `/promo-codes/*` | orders-service | 8003 |

## Публичные endpoints (без авторизации)

- `/auth/register`
- `/auth/login`
- `/auth/refresh`
- `/health`
- `/docs`
- `/openapi.json`

## Логирование

Все запросы логируются в JSON формате:

```json
{
  "request_id": "uuid",
  "method": "POST",
  "endpoint": "/products",
  "status_code": 201,
  "duration_ms": 150,
  "user_id": "uuid or null",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Запуск

### Локально

```bash
# Установка зависимостей
uv sync

# Запуск
uv run uvicorn src.main:app --reload --port 8000
```

### Docker

```bash
# Сборка образа
docker build -t gateway-service .

# Запуск
docker run -p 8000:8000 gateway-service
```

### Docker Compose

```bash
# Запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f gateway
```

## Middleware

### RequestIdMiddleware
Генерирует уникальный `X-Request-ID` для каждого запроса и добавляет его в заголовки ответа.

### LoggingMiddleware
Логирует все запросы в JSON формате с информацией о:
- Request ID
- HTTP метод
- Endpoint
- Status code
- Duration
- User ID
- Timestamp

### AuthMiddleware
Валидирует JWT токены для защищенных endpoints. Пропускает публичные endpoints без проверки.

## Конфигурация

Переменные окружения:

- `USERS_SERVICE_URL` - URL users-service (default: `http://users-service:8001`)
- `CATALOG_SERVICE_URL` - URL catalog-service (default: `http://catalog-service:8002`)
- `ORDERS_SERVICE_URL` - URL orders-service (default: `http://orders-service:8003`)
- `JWT_SECRET_KEY` - Секретный ключ для JWT (default: `your-secret-key-change-in-production`)
- `JWT_ALGORITHM` - Алгоритм JWT (default: `HS256`)
- `GATEWAY_PORT` - Порт gateway (default: `8000`)
- `GATEWAY_HOST` - Хост gateway (default: `0.0.0.0`)

## Примеры запросов

### Регистрация (публичный endpoint)
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'
```

### Получение продуктов (требует авторизации)
```bash
curl -X GET http://localhost:8000/products \
  -H "Authorization: Bearer <jwt_token>"
```

### Создание заказа (требует авторизации)
```bash
curl -X POST http://localhost:8000/orders \
  -H "Authorization: Bearer <jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{"product_id": "uuid", "quantity": 1}'
```

## Health Check

```bash
curl http://localhost:8000/health
```

Ответ:
```json
{
  "status": "healthy",
  "service": "gateway"
}
```

## API Documentation

Swagger UI доступен по адресу: `http://localhost:8000/docs`

OpenAPI JSON: `http://localhost:8000/openapi.json`
