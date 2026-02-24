# Альтернативные варианты декомпозиции

Документ описывает три альтернативных варианта архитектурной декомпозиции маркетплейса с анализом trade-off'ов для каждого варианта.

---

## Вариант A: DDD-based (Крупнозернистый подход)

### Описание

Микросервисы выстраиваются по Bounded Contexts. Каждый сервис объединяет несколько родственных доменов.

### Сервисы

Сервис | Домены | Технология
--------|--------|------------
Identity Service | User Management | FastAPI + PostgreSQL
Catalog Service | Product Catalog | FastAPI + PostgreSQL
Order Service | Order Management + Payment Processing | FastAPI + PostgreSQL
Notification Service | Notifications | FastAPI + PostgreSQL
Recommendations Service | Personalization | FastAPI + PostgreSQL

### Границы владения данными

```
Identity DB (users, roles)

Catalog DB (products, categories, inventory)

Order DB (orders, items, payments)

Notification DB (notifications, templates, delivery_status)
Recommendations DB (user_behaviors, recommendations, products_embeddings)
```

### Взаимодействия

Синхронные (HTTP/gRPC):
- Catalog -> Order (проверка наличия товара)
- Identity -> все сервисы (валидация токена)
- Order -> Catalog (резервирование товара)

Асинхронные (Message Queue):
- Order -> Notification (статус заказа)
- Order -> Recommendations (покупка пользователя)
- Catalog -> Recommendations (обновления товаров)

### Trade-off'ы Варианта A

Плюсы:
- Простота развертывания (5 сервисов)
- Меньше межсервисных коммуникаций
- Единая транзакция для заказа+платежа
- Быстрый старт для команды
- Единая точка тестирования (меньше интеграций)

Минусы:
- Order Service перегружен (2 домена)
- Payment тесно связан с Order - сложно эволюционировать
- Notifications Service и Recommendations Service разделены
- Сложнее независимо масштабировать домены
- Общее состояние - если упадет Order, блокируется и Payment

Масштабируемость: Средняя
Потенциальные узкие места: Order Service (CPU/IO при нагрузке на платежи)

---

## Вариант B: Single Responsibility (Мелкозернистый подход)

### Описание

Каждый домен - отдельный сервис. Максимальное разбиение ответственности.

### Сервисы

Сервис | Домен | Технология
--------|-------|------------
Identity Service | User Management | FastAPI + PostgreSQL
Catalog Service | Product Catalog | FastAPI + PostgreSQL
Order Service | Order Management | FastAPI + PostgreSQL
Payment Service | Payment Processing | FastAPI + PostgreSQL
Notification Service | Notifications | FastAPI + PostgreSQL
Personalization Service | Personalization | Python + PostgreSQL

### Границы владения данными

```
Identity DB  Payment DB

Catalog DB  Notification DB

Order DB  Personalization DB
```

### Взаимодействия

Синхронные (HTTP/gRPC):
- Order -> Catalog (резервирование товаров)
- Order -> Payment (инициация платежа)
- Identity -> все сервисы (аутентификация)
- Personalization -> Catalog (получение данных для рекомендаций)

Асинхронные (Message Queue):
- Order -> Notification (все события заказа)
- Order -> Personalization (действия пользователя)
- Payment -> Order (результат платежа)
- Catalog -> Personalization (обновления товаров)
- Identity -> Personalization (новый пользователь)

### Trade-off'ы Варианта B

Плюсы:
- Чистая ответственность: 1 домен = 1 сервис
- Независимое масштабирование каждого домена
- Изоляция сбоев (падение одного не блокирует другие)
- Гибкость выбора технологий для каждого сервиса
- Независимые релизы (команды работают параллельно)
- Ясные границы между командами

Минусы:
- Сложность развертывания (6 сервисов)
- Распределенные транзакции (SAGA pattern)
- Много межсервисных коммуникаций (latency)
- Высокая сложность операций/мониторинга
- Усложнение интеграционного тестирования
- Накладные расходы на инфраструктуру (6 сервисов vs 4)

Масштабируемость: Высокая
Потенциальные узкие места: Message Queue (при высокой нагрузке), наблюдаемость (сложность tracing)

---

## Вариант C: Event-Driven (Событийно-ориентированный подход)

### Описание

Все взаимодействия между сервисами асинхронные через Event Bus. Синхронные коммуникации минимизированы.

### Сервисы

Сервис | Домен | Технология
--------|-------|------------
Identity Service | User Management | FastAPI + PostgreSQL
Catalog Service | Product Catalog | FastAPI + PostgreSQL
Order Orchestrator | Order Management (координация) | FastAPI + PostgreSQL
Payment Service | Payment Processing | FastAPI + PostgreSQL
Notification Service | Notifications | FastAPI + PostgreSQL
Personalization Service | Personalization | Python + PostgreSQL
Event Bus | Event Bus | Kafka / RabbitMQ

### Границы владения данными

Аналогично Варианту B, но добавляется Event Bus:

```
Event Bus (Kafka/RabbitMQ)
```

### Взаимодействия

Синхронные (HTTP/gRPC):
- Только Identity -> другие сервисы (аутентификация)

Асинхронные (Event Bus):
- ВСЕ доменные события:
  - OrderCreated
  - PaymentProcessed
  - ProductUpdated
  - UserRegistered
  - и т.д.

