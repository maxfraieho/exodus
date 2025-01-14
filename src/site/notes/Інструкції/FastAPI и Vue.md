---
{"title":"FastAPI и Vue","dg-publish":true,"dg-metatags":null,"dg-home":null,"permalink":"/instrukcziyi/fast-api-i-vue/","dgPassFrontmatter":true,"noteIcon":""}
---


Сегодня я рад представить вам новый крупный проект, в рамках которого мы разберем технологии и подходы, которые ранее не освещались в моих статьях.

На этот раз мы создадим телеграм-бота с MiniApp (ранее известным как WebApp) — другими словами, это будет бот с интегрированным мини-сайтом прямо в Telegram. Для реализации этого проекта мы используем два основных фреймворка:

*   FastAPI — мощный Python-фреймворк, который мы задействуем для разработки API нашего телеграм-бота. Мы рассмотрим нетривиальный подход, который позволит создать полноценный бэкенд закрывающий, как API методы, так и телеграмм бота.
    
*   Vue.js 3 — JavaScript-фреймворк, выбранный за удобство разработки и возможности создания сложных визуальных элементов.
    

Помимо этих двух столпов, мы также подключим полезные библиотеки из мира Python и JavaScript, которые помогут нам справиться с задачами проекта. О них я расскажу подробнее, когда начнем обсуждать используемый стек технологий.

### Что будем создавать?

Наш проект — это телеграм-бот для выдуманной клиники «Здоровье Плюс». Основная задача — дать пользователям возможность записаться к врачу в удобный день и время.

Наиболее сложная часть разработки — это реализация системы записи к врачу. Я разберу этот блок максимально подробно, тогда как более простые части будут описаны компактно, чтобы сэкономить время.

Проект будет состоять из трех ключевых компонентов:

1.  API — сердцевина логики, взаимодействующая с базой данных, обрабатывающая файлы и поддерживающая функциональность бота.
    
2.  Телеграм-бот — самостоятельная реализация без готовых библиотек для работы с Telegram API на базе библиотеки HTTPX, связанной с FastApi.
    
3.  Фронтенд — интерфейс для взаимодействия с пользователем.
    

В рамках фронтенда реализуем следующие страницы:

*   Страница выбора направления (терапия, стоматология и т. д.) с удобным реактивным поиском. Отобразим направления в виде карточек, как в интернет-магазине.
    
*   Страница выбора врача в выбранной категории.
    
*   Страница записи на прием с использованием временных слотов.
    

Функционал телеграм-бота будет включать:

*   Раздел «О нас».
    
*   Просмотр записей.
    
*   Возможность записи через MiniApp.
    

Для взаимодействия всех частей напишем API, используя чистый Telegram Bot API с помощью библиотеки HTTPX.

В результате должен получиться вот такой проект:

В рамках сегодняшней статьи мы реализуем всю логику бэкенда: API-методы, Telegram бот и настройка автоматических уведомлений (задачи по расписанию). В следующей части займемся написанием фронтенд части на VUE.JS 3.

### Технологический стек

**Стилизация фронтенда**:

*   Tailwind CSS — с его помощью мы создадим стильный интерфейс без написания CSS вручную.
    
*   FontAwesome — для иконок.
    

**Python**:

*   FastAPI — основной инструмент для разработки API.
    
*   SQLAlchemy 2 — взаимодействие с базой данных (в проекте используется SQLite).
    
*   Apscheduler — управление задачами по расписанию (например, отправка уведомлений).
    
*   HTTPX — для общения с Telegram API.
    
*   Дополнительно: Loguru, Pydantic 2, Uvicorn и другие библиотеки.
    

**JavaScript**:

*   Vue.js 3 — основа для создания фронтенда.
    
*   VueRouter — создание многостраничного приложения.
    
*   useFetch — для работы с API.
    
*   VueTG — упрощает интеграцию MiniApp.
    

### Этапы разработки

1.  Настройка базы данных с SQLAlchemy, Aiosqlite и Alembic.
    
2.  Создание API для взаимодействия с данными.
    
3.  Разработка телеграм-бота с использованием HTTPX.
    
4.  Реализация логики уведомлений (APSCHEDULER).
    
5.  Создание фронтенда на Vue.js 3.
    
6.  Деплой.
    

### Деплой

Хочу отдельно остановиться на процессе деплоя. Сегодня я продемонстрирую вам самый простой и доступный способ, с помощью которого вы сможете самостоятельно запускать свои проекты удаленно. В рамках данного проекта нам предстоит выполнить деплой дважды: сначала бэкенд-часть, а затем фронтенд.

