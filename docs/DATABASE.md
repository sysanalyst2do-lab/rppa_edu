# Схема базы данных

Проект использует **Cloudflare D1** (SQLite) для хранения данных.

## База данных: `edu_rppa_db`

---

## Таблицы

### 1. users

Хранит информацию о пользователях.

**Структура:**

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | INTEGER | Первичный ключ (генерируется как `Date.now()`) |
| `name` | TEXT | Имя пользователя |
| `email` | TEXT | Email (уникальный) |
| `created_at` | TEXT | ISO дата создания |

**Индексы:**
- `UNIQUE(email)` - Email должен быть уникальным

**Пример записи:**
```sql
INSERT INTO users (id, name, email, created_at) 
VALUES (1234567890, 'Иван Иванов', 'ivan@example.com', '2024-01-15T10:30:00.000Z');
```

---

### 2. products

Хранит информацию о товарах.

**Структура:**

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | INTEGER | Первичный ключ (генерируется как `Date.now()`) |
| `name` | TEXT | Название товара |
| `description` | TEXT | Описание товара |
| `price_cents` | INTEGER | Цена в центах (неотрицательное целое) |
| `image_url` | TEXT | URL изображения (может быть NULL) |

**Пример записи:**
```sql
INSERT INTO products (id, name, description, price_cents, image_url) 
VALUES (1234567890, 'Товар', 'Описание товара', 9999, 'https://example.com/image.jpg');
```

---

### 3. orders

Хранит информацию о заказах.

**Структура:**

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | INTEGER | Первичный ключ (генерируется как `Date.now()`) |
| `user_id` | INTEGER | ID пользователя (внешний ключ на users.id) |
| `items_json` | TEXT | JSON строка с позициями заказа |
| `total_cents` | INTEGER | Итоговая сумма в центах |
| `created_at` | TEXT | ISO дата создания |

**Формат `items_json`:**
```json
{
  "1234567890": {
    "qty": 2,
    "price_cents": 9999,
    "line_total_cents": 19998,
    "name": "Название товара"
  },
  "1234567891": {
    "qty": 1,
    "price_cents": 4999,
    "line_total_cents": 4999,
    "name": "Другой товар"
  }
}
```

**Пример записи:**
```sql
INSERT INTO orders (id, user_id, items_json, total_cents, created_at) 
VALUES (
  1234567890, 
  1234567890, 
  '{"1234567890":{"qty":2,"price_cents":9999,"line_total_cents":19998,"name":"Товар"}}',
  19998,
  '2024-01-15T10:30:00.000Z'
);
```

---

### 4. sessions

Хранит активные сессии пользователей.

**Структура:**

| Поле | Тип | Описание |
|------|-----|----------|
| `session_id` | TEXT | Уникальный ID сессии (32 символа hex) |
| `email` | TEXT | Email пользователя |
| `expires_at` | INTEGER | Unix timestamp истечения сессии |
| `created_at` | INTEGER | Unix timestamp создания сессии |

**Особенности:**
- Сессия действует 7 дней (604800 секунд)
- `session_id` используется как значение cookie `sid`
- При выходе сессия удаляется из БД

**Пример записи:**
```sql
INSERT INTO sessions (session_id, email, expires_at, created_at) 
VALUES (
  'a1b2c3d4e5f6...',
  'user@example.com',
  1705320000, -- Unix timestamp
  1704715200
);
```

---

### 5. auth_codes

Хранит коды для входа (OTP).

**Структура:**

| Поле | Тип | Описание |
|------|-----|----------|
| `email` | TEXT | Email пользователя |
| `code_hash` | TEXT | SHA-256 хеш кода (64 символа hex) |
| `expires_at` | INTEGER | Unix timestamp истечения кода |
| `created_at` | INTEGER | Unix timestamp создания кода |

**Особенности:**
- Код действителен 10 минут (600 секунд)
- Код хранится как SHA-256 хеш (не в открытом виде)
- Код генерируется как 6-значное число (100000-999999)
- При проверке используется последний созданный код для email

**Пример записи:**
```sql
INSERT INTO auth_codes (email, code_hash, expires_at, created_at) 
VALUES (
  'user@example.com',
  'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', -- SHA-256 хеш
  1704715800, -- expires_at (now + 10 min)
  1704715200  -- created_at (now)
);
```

---

## SQL запросы для создания таблиц

```sql
-- Таблица пользователей
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL
);

-- Таблица товаров
CREATE TABLE IF NOT EXISTS products (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT NOT NULL,
  price_cents INTEGER NOT NULL CHECK(price_cents >= 0),
  image_url TEXT
);

-- Таблица заказов
CREATE TABLE IF NOT EXISTS orders (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  items_json TEXT NOT NULL,
  total_cents INTEGER NOT NULL CHECK(total_cents >= 0),
  created_at TEXT NOT NULL
);

-- Таблица сессий
CREATE TABLE IF NOT EXISTS sessions (
  session_id TEXT PRIMARY KEY,
  email TEXT NOT NULL,
  expires_at INTEGER NOT NULL,
  created_at INTEGER NOT NULL
);

-- Таблица кодов аутентификации
CREATE TABLE IF NOT EXISTS auth_codes (
  email TEXT NOT NULL,
  code_hash TEXT NOT NULL,
  expires_at INTEGER NOT NULL,
  created_at INTEGER NOT NULL
);
```

---

## Связи между таблицами

```
users (id)
  └── orders.user_id → users.id
  └── sessions.email → users.email
  └── auth_codes.email → users.email
```

**Примечание:** В SQLite нет внешних ключей по умолчанию, связи логические.

---

## Индексы (рекомендуемые)

Для оптимизации запросов можно добавить индексы:

```sql
-- Индекс для поиска пользователя по email
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Индекс для поиска заказов пользователя
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);

-- Индекс для поиска сессии
CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON sessions(session_id);

-- Индекс для поиска кодов по email
CREATE INDEX IF NOT EXISTS idx_auth_codes_email ON auth_codes(email);
```

---

## Особенности реализации

1. **ID генерация**: Используется `Date.now()` для генерации ID (timestamp в миллисекундах)
2. **Даты**: 
   - ISO формат для `created_at` в users, products, orders
   - Unix timestamp для sessions и auth_codes
3. **Хеширование**: SHA-256 для кодов аутентификации
4. **JSON хранение**: `items_json` хранит структурированные данные заказа
5. **Валидация**: Проверка на уровне приложения (не на уровне БД)

---

## Миграции

В текущей версии миграции выполняются вручную через Cloudflare Dashboard или Wrangler CLI.

Пример команды для создания таблиц через Wrangler:

```bash
wrangler d1 execute edu_rppa_db --file=./schema.sql
```