### Trade-off'ы Варианта C

Плюсы:
- Полная развязка сервисов (loose coupling)
- Легкое добавление новых подписчиков на события
- Отличная масштабируемость (высокая пропускная способность)
- Audit trail встроен (история событий)
- Устойчивость к всплескам нагрузки (event replay)
- Естественная поддержка интеграции (webhooks, CDC)
- Независимость от протоколов (service-agnostic)

Минусы:
- Сложность отладки (трассировка событий)
- Eventual consistency (задержка синхронизации)
- Сложность бизнес-процессов (long-running sagas)
- Дублирование данных (read models, CQRS)
- Сложность обеспечения order-of-operations
- Накладные расходы на инфраструктуру Event Bus
- Требует дополнительного инструмента (Kafka UI)

Масштабируемость: Очень высокая
Потенциальные узкие места: Event Bus (пропускная способность), сложность sagas (orchestration vs choreography)

---

## Сравнительная таблица вариантов

Характеристика | Вариант A (DDD) | Вариант B (Single Responsibility) | Вариант C (Event-Driven)
----------------|-------------------|-----------------------------------|--------------------------
Количество сервисов | 5 | 6 | 6 + Event Bus
Количество баз данных | 5 | 6 | 6
Сложность развертывания | Низкая | Средняя | Высокая
Сложность операций | Низкая | Средняя | Высокая
Масштабируемость | Средняя | Высокая | Очень высокая
Связность сервисов | Средняя | Низкая | Очень низкая
Сложность тестирования | Средняя | Высокая | Очень высокая
Latency запросов | Низкая | Средняя | Высокая
Обработка сбоев | Прямая retry/retry | Circuit breaker + SAGA | Event replay + DLQ
Независимые релизы | Ограничена | Высокая | Очень высокая
Кривая обучения команды | Низкая | Средняя | Высокая
Инфраструктурные затраты | Низкие | Средние | Высокие

---

## Выбор финального варианта

### Выбранный вариант: Вариант A (DDD, крупнозернистый)

### Обоснование выбора

#### 1. Учебный контекст
- Ограничение "1 сервис в Docker" указывает на то, что полное развертывание не требуется сейчас
- Вариант A дает реалистичную архитектуру, которую можно показать в будущем, но начать проще
- Из 4 сервисов легко выделить Payment и Personalization в будущем (экстракция домена)

#### 2. Баланс сложности/пользы
- Достаточно декомпозиции для демонстрации bounded contexts
- Не перегружен деталями распределенных транзакций
- Понятен для объяснения на защите

#### 3. Эволюционный путь
```
Phase 1 (сейчас): 5 сервисов (Notifications и Recommendations разделены)
Phase 2: 6 сервисов (выделение Payment из Orders)
Phase 3: Event-Driven (внедрение Kafka)
```

#### 4. Оценка риска
- Низкий риск архитектурных ошибок при расширении
- Доказанная практика в реальных маркетплейсах (early-stage)
- Команда с невысоким опытом быстро освоится

#### 5. Соответствие требованиям кейса
- Домены выделены четко
- Нет разделяемых баз данных
- Сервисы имеют ясные границы ответственности
- Взаимодействия описаны (синхронные + асинхронные)

### Когда бы выбрал Вариант B

Я бы выбрал Вариант B (Single Responsibility) если:
- Нагрузка >10k RPS и требуется независимое масштабирование доменов
- Команда >5 разработчиков и команды работают параллельно
- Требование к независимым релизам каждого домена
- Разные домены требуют разных технологий (например, Personalization на ML stack)

### Когда бы выбрал Вариант C

Я бы выбрал Вариант C (Event-Driven) если:
- Hyper-scale (>1M users, >100k RPS)
- Требование к near real-time (например, flash sales)
- Сильное требование к loose coupling (много внешних интеграций)
- Нужен audit trail для compliance

---

## Альтернативные сценарии

### Scenario 1: Рост команды до 10 человек

Действие: Переход от Варианта A к Варианту B

Шаги:
1. Выделить Payment Service из Order Service (SAGA pattern)
2. Выделить Personalization Service из Notification Service
3. Внедрить Service Mesh для управления коммуникациями

Сложность: Средняя (3-4 недели)
Риск: Низкий

### Scenario 2: Рост нагрузки до 50k RPS

Действие: Вариант B -> Event-Driven для критических путей

Шаги:
1. Внедрить Kafka для event streaming
2. Перевести Order Service на event-driven (OrderCreated, OrderUpdated)
3. Оставить синхронные только для критичных операций (резервирование товара)

Сложность: Высокая (6-8 недель)
Риск: Средний

### Scenario 3: Требование к глобальному деплою

Действие: Вариант B + Multi-region

Шаги:
1. Шардировать базы данных по регионам
2. Внедрить GeoDNS routing
3. Использовать Event Bus для cross-region синхронизации

Сложность: Очень высокая (12+ недель)
Риск: Высокий

---

## Заключение

Вариант A является оптимальным выбором для текущего этапа проекта, так как:
- Обеспечивает баланс между простотой и архитектурной качеством
- Имеет четкий эволюционный путь
- Соответствует учебным ограничениям
- Минимизирует риски и сложность операций

Архитектура готова к расширению, и при росте требований можно плавно переходить к Варианту B или Варианту C.
