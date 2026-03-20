# Схема базы данных

Проект использует **PostgreSQL 16** для хранения данных.

## База данных: `edu_rppa`

---

## Таблицы

### 1. users

Хранит информацию о пользователях.

**Структура:**

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | BIGSERIAL | Первичный ключ (автоинкремент) |
| `name` | TEXT | Имя пользователя |
| `email` | TEXT | Email (уникальный) |
| `created_at` | TIMESTAMPTZ | Дата создания (DEFAULT NOW()) |

**Ограничения:**
- `PRIMARY KEY (id)` — уникальный автоинкрементный идентификатор
- `UNIQUE (email)` — email должен быть уникальным
- `NOT NULL` на name, email, created_at

**Пример записи:**
```sql
INSERT INTO users (name, email) VALUES ('Иван Иванов', 'ivan@example.com');
-- id и created_at заполняются автоматически
```

---

### 2. products

Хранит информацию о товарах.

**Структура:**

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | BIGSERIAL | Первичный ключ (автоинкремент) |
| `name` | TEXT | Название товара |
| `description` | TEXT | Описание товара |
| `price_cents` | INTEGER | Цена в центах (неотрицательное целое) |
| `image_url` | TEXT | URL изображения (может быть NULL) |

**Ограничения:**
- `CHECK (price_cents >= 0)` — цена не может быть отрицательной

**Пример записи:**
```sql
INSERT INTO products (name, description, price_cents, image_url)
VALUES ('Товар', 'Описание товара', 9999, 'https://example.com/image.jpg');
```

---

### 3. orders

Хранит информацию о заказах.

**Структура:**

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | BIGSERIAL | Первичный ключ (автоинкремент) |
| `user_id` | BIGINT | ID пользователя (внешний ключ на users.id) |
| `items_json` | JSONB | Позиции заказа в формате JSON |
| `total_cents` | INTEGER | Итоговая сумма в центах |
| `created_at` | TIMESTAMPTZ | Дата создания (DEFAULT NOW()) |

**Ограничения:**
- `REFERENCES users(id) ON DELETE CASCADE` — при удалении пользователя удаляются его заказы

**Формат `items_json` (JSONB):**
```json
{
  "1": {
    "qty": 2,
    "price_cents": 9999,
    "line_total_cents": 19998,
    "name": "Название товара"
  },
  "2": {
    "qty": 1,
    "price_cents": 4999,
    "line_total_cents": 4999,
    "name": "Другой товар"
  }
}
```

**Пример записи:**
```sql
INSERT INTO orders (user_id, items_json, total_cents)
VALUES (
  1,
  '{"1":{"qty":2,"price_cents":9999,"line_total_cents":19998,"name":"Товар"}}'::jsonb,
  19998
);
```

---

### 4. sessions

Хранит активные сессии пользователей.

**Структура:**

| Поле | Тип | Описание |
|------|-----|----------|
| `session_id` | TEXT | Уникальный ID сессии (64 символа hex) |
| `email` | TEXT | Email пользователя |
| `expires_at` | BIGINT | Unix timestamp истечения сессии |
| `created_at` | BIGINT | Unix timestamp создания сессии |

**Особенности:**
- Сессия действует 7 дней (604800 секунд)
- `session_id` используется как значение cookie `sid`
- При выходе сессия удаляется из БД

**Пример записи:**
```sql
INSERT INTO sessions (session_id, email, expires_at, created_at)
VALUES (
  'a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2',
  'user@example.com',
  1705320000,
  1704715200
);
```

---

### 5. auth_codes

Хранит коды для входа (OTP).

**Структура:**

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | BIGSERIAL | Первичный ключ (автоинкремент) |
| `email` | TEXT | Email пользователя |
| `code_hash` | TEXT | SHA-256 хеш кода (64 символа hex) |
| `expires_at` | BIGINT | Unix timestamp истечения кода |
| `created_at` | BIGINT | Unix timestamp создания кода |

**Особенности:**
- Код действителен 10 минут (600 секунд)
- Код хранится как SHA-256 хеш (не в открытом виде)
- Код генерируется как 6-значное число (100000–999999)
- При проверке используется последний созданный код для email

---

## SQL-схема (schema.sql)

```sql
CREATE TABLE IF NOT EXISTS users (
    id          BIGSERIAL    PRIMARY KEY,
    name        TEXT         NOT NULL,
    email       TEXT         UNIQUE NOT NULL,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS products (
    id          BIGSERIAL    PRIMARY KEY,
    name        TEXT         NOT NULL,
    description TEXT         NOT NULL DEFAULT '',
    price_cents INTEGER      NOT NULL CHECK (price_cents >= 0),
    image_url   TEXT
);

CREATE TABLE IF NOT EXISTS orders (
    id          BIGSERIAL    PRIMARY KEY,
    user_id     BIGINT       NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    items_json  JSONB        NOT NULL,
    total_cents INTEGER      NOT NULL,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id  TEXT   PRIMARY KEY,
    email       TEXT   NOT NULL,
    expires_at  BIGINT NOT NULL,
    created_at  BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS auth_codes (
    id          BIGSERIAL PRIMARY KEY,
    email       TEXT      NOT NULL,
    code_hash   TEXT      NOT NULL,
    expires_at  BIGINT    NOT NULL,
    created_at  BIGINT    NOT NULL
);
```

Таблицы создаются автоматически при старте сервера (`backend/db.py` выполняет `schema.sql` с `IF NOT EXISTS`).

---

## Связи между таблицами

```
users (id)
  └── orders.user_id → users.id (ON DELETE CASCADE)
  └── sessions.email → users.email (логическая связь)
  └── auth_codes.email → users.email (логическая связь)
```

В PostgreSQL внешний ключ `orders.user_id → users.id` задан явно с каскадным удалением.

---

## Особенности реализации

1. **ID генерация**: `BIGSERIAL` — автоинкремент PostgreSQL
2. **Даты**:
   - `TIMESTAMPTZ` с `DEFAULT NOW()` для `created_at` в users, products, orders
   - Unix timestamp (BIGINT) для sessions и auth_codes
3. **Хеширование**: SHA-256 для кодов аутентификации (`hashlib.sha256`)
4. **JSON хранение**: `JSONB` для `items_json` в orders (поддержка индексирования и запросов)
5. **Валидация**: `CHECK` ограничения на уровне БД + проверки в Python-коде

---

## Полезные запросы

```sql
-- Все пользователи
SELECT * FROM users ORDER BY id DESC;

-- Все товары
SELECT * FROM products ORDER BY id DESC;

-- Заказы с именем покупателя
SELECT o.id, u.name, u.email, o.total_cents, o.created_at
FROM orders o
JOIN users u ON u.id = o.user_id
ORDER BY o.created_at DESC;

-- Активные сессии
SELECT session_id, email, to_timestamp(expires_at) AS expires
FROM sessions
WHERE expires_at > extract(epoch FROM now());

-- Очистить все данные
TRUNCATE auth_codes, sessions, orders, products, users RESTART IDENTITY CASCADE;
```
