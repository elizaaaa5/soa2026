# Границы владения данными

## Общий принцип

Каждый микросервис владеет своей базой данных и отвечает за консистентность своих данных. Нет разделяемых баз данных между сервисами.

## Карта данных

Структура баз данных:
- Users DB: users, roles, profiles (Users Service)
- Catalog DB: products, categories, inventory (Catalog Service)
- Orders DB: orders, items, payments (Orders Service)
- Notifications DB: notifications, templates, recommendations (Notifications Service)
- Message Queue: для асинхронной коммуникации между сервисами

## Детальное описание баз данных

### 1. Users DB (владеет Users Service)

База данных: PostgreSQL

Таблицы:

Таблица | Описание | Кол-во записей (прогноз)
---------|----------|-------------------------
users | Пользователи | 1M
profiles | Профили пользователей | 1M
roles | Роли (BUYER, SELLER, ADMIN) | 3
sessions | Активные сессии | 100K

Схема (упрощенная):

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role_id UUID REFERENCES roles(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE profiles (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) UNIQUE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    address JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE roles (
    id UUID PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE sessions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    token VARCHAR(500) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

Что владеет:
- Все данные о пользователях
- Информация о ролях и правах доступа
- Активные сессии

Что НЕ владеет:
- Информация о заказах (Orders DB)
- Информация о товарах (Catalog DB)
- Уведомления (Notifications DB)

---

### 2. Catalog DB (владеет Catalog Service)

База данных: PostgreSQL

Таблицы:

Таблица | Описание | Кол-во записей (прогноз)
---------|----------|-------------------------
products | Товары | 10M
categories | Категории (дерево) | 10K
inventory | Инвентарь товаров | 10M
prices | История цен | 50M

Схема (упрощенная):

```sql
CREATE TABLE categories (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    parent_id UUID REFERENCES categories(id),
    level INT NOT NULL
);

CREATE TABLE products (
    id UUID PRIMARY KEY,
    name VARCHAR(500) NOT NULL,
    description TEXT,
    category_id UUID REFERENCES categories(id),
    seller_id UUID NOT NULL, -- ссылка на внешний Users Service
    price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE inventory (
    id UUID PRIMARY KEY,
    product_id UUID REFERENCES products(id) UNIQUE,
    quantity INT NOT NULL DEFAULT 0,
    reserved_quantity INT NOT NULL DEFAULT 0
);

CREATE TABLE prices (
    id UUID PRIMARY KEY,
    product_id UUID REFERENCES products(id),
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    valid_from TIMESTAMP NOT NULL,
    valid_to TIMESTAMP
);
```

Что владеет:
- Все данные о товарах
- Структура категорий
- Инвентарь и количество
- История цен

Что НЕ владеет:
- Информация о продавцах (Users DB - только seller_id как ссылка)
- Информация о заказах (Orders DB)

---

### 3. Orders DB (владеет Orders Service)

База данных: PostgreSQL

Таблицы:

Таблица | Описание | Кол-во записей (прогноз)
---------|----------|-------------------------
orders | Заказы | 100M
order_items | Позиции заказов | 500M
payments | Платежи | 100M
invoices | Счета | 100M
carts | Корзины пользователей | 10M

Схема (упрощенная):

```sql
CREATE TABLE orders (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL, -- ссылка на внешний Users Service
    status VARCHAR(50) NOT NULL,
    total_amount DECIMAL(12, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE order_items (
    id UUID PRIMARY KEY,
    order_id UUID REFERENCES orders(id),
    product_id UUID NOT NULL, -- ссылка на внешний Catalog Service
    quantity INT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE payments (
    id UUID PRIMARY KEY,
    order_id UUID REFERENCES orders(id) UNIQUE,
    amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(50) NOT NULL,
    method VARCHAR(50) NOT NULL,
    gateway_transaction_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE carts (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL UNIQUE,
    items JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

Что владеет:
- Все данные о заказах
- Позиции заказов (snapshot цен и количества)
- Платежи и транзакции
- Корзины пользователей

Что НЕ владеет:
- Детальная информация о пользователях (Users DB)
- Детальная информация о товарах (Catalog DB)

---

### 4. Notifications DB (владеет Notifications Service)

База данных: PostgreSQL

Таблицы:

Таблица | Описание | Кол-во записей (прогноз)
---------|----------|-------------------------
notifications | Уведомления | 1B
templates | Шаблоны уведомлений | 100
delivery_logs | Логи доставки | 1B
recommendations | Рекомендации | 100M
user_behaviors | Поведение пользователей | 1B

Схема (упрощенная):

```sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL, -- ссылка на внешний Users Service
    type VARCHAR(50) NOT NULL,
    channel VARCHAR(50) NOT NULL,
    subject VARCHAR(500),
    body TEXT,
    status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE templates (
    id UUID PRIMARY KEY,
    event_type VARCHAR(100) UNIQUE NOT NULL,
    subject_template TEXT NOT NULL,
    body_template TEXT NOT NULL,
    channel VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE delivery_logs (
    id UUID PRIMARY KEY,
    notification_id UUID REFERENCES notifications(id),
    timestamp TIMESTAMP DEFAULT NOW(),
    status VARCHAR(50) NOT NULL,
    error_message TEXT
);

CREATE TABLE user_behaviors (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    product_id UUID NOT NULL, -- ссылка на внешний Catalog Service
    action_type VARCHAR(50) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE recommendations (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    product_id UUID NOT NULL,
    score DECIMAL(5, 4) NOT NULL, -- 0.0000 - 1.0000
    generated_at TIMESTAMP DEFAULT NOW()
);
```

Что владеет:
- Все уведомления
- Шаблоны уведомлений
- История доставки
- Рекомендации
- Поведение пользователей для персонализации

Что НЕ владеет:
- Контент уведомлений (сгенерирован из шаблонов)

---

## Внешние ссылки между сервисами

### Ссылки по ID (Foreign Keys не используются)

Откуда | Куда | Ссылочное поле | Пояснение
--------|------|----------------|-----------
Orders DB | Users DB | user_id | UUID пользователя
Orders DB | Catalog DB | product_id | UUID товара
Catalog DB | Users DB | seller_id | UUID продавца
Notifications DB | Users DB | user_id | UUID пользователя
Notifications DB | Catalog DB | product_id | UUID товара

### Получение связанных данных

Для получения связанных данных используются:

1. Синхронные запросы (HTTP)
   - Orders -> Users: получить данные пользователя
   - Orders -> Catalog: получить детали товара

2. Кэширование
   - Часто используемые данные кэшируются в Redis

3. Дублирование данных
   - Некритичные данные дублируются в Orders DB (snapshot цены при заказе)

---

## Обеспечение консистентности

### Синхронные операции (транзакции)
- В рамках одного сервиса транзакции ACID
- При синхронных вызовах используется SAGA pattern для распределенных транзакций

### Асинхронные операции (Message Queue)
- Eventual consistency
- События гарантированно доставляются через RabbitMQ
- Dead Letter Queue для обработки сбоев

---

## Шардирование и масштабирование

### Варианты шардирования

База данных | Стратегия шардирования | Ключ шардирования
-------------|------------------------|-------------------
Users DB | User-based | user_id
Catalog DB | Product-based | product_id
Orders DB | User-based | user_id
Notifications DB | User-based | user_id

### Read Replicas

- Каждая БД имеет read replicas для чтения
- Write operations идут на master
- Read operations идут на replicas

---

## Резервное копирование

База данных | Частота бэкапа | Тип бэкапа | Retention
-------------|----------------|------------|----------
Users DB | Ежедневно | Full | 30 дней
Catalog DB | Ежедневно | Full | 30 дней
Orders DB | Ежедневно | Full + Incremental | 90 дней
Notifications DB | Еженедельно | Full | 7 дней

---

## Заключение

Четкое разделение баз данных обеспечивает:

- Изоляцию сбоев - падение одной БД не влияет на другие
- Независимое масштабирование - каждая БД масштабируется отдельно
- Технологическую свободу - разные сервисы могут использовать разные БД
- Четкие границы ответственности - каждый сервис владеет своими данными
- Независимую эволюцию - схема одной БД не блокирует изменения в другой

Отсутствие разделяемых баз данных - это фундаментальный принцип микросервисной архитектуры.
