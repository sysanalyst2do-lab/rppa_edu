# edu_rppa

Демонстрационное веб-приложение для мастер-класса по архитектуре информационных систем.

## Описание

**edu_rppa** показывает полный цикл разработки веб-приложения:
- Frontend на HTML/CSS/JavaScript
- Backend на Cloudflare Pages Functions
- База данных Cloudflare D1 (SQLite)
- Аутентификация через email-код

## Основные возможности

- ✅ Управление пользователями (CRUD)
- ✅ Управление товарами (CRUD)
- ✅ Создание заказов с корзиной покупок
- ✅ Аутентификация через одноразовый email-код
- ✅ Защита маршрутов через middleware

## Технологии

- **Frontend**: HTML, CSS, Vanilla JavaScript
- **Backend**: Cloudflare Pages Functions (Serverless)
- **База данных**: Cloudflare D1 (SQLite)
- **Хостинг**: Cloudflare Pages

## Документация

Полная документация находится в папке [`docs/`](./docs/):

- **[README.md](./docs/README.md)** - Общая документация проекта
- **[SUMMARY.md](./docs/SUMMARY.md)** - Краткое резюме
- **[API.md](./docs/API.md)** - Детальное описание API эндпоинтов
- **[DATABASE.md](./docs/DATABASE.md)** - Схема базы данных
- **[AUTHENTICATION.md](./docs/AUTHENTICATION.md)** - Система аутентификации
- **[FRONTEND.md](./docs/FRONTEND.md)** - Структура Frontend
- **[EXAMPLES.md](./docs/EXAMPLES.md)** - Примеры использования

## Быстрый старт

1. Настроить Cloudflare D1 базу данных
2. Создать таблицы (см. [DATABASE.md](./docs/DATABASE.md))
3. Настроить переменные окружения
4. Деплой на Cloudflare Pages

## Структура проекта

```
rppa_edu/
├── functions/          # Серверная логика (Cloudflare Functions)
│   ├── _middleware.js  # Middleware для проверки аутентификации
│   ├── _lib/          # Вспомогательные библиотеки
│   └── api/           # API эндпоинты
│       ├── auth/      # Аутентификация
│       ├── users.js   # Пользователи
│       ├── products.js # Товары
│       └── orders.js  # Заказы
│
├── public/            # Frontend (статические файлы)
│   ├── assets/       # CSS, JS, изображения
│   ├── index.html    # Главная страница
│   ├── login.html    # Страница входа
│   ├── users/        # Управление пользователями
│   ├── products/     # Управление товарами
│   └── orders/       # Создание заказов
│
└── docs/             # Документация
```

## Лицензия

Образовательный проект для демонстрации архитектуры веб-приложений.

