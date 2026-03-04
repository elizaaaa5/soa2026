# Orders Service

Сервис для управления заказами маркетплейса.

## Технологии

- FastAPI
- PostgreSQL
- Alembic
- SQLAlchemy (async)

## Установка и запуск

### Локальная разработка

1. Установите зависимости:
```bash
uv sync
```

2. Настройте переменные окружения в `.env`:
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/orders_db
CATALOG_SERVICE_URL=http://localhost:8001
USERS_SERVICE_URL=http://localhost:8002
```

3. Запустите базу данных:
```bash
docker-compose up -d orders-db
```

4. Примените миграции:
```bash
uv run alembic upgrade head
```

5. Запустите сервис:
```bash
uv run python -m uvicorn src.main:app --reload
```

### Docker

Запустите все сервисы:
```bash
docker-compose up -d
```

## API Документация

- Swagger UI: http://localhost:8003/docs
- ReDoc: http://localhost:8003/redoc

## Основные эндпоинты

### Заказы

- `POST /api/v1/orders` - Создание заказа
- `GET /api/v1/orders/{id}` - Получение заказа
- `PUT /api/v1/orders/{id}` - Обновление заказа
- `POST /api/v1/orders/{id}/cancel` - Отмена заказа

### Промокоды

- `POST /api/v1/promo-codes` - Создание промокода

## Бизнес-логика

### Создание заказа

1. Rate limiting (проверка последней операции CREATE_ORDER)
2. Проверка активных заказов (CREATED или PAYMENT_PENDING)
3. Проверка товаров (существуют и ACTIVE)
4. Проверка остатков (stock >= quantity)
5. Резервирование остатков (stock -= quantity)
6. Снапшот цен (price_at_order)
7. Расчет стоимости с промокодом
8. Запись операции в user_operations

### Статусы заказа

- `CREATED` - Заказ создан
- `PAYMENT_PENDING` - Ожидание оплаты
- `PAID` - Оплачен
- `SHIPPED` - Отправлен
- `COMPLETED` - Завершен
- `CANCELED` - Отменен

### Промокоды

- `PERCENTAGE`: discount = total * value / 100 (макс 70%)
- `FIXED_AMOUNT`: discount = min(value, total)

Проверки промокода:
- active = true
- current_uses < max_uses
- valid_from <= now <= valid_until
- total >= min_order_amount

## Миграции

Создание новой миграции:
```bash
uv run alembic revision --autogenerate -m "description"
```

Применение миграций:
```bash
uv run alembic upgrade head
```

Откат миграции:
```bash
uv run alembic downgrade -1
```

## Тестирование

Пример создания заказа:
```bash
curl -X POST http://localhost:8003/api/v1/orders \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "items": [
      {
        "product_id": "550e8400-e29b-41d4-a716-446655440000",
        "quantity": 2
      }
    ],
    "promo_code": "SUMMER2024"
  }'
```
