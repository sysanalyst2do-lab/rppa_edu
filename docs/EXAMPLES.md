# Примеры использования

## Быстрый старт

### 1. Вход в систему

```javascript
// Шаг 1: Запрос кода
const requestRes = await fetch('/api/auth/request-code', {
  method: 'POST',
  headers: { 'content-type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    name: 'Иван Иванов' // опционально
  })
});
const requestData = await requestRes.json();
console.log('Код:', requestData.demo_code); // в демо-режиме

// Шаг 2: Верификация кода
const verifyRes = await fetch('/api/auth/verify-code', {
  method: 'POST',
  headers: { 'content-type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    code: '123456'
  })
});
const verifyData = await verifyRes.json();
if (verifyData.ok) {
  console.log('Вход выполнен!');
  // Cookies установлены автоматически
}
```

---

## Работа с пользователями

### Получить список пользователей

```javascript
const res = await fetch('/api/users');
const data = await res.json();
console.log('Пользователи:', data.users);
```

### Создать пользователя

```javascript
const res = await fetch('/api/users', {
  method: 'POST',
  headers: { 'content-type': 'application/json' },
  body: JSON.stringify({
    name: 'Иван Иванов',
    email: 'ivan@example.com'
  })
});
const data = await res.json();
console.log('Создан пользователь с ID:', data.id);
```

### Обновить пользователя

```javascript
const res = await fetch('/api/users', {
  method: 'PUT',
  headers: { 'content-type': 'application/json' },
  body: JSON.stringify({
    id: 1234567890,
    name: 'Новое имя',
    email: 'new@example.com'
  })
});
const data = await res.json();
if (data.ok) {
  console.log('Пользователь обновлен');
}
```

### Удалить пользователя

```javascript
const res = await fetch('/api/users?id=1234567890', {
  method: 'DELETE'
});
const data = await res.json();
if (data.ok) {
  console.log('Пользователь удален');
}
```

---

## Работа с товарами

### Получить список товаров

```javascript
const res = await fetch('/api/products');
const data = await res.json();
console.log('Товары:', data.products);
```

### Создать товар

```javascript
const res = await fetch('/api/products', {
  method: 'POST',
  headers: { 'content-type': 'application/json' },
  body: JSON.stringify({
    name: 'Название товара',
    description: 'Описание товара',
    price_cents: 9999, // 99.99 $
    image_url: 'https://example.com/image.jpg' // опционально
  })
});
const data = await res.json();
console.log('Создан товар с ID:', data.id);
```

### Получить товар по ID

```javascript
const res = await fetch('/api/products?id=1234567890');
const data = await res.json();
console.log('Товар:', data.product);
```

---

## Создание заказа

### Формирование корзины

```javascript
// Получить список товаров
const productsRes = await fetch('/api/products');
const productsData = await productsRes.json();
const products = productsData.products;

// Сформировать корзину
const cart = {
  1234567890: 2, // product_id: quantity
  1234567891: 1
};

// Преобразовать в формат API
const items = Object.entries(cart).map(([product_id, qty]) => ({
  product_id: Number(product_id),
  qty: Number(qty)
}));

// Рассчитать итоговую сумму
let total_cents = 0;
for (const {product_id, qty} of items) {
  const product = products.find(p => p.id === product_id);
  if (product) {
    total_cents += product.price_cents * qty;
  }
}

// Получить информацию о пользователе из cookie
function getUserFromCookie() {
  const cookies = document.cookie.split(';').reduce((acc, p) => {
    const i = p.indexOf('=');
    if (i > 0) acc[p.slice(0, i).trim()] = decodeURIComponent(p.slice(i + 1));
    return acc;
  }, {});
  if (!cookies.u) return null;
  return JSON.parse(cookies.u);
}

const user = getUserFromCookie();

// Сформировать payload
const payload = {
  user: user || null,
  items,
  total_cents,
  total_formatted: (total_cents / 100).toFixed(2) + ' $'
};
```

### Создание заказа

```javascript
const res = await fetch('/api/orders', {
  method: 'POST',
  headers: { 'content-type': 'application/json' },
  credentials: 'include', // важно для отправки cookies
  body: JSON.stringify(payload)
});

const data = await res.json();
if (data.ok) {
  console.log('Заказ создан:', data.order);
  console.log('ID заказа:', data.order.id);
  console.log('Итоговая сумма:', data.order.total_cents / 100, '$');
}
```

---

## Использование общих функций (app.js)

### API запрос с логированием

```javascript
// Использует встроенную функцию apiRequest из app.js
const data = await apiRequest('my-request', 'GET', '/api/users');
console.log('Данные:', data);

// С обработкой ошибок
try {
  const data = await apiRequest('create-user', 'POST', '/api/users', {
    name: 'Иван',
    email: 'ivan@example.com'
  });
  toast('Пользователь создан', 'ok');
} catch (err) {
  toast('Ошибка: ' + err.message, 'err');
}
```

### Показ уведомлений

```javascript
// Успех
toast('Операция выполнена успешно', 'ok');

// Ошибка
toast('Произошла ошибка', 'err');

// С кастомным временем показа
toast('Сообщение', 'ok', 5000); // 5 секунд
```

### Экранирование HTML

```javascript
const userInput = '<script>alert("XSS")</script>';
const safe = esc(userInput);
console.log(safe); // &lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;
```

---

## Работа с сессиями

### Проверка авторизации

```javascript
// Проверка cookie sid
function isAuthenticated() {
  const cookies = document.cookie.split(';').reduce((acc, p) => {
    const i = p.indexOf('=');
    if (i > 0) acc[p.slice(0, i).trim()] = decodeURIComponent(p.slice(i + 1));
    return acc;
  }, {});
  return !!cookies.sid;
}

if (!isAuthenticated()) {
  window.location.href = '/login.html';
}
```

