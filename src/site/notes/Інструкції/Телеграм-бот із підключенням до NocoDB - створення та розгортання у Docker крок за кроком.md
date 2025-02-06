---
{"title":"Телеграм-бот із підключенням до NocoDB - створення та розгортання у Docker крок за кроком","dg-publish":true,"dg-metatags":null,"dg-home":null,"permalink":"/instrukcziyi/telegram-bot-iz-pidklyuchennyam-do-noco-db-stvorennya-ta-rozgortannya-u-docker-krok-za-krokom/","dgPassFrontmatter":true,"noteIcon":""}
---


Опис, як можна розробити подібного телеграм-бота, але вже з використанням [NocoDB](https://www.nocodb.com/) замість прямого підключення до MS SQL.

## Загальна ідея

1. **NocoDB** використовується як проміжне рішення для керування даними (в ролі «No-Code»/«Low-Code» платформи). Ви можете під’єднати NocoDB до вже наявної бази даних або скористатись її вбудованим рушієм (SQLite за замовчуванням або інша СУБД).
2. Бот працює на **Python** (з використанням бібліотеки **aiogram 3**), як і в попередньому прикладі.
3. Для зберігання та читання даних **бот** звертається не безпосередньо до СУБД, а до **API NocoDB** (REST API).

> **Примітка.** Якщо вам потрібно під’єднатися до NocoDB як до «проксі» над іншою базою (наприклад, MS SQL, PostgreSQL тощо), достатньо додати нове джерело даних (Data Source) у NocoDB. Детальніше можна прочитати в [офіційній документації](https://docs.nocodb.com/).

---

## Налаштування NocoDB

### 1. Встановлення NocoDB (Docker-варіант)

Якщо ви хочете швидко запустити NocoDB в локальному середовищі через Docker, використайте, наприклад:

```bash
docker run -d \
  --name nocodb \
  -p 8080:8080 \
  nocodb/nocodb:latest
```

У результаті в браузері за адресою `http://localhost:8080` (або IP вашого сервера) буде доступний інтерфейс NocoDB.

### 2. Створення проєкту та таблиць

При першому запуску NocoDB запропонує створити або під’єднати базу.  
Для простоти:

- Обираємо **SQLite** (або іншу СУБД на ваш розсуд),
- Створюємо новий **Проєкт** (Project).

Потім у цьому проєкті додамо дві таблиці (можна через GUI NocoDB або через пункт “Add Table”):

1. **bot_user** (для користувачів бота)
    
    - **id** — первинний ключ (вмикаємо “Auto Increment”)
    - **tg_id** (тип: Number або Text, залежно від уподобань)
    - **user_name** (Text)
    - **user_type** (Text або Single Select/Enum)
2. **issue** (для зберігання інцидентів)
    
    - **id** — первинний ключ (“Auto Increment”)
    - **f_bot_user** — посилання (Relation) на таблицю **bot_user** (колонка `id`)
    - **created** — (DateTime)
    - **issue_type** — (Text або Number) — щоб зберігати тип інциденту: 2 (“Механіка”), 3 (“Електрика”)
    - **f_bot_user_resp** — (Relation) на таблицю **bot_user** (колонка `id`) або можна зберігати окремо як Number/Text
    - **closed** — (DateTime, nullable)

> Усе, що стосується доступу/прав користувачів до таблиць у NocoDB, ви можете налаштувати окремо (RBAC, групи, тощо), але для демо прикладу вистачить ролі Admin чи згенерованого токена.

### 3. Генеруємо API-токен для доступу (або використовуємо API Key проєкту)

Щоб бот міг звертатися до вашого NocoDB-проєкту, потрібно **згенерувати** ключ (`API Token`) або взяти його з налаштувань вашого облікового запису.

- Заходимо в **User Settings** (профіль користувача) → **API Tokens**, створюємо токен.
- Записуємо цей токен (наприклад, `NOCO_API_TOKEN`).
- Також за потреби зверніть увагу на **Base URL** вашого проєкту, воно приблизно таке:
    
    ```
    https://<Ваш_домен_або_IP>:8080
    ```
    
- Для кожної таблиці в NocoDB стандартно формується REST-ендпоінт на кшталт:
    
    ```
    GET/POST: /api/v1/{ProjectName}/tables/{TableName}/rows
    GET/POST: /api/v1/{ProjectName}/views/{ViewName}/rows
    ```
    
    або
    
    ```
    /api/v1/db/data/v1/{ProjectName}/{TableName}
    ```
    
    (Залежить від версії NocoDB та способу налаштування. Найкраще натиснути «Explore APIs» у самій NocoDB, щоб побачити точний шлях.)

---

## Структура бота

Логіка схожа до попередньої:

1. **/start**
    
    - Перевіряємо, чи є користувач у таблиці `bot_user` (за `tg_id`). Якщо ні, створюємо.
    - Повертаємо користувачеві вітальний текст + його `user_type`.
2. **/issue**
    
    - Запитуємо користувача, який тип інциденту («Механіка» чи «Електрика»).
    - Надсилаємо inline-клавіатуру з варіантами.
3. **/close**
    
    - Закриваємо всі відкриті інциденти для даного користувача (у таблиці `issue`), заповнюючи поле `closed` поточним часом.
    - Відповідаємо, скільки інцидентів було закрито.

Нижче приклад мінімального коду, розбитого на кілька файлів для зручності.

---

### 1. Файл `db_nocodb.py` (запити до NocoDB через REST API)

```python
# db_nocodb.py

import os
import requests
import logging
from datetime import datetime

LOG = logging.getLogger(__name__)

class NocoDBClient:
    BASE_URL = os.getenv("NOCO_BASE_URL", "http://localhost:8080")
    PROJECT_NAME = os.getenv("NOCO_PROJECT", "MyProject")
    API_TOKEN = os.getenv("NOCO_API_TOKEN", "")
    TABLE_USER = os.getenv("NOCO_TABLE_USER", "bot_user")  # назва таблиці з юзерами
    TABLE_ISSUE = os.getenv("NOCO_TABLE_ISSUE", "issue")   # назва таблиці з інцидентами

    HEADERS = {
        "xc-token": API_TOKEN,  # ключ для авторизації в NocoDB
        "Content-Type": "application/json"
    }

    @classmethod
    def _table_url(cls, table_name: str) -> str:
        """
        Формуємо URL для таблиці.  
        /api/v1/db/data/v1/{ProjectName}/{TableName}
        або інший, залежно від того, як налаштовано ваш NocoDB.
        """
        return f"{cls.BASE_URL}/api/v1/db/data/v1/{cls.PROJECT_NAME}/{table_name}"

    @classmethod
    def get_or_create_user(cls, tg_id: int, user_name: str) -> dict:
        """
        1. Шукаємо в таблиці bot_user рядок, де tg_id = tg_id.
        2. Якщо немає, створюємо.
        3. Повертаємо словник із даними користувача (наприклад, {'id': 1, 'tg_id': ..., 'user_name': ...}).
        """
        try:
            # 1. Шукаємо
            url = cls._table_url(cls.TABLE_USER) + f"?where=(tg_id,eq,{tg_id})"
            resp = requests.get(url, headers=cls.HEADERS, timeout=10)
            resp.raise_for_status()
            data = resp.json()  # { "list": [...], "page_info": { ... } }
            if len(data["list"]) > 0:
                # користувач вже існує
                return data["list"][0]
            else:
                # 2. Створюємо
                payload = {
                    "tg_id": tg_id,
                    "user_name": user_name,
                    "user_type": "Робочий"  # за замовчуванням
                }
                create_resp = requests.post(
                    cls._table_url(cls.TABLE_USER),
                    headers=cls.HEADERS,
                    json=payload,
                    timeout=10
                )
                create_resp.raise_for_status()
                return create_resp.json()  # Створений запис
        except Exception as e:
            LOG.error(f"get_or_create_user error: {e}")
            return {"error": str(e)}

    @classmethod
    def create_issue(cls, tg_id: int, issue_type: int) -> dict:
        """
        1. Знаходимо bot_user.id за tg_id
        2. Перевіряємо, чи є вже відкритий issue цього типу (issue_type) у цього користувача
        3. Якщо немає, створюємо (created=NOW, closed=NULL)
        4. Якщо є, "імітуємо" призначення виконавця (f_bot_user_resp)
        5. Повертаємо інформацію про інцидент.
        """
        try:
            user_info = cls.get_or_create_user(tg_id, "Unknown")
            if "error" in user_info:
                return {"error": user_info["error"]}

            user_id = user_info["id"]  # ідентифікатор у таблиці bot_user

            # 2. Шукаємо відкритий інцидент
            url_issues = cls._table_url(cls.TABLE_ISSUE)
            query = f"?where=(f_bot_user,eq,{user_id})~and(issue_type,eq,{issue_type})~and(closed,is,null)"
            resp = requests.get(url_issues + query, headers=cls.HEADERS, timeout=10)
            resp.raise_for_status()
            rows = resp.json()["list"]

            if len(rows) == 0:
                # 3. Створюємо новий issue
                payload = {
                    "f_bot_user": user_id,
                    "created": datetime.now().isoformat(timespec='seconds'),
                    "issue_type": issue_type,
                    "f_bot_user_resp": None,
                    "closed": None
                }
                create_resp = requests.post(
                    url_issues,
                    headers=cls.HEADERS,
                    json=payload,
                    timeout=10
                )
                create_resp.raise_for_status()
                issue_data = create_resp.json()
            else:
                # 4. "імітуємо" призначення виконавця
                issue_data = rows[0]
                # Припустимо, вибираємо останнього користувача з таким user_type
                # (або можна призначати довільно).
                # В NocoDB ми також можемо шукати bot_user з фільтром user_type=...
                # Для спрощення зробимо "призначення" на першого-ліпшого:
                user_resp = cls._find_any_user_by_type(issue_type)
                update_payload = {
                    "f_bot_user_resp": user_resp["id"] if user_resp else None
                }
                update_url = f"{url_issues}/{issue_data['id']}"
                update_resp = requests.patch(update_url, headers=cls.HEADERS, json=update_payload, timeout=10)
                update_resp.raise_for_status()
                # Перечитуємо оновлений запис
                issue_data = update_resp.json()

            return issue_data

        except Exception as e:
            LOG.error(f"create_issue error: {e}")
            return {"error": str(e)}

    @classmethod
    def close_all_issues(cls, tg_id: int) -> int:
        """
        Шукаємо всі відкриті інциденти користувача і заповнюємо `closed` поточним часом.
        Повертаємо кількість закритих.
        """
        try:
            user_info = cls.get_or_create_user(tg_id, "Unknown")
            if "error" in user_info:
                return -1

            user_id = user_info["id"]

            # 1. Шукаємо всі відкриті issue
            url_issues = cls._table_url(cls.TABLE_ISSUE)
            query = f"?where=(f_bot_user,eq,{user_id})~and(closed,is,null)"
            resp = requests.get(url_issues + query, headers=cls.HEADERS, timeout=10)
            resp.raise_for_status()
            open_issues = resp.json()["list"]
            if not open_issues:
                return 0

            # 2. Закриваємо (patch для кожного інциденту)
            now_str = datetime.now().isoformat(timespec='seconds')
            count_closed = 0
            for issue_row in open_issues:
                update_url = f"{url_issues}/{issue_row['id']}"
                payload = {"closed": now_str}
                update_resp = requests.patch(update_url, headers=cls.HEADERS, json=payload, timeout=10)
                update_resp.raise_for_status()
                count_closed += 1

            return count_closed

        except Exception as e:
            LOG.error(f"close_all_issues error: {e}")
            return -1

    @classmethod
    def _find_any_user_by_type(cls, user_type: int) -> dict:
        """
        Допоміжний метод: знайти користувача з таблиці bot_user, де, наприклад,
        user_type = 'Механік' або 'Електрик'.
        Для демо припустимо:
            - Якщо issue_type == 2 -> user_type='Механік'
            - Якщо issue_type == 3 -> user_type='Електрик'
        """
        if user_type == 2:
            utype_str = "Механік"
        elif user_type == 3:
            utype_str = "Електрик"
        else:
            return {}

        try:
            url = cls._table_url(cls.TABLE_USER) + f"?where=(user_type,eq,{utype_str})"
            resp = requests.get(url, headers=cls.HEADERS, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if data["list"]:
                # Беремо перший запис
                return data["list"][0]
            return {}
        except Exception:
            return {}
```

> Зверніть увагу, що в прикладі ми використовуємо `requests` для відправки HTTP-запитів до API NocoDB. В реальних проєктах можна використовувати асинхронні бібліотеки (`aiohttp` тощо), але для демо підійде синхронний варіант.

---

### 2. Файл `bot.py` (логіка телеграм-бота)

```python
# bot.py

import asyncio
import logging
from re import Match
import os

from aiogram import Bot, F, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram.types.bot_command import BotCommand
from dotenv import load_dotenv

from db_nocodb import NocoDBClient

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger(__name__)

# Читаємо змінні середовища із .env
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

BOT_TOKEN = os.getenv("BOT_TOKEN")
SERVICE_CHAT_ID = os.getenv("SERVICE_CHAT_ID")

# Створюємо об’єкти бота
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
router = Router()


def get_inline_keyboard() -> InlineKeyboardMarkup:
    keyboard_list = [
        [
            InlineKeyboardButton(text="Механіка", callback_data="issue#2"),
            InlineKeyboardButton(text="Електрика", callback_data="issue#3"),
        ],
        [
            InlineKeyboardButton(text="Скасувати", callback_data="issue#0"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard_list)

@router.message(Command("start"))
async def start_command(message: Message):
    user_info = NocoDBClient.get_or_create_user(message.from_user.id, message.from_user.full_name)
    if "error" in user_info:
        await message.answer(f"Помилка під час реєстрації: {user_info['error']}")
        return

    # user_info містить поля з NocoDB, наприклад: {"id": 1, "tg_id": 12345, "user_name": "...", "user_type": "..."}
    user_name = user_info.get("user_name", "невідомо")
    user_type = user_info.get("user_type", "Робочий")
    await message.answer(f"Привіт, {user_name}, ваша роль — {user_type}!")

@router.message(Command("issue"))
async def create_issue_command(message: Message):
    await message.answer(
        "Оберіть, який тип фахівця потрібен:",
        reply_markup=get_inline_keyboard()
    )

@router.callback_query(F.data.regexp("^issue#(\d+)").as_("match_type"))
async def choose_issue_type(call: CallbackQuery, match_type: Match[str]):
    issue_type = int(match_type.group(1))
    await call.message.edit_reply_markup(reply_markup=None)
    if issue_type == 0:
        # Операція скасована
        await call.message.answer("Операцію скасовано 💤")
    else:
        # Створюємо або оновлюємо інцидент
        issue_data = NocoDBClient.create_issue(call.from_user.id, issue_type)
        if "error" in issue_data:
            await call.message.answer(f"Помилка створення/оновлення інциденту: {issue_data['error']}")
        else:
            # Відобразимо коротку інформацію
            # issue_data містить поля: {"id":..., "created":..., "issue_type":..., "f_bot_user_resp":..., ...}
            _created = issue_data.get("created", "")
            _user_type = "Механіка" if issue_type == 2 else "Електрика"
            _resp_id = issue_data.get("f_bot_user_resp", None)
            if _resp_id:
                await call.message.answer(
                    f"✔ Інцидент <b>#{issue_data['id']}</b> з {_user_type} оновлено.\n"
                    f"Виконавець (id={_resp_id}) призначений.\n\n"
                    f"Час створення: {_created}"
                )
            else:
                await call.message.answer(
                    f"✔ Новий інцидент <b>#{issue_data['id']}</b> створено!\n"
                    f"Тип: {_user_type}\n"
                    f"Час створення: {_created}\n"
                    f"Виконавець поки не призначений."
                )

@router.message(Command("close"))
async def close_issues(message: Message):
    count = NocoDBClient.close_all_issues(message.from_user.id)
    if count < 0:
        await message.answer("Виникла помилка під час закриття інцидентів.")
    elif count == 0:
        await message.answer("Немає відкритих інцидентів.")
    else:
        word = "інцидент" if count == 1 else "інциденти(ів)"
        await message.answer(f"Успішно закрито {count} {word}!")


async def on_startup():
    # Налаштовуємо стандартні команди бота
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Почати роботу з ботом"),
            BotCommand(command="issue", description="Відкрити інцидент"),
            BotCommand(command="close", description="Закрити всі інциденти")
        ]
    )
    # Для прикладу, можна надіслати адміністратору повідомлення, що бот запущено
    if SERVICE_CHAT_ID:
        await bot.send_message(
            SERVICE_CHAT_ID,
            f"Бот запущено! Підключення до NocoDB — OK (імовірно)."
        )

async def main():
    dp.include_router(router)
    dp.startup.register(on_startup)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
```

---

### 3. Файл `requirements.txt`

```text
aiogram==3.17.0
python-dotenv==1.0.1
requests==2.31.0
```

> Зверніть увагу, що тут уже не потрібен `pyodbc` чи драйвер для SQL Server.

---

### 4. Файл `.env` (приклад)

```bash
# Телеграм
BOT_TOKEN=123456:ABC-...

# NocoDB
NOCO_BASE_URL=http://localhost:8080
NOCO_PROJECT=MyProject
NOCO_API_TOKEN=eyJhbGciOiJIUz...  # ваш реальний токен
NOCO_TABLE_USER=bot_user
NOCO_TABLE_ISSUE=issue

SERVICE_CHAT_ID=  # за бажанням
```

---

## Пакування в Docker

Створимо `Dockerfile` (мінімальний варіант):

```dockerfile
FROM --platform=linux/amd64 python:3.10-slim-buster

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH /app

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python", "bot.py"]
```

Припустимо, структура проєкту така:

```
my-tg-bot/
  ├─ bot.py
  ├─ db_nocodb.py
  ├─ .env
  ├─ requirements.txt
  └─ Dockerfile
```

Далі збираємо та запускаємо:

```bash
docker build -t tg-nocodb-bot .
docker run --rm -d \
    --name tg-nocodb-bot \
    --env-file .env \
    tg-nocodb-bot
```

Бот у контейнері буде намагатися підключитися до `NocoDB`, URL та токен якого ви передали через `.env`.

> Якщо `NocoDB` запущено в тому самому Docker-середовищі, треба звернути увагу на мережеві налаштування (docker-compose, docker network тощо). Можливо, `NOCO_BASE_URL` доведеться вказувати не як `localhost`, а як ім’я сервісу в docker-compose (наприклад, `http://nocodb:8080`).

---

## Перевірка

1. Запустіть контейнер (чи локально `bot.py`).
2. У Telegram зайдіть до вашого бота, виконайте `/start`. Має з’явитися запис у таблиці `bot_user` у NocoDB.
3. Виконайте `/issue`, виберіть «Механіка» чи «Електрика» — у таблиці `issue` з’явиться новий рядок.
4. Виконайте `/close` — у всіх рядках, де `f_bot_user` = ідентифікатор вашого користувача, поле `closed` заповниться поточним часом.

---

## Висновок

Таким чином, замість того, щоб напряму під’єднуватися до MS SQL через ODBC, ми використовуємо **NocoDB** як «проксі»-рівень між базою даних та додатком. Це може бути зручно, якщо ви хочете швидко налаштувати REST API над будь-якою СУБД, керувати схемою та правами доступу через веб-інтерфейс, або дати можливість іншим сервісам взаємодіяти через універсальне API.

Далі ви можете розвивати цього бота:

- Додавати більше полів у таблицях NocoDB.
- Використовувати фільтри та умови складнішої логіки (наприклад, різні статуси інцидентів).
- Розгортати все це (NocoDB + ваш бот) у Docker Compose чи Kubernetes.

Сподіваюся, цей приклад допоміг зрозуміти, як можна швидко і зручно створити телеграм-бота з підключенням до **NocoDB**!