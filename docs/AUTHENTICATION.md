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
3. Генерируется 6-значный код (100000-999999)
4. Код хешируется через SHA-256 и сохраняется в БД
5. Код отправляется на email (или возвращается в ответе в демо-режиме)
6. Код действителен 10 минут

**Код:**
```javascript
// Генерация кода
function genCode() {
  return String(Math.floor(100000 + Math.random() * 900000));
}

// Хеширование
async function sha256(s) {
  const b = new TextEncoder().encode(s);
  const d = await crypto.subtle.digest('SHA-256', b);
  return [...new Uint8Array(d)]
    .map(x => x.toString(16).padStart(2, '0'))
    .join('');
}
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

**Создание сессии:**
```javascript
const sid = cryptoRandom(32); // 32 байта в hex
const exp = now + 7 * 24 * 60 * 60; // 7 дней

await db.prepare(
  "INSERT INTO sessions(session_id, email, expires_at, created_at) VALUES(?,?,?,?)"
).bind(sid, email, exp, now).run();
```

---

## Cookies

### sid (Session ID)

**Назначение:** Идентификатор сессии для проверки аутентификации

**Параметры:**
- `HttpOnly: true` - Недоступен из JavaScript
- `Secure: true` - Только через HTTPS
- `SameSite: Lax` - Защита от CSRF
- `Path: /` - Действует для всего сайта
- `Max-Age: 604800` - 7 дней

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
- `HttpOnly: false` - Доступен из JavaScript
- `Secure: true` - Только через HTTPS
- `SameSite: Lax` - Защита от CSRF
- `Path: /` - Действует для всего сайта
- `Max-Age: 604800` - 7 дней

**Использование:**
- Отображается в topbar как "Signed in: Имя"
- Используется в форме заказа для предзаполнения данных

**Пример чтения:**
```javascript
function getUserFromCookie() {
  try {
    const c = parseCookies();
    if (!c.u) return null;
    return JSON.parse(c.u);
  } catch {
    return null;
  }
}
```

---

## Middleware защита

**Файл:** `functions/_middleware.js`

### Открытые маршруты

Следующие маршруты доступны без аутентификации:

- `/` - Главная страница
- `/index.html` - Главная страница
- `/login` - Страница входа
- `/login.html` - Страница входа
- `/api/auth/request-code` - Запрос кода
- `/api/auth/verify-code` - Верификация кода
- `/api/auth/logout` - Выход
- `/assets/*` - Статические файлы
- `/favicon*` - Иконки
- `/robots.txt` - Файл для поисковых роботов

### Защищенные маршруты

Все остальные маршруты требуют валидной сессии:

- `/users/*` - Управление пользователями
- `/products/*` - Управление товарами
- `/orders/*` - Создание заказов
- `/api/users` - API пользователей
- `/api/products` - API товаров
- `/api/orders` - API заказов

### Логика проверки

```javascript
// 1. Проверка cookie sid
const cookies = parseCookie(request.headers.get('cookie') || '');
const sid = cookies['sid'];
if (!sid) return redirectToLogin(url);

// 2. Проверка сессии в БД
const session = await db
  .prepare('SELECT email, expires_at FROM sessions WHERE session_id = ?')
  .bind(sid)
  .first();

// 3. Проверка срока действия
const now = Math.floor(Date.now() / 1000);
if (!session || session.expires_at < now) {
  return redirectToLogin(url);
}

// 4. Разрешить доступ
return await ctx.next();
```

---

## Выход из системы

**Эндпоинт:** `POST /api/auth/logout`

**Процесс:**
1. Удаляется сессия из БД
2. Очищаются cookies `sid` и `u` (устанавливаются в `deleted` с `Max-Age=0`)
3. Пользователь перенаправляется на страницу входа

**Код:**
```javascript
// Удаление сессии из БД
if (sid) {
  await db.prepare("DELETE FROM sessions WHERE session_id=?").bind(sid).run();
}

// Очистка cookies
headers.append('Set-Cookie', 'sid=deleted; Path=/; Max-Age=0; HttpOnly; SameSite=Lax');
headers.append('Set-Cookie', 'u=deleted; Path=/; Max-Age=0; SameSite=Lax');
```

---

## Безопасность

### Защита от атак

1. **Brute Force:**
   - Код действителен только 10 минут
   - После использования код не удаляется (можно добавить флаг `used`)

2. **CSRF:**
   - `SameSite=Lax` защищает от межсайтовых запросов
   - Cookie `sid` с `HttpOnly` недоступен из JavaScript

3. **XSS:**
   - Cookie `sid` недоступен из JavaScript (`HttpOnly`)
   - Данные экранируются при выводе (`esc()` функция)

4. **Session Hijacking:**
   - Cookie `sid` передается только через HTTPS (`Secure`)
   - Сессия имеет срок действия (7 дней)

### Рекомендации по улучшению

1. **Rate Limiting:** Ограничить количество запросов кода с одного IP
2. **IP Tracking:** Сохранять IP адрес при создании сессии
3. **Device Fingerprinting:** Отслеживать устройства пользователя
4. **2FA:** Добавить двухфакторную аутентификацию
5. **Session Rotation:** Обновлять `session_id` при критических операциях

---

## Демо-режим

Для разработки и тестирования можно включить демо-режим:

**Переменная окружения:** `DEV_DELIVERY=true`

**Поведение:**
- Email не отправляется реально
- Код выводится в консоль (Cloudflare Logs)
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
  name: 'Иван Иванов' // опционально
});

if (res.demo_code) {
  codeInput.value = res.demo_code; // Автозаполнение в демо-режиме
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

### Backend: Проверка сессии

```javascript
async function getCurrentUser(ctx) {
  const cookies = parseCookie(ctx.request.headers.get('cookie') || '');
  const sid = cookies['sid'];
  if (!sid) return null;

  const session = await ctx.env.edu_rppa_db
    .prepare('SELECT email, expires_at FROM sessions WHERE session_id = ?')
    .bind(sid)
    .first();

  const now = Math.floor(Date.now() / 1000);
  if (!session || session.expires_at < now) return null;

  const user = await ctx.env.edu_rppa_db
    .prepare('SELECT id, name FROM users WHERE email = ? LIMIT 1')
    .bind(session.email)
    .first();

  return user ? { user_id: user.id, email: session.email, name: user.name } : null;
}
```

---

## Диаграмма потока

```
Пользователь
    │
    ├─→ [Ввод email] ──→ POST /api/auth/request-code
    │                        │
    │                        ├─→ Генерация кода
    │                        ├─→ Хеширование (SHA-256)
    │                        ├─→ Сохранение в БД
    │                        └─→ Отправка email / возврат demo_code
    │
    ├─→ [Ввод кода] ────→ POST /api/auth/verify-code
    │                        │
    │                        ├─→ Хеширование кода
    │                        ├─→ Поиск в БД
    │                        ├─→ Проверка срока действия
    │                        ├─→ Создание сессии
    │                        └─→ Установка cookies (sid, u)
    │
    └─→ [Доступ к защищенным страницам]
                              │
                              ├─→ Middleware проверяет cookie sid
                              ├─→ Проверка сессии в БД
                              ├─→ Проверка срока действия
                              └─→ Разрешение доступа или редирект на /login
```

