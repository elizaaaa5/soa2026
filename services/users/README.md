# Users Service

## Описание

Users Service - микросервис для управления пользователями маркетплейса.

### Ответственность

- Регистрация новых пользователей (покупатели и продавцы)
- Аутентификация и авторизация
- Управление профилями пользователей
- Управление ролями и правами доступа

### Технологический стек

- Язык: Python 3.11+
- Фреймворк: FastAPI
- Сервер: Uvicorn
- База данных: PostgreSQL (будет подключена в будущем)

## API

### Health Check

```http
GET /health
```

Response (200 OK):
```json
{
  "status": "ok",
  "service": "users-service",
  "version": "1.0.0"
}
```

### Root

```http
GET /
```

Response (200 OK):
```json
{
  "service": "users-service",
  "version": "1.0.0",
  "message": "Users Service is running"
}
```

## Запуск

### Локально

```bash
cd services/users/src
pip install -r requirements.txt
python main.py
```

### Через Docker

```bash
cd services/users
docker-compose up -d
```

### Проверка

```bash
curl http://localhost:8000/health
```

## Текущее состояние

- Health check endpoint
- Docker контейнеризация
- Docker Compose конфигурация
- База данных (PostgreSQL) - TBD
- Регистрация пользователей - TBD
- Аутентификация (JWT) - TBD
- Управление профилями - TBD

## Архитектура

```
Users Service
    |
    | FastAPI Application
    | - / (root)
    | - /health
    | - /register (TBD)
    | - /login (TBD)
    | - /users (TBD)
    |
    V
PostgreSQL DB (будет подключена)
```

## Взаимодействия с другими сервисами

### Синхронные (HTTP)

Откуда | Куда | Операция
--------|------|----------
API Gateway | Users Service | Валидация токена
Orders Service | Users Service | Получение данных пользователя
Notifications Service | Users Service | Получение контактных данных

### Асинхронные (Message Queue)

Откуда | Куда | Событие
--------|------|--------
Users Service | Message Queue | UserRegistered
