# Система аутентификации

## Обзор

Проект использует **аутентификацию через одноразовый email-код (OTP)** без паролей.

---

## Процесс аутентификации

### Шаг 1: Запрос кода

**Эндпоинт:** `POST /api/auth/request-code`

**Процесс:**
1. Пользователь вводит email (и опционально имя)
2. Если пользователя нет в БД и указано имя → создается новый пользователь
3. Генерируется 6-значный код (100000–999999)
4. Код хешируется через SHA-256 и сохраняется в БД
5. Код отправляется на email (или возвращается в ответе в демо-режиме)
6. Код действителен 10 минут

**Код (Python):**
```python
import hashlib
import secrets

def _gen_code() -> str:
    return str(secrets.randbelow(900000) + 100000)

def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()
```

---

### Шаг 2: Верификация кода

**Эндпоинт:** `POST /api/auth/verify-code`

**Процесс:**
1. Пользователь вводит код
2. Код хешируется и ищется в БД
3. Проверяется срок действия кода
4. Если код валиден → создается сессия
5. Устанавливаются cookies: `sid` и `u`
6. Пользователь перенаправляется на главную страницу

**Создание сессии (Python):**
```python
import secrets
import time

sid = secrets.token_hex(32)           # 64-символьная hex-строка
exp = int(time.time()) + 7 * 24 * 3600  # 7 дней

await conn.execute(
    "INSERT INTO sessions (session_id, email, expires_at, created_at) "
    "VALUES ($1, $2, $3, $4)",
    sid, email, exp, int(time.time()),
)
```

---

## Cookies

### sid (Session ID)

**Назначение:** Идентификатор сессии для проверки аутентификации

**Параметры:**
- `HttpOnly: true` — Недоступен из JavaScript
- `SameSite: Lax` — Защита от CSRF
- `Path: /` — Действует для всего сайта
- `Max-Age: 604800` — 7 дней

**Использование:**
- Проверяется в middleware для защищенных маршрутов
- Хранится в таблице `sessions` в БД

---

### u (User Info)

**Назначение:** Информация о пользователе для отображения в UI

**Содержимое:**
```json
{
  "email": "user@example.com",
  "name": "Имя пользователя"
}
```

**Параметры:**
- `HttpOnly: false` — Доступен из JavaScript
- `SameSite: Lax` — Защита от CSRF
- `Path: /` — Действует для всего сайта
- `Max-Age: 604800` — 7 дней

**Использование:**
- Отображается в topbar как «Signed in: Имя»
- Используется в форме заказа для предзаполнения данных

---

## Middleware защита

**Файл:** `backend/app.py` → класс `AuthMiddleware`

### Открытые маршруты

Следующие маршруты доступны без аутентификации:

- `/` — Главная страница
- `/index.html` — Главная страница
- `/login` — Страница входа
- `/login.html` — Страница входа
- `/api/auth/request-code` — Запрос кода
- `/api/auth/verify-code` — Верификация кода
- `/api/auth/logout` — Выход
- `/assets/*` — Статические файлы
- `/favicon*` — Иконки
- `/robots.txt` — Файл для поисковых роботов
- `/site.webmanifest` — Манифест PWA

### Защищенные маршруты

Все остальные маршруты требуют валидной сессии:

- `/users/*` — Управление пользователями
- `/products/*` — Управление товарами
- `/orders/*` — Создание заказов
- `/api/users` — API пользователей
- `/api/products` — API товаров
- `/api/orders` — API заказов

### Логика проверки (Python)

```python
# 1. Проверка cookie sid
sid = request.cookies.get("sid")
if not sid:
    return _deny(request)

# 2. Проверка сессии в БД
async with pool.acquire() as conn:
    row = await conn.fetchrow(
        "SELECT email, expires_at FROM sessions WHERE session_id = $1", sid
    )

# 3. Проверка срока действия
if not row or row["expires_at"] < int(time.time()):
    return _deny(request)

# 4. Разрешить доступ
return await call_next(request)
```

**Поведение `_deny()`:**
- Для API-запросов (`/api/*`) — возвращает `401 JSON {"error": "unauthorized"}`
- Для HTML-страниц — редирект на `/login.html?next=...`

---

## Выход из системы