Использовать для этих целей мы будем сервис [Amvera Cloud](https://amvera.ru/?utm_source=habr&utm_medium=article&utm_campaign=yakvenalex_vue_fast_api_part_1). Данный сервис, как обычно, я выбираю за простоту и доступность. То есть, если у вас есть базовое представление о кодинге, то вы точно сможете разобраться. Технически, деплой и фронтедна и бэкенда будет заключаться в прохождении следующих шагов:

1.  Написание проекта.
    
2.  Создание конфигурационного файла.
    
3.  Доставка проекта на платформу.
    
4.  Получение бесплатного домена с HTTPS.
    
5.  Сборка.
    

На практике будет так же просто как описал выше, поэтому, обязательно дочитайте статью до конца, так как там этот блок я буду рассматривать более подробно.

#### Дисклеймер

Прежде чем мы погрузимся в код, хочу сделать небольшое отступление.

Изначально я планировал уместить весь материал в одной статье. Однако его оказалось настолько много, что я решил разделить материал на две части. Сейчас вы читаете **первую часть**, в которой мы полностью реализуем бэкенд приложения. А именно:

*   **API-методы**,
    
*   **Telegram-бот**,
    
*   **Логику автоматической отправки уведомлений**.
    

Во второй части мы займемся созданием фронтенда на Vue.JS 3, который будет работать с этим API.

Я постараюсь объяснить всё максимально доступно, чтобы каждый из вас смог разобраться. Но нужно учитывать, что используемые сегодня технологии и подходы достаточно сложны.

Чтобы не превращать статью в многочасовой марафон, я буду избегать излишних деталей. Если вы только начинаете разбираться с некоторыми из этих инструментов, рекомендую сначала ознакомиться с моими предыдущими статьями, где я подробно разбирал **FastAPI** и **SQLAlchemy**. Это поможет вам лучше понимать текущий материал.

Что касается **Vue.js 3**, ранее я о нём не писал. Поэтому, прежде чем двигаться дальше, рекомендую изучить основы этого фреймворка. Это позволит вам легче разобраться с материалом следующей статьи.

Если после прочтения у вас останутся вопросы, обязательно загляните в моё сообщество **«**[**Лёгкий путь в Python**](https://t.me/PythonPathMaster)**»**. Нас уже более 2000 единомышленников, готовых поддержать друг друга. Там вы найдёте эксклюзивный контент, который я публикую только в своём Telegram-канале, а также сможете задать вопросы мне или другим участникам сообщества.

Кстати, полный исходный код бэкенда и фронтенда уже доступен в сообществе.

Если эта статья окажется полезной, поддержите её лайком и комментарием. Для меня это не только мотивация продолжать, но и лучший способ понять, что я на верном пути.

Начнем!

### Подготовка к созданию бэкенда

**Шаг 1: Настройка окружения**

Первое, что необходимо сделать — это открыть любимое IDE, в котором вы привыкли писать код на Python, и создать новый проект. Я, как обычно, выбираю PyCharm.

После создания пустого проекта и активации виртуального окружения необходимо установить ряд библиотек. Для удобства мы будем использовать файл `requirements.txt`. Заполним его следующим образом:

```
fastapi==0.115.0
pydantic==2.9.2
uvicorn==0.31.0
pydantic_settings==2.7.1
loguru==0.7.2
SQLAlchemy==2.0.35
aiosqlite==0.20.0
alembic==1.14.0
httpx==0.28.1
apscheduler==3.11.0
pytz==2024.2
```


Установим зависимости командой:

```
pip install -r requirements.txt
```


**Шаг 2: Настройка переменных окружения**

Следующий важный этап — создание файла .env. Создаём его в корне проекта и заполняем следующими переменными:

```
ADMIN_IDS=[12345]
BASE_SITE=http://127.0.0.1:8000
BOT_TOKEN=your_bot_token
TG_API_SITE=https://api.telegram.org
FRONT_SITE=http://127.0.0.1:3000
```


Разберём каждую переменную:

*   `ADMIN_IDS` — список Telegram ID администраторов вашего бота. Для получения своего ID и ID любого пользователя можно воспользоваться моим ботом: [Telegram-ботом](https://t.me/get_tg_ids_universeBOT).
    
*   `BASE_SITE` — адрес, на котором будет работать ваш FastAPI. Указан стандартный адрес для локального запуска. При деплое заменим его на тот, который предоставит [Amvera Cloud](https://amvera.ru/?utm_source=habr&utm_medium=article&utm_campaign=yakvenalex_vue_fast_api_part_1) (адрес без слеша в конце).
    
*   `BOT_TOKEN` — токен вашего Telegram-бота. Его можно получить через [BotFather](https://t.me/BotFather).
    
*   `TG_API_SITE` — константа для взаимодействия с API Telegram.
    
*   `FRONT_SITE` — адрес фронтенд-приложения (до него мы доберёмся позже).
    

**Шаг 3: Создание структуры проекта**

В корне проекта создаём две папки:

*   `data` — для хранения баз данных SQLite.
    
*   `app` — для основного кода FastApi приложения.
    

Далее создаём структуру папки app:

*   `api` — основные эндпоинты API.
    
*   `dao` — логика работы с базой данных через SQLAlchemy.
    
*   `static` — для хранения статических файлов (например, фото врачей).
    
*   `tg_bot` — для описания логики Telegram-бота.
    

В корне папки app создаём три файла:

1.  `async_client.py` — класс для работы с HTTP-клиентом (HTTPX).
    
2.  `config.py` — файл настроек проекта.
    
3.  `main.py` — основной файл приложения.
    

**Шаг 4: Настройка конфигураций**

Заполним файл `app/config.py` следующим образом:

```
import os
from typing import List

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    BOT_TOKEN: str
    ADMIN_IDS: List[int]
    FORMAT_LOG: str = "{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}"
    LOG_ROTATION: str = "10 MB"
    DB_URL: str = 'sqlite+aiosqlite:///data/db.sqlite3'
    STORE_URL: str = 'sqlite:///data/jobs.sqlite'
    BASE_SITE: str
    TG_API_SITE: str
    FRONT_SITE: str

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
    )

    def get_webhook_url(self) -> str:
        """Возвращает URL вебхука."""
        return f"{self.BASE_SITE}/webhook"

    def get_tg_api_url(self) -> str:
        """Возвращает URL Telegram API."""
        return f"{self.TG_API_SITE}/bot{self.BOT_TOKEN}"


# Инициализация настроек и планировщика задач
settings = Settings()
database_url = settings.DB_URL
scheduler = AsyncIOScheduler(
    jobstores={'default': SQLAlchemyJobStore(url=settings.STORE_URL)}
)

```


Я использовал тут библиотеку `pydantic_settings` для работы с переменными окружения.

Из нового, это то, что мы добавляем в файл настроек интеграцию с библиотекой APScheduler. Это мощный инструмент для управления задачами и их расписанием. В нашем проекте APScheduler будет использоваться для отправки напоминаний о записях к докторам в указанное время.

**Хранилище задач.** Мы используем `SQLAlchemyJobStore`, чтобы сохранять задачи в базе данных SQLite (data/jobs.sqlite). Чаще для таких целей используется хранилище Redis, но я, для разнообразия, решил рассказать о данном хранилище.

**Асинхронный планировщик.** В проекте используется `AsyncIOScheduler`, который идеально подходит для асинхронных приложений, таких как наше. Он позволяет запускать задачи без блокировки основного цикла приложения.

Подробнее про `APSCheduler` поговорим в блоке про настройку отправки уведомлений.

**Шаг 5: Настройка HTTP-клиента**

Теперь создадим файл app/async\_client.py:

```
import httpx
from typing import Optional


class HTTPClientManager:
    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None

    def get_client(self) -> httpx.AsyncClient:
        """Возвращает экземпляр HTTP-клиента."""
        if self._client is None:
            self._client = httpx.AsyncClient()
        return self._client

    async def close_client(self):
        """Закрывает HTTP-клиент."""
        if self._client:
            await self._client.aclose()
            self._client = None


# Создаём глобальный объект для управления HTTP-клиентом
http_client_manager = HTTPClientManager()

```


Здесь мы реализовали глобальный объект соединения, который упрощает отправку запросов. Этот подход позволяет держать соединение открытым на протяжении всего цикла работы приложения, что критически важно для быстрого получения обновлений от серверов Telegram.

На этом этапе подготовка к созданию бэкенда завершена. В следующих разделах мы будем развивать функционал API, работать с базой данных и интегрировать Telegram-бота.

### Подключаем к проекту SQLAlchemy и Alembic

На этом этапе мы с вами подготовим структуру будущих таблиц базы данных и выполним миграции (трансформируем абстрактные классы в настоящие таблицы базы данных SQLite). Перед продолжением прочтения настоятельно рекомендую ознакомиться с моими статьями:

1.  [Асинхронный SQLAlchemy 2: простой пошаговый гайд по настройке, моделям, связям и миграциям с использованием Alembic.](https://habr.com/ru/companies/amvera/articles/849836/)
    
2.  [Асинхронный SQLAlchemy 2: пошаговый гайд по управлению сессиями, добавлению и извлечению данных с Pydantic.](https://habr.com/ru/companies/amvera/articles/850470/)
    
3.  [Асинхронный SQLAlchemy 2: улучшение кода, методы обновления и удаления данных.](https://habr.com/ru/companies/amvera/articles/855740/)
    

В этих статьях вы найдете подробную информацию о работе с моделями, связями и миграциями. Я буду предполагать, что вы уже знакомы с основами или изучили их из указанных материалов.

Весь код, связанный с базой данных, будет находиться в папке `app/dao`. Создайте её со следующей структурой:

```
├── dao/
│   ├── __init__.py                # Пакетный файл для удобства импортов
│   ├── database.py                # Настройки SQLAlchemy
│   ├── models.py                  # Модели базы данных
│   ├── base.py                    # Универсальный класс для взаимодействия с БД
│   └── session_maker_fast_api.py  # Класс для генерации сессий в эндпоинтах FastAPI
```


### Файл database.py

Файл `database.py` отвечает за настройки SQLAlchemy и создание базового класса для всех моделей.

```
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine, AsyncSession
from app.config import database_url

engine = create_async_engine(url=database_url)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession)

class Base(AsyncAttrs, DeclarativeBase):
    __abstract__ = True

```


*   **engine**: Асинхронный движок для работы с базой данных. Подключается с помощью `create_async_engine`.
    
*   **async\_session\_maker**: Фабрика для создания асинхронных сессий.
    
*   **Класс Base**: Базовый абстрактный класс для всех моделей.
    

### Файл app/models.py

В этом файле описаны основные модели базы данных: пользователи, доктора, направления и заявки. Опишем модели:

```
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Integer, Text, ForeignKey, DateTime, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import time, date
from app.dao.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True)
    username: Mapped[str | None]
    first_name: Mapped[str]
    last_name: Mapped[str | None]

    # Relationships
    bookings: Mapped[List["Booking"]] = relationship(back_populates="user")


class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str]
    last_name: Mapped[str]
    patronymic: Mapped[Optional[str]]
    special: Mapped[str]
    specialization_id: Mapped[int] = mapped_column(ForeignKey("specializations.id"), server_default=text("1"))
    work_experience: Mapped[int] = mapped_column(Integer, nullable=False)
    experience: Mapped[str]
    description: Mapped[str] = mapped_column(Text)
    photo: Mapped[str]

    # Relationships
    bookings: Mapped[List["Booking"]] = relationship(back_populates="doctor")

    specialization: Mapped["Specialization"] = relationship("Specialization", back_populates="doctors",
                                                            lazy="joined")


class Specialization(Base):
    __tablename__ = "specializations"

    id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str] = mapped_column(Text)
    icon: Mapped[str]
    label: Mapped[str]
    specialization: Mapped[str]

    doctors: Mapped[List["Doctor"]] = relationship(back_populates="specialization")


class Booking(Base):
    __tablename__ = "booking"

    id: Mapped[int] = mapped_column(primary_key=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    day_booking: Mapped[date] = mapped_column(nullable=False)
    time_booking: Mapped[time] = mapped_column(nullable=False)
    booking_status: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # Relationships
    doctor: Mapped["Doctor"] = relationship(back_populates="bookings")
    user: Mapped["User"] = relationship(back_populates="bookings")

```


Если читали мои статьи по SQLAlchemy, то должно быть всё понятно. Единственное, обратите внимание на связи между таблицами (relationship). Они нам пригодятся на этапе создания методов для взаимодействия с этими таблицами.

Теперь превратим эти модели в реальные таблицы. Для этого мы воспользуемся инструментом Alembic, который установили ранее.

### Настройка Alembic и создание первой миграции

Для начала переходим в директорию `app`. В терминале вводите:

```
cd app
```


Инициализируем Alembic с асинхронной поддержкой базы данных:

```
alembic init -t async migration
```


После выполнения команды появится папка `migration` и файл `alembic.ini`. Переместите `alembic.ini` в корневую директорию проекта для удобства работы.

#### Настройка файла alembic.ini

Откройте файл `alembic.ini` и измените строку:

```
script_location = migration
```


на:

```
script_location = app/migration
```


Это упрощает использование миграций и запуск проекта из корневой директории.

#### Изменение env.py для подключения к базе данных

Теперь нам нужно внести изменения в файл `app/migration/env.py`, чтобы Alembic мог корректно работать с нашей базой данных. Откройте файл и замените его содержимое следующим образом:

**Было**:

```
import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = None

```


**Стало**:

```
import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
from app.config import database_url
from app.dao.database import Base
from app.dao.models import User, Doctor, Specialization, Booking

config = context.config

config.set_main_option("sqlalchemy.url", database_url)
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

```


Оставшуюся часть файла можно оставить без изменений.

### Создание первой миграции

Перейдите в корневую директорию проекта:

```
cd ../
```


Сгенерируйте файл миграции:

```
alembic revision --autogenerate -m "Initial revision"
```


Примените миграции для создания таблиц в базе данных:

```
alembic upgrade head
```


После выполнения этой команды в корне проекта появится файл `db.sqlite3`, содержащий таблицы `users`, `doctors`, `booking` и `specializations`.

В рамках данного проекта я не буду описывать логику для управления докторами в базе данных и направлениями. Поэтому эту информацию я заполнил отдельно «за кулисами», а сейчас дам пример добавленных данных для докторов и направлений.

#### Пример данных для докторов:

```
{
  "id": 1,
  "first_name": "Иван",
  "patronymic": "Иванович",
  "specialization_id": 1,
  "experience": "лет",
  "last_name": "Иванов",
  "special": "Терапевт",
  "work_experience": 15,
  "description": "Специализируется на диагностике и лечении внутренних болезней. Регулярно проходит курсы повышения квалификации.",
  "photo": "man1.jpg"
}

```


Отдельного внимания тут заслуживает только значение ключа **photo**. Смысл в том, что у нас на стороне FastAPI будут лежать фото, а в колонке **photo** мы будем сохранять только название.

#### Пример данных для специализации:

```
{
  "id": 1,
  "description": "Терапевты нашей клиники помогут вам справиться с общими заболеваниями, предложат индивидуальные рекомендации по лечению и профилактике. Заботьтесь о своем здоровье вместе с профессионалами.",
  "specialization": "Терапевты",
  "label": "Выбрать терапевта",
  "icon": "fas fa-user-md"
}

```


Тут внимания заслуживает только колонка **icon**. Там я храню названия иконок Font Awesome. Это тоже сделано для удобства.

Таблицы **users** и **booking** мы будем заполнять в «боевом режиме» при работе приложения. Если не хотите заполнять всё самостоятельно, то в телеграмм-канале «[Легкий путь в Python](https://t.me/PythonPathMaster)» можно найти как полный исходный код бэкенда, так и пример заполненной базы данных. В базе данных — 10 направлений и 20 докторов.

### Пишем методы для взаимодействия с базой данных

Теперь мы переходим к одному из самых важных и сложных блоков всего нашего проекта — созданию методов для работы с таблицами в базе данных. Для взаимодействия с базой данных я буду использовать класс **BaseDao**, который включает универсальные методы, применимые ко всем таблицам, а также подход с дочерними классами, в которых будут описаны индивидуальные методы, выходящие за рамки универсальной логики.

**Структура проекта**

В папке `app/dao`, в файле `base.py`, мы опишем этот универсальный класс. В отдельных папках микросервисов (например, в папке `api`) будут описаны дочерние классы. Приведу короткий пример файла `app/dao/base.py`, чтобы вы поняли общий подход. Полный код файла вы можете найти в моем [телеграмм канале](https://t.me/PythonPathMaster).

```
from typing import List, Any, TypeVar, Generic
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from sqlalchemy import update as sqlalchemy_update, delete as sqlalchemy_delete, func
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from app.dao.database import Base

# Объявляем типовой параметр T с ограничением, что это наследник Base
T = TypeVar("T", bound=Base)

class BaseDAO(Generic[T]):
    model: type[T]

    @classmethod
    async def find_one_or_none_by_id(cls, data_id: int, session: AsyncSession):
        # Найти запись по ID
        logger.info(f"Поиск {cls.model.__name__} с ID: {data_id}")
        try:
            query = select(cls.model).filter_by(id=data_id)
            result = await session.execute(query)
            record = result.scalar_one_or_none()
            if record:
                logger.info(f"Запись с ID {data_id} найдена.")
            else:
                logger.info(f"Запись с ID {data_id} не найдена.")
            return record
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при поиске записи с ID {data_id}: {e}")
            raise

    @classmethod
    async def find_one_or_none(cls, session: AsyncSession, filters: BaseModel):
        # Найти одну запись по фильтрам
        filter_dict = filters.model_dump(exclude_unset=True)
        logger.info(f"Поиск одной записи {cls.model.__name__} по фильтрам: {filter_dict}")
        try:
            query = select(cls.model).filter_by(**filter_dict)
            result = await session.execute(query)
            record = result.scalar_one_or_none()
            if record:
                logger.info(f"Запись найдена по фильтрам: {filter_dict}")
            else:
                logger.info(f"Запись не найдена по фильтрам: {filter_dict}")
            return record
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при поиске записи по фильтрам {filter_dict}: {e}")
            raise

    @classmethod
    async def add(cls, session: AsyncSession, values: BaseModel):
        # Добавить одну запись
        values_dict = values.model_dump(exclude_unset=True)
        logger.info(f"Добавление записи {cls.model.__name__} с параметрами: {values_dict}")
        new_instance = cls.model(**values_dict)
        session.add(new_instance)
        try:
            await session.flush()
            logger.info(f"Запись {cls.model.__name__} успешно добавлена.")
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Ошибка при добавлении записи: {e}")
            raise e
        return new_instance

```


В методах **BaseDAO** намеренно отсутствуют фиксации (commit) изменений в базе. Это позволяет выполнять несколько операций в рамках одной сессии и фиксировать их одним коммитом при необходимости. В этом проекте вы сможете оценить преимущества такого подхода.

### Использование BaseDAO

Для каждой модели создается дочерний класс, унаследованный от **BaseDAO**. Например:

```
class UserDAO(BaseDAO[User]):
    model = User

```


Это позволяет вызывать методы напрямую:

```
user_info = await UserDAO.find_one_or_none(session=session, filters=filters)

```


Если базовых методов недостаточно, в дочернем классе можно добавлять собственные методы. Все дочерние классы от **BaseDao** будут описаны в файле `app/api/dao.py`.

### Написание индивидуальных методов и создание дочерних классов

Начнем с заполнения файла `app/api/dao.py`. Для начала выполним импорты:

```
from datetime import date, timedelta, datetime, time, timezone
from typing import List
from fastapi import HTTPException
from loguru import logger
from sqlalchemy import select, and_, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from app.dao.base import BaseDAO
from app.dao.models import User, Specialization, Doctor, Booking

```


Теперь опишем два дочерних класса без эксклюзивных методов для удобства вызова:

```
class SpecializationDAO(BaseDAO[Specialization]):
    model = Specialization

class DoctorDAO(BaseDAO[Specialization]):
    model = Doctor

```


Далее подготовим дочерний класс для таблицы пользователей. Он будет простым и будет содержать только один дополнительный метод:

```
class UserDAO(BaseDAO[User]):
    model = User

    @classmethod
    async def get_user_id(cls, session: AsyncSession, telegram_id: int) -&gt; int | None:
        query = select(cls.model.id).filter_by(telegram_id=telegram_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()

```


Этот метод нужен для получения ID пользователя по его `telegram_id`.

### Разбор класса BookingDAO

Остался последний дочерний класс для таблицы записей. Он будет самым сложным и требует более детального разбора. Вот полный класс:

```
class BookingDAO(BaseDAO[Booking]):
    model = Booking

    @classmethod
    async def count_user_booking(cls, session: AsyncSession, user_id: int) -> int:
        query = select(func.count()).where(cls.model.user_id == user_id)
        result = await session.execute(query)
        return result.scalar_one()

    @classmethod
    async def get_user_bookings_with_doctor_info(cls, session: AsyncSession, user_id: int):
        query = (
            select(cls.model)
            .options(joinedload(cls.model.doctor))
            .where(cls.model.user_id == user_id)
            .order_by(cls.model.day_booking, cls.model.time_booking)
        )
        result = await session.execute(query)
        result_draft = result.unique().scalars().all()
        data_list = []
        for info in result_draft:
            data_list.append({
                "id": info.id,
                "day_booking": info.day_booking.strftime("%Y-%m-%d"),
                "time_booking": info.time_booking.strftime("%H:%M"),
                "special": info.doctor.special,
                "doctor_full_name": f"{info.doctor.first_name} {info.doctor.last_name} {info.doctor.patronymic}",
            })
        return data_list

    @classmethod
    def generate_working_hours(cls, start_hour=8, end_hour=20, step_minutes=30) -&gt; List[str]:
        """Генерирует список рабочих часов с заданным интервалом"""
        working_hours = []
        current_time = datetime.strptime(f"{start_hour}:00", "%H:%M")
        end_time = datetime.strptime(f"{end_hour}:00", "%H:%M")

        while current_time &lt;= end_time:
            working_hours.append(current_time.strftime("%H:%M"))
            current_time += timedelta(minutes=step_minutes)

        return working_hours[:-1]

    @classmethod
    async def get_available_slots(
            cls,
            session: AsyncSession,
            doctor_id: int,
            start_date: date
    ) -> dict[str, int | list[dict[str, str | int | list[str]]]]:
        """
        Получает доступные слоты для записи к врачу на неделю вперед, с учетом требований.

        Args:
            session: AsyncSession - сессия базы данных
            doctor_id: int - ID врача
            start_date: date - дата заказа

        Returns:
            List[Dict[str, Union[str, List[str], int]]] - список дней с доступными слотами
        """
        try:
            # Сопоставляем дату с началом недели (понедельник)
            start_of_week = start_date - timedelta(days=start_date.weekday())
            end_of_week = start_of_week + timedelta(days=5)

            # Получаем существующие брони
            query = select(cls.model).where(
                and_(
                    cls.model.doctor_id == doctor_id,
                    cls.model.day_booking &gt;= start_of_week,
                    cls.model.day_booking &lt;= end_of_week
                )
            )
            result = await session.execute(query)
            existing_bookings = result.scalars().all()

            # Получаем список рабочих часов
            working_hours = cls.generate_working_hours()

            # Создаем множество занятых слотов
            booked_slots = {
                (
                    booking.day_booking.isoformat(),
                    booking.time_booking.strftime("%H:%M")
                )
                for booking in existing_bookings
            }

            # Названия дней недели на русском
            week_days_rus = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]

            # Результат
            available_slots = []

            for day_offset in range(6):
                current_date = start_of_week + timedelta(days=day_offset)
                current_date_str = current_date.isoformat()
                day_name_rus = week_days_rus[day_offset]

                # Если текущая дата меньше сегодняшней, слоты пустые
                day_slots = []
                if current_date &gt;= datetime.now().date():
                    for time_str in working_hours:
                        is_available = (current_date_str, time_str) not in booked_slots

                        if current_date == datetime.now().date():
                            slot_time = datetime.strptime(time_str, "%H:%M").time()
                            if slot_time &lt;= datetime.now().time():
                                is_available = False

                        if is_available:
                            day_slots.append(time_str)

                # Добавляем в результат
                available_slots.append({
                    "day": day_name_rus,
                    "date": current_date_str,
                    "slots": day_slots,
                    "total_slots": len(day_slots)
                })

            # Фильтруем дни для переданной даты
            filter_data = [
                day for day in available_slots if
                start_of_week &lt;= datetime.fromisoformat(day["date"]).date() &lt;= end_of_week
            ]

            return {"days": filter_data, "total_week_slots": sum(day["total_slots"] for day in filter_data)}

        except Exception as e:
            # Логирование ошибки
            logger.error(f"Error in get_available_slots: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Error while getting available slots"
            )

    @classmethod
    async def book_appointment(
            cls,
            session: AsyncSession,
            doctor_id: int,
            user_id: int,
            day_booking: date,
            time_booking: time
    ) -> Booking:
        """
        Метод для бронирования записи.

        Args:
            session: AsyncSession - сессия базы данных
            doctor_id: int - ID врача
            user_id: int - ID пользователя
            day_booking: date - дата брони
            time_booking: time - время брони

        Returns:
            Booking - созданная запись
        """
        try:
            today = date.today()
            logger.info(f"today: {today}, day_booking: {day_booking}")
            if day_booking &lt; date.today():
                raise HTTPException(
                    status_code=400,
                    detail="Дата бронирования не может быть меньше сегодняшней даты"
                )

            # Проверяем, что время бронирования в правильном диапазоне и с шагом в 30 минут
            if not (time(8, 0) &lt;= time_booking &lt;= time(19, 30)):
                raise HTTPException(
                    status_code=400,
                    detail="Время бронирования должно быть между 08:00 и 19:30"
                )
            logger.info(f"МИНУТЫ: {time_booking.minute}")
            if time_booking.minute not in [0, 30]:
                raise HTTPException(
                    status_code=400,
                    detail="Время бронирования должно быть на целый час или на 30 минут"
                )

            # Проверяем, что слот не занят
            query = select(cls.model).where(
                and_(
                    cls.model.doctor_id == doctor_id,
                    cls.model.day_booking == day_booking,
                    cls.model.time_booking == time_booking
                )
            )
            result = await session.execute(query)
            existing_booking = result.scalar_one_or_none()

            if existing_booking:
                raise HTTPException(
                    status_code=400,
                    detail="Слот уже забронирован"
                )

            # Создаем новую бронь
            new_booking = cls.model(
                doctor_id=doctor_id,
                user_id=user_id,
                day_booking=day_booking,
                time_booking=time_booking,
                booking_status="confirmed",  # Статус брони
                created_at=datetime.now(timezone.utc)  # Обновлено
            )
            session.add(new_booking)
            await session.flush()
            return new_booking

        except IntegrityError as e:
            logger.error(f"IntegrityError in book_appointment: {str(e)}")
            await session.rollback()
            raise HTTPException(
                status_code=500,
                detail="Ошибка базы данных при создании брони"
            )

```


Класс `BookingDAO` наследуется от универсального класса `BaseDAO` и включает методы для работы с записями на прием к врачу. Рассмотрим его более подробно.

```
class BookingDAO(BaseDAO[Booking]):
    model = Booking

```


#### Основные методы класса

1.  **count\_user\_booking**
    

```
@classmethod
async def count_user_booking(cls, session: AsyncSession, user_id: int) -> int:
    query = select(func.count()).where(cls.model.user_id == user_id)
    result = await session.execute(query)
    return result.scalar_one()

```


Этот метод возвращает количество записей для конкретного пользователя. Он использует SQLAlchemy для выполнения запроса и подсчета количества записей в таблице `Booking`, связанных с данным `user_id`.

2.  **get\_user\_bookings\_with\_doctor\_info**
    

```
@classmethod
async def get_user_bookings_with_doctor_info(cls, session: AsyncSession, user_id: int):

```


Этот метод извлекает все записи пользователя и информацию о врачах, с которыми они связаны. Используется `joinedload`, чтобы избежать N+1 проблемы при загрузке связанных данных о врачах.

3.  **generate\_working\_hours**
    

```
@classmethod
def generate_working_hours(cls, start_hour=8, end_hour=20, step_minutes=30) -> List[str]:
    """Генерирует список рабочих часов с заданным интервалом"""

```


Этот метод создает список доступных рабочих часов врача с заданным шагом (например, каждые 30 минут). Это важно для формирования слотов записи.

4.  **get\_available\_slots**
    

```
@classmethod
async def get_available_slots(
        cls,
        session: AsyncSession,
        doctor_id: int,
        start_date: date
) -&gt; dict[str, int | list[dict[str, str | int | list[str]]]]:
    """
    Получает доступные слоты для записи к врачу на неделю вперед, с учетом требований.
    """
```


Этот метод получает доступные слоты для записи к врачу на неделю вперед. Он учитывает существующие брони и формирует список доступных временных интервалов.

5.  **book\_appointment**
    

```
@classmethod
async def book_appointment(
        cls,
        session: AsyncSession,
        doctor_id: int,
        user_id: int,
        day_booking: date,
        time_booking: time
) -> Booking:
    """
    Метод для бронирования записи.
    """
```


Этот метод отвечает за создание новой записи на прием. Он проверяет корректность даты и времени бронирования и создает новую запись в базе данных.

Таким образом, класс BookingDAO предоставляет все необходимые методы для работы с записями на прием к врачу. Он включает функционал для подсчета записей пользователя, получения информации о записях вместе с данными врачей, генерации рабочих часов и управления доступными слотами для записи.

Таким образом мы подготовили базу данных для работы. Теперь можем приступить к созданию API методов.

Пишем API методы
----------------

Мы продолжим работать с папкой `app/api`. Давайте дополнительно создадим в ней следующие файлы:

*   `api/schemas.py`: файл, в котором будем описывать модели Pydantic (схемы) для нашего проекта.
    
*   `api/router.py`: файл, в котором будем описывать наши API-методы.
    

### Схемы в файле api/schemas.py

Начнем с файла `api/schemas.py`. Там мы опишем сразу схемы как для телеграм-бота, так и для самого API-приложения.

```
from datetime import date, time
from typing import List, Dict
from pydantic import BaseModel, ConfigDict

class BookingRequest(BaseModel):
    doctor_id: int
    user_id: int
    day_booking: date
    time_booking: time

class TelegramIDModel(BaseModel):
    telegram_id: int

    model_config = ConfigDict(from_attributes=True)

class SpecIDModel(BaseModel):
    specialization_id: int

class UserModel(TelegramIDModel):
    username: str | None
    first_name: str | None
    last_name: str | None

class BookingSlot(BaseModel):
    time: str
    isAvailable: bool

class BookingWeek(BaseModel):
    week: Dict[str, List[BookingSlot]]

```


#### Пояснение по моделям

В данном коде мы определили несколько моделей:

*   **BookingRequest**: используется для запроса на запись к врачу, включает идентификаторы врача и пользователя, а также дату и время записи.
    
*   **TelegramIDModel**: модель для хранения идентификатора пользователя в Telegram.
    
*   **SpecIDModel**: модель для хранения идентификатора специальности.
    
*   **UserModel**: расширяет `TelegramIDModel`, добавляя дополнительные поля для имени пользователя.
    
*   **BookingSlot**: представляет временной слот и информацию о его доступности.
    
*   **BookingWeek**: хранит информацию о доступных слотах на неделю.
    

Теперь вернемся к файлу `app/api/router.py`.

### Импорты в файле app/api/router.py

Начнем с импортов:

```
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dao import SpecializationDAO, DoctorDAO, BookingDAO, UserDAO
from app.api.schemas import SpecIDModel, BookingRequest
from app.dao.session_maker_fast_api import db
from app.tg_bot.scheduler_task import schedule_appointment_notification
import pytz

```


Пока на импорт `schedule_appointment_notification` не обращаем внимание. Данный метод мы напишем немного позже. А вот что нас действительно интересует – это строка:

```
from app.dao.session_maker_fast_api import db

```


Благодаря этому импорту у нас появляется возможность управлять подключением к базе данных, используя механизм зависимостей FastAPI. Если коротко, то смысл в том, что обращаясь к нашим эндпоинтам, у нас будет автоматически открываться соединение с базой данных, а после завершения работы – будет происходить автоматическое закрытие сессии.

### Описание файла app/dao/session\_maker\_fast\_api.py

```
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.dao.database import async_session_maker

class DatabaseSession:
    @staticmethod
    async def get_session(commit: bool = False) -&gt; AsyncGenerator[AsyncSession, None]:
        async with async_session_maker() as session:
            try:
                yield session
                if commit:
                    await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    @staticmethod
    async def get_db() -&gt; AsyncGenerator[AsyncSession, None]:
        """Dependency для получения сессии без автоматического коммита"""
        async for session in DatabaseSession.get_session(commit=False):
            yield session

    @staticmethod
    async def get_db_with_commit() -&gt; AsyncGenerator[AsyncSession, None]:
        """Dependency для получения сессии с автоматическим коммитом"""
        async for session in DatabaseSession.get_session(commit=True):
            yield session

# Создаем экземпляр для удобного импорта
db = DatabaseSession()

```


Класс достаточно простой. Если коротко, то основной его смысл – вернуть два метода:

*   **get\_db** – метод, который будет создавать сессию без коммита (полезно когда нам просто нужно получить данные из БД без фиксаций).
    
*   **get\_db\_with\_commit** – метод, который будет выполнять автоматический коммит после завершения логики эндпоинта FastAPI.
    

#### Пример использования

```
@router.get("/items")
async def get_items(session: AsyncSession = Depends(db.get_db)):
    # Используем сессию без автоматического коммита
    ...

@router.post("/items")
async def create_item(session: AsyncSession = Depends(db.get_db_with_commit)):
    # Используем сессию с автоматическим коммитом
    ...

```


### Возвращаемся к файлу api/router.py

Подкинем московское время и инициализируем роутер:

```
MOSCOW_TZ = pytz.timezone("Europe/Moscow")
router = APIRouter()
```


Теперь начнем описывать эндпоинты. Сами эндпоинты будут достаточно простыми за исключением логики фиксации заявки. Начнем писать:

#### Эндпоинты API

```
@router.get("/specialists")
async def get_specialists(session: AsyncSession = Depends(db.get_db)):
    return await SpecializationDAO.find_all(session=session)

```


Этот эндпоинт использует универсальный метод класса `BaseDao` для получения всей информации из указанной таблицы. Для сокращения кода не использовал валидацию исходящих данных, но в «боевой практике» обычно описывается специальная модель Pydantic.

```
@router.get("/doctors/{spec_id}")
async def get_doctors_spec(spec_id: int, session: AsyncSession = Depends(db.get_db)):
    return await DoctorDAO.find_all(session=session,
                                    filters=SpecIDModel(specialization_id=spec_id))

```


Эндпоинт принимает ID направления и возвращает список докторов по направлениям (например список всех терапевтов).

```
@router.get("/doctor/{doctor_id}")
async def get_doctor_by_id(doctor_id: int, session: AsyncSession = Depends(db.get_db)):
    return await DoctorDAO.find_one_or_none_by_id(session=session, data_id=doctor_id)

```


Здесь мы получаем полную информацию по доктору, принимая его ID.

```
@router.get("/booking/available-slots/{doctor_id}")
async def get_available_slots(
        doctor_id: int,
        start_date: date,
        session: AsyncSession = Depends(db.get_db)
):
    return await BookingDAO.get_available_slots(session=session, doctor_id=doctor_id, start_date=start_date)

```


Благодаря этому методу мы получаем информацию о свободных слотах на запись к конкретному доктору на конкретный день. Логику мы описали ранее в классе `BookingDAO`.

Теперь у нас остается всего один эндпоинт нашего API для фиксации записи в базе данных. Для того чтобы реализовать эту логику нам необходимо выполнить предварительную подготовку — а именно написать логику APSCheduler для установки задач на напоминание в указанное время.

#### Общий принцип работы эндпоинта

Общий принцип будет сводиться к следующему:

1.  Эндпоинт получает информацию о том, что нужно выполнить запись.
    
2.  Устанавливается задача на отправку ряда напоминаний.
    
3.  Эндпоинт завершает работу.
    

Благодаря APSCheduler мы сделаем так, чтобы наш эндпоинт только установил задачи и завершил свою работу. Дальнейшая логика отправки уведомлений с напоминанием о записи ляжет уже на сторону APSCheduler.

Вернемся к эндпоинту для фиксации записи, когда реализуем логику нашего телеграмм бота.

### Создаем телеграмм бота на FastAPI + HTTPX

В этом проекте для реализации телеграмм бота мы не будем использовать стандартный Aiogram 3, а напишем все самостоятельно. В этом нам помогут FastAPI и асинхронная библиотека HTTPX. Вся логика будет описана в папке `app/tg_bot`.

#### Структура проекта

Сразу подготовим структуру с пустыми файлами:

```
├── tg_bot/
│   ├── handlers.py            # функции бота (реагирование на команду /start и т.д.)
│   ├── kbs.py                 # клавиатуры бота
│   ├── methods.py             # универсальные методы бота (отправка сообщений, ответ на callback и т.д.)
│   ├── router.py              # основная логика бота
│   └── scheduler_task.py       # задачи по расписанию

```


Задачи по расписанию вынесены в логику бота, так как они будут напрямую связаны с ботом. Поскольку статья не посвящена теме самописных ботов, сейчас кратко пробежимся по элементам и сути подхода.

Если будет интересно, то под запрос я могу написать отдельную статью, где я подробно расскажу о самостоятельной разработке ботов для Telegram без фреймворков и о преимуществах, которые открывает этот подход.

#### Клавиатуры

Начнем с клавиатур:

```
from app.config import settings

main_kb = [
    [{"text": "📅 Мои записи", "callback_data": "booking"}],
    [{"text": "🔖 Записаться", "web_app": {"url": f"{settings.FRONT_SITE}"}}],
    [{"text": "ℹ️ О нас", "callback_data": "about_us"}]
]

back_kb = [
    [{"text": "🏠 Главное меню", "callback_data": "home"}],
    [{"text": "🔖 Записаться", "web_app": {"url": f"{settings.FRONT_SITE}"}}]
]

def generate_kb_profile(user_db_id: int, count_booking: int):
    kb_profile = [
        [{"text": "🏠 Главное меню", "callback_data": "home"}],
        [{"text": "🔖 Записаться", "web_app": {"url": f"{settings.FRONT_SITE}"}}]
    ]
    if count_booking &gt; 0:
        kb_profile.append([{"text": f"🔒 Мои записи ({count_booking})", "callback_data": f"my_booking_{user_db_id}"}])
    return kb_profile

```


Здесь описана главная клавиатура, клавиатура «в главное меню» и клавиатура внутри профиля в боте. Использованы только инлайн-клавиатуры.

#### Универсальные методы

Теперь опишем универсальные методы нашего бота в файле `tg_bot/methods.py`.

Выполним импорты:

```
from datetime import datetime
from httpx import AsyncClient
from app.config import settings

```


`AsyncClient` импортирован для аннотаций. Начнем с методов.

```
async def bot_send_message(client: AsyncClient, chat_id: int, text: str, kb: list | None = None):
    send_data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if kb:
        send_data["reply_markup"] = {"inline_keyboard": kb}
    await client.post(f"{settings.get_tg_api_url()}/sendMessage", json=send_data)

```


Этот универсальный метод позволяет отправлять сообщение пользователю с инлайн клавиатурой или без нее. В написании этого кода вдохновлялся методом `bot.send_message` из Aiogram 3.

Что касается Aiogram 3, то в [моём профиле на Хабре](https://habr.com/ru/users/yakvenalex/publications/articles/) есть около десяти публикаций, посвящённых этому Python-фреймворку, который был создан для удобной разработки Telegram-ботов. В своих статьях я подробно рассмотрел все аспекты этого инструмента.

```
async def call_answer(client: AsyncClient, callback_query_id: int, text: str):
    await client.post(f"{settings.get_tg_api_url()}/answerCallbackQuery", json={
        "callback_query_id": callback_query_id,
        "text": text
    })

```


Метод для ответа на callback. Аналог `call.answer()` из Aiogram 3.

Далее идут несколько методов для генерации текстовых сообщений с f-строками и метод для генерации информации по записи. Вот метод:

```
def format_appointment(appointment, start_text="🗓 <b>Запись на прием</b>"):
    appointment_date = datetime.strptime(appointment['day_booking'], '%Y-%m-%d').strftime('%d.%m.%Y')
    return f"""
{start_text}

📅 Дата: {appointment_date}
🕒 Время: {appointment['time_booking']}
👨‍⚕️ Врач: {appointment['doctor_full_name']}
🏥 Специализация: {appointment['special']}

ℹ️ Номер записи: {appointment['id']}

Пожалуйста, приходите за 10-15 минут до назначенного времени.
"""

```


#### Хендлеры бота

Теперь мы можем описать хендлеры бота в файле `tg_bot/handlers.py`. Выполним импорты:

```
from httpx import AsyncClient
from app.api.dao import UserDAO, BookingDAO
from app.api.schemas import TelegramIDModel, UserModel
from app.tg_bot.kbs import back_kb, main_kb, generate_kb_profile
from app.tg_bot.methods import call_answer, bot_send_message, get_greeting_text, get_about_text, get_booking_text, format_appointment

```


Опишем первый хендлер, который будет реагировать на команду `/start`:

```
async def cmd_start(client: AsyncClient, session, user_info):
    user_in_db = await UserDAO.find_one_or_none(session=session, filters=TelegramIDModel(telegram_id=user_info["id"]))

    if not user_in_db:
        # Добавляем нового пользователя
        values = UserModel(
            telegram_id=user_info["id"],
            username=user_info.get("username"),
            first_name=user_info.get("first_name"),
            last_name=user_info.get("last_name")
        )
        await UserDAO.add(session=session, values=values)

    greeting_message = get_greeting_text(user_info.get("first_name"))
    await bot_send_message(client, user_info["id"], greeting_message, main_kb)

```


Данный хендлер принимает следующие ключевые аргументы:

*   **client**: клиент (сессия), связанная с подключениями.
    
*   **session**: сессия для взаимодействия с базой данных.
    
*   **user\_info**: информация о пользователе.
    

Далее идет стандартная логика записи пользователя в базу данных при его отсутствии и отправка приветственного сообщения.

```
async def handler_back_home(client: AsyncClient, callback_query_id: int, chat_id: int):
    await call_answer(client, callback_query_id, "Главное меню")
    await bot_send_message(client, chat_id, "Вы на главной странице!", main_kb)

```


Этот хендлер срабатывает при нажатии на кнопку «Главное меню».

```
async def handler_about_us(client: AsyncClient, callback_query_id: int, chat_id: int):
    await call_answer(client, callback_query_id, "О нас")
    about_us_text = get_about_text()
    await bot_send_message(client, chat_id, about_us_text, back_kb)

```


Этот хендлер возвращает пользователю текст «О нас».

```
async def handler_my_appointments(client: AsyncClient, callback_query_id: int, chat_id: int, session):
    await call_answer(client, callback_query_id, "Ваши записи к врачам")
    db_user_id = await UserDAO.get_user_id(session=session, telegram_id=chat_id)
    appointment_count = await BookingDAO.count_user_booking(session=session, user_id=db_user_id)
    message_text = get_booking_text(appointment_count)
    keyboard = generate_kb_profile(db_user_id, appointment_count)
    await bot_send_message(client, chat_id, message_text, kb=keyboard)

```


Этот хендлер вызывается при нажатии на кнопку «Мои записи». Сначала мы отвечаем на callback и получаем ID пользователя для извлечения количества записей.

```
async def handler_my_appointments_all(client: AsyncClient,
                                      callback_query_id: int,
                                      chat_id: int,
                                      user_db_id: int,
                                      session):
    await call_answer(client, callback_query_id, "Ваши записи к врачам (подробно)")
    appointments = await BookingDAO.get_user_bookings_with_doctor_info(session=session, user_id=user_db_id)

    for appointment in appointments:
        await bot_send_message(client, chat_id, format_appointment(appointment))

    await bot_send_message(client, chat_id, "Это все ваши текущие записи.", main_kb)

```


Этот хендлер возвращает информацию по всем записям пользователя. Как видно из примеров выше, хендлеры достаточно простые. Именно поэтому я решил не использовать Aiogram 3 и показать как подобное можно описать самостоятельно.

#### Основной API-эндпоинт

Теперь мы можем описать наш основной API-эндпоинт в файле `tg_bot/router.py`.

Выполним импорты:

```
from fastapi import APIRouter, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.async_client import http_client_manager
from app.dao.session_maker_fast_api import db
from app.tg_bot.handlers import cmd_start, handler_my_appointments,\
     handler_about_us,\
     handler_back_home,\
     handler_my_appointments_all

```


Инициируем роутер:

```
router = APIRouter()

```


Теперь опишем полный код веб-хука:

```
@router.post("/webhook")
async def webhook(request: Request, session: AsyncSession = Depends(db.get_db_with_commit)):
    data = await request.json()
    client = http_client_manager.get_client()

    if "message" in data and "text" in data["message"]:
        if data["message"]["text"] == "/start":
            await cmd_start(client=client,
                             session=session,
                             user_info=data["message"]["from"])

    elif "callback_query" in data:
        callback_query = data["callback_query"]
        callback_query_id = callback_query["id"]
        chat_id = callback_query["message"]["chat"]["id"]
        callback_data: str = callback_query["data"]

        if callback_data.startswith('my_booking_'):
            await handler_my_appointments_all(client=client,
                                              callback_query_id=callback_query_id,
                                              chat_id=chat_id,
                                              session=session,
                                              user_db_id=int(callback_data.replace('my_booking_', '')))
        else:
            if callback_data == "booking":
                await handler_my_appointments(client=client,
                                              callback_query_id=callback_query_id,
                                              chat_id=chat_id,
                                              session=session)
            elif callback_data == "about_us":
                await handler_about_us(client=client,
                                       callback_query_id=callback_query_id,
                                       chat_id=chat_id)
            elif callback_data == "home":
                await handler_back_home(client=client,
                                        callback_query_id=callback_query_id,
                                        chat_id=chat_id)

    return {"ok": True}

```


Это обычный эндпоинт FastAPI для обработки POST запросов по адресу `/webhook`. Строка `data = await request.json()` получает информацию от сервера Telegram о произошедших событиях в нашем боте. Далее мы реагируем на сообщение соответствующим хендлером.

Для работы нам необходимо получить асинхронный клиент HTTPX:

```
client = http_client_manager.get_client()

```


Далее идет ответ в зависимости от типа информации от Telegram. Обязательно завершаем возвратом `{"ok": True}`, чтобы Telegram понял что все прошло успешно.

### Настраиваем задачи по расписанию через APSCheduler

В этой главе мы рассмотрим, как настроить задачи по расписанию с использованием APSCheduler. Мы будем работать с файлом `tg_bot/scheduler_task.py`.

#### Импорты

Начнем с необходимых импортов:

```
from loguru import logger
from app.async_client import http_client_manager
from app.config import scheduler
from app.tg_bot.methods import bot_send_message, format_appointment
from datetime import datetime

```


#### Функция отправки уведомлений

Далее опишем функцию, которая будет выполнять отправку уведомления пользователю:

```
async def send_user_noti(user_tg_id: int, appointment: dict):
    client = http_client_manager.get_client()
    text = format_appointment(appointment, start_text="❗ Напоминаем, что у вас назначена запись к доктору ❗")
    try:
        await bot_send_message(client=client, chat_id=user_tg_id, text=text)
    except Exception as e:
        logger.error(e)

```


Функция достаточно проста. На вход она принимает Telegram ID пользователя и информацию по его заявке, после чего пытается отправить ему уведомление.

#### Логика планирования задач

Теперь нам нужно описать логику, которая позволит поставить эту задачу в расписание. То есть сделать так, чтобы наша система понимала, что нужно выполнить это действие с определенным пользователем в указанное время.

```
async def schedule_appointment_notification(user_tg_id: int, appointment: dict, notification_time: datetime,
                                            reminder_label: str):
    """
    Планирует напоминание с уникальным job_id для каждого случая.

    :param user_tg_id: ID пользователя Telegram
    :param appointment: Данные о записи
    :param notification_time: Время напоминания
    :param reminder_label: Уникальный идентификатор напоминания (например, 'immediate', '24h', '6h', '30min')
    """
    # Уникальный идентификатор задания
    job_id = f"notification_{user_tg_id}_{appointment['id']}_{reminder_label}"

    # Планируем задание
    scheduler.add_job(
        send_user_noti,
        'date',
        run_date=notification_time,
        args=[user_tg_id, appointment],
        id=job_id,
        replace_existing=True
    )

```


Как видите, для планирования задания я использовал метод APSCheduler – `add_job`.

Данный метод принимает:

*   **Функцию**, которую нужно выполнить.
    
*   **Тип запуска** (в моем случае это «date»).
    
*   **Время запуска задачи**.
    
*   **Необходимые аргументы**.
    
*   **ID задачи**.
    
*   **Флаг**, указывающий на то, чтобы происходила перезапись задач с одинаковыми ID. Это необходимо для избежания ошибок при накладках по ID.
    

#### Общая концепция

Теперь давайте разберемся с общей концепцией. В чем суть?

При формировании записи к доктору наш другой API эндпоинт, который мы скоро опишем, будет не только фиксировать данные в базе данных, но и сразу устанавливать задачи к выполнению. Ключевым элементом здесь будет ID задачи. После установки задачи ей будет присвоен уникальный идентификатор, который будет записан в хранилище задач APSCheduler.

Напоминаю, что мы настроили хранилище как SQLite базу данных. Сама база данных будет создана APSCheduler автоматически.

Таким образом, используя APSCheduler и описанные функции, мы можем эффективно управлять задачами по расписанию и обеспечивать своевременную отправку уведомлений пользователям о запланированных встречах с врачами.

### Создание эндпоинта для регистрации записей к докторам

Теперь мы можем вернуться к файлу `api/router.py` и описать эндпоинт для регистрации записи к врачу. Ниже представлен полный код, после чего мы разберем его:

```
@router.post("/book")
async def book_appointment_and_schedule_notifications(
        booking_request: BookingRequest, session: AsyncSession = Depends(db.get_db_with_commit)
):
    """
    Эндпоинт для бронирования записи и планирования уведомлений.
    """
    try:
        # Получение user_id по Telegram ID
        user_id = await UserDAO.get_user_id(session=session, telegram_id=booking_request.user_id)

        # Создание брони в базе данных
        appointment = await BookingDAO.book_appointment(
            session=session,
            doctor_id=booking_request.doctor_id,
            user_id=user_id,
            day_booking=booking_request.day_booking,
            time_booking=booking_request.time_booking
        )
        doctor_info = await DoctorDAO.find_one_or_none_by_id(session=session, data_id=booking_request.doctor_id)

        # Формирование объекта appointment для уведомлений
        appointment_details = {
            'id': appointment.id,
            'day_booking': appointment.day_booking.strftime("%Y-%m-%d"),
            'time_booking': appointment.time_booking.strftime("%H:%M"),
            'special': doctor_info.special,
            'doctor_full_name': f'{doctor_info.first_name} {doctor_info.last_name} {doctor_info.patronymic}'
        }

        # Расчет времени напоминаний
        booking_time_str = f"{appointment_details['day_booking']} {appointment_details['time_booking']}"
        booking_time = datetime.strptime(booking_time_str, "%Y-%m-%d %H:%M").replace(tzinfo=MOSCOW_TZ)
        now = datetime.now(MOSCOW_TZ)
        notification_times = []

        # Напоминание 1: Сразу
        await schedule_appointment_notification(
            user_tg_id=booking_request.user_id,
            appointment=appointment_details,
            notification_time=now,
            reminder_label="immediate"
        )
        notification_times.append(now)

        # Напоминание 2: За сутки
        time_24h = booking_time - timedelta(hours=24)
        if time_24h &gt; now:
            await schedule_appointment_notification(
                user_tg_id=booking_request.user_id,
                appointment=appointment_details,
                notification_time=time_24h,
                reminder_label="24h"
            )
            notification_times.append(time_24h)

        # Напоминание 3: За 6 часов
        time_6h = booking_time - timedelta(hours=6)
        if time_6h &gt; now:
            await schedule_appointment_notification(
                user_tg_id=booking_request.user_id,
                appointment=appointment_details,
                notification_time=time_6h,
                reminder_label="6h"
            )
            notification_times.append(time_6h)

        # Напоминание 4: За 30 минут
        time_30min = booking_time - timedelta(minutes=30)
        if time_30min &gt; now:
            await schedule_appointment_notification(
                user_tg_id=booking_request.user_id,
                appointment=appointment_details,
                notification_time=time_30min,
                reminder_label="30min"
            )
            notification_times.append(time_30min)

        # Форматирование времени уведомлений для ответа
        notification_times_formatted = [time.strftime("%Y-%m-%d %H:%M:%S") for time in notification_times]

        return {
            "status": "SUCCESS",
            "message": "Запись успешно создана и напоминания запланированы!",
            "appointment": appointment_details,
            "notification_times": notification_times_formatted
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error in book_appointment_and_schedule_notifications endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при создании брони и планировании уведомлений"
        )

```


### Логика работы эндпоинта

Если вы внимательно прочитали предыдущее описание и разобрались в коде, то у вас не должно возникнуть вопросов по логике этого эндпоинта. Вкратце, мы проходим следующие этапы:

1.  Получаем ID пользователя по его Telegram ID.
    
2.  Выполняем запись в базу данных.
    
3.  Получаем полную информацию о докторе.
    
4.  Формируем объект для уведомлений.
    
5.  Рассчитываем время для напоминаний. По каждой заявке будет минимум одно напоминание и максимум четыре.
    
6.  Возвращаем ответ, если все прошло успешно.
    

### Установка задач по расписанию

Внимание заслуживает то, как мы устанавливаем задачи по расписанию. Суть сводится к тому, что мы просто вызываем заранее подготовленную функцию с необходимыми параметрами и «забываем» об этом, так как FastAPI больше не нужно помнить о задачах — он их уже поставил. Далее APScheduler займется их выполнением.

Таким образом, мы закрыли достаточно сложную логику бэкенда, и далее нам останется только корректно запустить нашу систему, о чем мы поговорим уже в следующей главе.

### Запуск бэкенда с Telegram-ботом

В этой главе мы рассмотрим, как настроить бэкенд для работы с Telegram-ботом. Нам необходимо сделать так, чтобы Telegram начал отправлять уведомления об обновлениях в нашем боте. Для этого мы должны стать «видимыми» и «безопасными».

#### Подготовка к работе

Чтобы Telegram мог отправлять запросы на наш сервер (наше FastAPI приложение), нам нужно создать техническую возможность для этого. На этапе разработки мы можем использовать туннель на своем локальном компьютере, а после деплоя — постоянное доменное имя, которое нам предоставит [Amvera Cloud](https://amvera.ru/?utm_source=habr&utm_medium=article&utm_campaign=yakvenalex_vue_fast_api_part_1) или собственное доменное имя, которое вы купите у любого регистратора.

Важно, чтобы туннель (доменное имя) поддерживал HTTPS-протокол, так как Telegram не будет доверять соединениям без него и не отправит обновления.

Для туннелирования на локальной машине можно использовать такие сервисы, как NGROK, TUNA или аналогичные.

Проведу демонстрацию на примере сервиса NGROK.

#### Установка NGROK

1.  Перейдите на [официальный сайт NGROK](https://ngrok.com/).
    
2.  Зарегистрируйтесь и войдите в свой профиль.
    
3.  Перейдите на вкладку установки и выберите вашу операционную систему (например, Windows).
    
4.  Скачайте установочный файл и выполните установку.
    
5.  Скопируйте строку с токеном авторизации из вашего профиля — она понадобится для настройки.
    
6.  Запустите NGROK командой:
    

```
ngrok http 8000
```


Здесь `8000` — порт, на котором будет работать ваш веб-сервер. Вы можете указать другой порт.

После успешного запуска NGROK выдаст ссылку вида `https://&lt;ваш-домен&gt;.ngrok.io`. На этапе разработки используйте её как временное доменное имя.

Полученную ссылку установите в файле `.env` в качестве значения переменной для `BASE_SITE`.

#### Настройка файла app/main.py

Теперь перейдем к настройке файла `app/main.py`. Начнем с импортов:

```
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from fastapi.staticfiles import StaticFiles
from app.api.router import router as router_api
from app.async_client import http_client_manager
from app.config import settings, scheduler
from app.tg_bot.router import router as router_tg_bot

```


Теперь напишем функцию, которая будет устанавливать вебхук со стороны серверов Telegram:

```
async def set_webhook(client):
    """Устанавливает вебхук для Telegram-бота."""
    try:
        response = await client.post(f"{settings.get_tg_api_url()}/setWebhook", json={
            "url": settings.get_webhook_url()
        })
        response_data = response.json()
        if response.status_code == 200 and response_data.get("ok"):
            logger.info(f"Webhook установлен: {response_data}")
        else:
            logger.error(f"Ошибка при установке вебхука: {response_data}")
    except Exception as e:
        logger.exception(f"Не удалось установить вебхук: {e}")

```


После запуска этой функции сервера Telegram узнают, что мы хотим получать обновления на конкретный эндпоинт. Если ответ «ok», это означает, что хук установлен, и Telegram знает, куда отправлять обновления.

Далее напишем простую функцию, с помощью которой администраторы будут получать сообщения о запуске и остановке бота:

```
async def send_admin_msg(client, text):
    for admin in settings.ADMIN_IDS:
        try:
            await client.post(f"{settings.get_tg_api_url()}/sendMessage",
                              json={"chat_id": admin, "text": text, "parse_mode": "HTML"})
        except Exception as E:
            logger.exception(f"Ошибка при отправке сообщения админу: {E}")

```


#### Жизненный цикл приложения FastAPI

Теперь, используя жизненный цикл FastAPI, мы сделаем так, чтобы при запуске приложения происходило следующее:

1.  Инициировался клиент HTTPX.
    
2.  Запускался scheduler.
    
3.  Пробрасывался вебхук.
    
4.  Устанавливалось командное меню с командой `/start`.
    
5.  Администраторы получали сообщение о том, что бот запущен.
    

После остановки работы приложения сделаем так, чтобы:

1.  Администраторы получали сообщение о том, что бот остановлен.
    
2.  Мы разрывали соединение через HTTPX.
    
3.  Мы останавливали scheduler.
    

Вот реализация:

```
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Контекстный менеджер для настройки и завершения работы бота."""
    client = http_client_manager.get_client()
    logger.info("Настройка бота...")
    scheduler.start()
    await set_webhook(client)
    await client.post(f"{settings.get_tg_api_url()}/setMyCommands",
                      data={"commands": json.dumps([{"command": "start", "description": "Главное меню"}])})
    await send_admin_msg(client, "Бот запущен!")
    yield
    logger.info("Завершение работы бота...")
    await send_admin_msg(client, "Бот остановлен!")
    await http_client_manager.close_client()
    scheduler.shutdown()

```


Теперь инициируем приложение FastAPI, подключив к нему функцию жизненного цикла:

```
app = FastAPI(lifespan=lifespan)
```


#### Обработчик статических файлов

Подключим к нашему приложению обработчик статических файлов:

```
app.mount('/static', StaticFiles(directory='app/static'), name='static')
```


Это необходимо для хранения фотографий докторов на стороне бэкенда, а не на стороне фронтенда. Для корректной работы создайте папку `static` внутри папки `app`, а внутри неё — папку `images`, куда поместите фото всех докторов. После подключения доступ к каждому фото будет осуществляться через `/static/images/photo.jpg`.

#### Настройка CORS

Добавим Middleware для CORS:

```
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешаем все источники
    allow_credentials=True,
    allow_methods=["*"],  # Разрешаем все методы
    allow_headers=["*"],  # Разрешаем все заголовки
)

```


#### Регистрация роутеров

Теперь остается зарегистрировать роутеры Telegram-бота и API:

```
app.include_router(router_api)
app.include_router(router_tg_bot)

```


#### Запуск бота

Теперь можно запустить бота. Для этого в корне проекта введите команду:

```
uvicorn app.main:app --reload --port 8000

```


Проверьте, чтобы порт соответствовал порту, который вы указали при запуске туннеля на локальной машине. Кроме того, убедитесь что перед запуском FastApi приложения вы кликнули на /start в боте и указали свой телеграмм айди в списке `ADMIN_IDS` файла `.env`.

Иначе бот после запуска не сможет отправить вам сообщение об успешном запуске.

### Тестирование перед деплоем

Перед тем как перейти к этапу деплоя, важно провести тщательное тестирование нашего API и Telegram-бота. Несмотря на то, что фронтенд-часть еще не реализована, вся остальная логика должна функционировать корректно.

#### Тестирование API

Для тестирования методов API мы можем воспользоваться автоматически сгенерированной документацией вашего FastAPI приложения. Для этого просто перейдите по адресу `/docs`.

В этом интерфейсе вы увидите все доступные методы, которые можно протестировать вручную. Это позволит убедиться в правильности работы каждого эндпоинта и его функциональности.

![Документация с API-методами](https://habrastorage.org/r/w1560/getpro/habr/upload_files/682/dc7/7b5/682dc77b5012b58a752438d6e5c2138b.png "Документация с API-методами")

Документация с API-методами

#### Тестирование Telegram-бота

Что касается Telegram-бота, то на данный момент он должен выполнять следующие действия:

*   **Регистрация пользователя**: После ввода команды `/start` бот должен зарегистрировать пользователя в базе данных.
    

![](https://habrastorage.org/r/w1560/getpro/habr/upload_files/228/4ce/ae2/2284ceae2555cf227d7248a2800ae1fc.png)

*   **Приветственное сообщение**: Бот должен отправить приветственное сообщение с инлайн-клавиатурой, чтобы пользователи могли легко взаимодействовать с ним.
    
*   **Кнопка «О нас»**: При нажатии на кнопку «О нас» бот должен предоставить текст о клинике, информируя пользователей о ее услугах и особенностях.
    

![](https://habrastorage.org/r/w1560/getpro/habr/upload_files/89b/639/71e/89b63971e59f8873d3c09aa4e56d97da.png)

*   Кнопка «Мои записи»: При нажатии на эту кнопку бот должен уведомить вас о том, что записей пока нет. Это вполне нормально для начального этапа использования. В моём случае, после добавления записей к врачам, профиль принял следующий вид:
    

![](https://habrastorage.org/r/w1560/getpro/habr/upload_files/781/55d/465/78155d46512b263d23409b94209c0429.png)

Только после успешного тестирования всех этих блоков можно переходить к этапу деплоя.

### Деплой проекта в Amvera Cloud

Теперь мы готовы к удаленному запуску нашего FastApi приложения, и для этого воспользуемся сервисом [**Amvera Cloud**](https://amvera.ru/?utm_source=habr&utm_medium=article&utm_campaign=yakvenalex_vue_fast_api_part_1).

**Шаг 1: Остановка FastAPI проекта**

Первым делом необходимо остановить FastAPI приложение на локальной машине.

**Шаг 2: Создание конфигурационного файла**

После остановки, в корне проекта создайте конфигурационный файл для запуска на удаленном сервере Amvera. Назовите его `amvera.yml` и заполните следующим образом:

```
meta:
  environment: python
  toolchain:
    name: pip
    version: 3.12
build:
  requirementsPath: requirements.txt
run:
  persistenceMount: /data
  containerPort: 8000
  command: uvicorn app.main:app --host 0.0.0.0 --port 8000

```


Этот файл сообщает сервису Amvera, как запускать наше приложение.

Особое внимание обратите на строку: `persistenceMount: /data`. После деплоя проверьте чтоб файлы базы данных находились именно в папке /data, так как это будет важно при обновлениях проекта если они потребуются.

**Шаг 3: Процесс деплоя**

Сам деплой будет включать в себя следующие шаги:

1.  Создайте новый проект в [Amvera Cloud.](https://amvera.ru/?utm_source=habr&utm_medium=article&utm_campaign=yakvenalex_vue_fast_api_part_1)
    
2.  Загрузите файлы FastAPI приложения (это можно сделать через веб-интерфейс или с помощью команд GIT).
    
3.  Привяжите к проекту бесплатное доменное имя HTTPS (это одна из особенностей Amvera).
    

Перед тем как приступить к развертыванию, необходимо зарегистрироваться на сервисе Amvera Cloud, если вы ещё не сделали этого. Новые пользователи получают 111 рублей на основной баланс, что вполне достаточно для ознакомления с возможностями сервиса.

#### Пошаговая инструкция

1.  **Создание проекта**
    

*   Заходим в личный кабинет. После кликаем на "Создать проект". Дайте проекту имя, выберите тип приложения (не база данных) и нажмите "Далее".
    

2.  **Загрузка файлов**
    

*   На следующем экране вы увидите инструкции по загрузке файлов через GIT и вкладку «Через интерфейс». Я выбрал второй вариант и просто перетащил файлы проекта. После этого нажмите "Далее".
    

3.  **Проверка настроек**
    

*   Убедитесь, что все настройки введены корректно; если нет, внесите изменения прямо на этом экране и нажмите "Завершить".
    

4.  **Привязка доменного имени**
    

*   Привяжите бесплатное доменное имя к вашему проекту (вы также можете использовать собственное доменное имя, это делается всего за пару кликов).
    

#### Добавление доменного имени

1.  Перейдите в созданный проект FastAPI.
    
2.  Кликните на «Настройки».
    
3.  Привяжите доменное имя, как показано на скриншоте ниже.
    

![](https://habrastorage.org/r/w1560/getpro/habr/upload_files/561/9b3/013/5619b3013856a79a479b4352f6da8ab8.png)

Если вам необходимо, вы можете связать собственное доменное имя с вашим проектом на том же экране. Для этого выберите опцию "Свой домен" и следуйте инструкциям. Важно отметить, что Amvera автоматически установит HTTPS-протокол для вашего доменного имени.

Теперь необходимо поработать с файлом .env. Мы сейчас получили постоянное доменное имя. Его необходимо установить в качестве значения переменной BASE\_SITE. В моем случае получилось так:

```
BASE_SITE=https://vue3fastapi-yakvenalex.amvera.io
```


Теперь переключитесь на вкладку «Репозиторий», удалите старый файл `.env` и загрузите обновленный файл с переменной `BASE_SITE`. Затем нажмите кнопку «Пересобрать проект» (верхняя стрелка на скриншоте). Через 2-3 минуты ваше приложение должно запуститься, и вы получите уведомление от бота о его запуске.

![](https://habrastorage.org/r/w1560/getpro/habr/upload_files/d26/190/3a7/d261903a7d87fcdb19e7cf3fc971dd23.png)

Поздравляю! Через пару минут ваш проект автоматически запустится, и вы будете готовы к созданию фронтенда, о чём мы поговорим в следующей статье.

Не забудьте протестировать API после деплоя!

Поклацать бота самостоятельно можно тут: [Vue3 FastApi](https://t.me/Vue3_FastApiBOT).

#### Заключение

Сегодня мы проделали значительную работу, разработав мощный и универсальный бэкенд. Примечательно, что созданный API идеально подходит не только для связки с приложением на **Vue.js 3**, которое мы будем разрабатывать в следующей статье, но и для любых других фронтенд-решений. Этот API легко интегрируется с любыми технологиями — будь то **React**, **Angular**, мобильные приложения или десктопные программы.

Особое внимание стоит уделить теме создания Telegram-бота на основе чистого **Telegram Bot API**. Мы настроили взаимодействие с ботом без использования готовых решений вроде **Aiogram 3**. Кроме того, я показал вам оригинальный способ связки Telegram-бота и **FastAPI**: в нашем проекте бот — это всего лишь один POST-эндпоинт, который получает обновления напрямую от серверов Telegram.

Еще одна важная часть работы — интеграция задач по расписанию с использованием **APScheduler**. Как вы могли заметить, всего несколько строк кода позволили нам добавить мощную логику для отправки уведомлений через бота.

В конце статьи мы развернули проект на платформе [Amvera Cloud](https://amvera.ru/?utm_source=habr&utm_medium=article&utm_campaign=yakvenalex_vue_fast_api_part_1), что позволило полностью завершить разработку бэкенда и подготовить все необходимое для реализации фронтенд-части.

Понимаю, что изложенный материал может показаться сложным. Если у вас остались вопросы, смело задавайте их в комментариях или в моем сообществе в Telegram.

Напоминаю, что в сообществе **«**[**Легкий путь в Python**](https://t.me/PythonPathMaster)**»** вы найдете не только поддержку единомышленников, но и полный исходный код проекта (как фронтенд, так и бэкенд). Более того, там доступен дополнительный эксклюзивный контент, который нигде больше не публикуется.

Если статья была для вас полезной, поддержите её лайком и комментарием. Обратная связь показывает, насколько вам интересны такие материалы. Отсутствие реакции станет для меня сигналом, что подобный формат не востребован, и это может повлиять на будущее подобных публикаций.

На этом всё. До встречи во второй части, где мы визуализируем наш API с помощью **Vue.js 3**.

Не прощаемся!