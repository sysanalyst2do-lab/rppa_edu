# Frontend документация

## Обзор

Frontend приложения построен на **Vanilla JavaScript** без использования фреймворков. Используется модульный подход с общими функциями в `app.js`.

---

## Структура файлов

```
public/
├── assets/
│   ├── app.css          # Основные стили
│   ├── app.js           # Общие JavaScript функции
│   └── *.png            # Иконки и изображения
├── index.html           # Главная страница
├── login.html           # Страница входа
├── users/
│   └── index.html       # Управление пользователями
├── products/
│   └── index.html       # Управление товарами
└── orders/
    └── index.html       # Создание заказов
```

---

## Общие компоненты

### app.js

Содержит общие функции, используемые на всех страницах.

#### Функции загрузки и уведомлений

```javascript
// Индикатор загрузки
function startLoading() { ... }
function stopLoading() { ... }

// Уведомления
function toast(msg, kind='ok', timeout=2600) { ... }
```

#### HTTP запросы

```javascript
async function apiRequest(where, method, url, body) {
  // Обертка для fetch с логированием и обработкой ошибок
  // Параметры:
  //   where - идентификатор для статуса (например, 'u-list')
  //   method - HTTP метод ('GET', 'POST', 'PUT', 'DELETE')
  //   url - URL эндпоинта
  //   body - тело запроса (объект, будет сериализован в JSON)
}
```

**Особенности:**
- Автоматическое отображение индикатора загрузки
- Логирование времени выполнения
- Обновление статуса запроса в UI
- Обработка ошибок с показом toast

#### Утилиты

```javascript
// Экранирование HTML
function esc(s) { ... }

// Установка статуса запроса
function setStatus(where, code, ms) { ... }

// Текст ошибки
function errText(err) { ... }
```

#### Роутинг

```javascript
// Hash-based роутинг для подстраниц
function initHashRouter(navSelector, defaultRoute='/list', onChange) {
  // Используется на страницах users и products
  // Параметры:
  //   navSelector - селектор навигации (например, '#nav')
  //   defaultRoute - маршрут по умолчанию
  //   onChange - callback при смене маршрута
}
```

**Пример использования:**
```javascript
initHashRouter('#nav', '/list', (route) => {
  if (route === '/list') loadUsers();
});
```

#### Выход из системы

```javascript
function bindLogout(selector) {
  // Привязывает обработчик выхода к кнопке
  // Параметры:
  //   selector - селектор кнопки (например, '#btn-logout')
}
```

---

## Страницы

### index.html (Главная)

**Назначение:** Описание проекта и навигация по разделам

**Особенности:**
- Отображает информацию о проекте
- Ссылки на разделы: Users, Products, Orders
- Схема архитектуры приложения
- Кнопка выхода

**JavaScript:**
```javascript
bindLogout('#btn-logout');
```

---

### login.html (Вход)

**Назначение:** Аутентификация пользователя

**Функциональность:**
- Форма запроса кода (email + опционально имя)
- Форма верификации кода
- Отображение ответов API
- Автозаполнение кода в демо-режиме

**JavaScript:**
```javascript
// Запрос кода
document.getElementById('form-send').addEventListener('submit', async (e) => {
  e.preventDefault();
  const res = await apiRequest('auth-send', 'POST', '/api/auth/request-code', {
    email: emailEl.value.trim(),
    name: nameEl.value.trim()
  });
  if (res.demo_code) {
    codeEl.value = res.demo_code; // Автозаполнение
  }
});

// Верификация кода
document.getElementById('form-verify').addEventListener('submit', async (e) => {
  e.preventDefault();
  const res = await apiRequest('auth-verify', 'POST', '/api/auth/verify-code', {
    email: emailEl.value.trim(),
    code: codeEl.value.trim()
  });
  if (res.ok) {
    toast('Успешный вход', 'ok');
    setTimeout(() => location.href = next, 400);
  }
});
```

---

### users/index.html (Пользователи)

**Назначение:** CRUD операции с пользователями

