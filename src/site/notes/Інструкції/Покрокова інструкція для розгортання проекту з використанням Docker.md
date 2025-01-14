---
{"title":"Покрокова інструкція для розгортання проекту з використанням Docker","dg-publish":true,"dg-metatags":null,"dg-home":null,"permalink":"/instrukcziyi/pokrokova-instrukcziya-dlya-rozgortannya-proektu-z-vikoristannyam-docker/","dgPassFrontmatter":true,"noteIcon":""}
---



## 1. Створення `.env` файлу

У корені проекту створіть файл `.env` з такими змінними:

```plaintext
ADMIN_IDS=[12345]
BASE_SITE=http://127.0.0.1:8000
BOT_TOKEN=your_bot_token
TG_API_SITE=https://api.telegram.org
FRONT_SITE=http://127.0.0.1:3000
DATABASE_URL=sqlite:///app/sqlite_data/database.db
```

Замініть `your_bot_token` на токен вашого Telegram-бота.

---

## 2. Підготовка Dockerfile

`Dockerfile` у вас вже коректний. У разі потреби він автоматично:

- Використовує базовий образ `arm64v8/python:3.11-alpine`.
- Встановлює системні залежності (`gcc`, `musl-dev`, `libffi-dev`).
- Встановлює Python-залежності з `requirements.txt`.
- Копіює файли проекту в контейнер.
- Відкриває порт `8000` і запускає сервер Uvicorn.

---

## 3. Оновлення `docker-compose.yml`

У вашому `docker-compose.yml` уже є:

- Опис сервісу `app` для роботи бекенду.
- Маунтинг директорій для зберігання коду та SQLite бази даних.
- Налаштування порту `8000`.

Перевірте, чи додано змінні оточення з `.env` файлу:

```yaml
environment:
  - DATABASE_URL=${DATABASE_URL}
  - BOT_TOKEN=${BOT_TOKEN}
```

---

## 4. Ініціалізація бази даних

Перед запуском проекту виконайте міграції для створення таблиць:

```bash
docker-compose run app alembic upgrade head
```

Це створить всі необхідні таблиці в SQLite базі даних.

---

## 5. Налаштування вебхука Telegram

Використовуйте тунелювання (наприклад, Ngrok), щоб зробити локальний сервер доступним:

```bash
ngrok http 8000
```

Скопіюйте отриману HTTPS-URL і додайте її в `.env` як значення `BASE_SITE`.

Виконайте запит для встановлення вебхука:

```bash
curl -X POST https://api.telegram.org/bot<your_bot_token>/setWebhook -d "url=https://<ngrok-url>/webhook"
```

---

## 6. Запуск проекту

Виконайте команду:

```bash
docker-compose up --build
```

Це створить і запустить контейнер.

---

## 7. Перевірка доступності

Переконайтеся, що бекенд доступний на [http://localhost:8000](http://localhost:8000).

Перевірте функціональність Telegram-бота.

---

## 8. Деплой

Для деплоя на хостинг (наприклад, Amvera Cloud або інший), оновіть `BASE_SITE` у `.env` на реальний домен і переконайтеся, що порт `8000` відкритий.

---

Якщо виникнуть додаткові питання, звертайтеся!
