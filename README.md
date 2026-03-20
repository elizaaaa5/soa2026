# SOA2026 - Marketplace API

API маркетплейса с контрактным подходом (OpenAPI-first) и микросервисной архитектурой.

## Архитектура

### Сервисы

| Сервис | Порт | Ответственность |
|--------|------|-----------------|
| **Gateway** | 8000 | Единая точка входа, JWT валидация, логирование |
| **Users** | 8001 | Регистрация, аутентификация, роли (USER, SELLER, ADMIN) |
| **Catalog** | 8002 | CRUD товаров, мягкое удаление, пагинация |
| **Orders** | 8003 | Заказы, промокоды, бизнес-логика |

### Технологии

- **Python 3.11** + **FastAPI**
- **PostgreSQL** + **SQLAlchemy** (async)
- **Alembic** (миграции)
- **JWT** (python-jose)
- **Docker** + **Docker Compose**

## Быстрый запуск

```bash
# Запуск всех сервисов
docker-compose up -d

# Проверка
curl http://localhost:8000/health
```

### Эндпоинты

| Endpoint | Описание |
|----------|----------|
| `POST /auth/register` | Регистрация |
| `POST /auth/login` | Вход |
| `POST /auth/refresh` | Обновление токена |
| `GET/POST/PUT/DELETE /products` | CRUD товаров |
| `POST /orders` | Создание заказа |
| `PUT /orders/{id}` | Обновление заказа |
| `POST /orders/{id}/cancel` | Отмена заказа |
| `POST /promo-codes` | Создание промокода |

## Структура проекта

```
soa2026/
├── docker-compose.yml          # Все сервисы
├── services/
│   ├── gateway/                # API Gateway (8000)
│   ├── users/                  # Auth + Users (8001)
│   ├── catalog/                # Products CRUD (8002)
│   ├── orders/                 # Orders + PromoCodes (8003)
│   └── shared/                 # OpenAPI спецификации
│       └── openapi/
│           ├── auth.yaml
│           ├── catalog.yaml
│           └── orders.yaml
└── docs/                       # Архитектурная документация
```

## Кодогенерация из OpenAPI

```bash
# Генерация моделей для всех сервисов
cd services/shared
uv run python generate.py --all
```

Сгенерированный код попадает в `*/api/generated/` и добавлен в `.gitignore`.

## Требования задания (task.md)

| Баллы | Требование | Статус |
|-------|------------|--------|
| 1 | OpenAPI спецификация CRUD | ✅ |
| 2 | Схемы данных в OpenAPI | ✅ |
| 3 | Кодогенерация из OpenAPI | ✅ |
| 4 | PostgreSQL + Alembic + мягкое удаление | ✅ |
| 5 | Контрактная обработка ошибок | ✅ |
| 6 | Контрактная валидация | ✅ |
| 7 | Бизнес-логика заказов | ✅ |
| 8 | JSON логирование | ✅ |
| 9 | JWT авторизация | ✅ |
| 10 | Ролевая модель | ✅ |

## Документация

- [Архитектура](docs/architecture.md)
- [Декомпозиция](docs/decomposition.md)
- [Домены](docs/domains.md)
- [Владение данными](docs/data-boundaries.md)
- [Взаимодействия](docs/service-interactions.md)

## Разработка

### Отдельный сервис

```bash
cd services/users
uv sync
alembic upgrade head
uv run uvicorn src.main:app --reload --port 8001
```

### Переменные окружения

| Переменная | Описание |
|------------|----------|
| `DATABASE_URL` | URL PostgreSQL |
| `JWT_SECRET_KEY` | Секретный ключ JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Время жизни access токена |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Время жизни refresh токена |
