# edu_rppa

Демонстрационное веб-приложение для мастер-класса по архитектуре информационных систем.

## Описание

**edu_rppa** показывает полный цикл разработки веб-приложения:
- Frontend на HTML/CSS/JavaScript
- Backend на Python (FastAPI)
- База данных PostgreSQL
- Аутентификация через email-код

## Основные возможности

- Управление пользователями (CRUD)
- Управление товарами (CRUD)
- Создание заказов с корзиной покупок
- Аутентификация через одноразовый email-код
- Защита маршрутов через middleware
- Сессии на основе cookies

## Технологии

- **Frontend**: HTML, CSS, Vanilla JavaScript
- **Backend**: Python 3.12, FastAPI, uvicorn
- **База данных**: PostgreSQL 16
- **Библиотеки**: asyncpg, httpx, python-dotenv

## Документация

Полная документация находится в папке [`docs/`](./docs/):

- **[README.md](./docs/README.md)** — Общая документация проекта
- **[SUMMARY.md](./docs/SUMMARY.md)** — Краткое резюме
- **[API.md](./docs/API.md)** — Детальное описание API эндпоинтов
- **[DATABASE.md](./docs/DATABASE.md)** — Схема базы данных
- **[AUTHENTICATION.md](./docs/AUTHENTICATION.md)** — Система аутентификации
- **[FRONTEND.md](./docs/FRONTEND.md)** — Структура Frontend
- **[EXAMPLES.md](./docs/EXAMPLES.md)** — Примеры использования
- **[LOCAL_SETUP.md](./docs/LOCAL_SETUP.md)** — Локальная работа и развёртывание

## Быстрый старт

1. Установить зависимости: `pip install --user -r requirements.txt`
2. Создать базу данных PostgreSQL: `createdb -U postgres edu_rppa`
3. Скопировать `.env.example` в `.env` и прописать `DATABASE_URL`
4. Запустить сервер: `python -m uvicorn backend.app:app --reload`
5. Открыть http://127.0.0.1:8000

Подробнее — в [LOCAL_SETUP.md](./docs/LOCAL_SETUP.md).

## Структура проекта

```
rppa_edu/
├── backend/               # Серверная логика (Python / FastAPI)
│   ├── app.py             # Точка входа, middleware, статика
│   ├── db.py              # Пул подключений asyncpg
│   ├── mailer.py          # Отправка email
│   └── routes/            # API эндпоинты
│       ├── auth.py        # Аутентификация
│       ├── users.py       # Пользователи
│       ├── products.py    # Товары
│       └── orders.py      # Заказы
│
├── public/                # Frontend (статические файлы)
│   ├── assets/            # CSS, JS, изображения
│   ├── index.html         # Главная страница
│   ├── login.html         # Страница входа
│   ├── users/             # Управление пользователями
│   ├── products/          # Управление товарами
│   └── orders/            # Создание заказов
│
├── docs/                  # Документация
├── schema.sql             # DDL для PostgreSQL
├── requirements.txt       # Python-зависимости
└── .env.example           # Шаблон переменных окружения
```

## Лицензия

Образовательный проект для демонстрации архитектуры веб-приложений.
