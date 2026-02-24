# SOA2026 - Marketplace Architecture

## Описание проекта

Архитектурное проектирование маркетплейса в рамках курса SOA (Service Oriented Architecture).

## Цель работы

Спроектировать масштабируемую архитектуру маркетплейса с использованием принципов DDD, C4 моделирования и микросервисов.

## Архитектура

### Выбранный подход: DDD-based (5 микросервисов)

Сервис | Домен | Ответственность
--------|-------|-----------------
Users Service | User Management | Регистрация, аутентификация, профили пользователей
Catalog Service | Product Catalog | Товары, категории, инвентарь, цены
Orders Service | Order Management + Payments | Заказы, корзина, обработка платежей
Notifications Service | Notifications | Отправка уведомлений (email, push, SMS)
Recommendations Service | Personalization | Рекомендации товаров, персонализированная лента

Выбор обоснован в docs/decomposition.md

## Структура проекта

```
soa2026/
├── README.md
├── docs/
│   ├── c4-container.c4                # C4 Container диаграмма (likeC4)
│   ├── architecture.md                # Общее описание архитектуры
│   ├── decomposition.md               # 3 варианта + trade-off'ы
│   ├── domains.md                     # Домены и их границы
│   ├── data-boundaries.md             # Владение данными
│   └── service-interactions.md        # Взаимодействия сервисов
├── services/
│   └── users/                         # Users Service (реализован)
│       ├── src/
│       │   ├── main.py               # FastAPI приложение
│       │   └── requirements.txt      # Зависимости
│       ├── Dockerfile                # Docker образ
│       ├── docker-compose.yml        # Docker Compose
│       └── README.md                 # Описание сервиса
├── Makefile
└── .gitignore
```

## Быстрый запуск

### Требования
- Docker
- Docker Compose
- Make

### Запуск Users Service

```bash
# Запуск сервиса
make up

# Проверка health endpoint
curl http://localhost:8000/health
# Ответ: {"status": "ok"}

# Просмотр логов
make logs

# Остановка
make down
```

### Просмотр C4 диаграммы (likeC4)

```bash
# Генерация диаграммы
make likec4-serve

# Открыть в браузере: http://localhost:9000
```

## Документация

- Общее описание архитектуры (docs/architecture.md) — обзор системы и решений
- Альтернативные варианты декомпозиции (docs/decomposition.md) — 3 подхода с trade-off'ами
- Домены и их границы (docs/domains.md) — 6 доменов маркетплейса
- Границы владения данными (docs/data-boundaries.md) — распределение баз данных
- Взаимодействия сервисов (docs/service-interactions.md) — протоколы общения
- C4 Container диаграмма (docs/c4-container.c4) — визуальная модель (likeC4)