**Эндпоинт:** `POST /api/auth/logout`

**Процесс:**
1. Удаляется сессия из БД
2. Очищаются cookies `sid` и `u`
3. Пользователь перенаправляется на страницу входа

**Код (Python):**
```python
sid = request.cookies.get("sid")
if sid:
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM sessions WHERE session_id = $1", sid)

resp = JSONResponse({"ok": True})
resp.delete_cookie("sid", path="/")
resp.delete_cookie("u", path="/")
```

---

## Безопасность

### Защита от атак

1. **Brute Force:**
   - Код действителен только 10 минут
   - 6-значный код даёт 900000 вариантов

2. **CSRF:**
   - `SameSite=Lax` защищает от межсайтовых запросов
   - Cookie `sid` с `HttpOnly` недоступен из JavaScript

3. **XSS:**
   - Cookie `sid` недоступен из JavaScript (`HttpOnly`)
   - Данные экранируются при выводе (`esc()` функция)

4. **SQL Injection:**
   - Все запросы параметризованные (`$1`, `$2`, ...)
   - asyncpg не допускает конкатенацию строк в запросах

5. **Session Hijacking:**
   - Сессия имеет срок действия (7 дней)
   - `session_id` генерируется криптографически безопасным `secrets.token_hex(32)`

### Рекомендации по улучшению

1. **Rate Limiting:** Ограничить количество запросов кода с одного IP
2. **IP Tracking:** Сохранять IP адрес при создании сессии
3. **Secure cookies:** Добавить флаг `Secure` при работе через HTTPS
4. **Session Rotation:** Обновлять `session_id` при критических операциях

---

## Демо-режим

Для разработки и тестирования включён демо-режим:

**Переменная окружения:** `DEV_DELIVERY=true`

**Поведение:**
- Email не отправляется реально
- Код выводится в лог Python (`logging.info`)
- Код возвращается в ответе API (`demo_code`)

**Пример ответа:**
```json
{
  "ok": true,
  "demo_code": "123456"
}
```

---

## Примеры использования

### Frontend: Запрос кода

```javascript
const res = await apiRequest('auth-send', 'POST', '/api/auth/request-code', {
  email: 'user@example.com',
  name: 'Иван Иванов'
});

if (res.demo_code) {
  codeInput.value = res.demo_code;
}
```

### Frontend: Верификация кода

```javascript
const res = await apiRequest('auth-verify', 'POST', '/api/auth/verify-code', {
  email: 'user@example.com',
  code: '123456'
});

if (res.ok) {
  toast('Успешный вход', 'ok');
  setTimeout(() => location.href = '/', 400);
}
```

### Backend: Проверка сессии (Python)

```python
async def _get_current_user(request: Request) -> dict | None:
    sid = request.cookies.get("sid")
    if not sid:
        return None

    pool = get_pool()
    async with pool.acquire() as conn:
        session = await conn.fetchrow(
            "SELECT email, expires_at FROM sessions WHERE session_id = $1", sid
        )

    if not session or session["expires_at"] < int(time.time()):
        return None

    async with pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT id, name FROM users WHERE email = $1", session["email"]
        )
    if not user:
        return None

    return {"user_id": user["id"], "email": session["email"], "name": user["name"]}
```

---

## Диаграмма потока

```
Пользователь
    │
    ├─→ [Ввод email] ──→ POST /api/auth/request-code
    │                        │
    │                        ├─→ Генерация кода (secrets.randbelow)
    │                        ├─→ Хеширование (hashlib.sha256)
    │                        ├─→ Сохранение в PostgreSQL
    │                        └─→ Отправка email / возврат demo_code
    │
    ├─→ [Ввод кода] ────→ POST /api/auth/verify-code
    │                        │
    │                        ├─→ Хеширование кода
    │                        ├─→ Поиск в БД
    │                        ├─→ Проверка срока действия
    │                        ├─→ Создание сессии (secrets.token_hex)
    │                        └─→ Установка cookies (sid, u)
    │
    └─→ [Доступ к защищенным страницам]
                              │
                              ├─→ AuthMiddleware проверяет cookie sid
                              ├─→ Проверка сессии в PostgreSQL
                              ├─→ Проверка срока действия
                              └─→ Доступ разрешен или редирект на /login
```
