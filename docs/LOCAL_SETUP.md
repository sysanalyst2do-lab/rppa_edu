# Локальная работа с проектом edu_rppa

## Что разворачивается локально

Для работы проекта на вашей машине поднимаются **два компонента**:

| Компонент | Что это | Порт |
|---|---|---|
| **PostgreSQL 16** | База данных (users, products, orders, sessions, auth_codes) | `5432` |
| **FastAPI (uvicorn)** | Python-сервер: API + отдача статики (фронтенд) | `8000` |

PostgreSQL работает как **служба Windows** — она стартует автоматически при включении компьютера.
FastAPI-сервер запускается **вручную** командой из терминала.

---

## Первоначальная настройка (один раз)

### 1. Установить зависимости Python

```powershell
pip install --user -r requirements.txt
```

### 2. Создать базу данных

```powershell
$env:PGPASSWORD="postgres"
& "C:\Program Files\PostgreSQL\16\bin\createdb.exe" -U postgres edu_rppa
```

### 3. Создать файл `.env`

Скопировать `.env.example` в `.env` и прописать подключение:

```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/edu_rppa
DEV_DELIVERY=true
RESEND_API_KEY=
HOST=0.0.0.0
PORT=8000
```

Таблицы создаются автоматически при первом запуске сервера (из `schema.sql`).

---

## Ежедневная работа

### Запустить сервер

```powershell
cd C:\Users\79688\Documents\dev\rppa_edu
python -m uvicorn backend.app:app --reload
```

После этого открыть в браузере: **http://127.0.0.1:8000**

Флаг `--reload` включает автоперезагрузку — при сохранении любого `.py` файла сервер перезапускается сам.

### Остановить сервер

Нажать **Ctrl+C** в терминале, где запущен uvicorn.

### Проверить что PostgreSQL работает

```powershell
tasklist /FI "IMAGENAME eq postgres.exe"
```

Если в списке есть `postgres.exe` — база работает.

### Запустить PostgreSQL (если вдруг остановлен)

```powershell
Start-Process powershell -Verb RunAs -ArgumentList '-Command', 'Start-Service postgresql-x64-16'
```

### Остановить PostgreSQL

```powershell
Start-Process powershell -Verb RunAs -ArgumentList '-Command', 'Stop-Service postgresql-x64-16'
```

> Обычно останавливать PostgreSQL не нужно — она потребляет мало ресурсов (~12 МБ RAM).

---

## Подключение к БД через DBeaver

### Создание подключения

1. Открыть DBeaver
2. **Файл → Новое подключение** (или иконка розетки с `+` в левом верхнем углу)
3. Выбрать **PostgreSQL** → Далее

### Параметры подключения

| Поле | Значение |
|---|---|
| **Host** | `localhost` |
| **Port** | `5432` |
| **Database** | `edu_rppa` |
| **Username** | `postgres` |
| **Password** | `postgres` |

Вкладка **Main** — заполнить как в таблице выше.

4. Нажать **Test Connection** — должно показать «Connected»
5. Если DBeaver предложит скачать драйвер PostgreSQL — нажать **Download**
6. Нажать **Готово**

### Навигация по таблицам

После подключения в левой панели:

```
edu_rppa
  └── Схемы
       └── public
            └── Таблицы
                 ├── users
                 ├── products
                 ├── orders
                 ├── sessions
                 └── auth_codes
```

Двойной клик на таблицу → вкладка **Data** покажет содержимое.

### Полезные SQL-запросы в DBeaver

Открыть SQL-редактор: **ПКМ на подключение → SQL Editor → New SQL Script** (или `Ctrl+]`).

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
SELECT session_id, email,
       to_timestamp(expires_at) AS expires
FROM sessions
WHERE expires_at > extract(epoch FROM now());

-- Очистить все данные (для перезапуска с нуля)
TRUNCATE auth_codes, sessions, orders, products, users RESTART IDENTITY CASCADE;
```

---

## Краткая шпаргалка

| Действие | Команда |
|---|---|
| **Запустить сервер** | `python -m uvicorn backend.app:app --reload` |
| **Остановить сервер** | `Ctrl+C` |
| **Открыть приложение** | http://127.0.0.1:8000 |
| **Проверить PostgreSQL** | `tasklist /FI "IMAGENAME eq postgres.exe"` |
| **Запустить PostgreSQL** | `Start-Process powershell -Verb RunAs -ArgumentList '-Command', 'Start-Service postgresql-x64-16'` |
| **Остановить PostgreSQL** | `Start-Process powershell -Verb RunAs -ArgumentList '-Command', 'Stop-Service postgresql-x64-16'` |
| **Подключение к БД** | `psql -U postgres -d edu_rppa` или DBeaver (см. выше) |

---

## Переменные окружения (.env)

| Переменная | Описание | Значение по умолчанию |
|---|---|---|
| `DATABASE_URL` | Строка подключения к PostgreSQL | `postgresql://postgres:postgres@localhost:5432/edu_rppa` |
| `DEV_DELIVERY` | `true` — email-коды пишутся в лог, не отправляются | `true` |
| `RESEND_API_KEY` | API-ключ Resend для реальной отправки email | пусто |
| `HOST` | Адрес, на котором слушает сервер | `0.0.0.0` |
| `PORT` | Порт сервера | `8000` |

---

## Сброс пароля PostgreSQL (если забыли)

1. Открыть файл `C:\Program Files\PostgreSQL\16\data\pg_hba.conf`
2. Найти строку:
   ```
   host    all    all    127.0.0.1/32    scram-sha-256
   ```
3. Заменить `scram-sha-256` на `trust`
4. Перезапустить PostgreSQL (от имени администратора):
   ```powershell
   Start-Process powershell -Verb RunAs -ArgumentList '-Command', 'Restart-Service postgresql-x64-16'
   ```
5. Задать новый пароль:
   ```powershell
   & "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -w -c "ALTER USER postgres PASSWORD 'новый_пароль';"
   ```
6. Вернуть `trust` обратно на `scram-sha-256` в `pg_hba.conf`
7. Снова перезапустить PostgreSQL (шаг 4)
8. Обновить пароль в `.env`