**Разделы (hash routing):**
- `#/list` - Список пользователей
- `#/get` - Получить по ID
- `#/create` - Создать пользователя
- `#/update` - Обновить пользователя
- `#/delete` - Удалить пользователя

**Функциональность:**
- Отображение списка пользователей в таблице
- Фильтрация по имени/email
- Формы для CRUD операций
- Отображение статуса запросов

**JavaScript:**
```javascript
// Инициализация роутера
initHashRouter('#nav', '/list', (route) => {
  if (route === '/list') loadUsers();
});

// Загрузка списка
async function loadUsers() {
  const data = await apiRequest('u-list', 'GET', '/api/users');
  cachedUsers = data.users || [];
  renderUsers(cachedUsers);
}

// Фильтрация
function applyUsersFilter() {
  const q = uFilter.value.trim().toLowerCase();
  if (!q) return renderUsers(cachedUsers);
  renderUsers(cachedUsers.filter(u =>
    String(u.name || '').toLowerCase().includes(q) ||
    String(u.email || '').toLowerCase().includes(q)
  ));
}
```

---

### products/index.html (Товары)

**Назначение:** CRUD операции с товарами

**Разделы (hash routing):**
- `#/list` - Список товаров
- `#/get` - Получить по ID
- `#/create` - Создать товар
- `#/update` - Обновить товар
- `#/delete` - Удалить товар

**Функциональность:**
- Отображение списка товаров в таблице
- Фильтрация по названию/описанию
- Формы для CRUD операций
- Отображение цен в формате денег
- Ссылки на изображения товаров

**JavaScript:**
```javascript
// Аналогично users/index.html
// Отличия:
// - Работа с products вместо users
// - Форматирование цен: moneyCents(price_cents)
// - Отображение image_url
```

---

### orders/index.html (Заказы)

**Назначение:** Создание заказов с корзиной покупок

**Функциональность:**
- Загрузка списка товаров
- Добавление товаров в корзину (кнопки +/-)
- Ручной ввод количества
- Фильтрация товаров
- Отображение итоговой суммы и количества
- Формирование JSON payload для API
- Отображение cookies
- Создание заказа
- Отображение квитанции после создания

**JavaScript:**

```javascript
// Состояние
let allProducts = [];
let cart = {}; // { product_id: qty }

// Загрузка товаров
async function loadProducts() {
  const data = await apiRequest('orders', 'GET', '/api/products');
  allProducts = data.products || [];
  renderProducts();
  renderCart();
}

// Рендеринг товаров
function renderProducts() {
  const q = filterI.value.trim().toLowerCase();
  const rowsData = q ? allProducts.filter(p =>
    String(p.name || '').toLowerCase().includes(q) ||
    String(p.description || '').toLowerCase().includes(q)
  ) : allProducts;

  rows.innerHTML = rowsData.map(p => {
    const qty = cart[p.id] || 0;
    return `
      <div class="row-item">
        <img src="${esc(p.image_url)}" alt="">
        <div class="name">${esc(p.name)}</div>
        <div class="desc">${esc(p.description || '')}</div>
        <div class="price">${fmtMoney(p.price_cents)}</div>
        <div class="qty">
          <button data-act="dec" data-id="${p.id}">-</button>
          <input data-id="${p.id}" value="${qty}"/>
          <button data-act="inc" data-id="${p.id}">+</button>
        </div>
      </div>
    `;
  }).join('');
}

// Расчет итогов
function calcTotalsAndPayload() {
  const items = Object.entries(cart)
    .map(([pid, qty]) => ({ product_id: Number(pid), qty: Number(qty) }))
    .filter(x => x.qty > 0);

  let total_cents = 0, count = 0;
  for (const {product_id, qty} of items) {
    const p = allProducts.find(x => x.id === product_id);
    if (!p) continue;
    total_cents += Number(p.price_cents || 0) * qty;
    count += qty;
  }

  const user = getUserFromCookie();
  const payload = {
    user: user || null,
    items,
    total_cents,
    total_formatted: fmtMoney(total_cents, false)
  };

  return { items, total_cents, count, payload };
}

// Создание заказа
async function createOrder() {
  const { items, payload } = calcTotalsAndPayload();
  if (items.length === 0) return toast('Корзина пуста', 'err');
  
  try {
    const res = await apiRequest('orders', 'POST', '/api/orders', payload);
    toast('Заказ создан: #' + res.order.id, 'ok');
    cart = {};
    renderProducts();
    renderCart();
    showReceipt(res.order);
  } catch (err) {
    toast(err.message || 'Ошибка создания заказа', 'err');
  }
}
```

