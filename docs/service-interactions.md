# Взаимодействия сервисов

## Обзор

Документ описывает все взаимодействия между сервисами маркетплейса: синхронные (HTTP/gRPC) и асинхронные (Message Queue).

## Карта взаимодействий

Синхронные взаимодействия:
- API Gateway -> Users Service (Auth)
- API Gateway -> Catalog Service (Products)
- API Gateway -> Orders Service
  - Orders Service -> Catalog Service (Check inventory)
  - Orders Service -> Users Service (Get user data)
- API Gateway -> Notifications Service
- API Gateway -> Recommendations Service
- Notifications Service -> Users Service (Get contact info)

Асинхронные взаимодействия (Message Queue):
- Orders Service -> Message Queue -> Notifications Service (Order events)
- Orders Service -> Message Queue -> Recommendations (User behavior)

## Синхронные взаимодействия (HTTP/gRPC)

### API Gateway -> Services

#### 1. API Gateway -> Users Service

Операция: Валидация JWT токена

HTTP Method: POST /api/v1/auth/validate

Headers:
```
Authorization: Bearer <jwt_token>
```

Request Body:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

Response (200 OK):
```json
{
  "valid": true,
  "user_id": "uuid",
  "role": "BUYER",
  "exp": 1704067200
}
```

Use case: Каждый запрос к API Gateway сначала валидирует токен

---

#### 2. API Gateway -> Catalog Service

Операция: Получение списка товаров

HTTP Method: GET /api/v1/products

Query Params:
```
?category=electronics&page=1&limit=20&sort=price
```

Response (200 OK):
```json
{
  "products": [
    {
      "id": "uuid",
      "name": "iPhone 15",
      "price": 999.99,
      "seller_id": "uuid"
    }
  ],
  "total": 1000,
  "page": 1,
  "limit": 20
}
```

Use case: Просмотр каталога товаров

---

#### 3. API Gateway -> Orders Service

Операция: Создание заказа

HTTP Method: POST /api/v1/orders

Request Body:
```json
{
  "user_id": "uuid",
  "items": [
    {
      "product_id": "uuid",
      "quantity": 2
    }
  ]
}
```

Response (201 Created):
```json
{
  "order_id": "uuid",
  "status": "CREATED",
  "total_amount": 1999.98
}
```

Use case: Оформление заказа

---

### Service -> Service

#### 4. Orders Service -> Catalog Service

Операция: Проверка наличия и резервирование товара

HTTP Method: POST /api/v1/products/reserve

Request Body:
```json
{
  "product_id": "uuid",
  "quantity": 2,
  "order_id": "uuid"
}
```

Response (200 OK):
```json
{
  "available": true,
  "reserved": true,
  "price": 999.99
}
```

Use case: Перед созданием заказа проверяем наличие товара

---

#### 5. Orders Service -> Users Service

Операция: Получение данных пользователя для чека

HTTP Method: GET /api/v1/users/{user_id}/checkout-data

Response (200 OK):
```json
{
  "email": "user@example.com",
  "name": "John Doe",
  "phone": "+1 234 567 890"
}
```

Use case: Формирование чека и отправка уведомления

---

#### 6. Notifications Service -> Users Service

Операция: Получение контактных данных для уведомления

HTTP Method: GET /api/v1/users/{user_id}/contacts

Response (200 OK):
```json
{
  "email": "user@example.com",
  "phone": "+1 234 567 890",
  "push_token": "expo_push_token"
}
```

Use case: Отправка уведомлений по разным каналам

---

## Асинхронные взаимодействия (Message Queue)

### RabbitMQ Exchanges

```
                RabbitMQ

  orders.exchange       catalog.exchange
        |                   |
  Q1 (notifications)    Q2 (updates)
         |                   |
  Notifications Service   Recommendations
```

---

### Events от Orders Service

#### 1. OrderCreated

Exchange: orders.exchange

Routing Key: order.created

Queue: notifications.order_created

Payload:
```json
{
  "event_id": "uuid",
  "event_type": "OrderCreated",
  "timestamp": "2024-01-01T12:00:00Z",
  "data": {
    "order_id": "uuid",
    "user_id": "uuid",
    "total_amount": 1999.98,
    "items": [
      {
        "product_id": "uuid",
        "product_name": "iPhone 15",
        "quantity": 2,
        "price": 999.99
      }
    ]
  }
}
```

Consumer: Notifications Service, Recommendations Service

Действие: Notifications Service - отправить уведомление "Заказ создан" пользователю; Recommendations Service - обновить рекомендации на основе покупки

---

#### 2. OrderStatusChanged

Exchange: orders.exchange

Routing Key: order.status_changed

Queue: notifications.order_status_changed