### Получение информации о пользователе

```javascript
function getUserFromCookie() {
  try {
    const cookies = document.cookie.split(';').reduce((acc, p) => {
      const i = p.indexOf('=');
      if (i > 0) acc[p.slice(0, i).trim()] = decodeURIComponent(p.slice(i + 1));
      return acc;
    }, {});
    if (!cookies.u) return null;
    return JSON.parse(cookies.u);
  } catch {
    return null;
  }
}

const user = getUserFromCookie();
if (user) {
  console.log('Пользователь:', user.name, user.email);
}
```

### Выход из системы

```javascript
async function logout() {
  await fetch('/api/auth/logout', {
    method: 'POST',
    credentials: 'include'
  });
  window.location.href = '/login.html';
}
```

---

## Фильтрация данных

### Фильтрация пользователей

```javascript
const users = [
  { id: 1, name: 'Иван', email: 'ivan@example.com' },
  { id: 2, name: 'Петр', email: 'petr@example.com' }
];

function filterUsers(users, query) {
  const q = query.trim().toLowerCase();
  if (!q) return users;
  return users.filter(u =>
    String(u.name || '').toLowerCase().includes(q) ||
    String(u.email || '').toLowerCase().includes(q)
  );
}

const filtered = filterUsers(users, 'иван');
console.log('Найдено:', filtered);
```

### Фильтрация товаров

```javascript
const products = [
  { id: 1, name: 'Товар 1', description: 'Описание 1' },
  { id: 2, name: 'Товар 2', description: 'Описание 2' }
];

function filterProducts(products, query) {
  const q = query.trim().toLowerCase();
  if (!q) return products;
  return products.filter(p =>
    String(p.name || '').toLowerCase().includes(q) ||
    String(p.description || '').toLowerCase().includes(q)
  );
}

const filtered = filterProducts(products, 'товар');
console.log('Найдено:', filtered);
```

---

## Форматирование данных

### Форматирование денег

```javascript
function fmtMoney(cents, withSymbol = true) {
  const v = (Number(cents || 0) / 100).toFixed(2);
  return withSymbol ? v + ' $' : v;
}

console.log(fmtMoney(9999));      // "99.99 $"
console.log(fmtMoney(9999, false)); // "99.99"
```

### Форматирование дат

```javascript
const isoDate = '2024-01-15T10:30:00.000Z';
const date = new Date(isoDate);

console.log(date.toLocaleString('ru-RU')); // "15.01.2024, 13:30:00"
console.log(date.toLocaleDateString('ru-RU')); // "15.01.2024"
console.log(date.toLocaleTimeString('ru-RU')); // "13:30:00"
```

---

## Обработка ошибок

### Базовый пример

```javascript
async function fetchUsers() {
  try {
    const res = await fetch('/api/users');
    if (!res.ok) {
      throw new Error(`HTTP error! status: ${res.status}`);
    }
    const data = await res.json();
    return data.users;
  } catch (error) {
    console.error('Ошибка загрузки пользователей:', error);
    toast('Не удалось загрузить пользователей', 'err');
    return [];
  }
}
```

### С детальной обработкой

```javascript
async function createUser(name, email) {
  try {
    const res = await fetch('/api/users', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ name, email })
    });
    
    const data = await res.json();
    
    if (!res.ok) {
      if (res.status === 409) {
        throw new Error('Email уже существует');
      }
      throw new Error(data.error || 'Ошибка создания пользователя');
    }
    
    toast('Пользователь создан', 'ok');
    return data;
  } catch (error) {
    toast(error.message, 'err');
    throw error;
  }
}
```

---

## Интеграция с внешними сервисами

### Отправка email (пример)

```javascript
// В функции request-code.js
async function sendEmail(env, { to, subject, text }) {
  if (env.DEV_DELIVERY === 'true') {
    console.log({ demoMail: { to, subject, text } });
    return { ok: true, demo: true };
  }

  // Интеграция с Resend (пример)
  const res = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${env.RESEND_API_KEY}`,
      'content-type': 'application/json'
    },
    body: JSON.stringify({
      from: 'no-reply@yourdomain.com',
      to,
      subject,
      text
    })
  });

  if (!res.ok) {
    throw new Error('Email send failed: ' + await res.text());
  }

  return { ok: true };
}
```

---

## Тестирование

### Тест создания пользователя

```javascript
async function testCreateUser() {
  const testUser = {
    name: 'Test User',
    email: `test${Date.now()}@example.com`
  };

  try {
    const res = await fetch('/api/users', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(testUser)
    });
    
    const data = await res.json();
    console.assert(res.ok, 'Пользователь должен быть создан');
    console.assert(data.id, 'Должен быть возвращен ID');
    console.log('✓ Тест пройден');
    return data;
  } catch (error) {
    console.error('✗ Тест провален:', error);
    throw error;
  }
}
```

### Тест создания заказа

```javascript
async function testCreateOrder() {
  // 1. Получить товары
  const productsRes = await fetch('/api/products');
  const productsData = await productsRes.json();
  const products = productsData.products;
  
  if (products.length === 0) {
    throw new Error('Нет товаров для теста');
  }

  // 2. Создать заказ с первым товаром
  const item = {
    product_id: products[0].id,
    qty: 1
  };

  const orderRes = await fetch('/api/orders', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({
      items: [item],
      total_cents: products[0].price_cents
    })
  });

  const orderData = await orderRes.json();
  console.assert(orderRes.ok, 'Заказ должен быть создан');
  console.assert(orderData.order.id, 'Должен быть возвращен ID заказа');
  console.log('✓ Тест пройден');
  return orderData;
}
```