---

## Стили (app.css)

### Цветовая схема

```css
:root {
  --bg: #0b0f17;           /* Фон */
  --panel: #121826;        /* Панели */
  --text: #e6e9ef;         /* Текст */
  --muted: #9aa3b2;        /* Приглушенный текст */
  --ok: #1fd6a8;           /* Успех */
  --err: #ff6b6b;          /* Ошибка */
  --grad1: #7c4dff;        /* Градиент 1 */
  --grad2: #00b4ff;        /* Градиент 2 */
}
```

### Компоненты

- **Topbar** - Верхняя панель навигации (sticky)
- **Sidebar** - Боковая панель для навигации по разделам
- **Card** - Карточка контента
- **Form** - Форма с полями
- **Table** - Таблица данных
- **Button** - Кнопки (primary, secondary, danger)
- **Badge** - Бейджи для статусов
- **Toast** - Уведомления
- **Loader** - Индикатор загрузки

### Адаптивность

- Grid layout для адаптации под разные экраны
- Медиа-запросы для мобильных устройств
- Гибкие размеры шрифтов и отступов

---

## Работа с Cookies

### Чтение cookies

```javascript
function parseCookies() {
  return (document.cookie || '').split(';').reduce((acc, p) => {
    const i = p.indexOf('=');
    if (i > 0) acc[p.slice(0, i).trim()] = decodeURIComponent(p.slice(i + 1));
    return acc;
  }, {});
}

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

### Отображение пользователя

В `app.js` есть автоматическое отображение пользователя в topbar:

```javascript
(function showUser() {
  try {
    const cookies = document.cookie.split(';').reduce((acc, p) => {
      const i = p.indexOf('=');
      if (i > 0) acc[p.slice(0, i).trim()] = decodeURIComponent(p.slice(i + 1));
      return acc;
    }, {});
    if (!cookies.u) return;
    const u = JSON.parse(cookies.u);
    const bar = document.querySelector('.topbar');
    if (!bar) return;
    const span = document.createElement('span');
    span.className = 'badge';
    span.textContent = `Signed in: ${u.name || u.email}`;
    bar.insertBefore(span, bar.querySelector('.spacer'));
  } catch {}
})();
```

---

## Форматирование данных

### Деньги

```javascript
function fmtMoney(cents, withSymbol = true) {
  const v = (Number(cents || 0) / 100).toFixed(2);
  return withSymbol ? v + ' $' : v;
}
```

### Даты

Используется стандартный `Date` API:

```javascript
new Date(order.created_at).toLocaleString();
```

---

## Обработка ошибок

Все ошибки обрабатываются через `apiRequest()`:

```javascript
try {
  const data = await apiRequest('u-list', 'GET', '/api/users');
  // Обработка успешного ответа
} catch (err) {
  toast(err.message || 'Ошибка', 'err');
  // Дополнительная обработка ошибки
}
```

---

## Производительность

### Оптимизации

1. **Кэширование данных** - списки пользователей/товаров кэшируются в памяти
2. **Ленивая загрузка** - данные загружаются только при необходимости
3. **Debouncing фильтров** - можно добавить для оптимизации поиска
4. **Минификация** - рекомендуется для production

### Рекомендации

- Использовать `localStorage` для сохранения корзины (не реализовано)
- Добавить виртуализацию для больших списков
- Использовать Service Worker для кэширования статики