Payload:
```json
{
  "event_id": "uuid",
  "event_type": "OrderStatusChanged",
  "timestamp": "2024-01-01T14:00:00Z",
  "data": {
    "order_id": "uuid",
    "user_id": "uuid",
    "old_status": "CONFIRMED",
    "new_status": "SHIPPED",
    "updated_at": "2024-01-01T14:00:00Z"
  }
}
```

Consumer: Notifications Service

Действие: Отправить уведомление о новом статусе заказа

---

#### 3. UserPurchase

Exchange: orders.exchange

Routing Key: user.purchase

Queue: recommendations.user_behavior

Payload:
```json
{
  "event_id": "uuid",
  "event_type": "UserPurchase",
  "timestamp": "2024-01-01T12:00:00Z",
  "data": {
    "user_id": "uuid",
    "order_id": "uuid",
    "products": [
      {
        "product_id": "uuid",
        "category_id": "uuid",
        "quantity": 2
      }
    ]
  }
}
```

Consumer: Recommendations Service

Действие: Обновить рекомендации на основе покупки

---

### Events от Catalog Service

#### 4. ProductViewed

Exchange: catalog.exchange

Routing Key: product.viewed

Queue: recommendations.user_behavior

Payload:
```json
{
  "event_id": "uuid",
  "event_type": "ProductViewed",
  "timestamp": "2024-01-01T12:00:00Z",
  "data": {
    "user_id": "uuid",
    "product_id": "uuid",
    "category_id": "uuid"
  }
}
```

Consumer: Recommendations Service

Действие: Обновить рекомендации на основе просмотра

---

#### 5. ProductUpdated

Exchange: catalog.exchange

Routing Key: product.updated

Queue: recommendations.catalog_updates

Payload:
```json
{
  "event_id": "uuid",
  "event_type": "ProductUpdated",
  "timestamp": "2024-01-01T12:00:00Z",
  "data": {
    "product_id": "uuid",
    "old_price": 999.99,
    "new_price": 899.99,
    "updated_at": "2024-01-01T12:00:00Z"
  }
}
```

Consumer: Recommendations Service

Действие: Обновить рекомендации, если изменилась цена

---

### Events от Users Service

#### 6. UserRegistered

Exchange: users.exchange

Routing Key: user.registered

Queue: recommendations.user_registered

Payload:
```json
{
  "event_id": "uuid",
  "event_type": "UserRegistered",
  "timestamp": "2024-01-01T12:00:00Z",
  "data": {
    "user_id": "uuid",
    "email": "user@example.com",
    "role": "BUYER"
  }
}
```

Consumer: Recommendations Service

Действие: Инициализировать пустую ленту для нового пользователя

---

## Обработка сбоев

### Синхронные запросы

#### Timeout
- Таймаут на запросы: 5 секунд
- Если сервис не отвечает - ошибка клиенту

#### Retry Policy
```python
retry_policy = {
    "max_attempts": 3,
    "backoff": "exponential",
    "initial_delay": 100ms,
    "max_delay": 1s
}
```

#### Circuit Breaker
```python
circuit_breaker = {
    "failure_threshold": 5,
    "success_threshold": 2,
    "timeout": 10s,
    "half_open_attempts": 1
}
```

---

### Асинхронные сообщения

#### Acknowledgment
- Сообщение подтверждается только после успешной обработки
- При ошибке - сообщение возвращается в очередь

#### Dead Letter Queue
```python
dlq_config = {
    "max_retries": 3,
    "delay_between_retries": "5min",
    "dlq_exchange": "dlq.exchange",
    "dlq_routing_key": "dlq.routing_key"
}
```

#### Exactly-Once Semantics
- Идемпотентные операции при обработке сообщений
- Использование event_id для дедупликации

---

## Мониторинг взаимодействий

### Метрики для синхронных запросов

Метрика | Описание | Агрегация
---------|----------|-----------
request_count | Кол-во запросов | По сервису, endpoint, методу
request_latency | Время ответа | P50, P95, P99
error_rate | Доля ошибок | По статусам (4xx, 5xx)
circuit_breaker_state | Состояние Circuit Breaker | Closed, Open, Half-Open

### Метрики для асинхронных сообщений

Метрика | Описание | Агрегация
---------|----------|-----------
message_count | Кол-во сообщений | По exchange, routing_key
processing_time | Время обработки | P50, P95, P99
retry_count | Кол-во retry | По типу события
dlq_count | Сообщения в DLQ | По типу события

---

## Заключение

Взаимодействия сервисов спроектированы с учетом:

- Баланс синхронных и асинхронных
  - Синхронные для консистентности
  - Асинхронные для развязки

- Отказоустойчивость
  - Timeouts, Retries, Circuit Breaker
  - Dead Letter Queue

- Наблюдаемость
  - Метрики для всех взаимодействий
  - Трассировка запросов

- Масштабируемость
  - Сообщения в очереди обрабатываются параллельно
  - Горизонтальное масштабирование consumers
