# Общее описание архитектуры

## Введение

Данный документ описывает архитектуру маркетплейса, спроектированную в рамках курса SOA. Архитектура базируется на принципах Domain-Driven Design (DDD), микросервисной архитектуре и C4 моделировании.

## Архитектурные принципы

### 1. Separation of Concerns
Каждый сервис отвечает за свой домен и имеет четкие границы ответственности.

### 2. Database per Service
Каждый сервис владеет своей базой данных. Нет разделяемых баз данных между сервисами.

### 3. Async Communication for Cross-Domain
Взаимодействие между сервисами разных доменов происходит асинхронно через Message Queue.

### 4. Sync Communication for Consistency
Взаимодействие, требующее строгой консистентности, происходит синхронно (HTTP/gRPC).

### 5. API Gateway
Единая точка входа для всех клиентов. Обеспечивает аутентификацию, rate limiting, routing.

## Высокоуровневая архитектура

Архитектура состоит из следующих слоев:
- Frontend Layer: Web и мобильные приложения
- API Gateway: Единая точка входа для всех клиентов
- Services Layer: Микросервисы (Users, Catalog, Orders, Notifications)
- Data Layer: Базы данных для каждого сервиса
- Message Queue: Очередь сообщений для асинхронной коммуникации

## Микросервисы

### 1. Users Service

Домен: User Management

Ответственность:
- Регистрация и аутентификация пользователей
- Управление профилями
- Управление ролями и правами доступа

API (планируется):
- POST /api/v1/users/register - регистрация
- POST /api/v1/auth/login - вход
- GET /api/v1/users/{id} - получение профиля
- PUT /api/v1/users/{id} - обновление профиля

База данных: PostgreSQL (users, profiles, roles)

---

### 2. Catalog Service

Домен: Product Catalog

Ответственность:
- Управление товарами и категориями
- Поиск и фильтрация товаров
- Управление инвентарем

API (планируется):
- POST /api/v1/products - создание товара
- GET /api/v1/products/{id} - получение товара
- GET /api/v1/products - поиск товаров
- PUT /api/v1/products/{id} - обновление товара
- DELETE /api/v1/products/{id} - удаление товара

База данных: PostgreSQL (products, categories, inventory)

---

### 3. Orders Service

Домен: Order Management + Payment Processing

Ответственность:
- Управление заказами и корзиной
- Инициация платежей
- Обработка результатов платежей

API (планируется):
- POST /api/v1/orders - создание заказа
- GET /api/v1/orders/{id} - получение заказа
- GET /api/v1/orders - список заказов пользователя
- PUT /api/v1/orders/{id}/status - изменение статуса

База данных: PostgreSQL (orders, order_items, payments)

---

### 4. Notifications Service

Домен: Notifications + Personalization

Ответственность:
- Отправка уведомлений пользователям
- Формирование персонализированной ленты
- Рекомендации товаров

API (планируется):
- GET /api/v1/feed - персонализированная лента
- GET /api/v1/notifications - список уведомлений
- POST /api/v1/notifications/{id}/read - отметить прочитанным

База данных: PostgreSQL (notifications, templates, recommendations)

---

## Взаимодействие между сервисами

### Синхронные (HTTP/gRPC)

Откуда | Куда | Операция | Протокол
--------|------|----------|-----------
Orders | Catalog | Проверка наличия товара | HTTP
Orders | Users | Получение данных пользователя | HTTP
API Gateway | Users | Валидация токена | HTTP

### Асинхронные (Message Queue)

Откуда | Куда | Событие | Событие
--------|------|---------|--------
Orders | Notifications | OrderCreated | RabbitMQ
Orders | Notifications | OrderStatusChanged | RabbitMQ
Orders | Personalization | UserPurchase | RabbitMQ
Catalog | Personalization | ProductUpdated | RabbitMQ

---

## Безопасность

### Аутентификация
- JWT токены, выдаваемые Users Service
- Валидация токена в API Gateway

### Авторизация
- Role-based access control (RBAC)
- Проверка прав на уровне сервисов

### Шифрование
- HTTPS для всех внешних коммуникаций
- Хеширование паролей (bcrypt)
- Шифрование чувствительных данных в БД

---

## Масштабируемость

### Горизонтальное масштабирование
- Каждый сервис можно масштабировать независимо
- Stateless сервисы (без состояния в памяти)
- Поддержка container orchestration (Kubernetes)

### Вертикальное масштабирование
- Выделенные ресурсы под каждый домен
- Оптимизация баз данных под нагрузку

---

## Отказоустойчивость

### Circuit Breaker
- Защита от каскадных сбоев
- Fallback значения при недоступности зависимостей

### Retry Pattern
- Автоматические повторы для временных сбоев
- Exponential backoff

### Dead Letter Queue
- Сообщения, которые не удалось обработать
- Ручной анализ и переработка

---

## Мониторинг и наблюдаемость

### Логирование
- Структурированные логи (JSON)
- Централизованный сбор логов (ELK stack)

### Метрики
- Business metrics (заказы, пользователи)
- Technical metrics (latency, throughput, error rate)
- Health checks для каждого сервиса

### Tracing
- Распределенный tracing (OpenTelemetry)
- Корреляция запросов через сервисы

---

## Технологический стек

### Backend
- Язык: Python (FastAPI) / Go (для высоконагруженных сервисов)
- Базы данных: PostgreSQL (реляционные), Redis (кэш)

### Инфраструктура
- Контейнеризация: Docker, Docker Compose
- Orchestration: Kubernetes (в будущем)
- Message Queue: RabbitMQ

### Разработка
- API Documentation: OpenAPI/Swagger
- Monitoring: Prometheus + Grafana
- Logging: ELK Stack (Elasticsearch, Logstash, Kibana)

---

## Эволюционный путь

### Phase 1: MVP (текущий этап)
- 4 сервиса
- Базовая функциональность
- Локальная разработка

### Phase 2: Развитие
- Выделение Payment Service из Orders
- Выделение Personalization Service из Notifications
- Внедрение CI/CD

### Phase 3: Масштабирование
- Kubernetes orchestration
- Шардирование баз данных
- CDN для статического контента

---

## Заключение

Предложенная архитектура обеспечивает:
- Четкое разделение ответственности
- Независимое масштабирование
- Изоляцию сбоев
- Гибкость к изменениям
- Баланс сложности и эффективности

Выбор 4 сервисов является оптимальным для учебного проекта и может легко эволюционировать в 6 сервисов при росте требований.
