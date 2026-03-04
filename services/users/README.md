# Users Service

Микросервис для управления пользователями и аутентификации.

## Функциональность

- Регистрация пользователей
- Аутентификация (JWT access + refresh tokens)
- Управление ролями (USER, SELLER, ADMIN)
- Refresh токены с хранением в БД

## Технологический стек

- Python 3.11+
- FastAPI
- PostgreSQL + SQLAlchemy (async)
- Alembic (миграции)
- JWT (python-jose)
- bcrypt (хеширование паролей)

## API Endpoints

| Метод | Endpoint | Описание | Auth |
|-------|----------|----------|------|
| POST | /auth/register | Регистрация | ❌ |
| POST | /auth/login | Вход | ❌ |
| POST | /auth/refresh | Обновление токена | ❌ |
| GET | /users/me | Профиль пользователя | ✅ |
| GET | /health | Health check | ❌ |

## Запуск

### Через Docker Compose

```bash
docker-compose up -d
```

### Локально

```bash
uv sync
alembic upgrade head
uv run uvicorn src.main:app --reload --port 8001
```

## Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| DATABASE_URL | URL базы данных | postgresql+asyncpg://... |
| JWT_SECRET_KEY | Секретный ключ JWT | - |
| JWT_ALGORITHM | Алгоритм JWT | HS256 |
| ACCESS_TOKEN_EXPIRE_MINUTES | Время жизни access токена | 30 |
| REFRESH_TOKEN_EXPIRE_DAYS | Время жизни refresh токена | 7 |

## Роли пользователей

| Роль | Описание |
|------|----------|
| USER | Покупатель - может создавать заказы |
| SELLER | Продавец - может управлять товарами |
| ADMIN | Администратор - полный доступ |

## Токены

- **Access token**: 30 минут, содержит user_id и role
- **Refresh token**: 7 дней, хранится в БД, можно отозвать
