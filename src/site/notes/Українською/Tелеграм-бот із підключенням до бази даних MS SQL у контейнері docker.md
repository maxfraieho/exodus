---
{"title":"Tелеграм-бот із підключенням до бази даних MS SQL у контейнері docker","dg-publish":true,"dg-metatags":null,"dg-home":null,"permalink":"/ukrayinskoyu/telegram-bot-iz-pidklyuchennyam-do-bazi-danih-ms-sql-u-kontejneri-docker/","dgPassFrontmatter":true,"noteIcon":""}
---


[Microsoft SQL Server\*](/ru/hubs/mssql/)  
[Python\*](/ru/hubs/python/)  
[ERP-системи\*](/ru/hubs/erp/)  

**Туторіал**  

![](https://habrastorage.org/r/w1560/getpro/habr/upload_files/ec1/6c2/c21/ec16c2c2148c5f435eafb8543364d5d3.png)

---

## Для кого ця стаття

Стаття призначена для тих, хто замислюється про цифровізацію підприємств. Телеграм-бот — чудовий спосіб надати інтерфейс між базою даних та співробітником, у якого немає в цей момент доступу до корпоративної мережі (до свого комп’ютера). Звісно, мобільний додаток розв’язує це питання краще, проте витрати на створення/підтримку мобільного застосунку непорівнянні з витратами на простого ТГ-бота (навіть середньої складності). Те саме стосується і часу на розробку/впровадження. Сподіваюся, дана стаття буде корисною для ентузіастів масштабного впровадження ТГ-ботів як технології цифровізації промислових (і не лише) підприємств.

---

## Легенда

Припустімо, ми перебуваємо всередині корпоративної мережі підприємства, маємо вихід в інтернет, але зовні немає відкритих інтерфейсів. Є облікова система підприємства на основі бази даних MS SQL; до неї можна підключитися довільному клієнту та виконувати запити в межах прав, визначених для цього клієнта. Наше завдання — дати можливість робітникові повідомити про поломку верстата через ТГ-бот (адже в робітника немає логіна в корпоративну мережу й немає підключення до облікової системи).

---

## Технології

Бота розроблятимемо на Python з використанням бібліотеки **aiogram3**, як описано в серії навчальних статей [@yakvenalex](/users/yakvenalex), наприклад, <https://habr.com/ru/companies/amvera/articles/820527/>.

Якщо практика цифровізації приживеться, ботів буде багато. Щоб якось керувати цим та орієнтуватися у сервісах, відразу проєктуємо їх у мікросервісній архітектурі — пакуємо в docker-контейнер і запускатимемо саме контейнер.

Для демонстрації працездатності MS SQL Server також запустимо в docker-контейнері, згідно з <https://hub.docker.com/r/microsoft/mssql-server>. Це просто емулює наявну базу даних облікової системи, детально на цьому не зупинятимемось, але поговоримо про права доступу.

---

## Схема роботи

![](https://habrastorage.org/r/w1560/getpro/habr/upload_files/3d0/687/816/3d0687816347146674699c4a129546db.png "Рис. 1 – Схема роботи застосунку")

**Рис. 1 — Схема роботи застосунку**

Два слова про шар збережених процедур, за посередництвом яких бот буде отримувати й записувати дані в таблиці. Він потрібний:

1. Як рівень абстракції (щоб не залежати від структури таблиць і мати змогу змінювати їх без потреби міняти код бота).
2. Щоб обмежити права користувача, під яким бот авторизуватиметься в робочій базі даних (тоді навіть за помилки програміста бот не зможе псувати довільні дані в базі).

---

## Підготовка MS SQL — емульований приклад робочої бази даних

### Запуск контейнера з SQL Server

```bash
docker run -e 'ACCEPT_EULA=Y' -e 'MSSQL_SA_PASSWORD=<password>' \
-p 1433:1433 \
--name mssql-server \
-v sqlvolume:/var/opt/mssql \
-d mcr.microsoft.com/mssql/server:2022-latest
````

### Створення схеми даних

Далі, підключаємося до сервера за допомогою SSMS (або іншого інструмента) під користувачем **sa** і виконуємо такий скрипт:

```sql
-- Стартовий скрипт
create database testdb; -- Тестова база даних для демонстрації
go;
use testdb;

-- Створюємо таблиці для роботи бота (у виробничій базі щось подібне можна додати)
create table bot_user_type( -- типи користувачів
    id int identity primary key, -- первинний ключ
    user_type varchar(32)        -- тип користувача
);
insert into bot_user_type(user_type)
values (N'Робочий'), (N'Механік'), (N'Електрик'), (N'Адміністратор');

create table bot_user(          -- користувачі бота
    id int identity primary key, -- первинний ключ
    user_name varchar(128),      -- ім'я користувача в ТГ
    tg_id bigint,                -- ID у Telegram
    f_bot_user_type int foreign key references bot_user_type(id) -- тип користувача
);
insert into bot_user(user_name, f_bot_user_type) -- фейкові користувачі для демонстрації
values(N'Петро Іванов', 2), (N'Василь Кузцов', 3);

create table issue(                       -- Поломки (інциденти)
    id int identity primary key,         -- первинний ключ
    f_bot_user int foreign key references bot_user(id), -- Хто подав заявку
    created smalldatetime,               -- Дата і час подання
    f_bot_user_type int foreign key references bot_user_type(id),  -- 1 - потрібен механік, 2 - електрик
    f_bot_user_resp int foreign key references bot_user(id),       -- відповідальний виконавець
    closed smalldatetime                 -- дата і час закриття
);
go;
create schema bot; -- спеціальна схема, де зберігатимуться збережені процедури
go;

create login tgbot with password = '<VeryStrongPassword>'; -- користувач, під яким бот входитиме
create user tgbot for login tgbot;
go;
grant execute on schema ::bot to tgbot; 
-- Дозволяємо запуск будь-яких збережених процедур у схемі bot,
-- решти прав не даємо!
go;
```

Наступний крок — створити шар збережених процедур, до яких звертатиметься бот для обміну даними. Він міститиме три процедури:

1. **bot.get_or_create_user** — викликатиметься під час реєстрації користувача й повертатиме набір даних.
2. **bot.create_issue** — створюватиме нову поломку або імітуватиме призначення виконавця (якщо виклик повторний).
3. **bot.close_all_issues** — закриватиме всі відкриті поломки користувача й повертатиме кількість закритих інцидентів.

```sql
-- Зберігаємо у базі даних інформацію про користувача ТГ
create procedure bot.get_or_create_user 
    @user_tg_id bigint,         -- ІD користувача ТГ
    @user_name varchar(128)     -- ім'я користувача ТГ
as
begin
    set nocount on;
    if not exists(select 1 from bot_user where tg_id = @user_tg_id)
        insert into bot_user(tg_id, user_name, f_bot_user_type)
        values (@user_tg_id, @user_name, 1); 
        -- за замовчуванням призначаємо роль "Робочий"

    select bu.id, bu.tg_id, bu.user_name, ut.user_type
    from bot_user bu
    join dbo.bot_user_type ut on ut.id = bu.f_bot_user_type
    where bu.tg_id = @user_tg_id;
end;
go;

-- Створюємо новий інцидент. Якщо вже існує відкритий інцидент цього типу у цього користувача, не дублюємо
create procedure bot.create_issue 
    @user_tg_id bigint, -- ІD користувача ТГ
    @issue_type int     -- тип поломки (2 або 3)
as
begin
    set nocount on;
    if @issue_type not in (2, 3)
        throw 50011, N'Невідомий тип поломки', 1;

    declare @last_issue int;
    select top 1 @last_issue = i.id
    from issue i
    join dbo.bot_user b on i.f_bot_user = b.id
    where b.tg_id = @user_tg_id
      and i.f_bot_user_type = @issue_type
      and closed is null
    order by i.id desc;

    if @@rowcount = 0 
    begin
        insert into issue(f_bot_user, created, f_bot_user_type)
        select u.id, getdate(), @issue_type
        from bot_user u
        where u.tg_id = @user_tg_id;
        set @last_issue = scope_identity();
    end
    else
    begin
        -- Імітуємо призначення виконавця, якщо інцидент уже існує
        update issue
        set f_bot_user_resp = (
            select top 1 id
            from bot_user
            where bot_user.f_bot_user_type = @issue_type
            order by id desc
        )
        where id = @last_issue;
    end;

    select i.id, i.created, bu.user_name, but.user_type,
           coalesce(resp.user_name, N'Не призначено') as responsible
    from issue i
    join dbo.bot_user bu on i.f_bot_user = bu.id
    join dbo.bot_user_type but on i.f_bot_user_type = but.id
    left join dbo.bot_user resp on resp.id = i.f_bot_user_resp
    where i.id = @last_issue;
end;
go;

-- Закриваємо всі відкриті інциденти (поломки) конкретного користувача
create procedure bot.close_all_issues
    @user_tg_id bigint
as
begin
    set nocount on;
    update i
    set i.closed = getdate()
    from issue i
    join dbo.bot_user bu on i.f_bot_user = bu.id
    where bu.tg_id = @user_tg_id 
      and i.closed is null;

    select @@rowcount; 
    -- повертаємо кількість закритих поломок
end;
go;
```

---

## Телеграм-бот

Мета статті — продемонструвати робочу зв’язку бота і MS SQL Server, тому бот буде досить примітивним. Завдання бота:

- По команді **/start** зареєструвати користувача у БД.
- По команді **/issue** запитати, чи потрібен механік чи електрик, і створити інцидент. Якщо інцидент уже створений із такою ж причиною, імітувати «призначення» виконавця.
- По команді **/close** закрити всі відкриті інциденти цього ініціатора.

Створюємо бота і отримуємо токен (як описано у статтях за посиланням вище).

Для демонстрації склав код проєкту всього у два файли. Перший — `bot.py` (все, що пов’язано з ботом):

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

from db import DbConn

LOG = logging.getLogger(__name__)

# Читаємо .env у змінні середовища
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

# Налаштування
BOT_TOKEN = os.getenv("BOT_TOKEN")
SERVICE_CHAT_ID = os.getenv("SERVICE_CHAT_ID")

# Створюємо об’єкти бота
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
router = Router()

# Онлайн-клавіатура під час створення інциденту
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
    user_info = DbConn.get_or_create_user(message.from_user.id, message.from_user.full_name)
    if isinstance(user_info, dict):
        await message.answer(f"😞 Щось пішло не так... Помилка: {user_info.get('error')}")
    else:
        await message.answer(f"Привіт, {user_info.user_name}, ваша роль — {user_info.user_type}!")

@router.message(Command("issue"))
async def create_issue_command(message: Message):
    await message.answer(
        "Вкажіть імовірну причину інциденту",
        reply_markup=get_inline_keyboard()
    )

@router.message(Command("close"))
async def close_issues(message: Message):
    count = DbConn.close_all_issues(message.from_user.id)
    if count == 0:
        await message.answer("Немає відкритих інцидентів")
    elif count < 0:
        await message.answer("😞 Щось пішло не так...")
    else:
        word = "подію" if count == 1 else "події"
        await message.answer(f"Усе гаразд, закрито {count} {word}")

@router.callback_query(F.data.regexp("^issue#(\d+)").as_("match_type"))
async def choose_issue_type(call: CallbackQuery, match_type: Match[str]):
    issue_type = int(match_type.group(1))
    # Прибираємо онлайн-клавіатуру
    await call.message.edit_reply_markup(reply_markup=None)
    if issue_type == 0:
        # Операція скасована
        await call.message.answer("Операцію скасовано 💤")
    else:
        # Створюємо новий інцидент
        issue = DbConn.create_issue(call.from_user.id, issue_type)
        if isinstance(issue, dict):
            await call.message.answer(f"😞 Щось пішло не так... Помилка — {issue.get('error')}")
        else:
            await call.message.answer(
                f"✔ Інцидент зареєстровано, час: {issue.created}, потрібен: "
                f"{issue.user_type}, виконавець: {issue.responsible}. Зачекайте."
            )

async def on_startup():
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Почати роботу з ботом"),
            BotCommand(command="issue", description="Відкрити інцидент"),
            BotCommand(command="close", description="Закрити всі інциденти")
        ]
    )
    # Перевіримо з’єднання з базою
    is_db_ready = DbConn.test_connection()
    if SERVICE_CHAT_ID:
        status_emoji = "✅" if is_db_ready else "❌"
        await bot.send_message(
            SERVICE_CHAT_ID,
            f"Бот запущено, з’єднання з БД {status_emoji}"
        )

async def main():
    dp.include_router(router)
    dp.startup.register(on_startup)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
```

Другий файл — `db.py` (взаємодія з БД):

```python
# db.py
import os
import logging

import pyodbc
from pyodbc import Cursor

LOG = logging.getLogger(__name__)

class DbConn:
    _conn_str = None

    @staticmethod
    def connection_string() -> str:
        if not isinstance(DbConn._conn_str, str):
            DbConn._conn_str = (
                "Driver={ODBC Driver 18 for SQL Server};"
                f"Server={os.environ.get('DB_SERVER')};"
                f"Database={os.environ.get('DB_DATABASE')};"
                f"UID={os.environ.get('DB_USER')};"
                f"PWD={os.environ.get('DB_PASSWORD')};"
                "TrustServerCertificate=yes;"
            )
        return DbConn._conn_str

    @staticmethod
    def test_connection() -> bool:
        try:
            with pyodbc.connect(DbConn.connection_string()) as conn:
                cursor = conn.cursor()
                cursor.execute("select @@version")
                records = cursor.fetchall()
                LOG.warning(records[0])
                return len(records) == 1
        except BaseException as e:
            LOG.error(e)
            return False

    @staticmethod
    def get_or_create_user(tg_user_id: int, tg_user_name: str) -> dict:
        try:
            with pyodbc.connect(DbConn.connection_string(), autocommit=True) as conn:
                cursor = conn.cursor()
                cursor.execute("exec bot.get_or_create_user ?, ?", tg_user_id, tg_user_name[:128])
                return cursor.fetchall()[0]
        except BaseException as e:
            LOG.error(e)
            return {"error": e}

    @staticmethod
    def create_issue(tg_user_id: int, issue_type: int) -> dict:
        try:
            with pyodbc.connect(DbConn.connection_string(), autocommit=True) as conn:
                cursor = conn.cursor()
                cursor.execute("exec bot.create_issue ?, ?", tg_user_id, issue_type)
                return cursor.fetchall()[0]
        except BaseException as e:
            LOG.error(e)
            return {"error": e}

    @staticmethod
    def close_all_issues(tg_user_id: int) -> int:
        try:
            with pyodbc.connect(DbConn.connection_string(), autocommit=True) as conn:
                cursor = conn.cursor()
                cursor.execute("exec bot.close_all_issues ?", tg_user_id)
                return cursor.fetchall()[0][0]
        except BaseException as e:
            LOG.error(e)
            return -1
```

Також потрібен файл `.env` із налаштуваннями змінних оточення (приклад):

```
BOT_TOKEN=455656336:AAHCw22T_qiA391bvLYOcSGMzg-4AADD346
SERVICE_CHAT_ID=436568544
DB_SERVER=localhost
DB_DATABASE=testdb
DB_USER=tgbot
DB_PASSWORD=VeryStrongPassword
```

---

## Пакування в Docker Container

Насамперед у проєкт додаємо `Dockerfile`:

```dockerfile
FROM --platform=linux/amd64 public.ecr.aws/docker/library/python:3.10-slim-buster

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH /

RUN apt-get update && apt-get install -y curl gnupg

RUN sh -c "curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -"
RUN apt-get update
RUN sh -c "curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list > /etc/apt/sources.list.d/mssql-release.list"
RUN apt-get update
RUN ACCEPT_EULA=Y apt-get install -y msodbcsql18
RUN apt-get install -y netcat gcc unixodbc-dev

COPY . /app
WORKDIR /app

RUN pip install --upgrade pip
RUN pip3 install -r requirements.txt

ENTRYPOINT ["python3", "run.py"]
```

Декілька пояснень:

- Як базовий образ використано `public.ecr.aws/docker/library/python:3.10-slim-buster`, оскільки з ним вдалося стабільно встановити `pyodbc` для MS SQL.
- Рядки 7–14 узято з матеріалів Microsoft щодо встановлення `pyodbc`.
- Решта кроків стандартні: копіюємо вміст проєкту у `/app` контейнера, встановлюємо бібліотеки та оголошуємо `run.py` файлом, який запускається під час старту.

Також створимо `requirements.txt`, щоб коректно встановити всі залежності:

```
aiofiles==24.1.0
aiogram==3.17.0
aiohappyeyeballs==2.4.4
aiohttp==3.11.11
aiosignal==1.3.2
annotated-types==0.7.0
attrs==25.1.0
certifi==2025.1.31
frozenlist==1.5.0
idna==3.10
magic-filter==1.0.12
multidict==6.1.0
propcache==0.2.1
pydantic==2.10.6
pydantic_core==2.27.2
pyodbc==5.2.0
python-dotenv==1.0.1
typing_extensions==4.12.2
yarl==1.18.3
```

Нарешті, збираємо контейнер. Якщо ми емулюємо MS SQL локально, варто в `.env` для `DB_SERVER` замінити `localhost` на `host.docker.internal`. Якщо ж у вас реальний окремий сервер (що найчастіше і буває на практиці), нічого міняти не потрібно.

```bash
# Збираємо контейнер
docker build -t tgbot .

# І запускаємо його
docker run --rm -d tgbot
```

Потім можна перевірити, чи все працює як належить, виконавши команди бота. Наприклад:

![](https://habrastorage.org/r/w1560/getpro/habr/upload_files/852/35f/93f/85235f93f736826be6fb3916fdba8c81.png)

---

## Висновки

Ми розглянули приклад, де Телеграм-бот слугує інтерфейсом між користувачем без доступу до корпоративної мережі та корпоративною базою даних (MS SQL). Такий підхід дає змогу створювати й розгортати мікросервісну архітектуру ботів (у docker-контейнерах), підвищуючи надійність та керованість системи.
